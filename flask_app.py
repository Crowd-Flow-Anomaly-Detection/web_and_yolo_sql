from flask import Flask, render_template, jsonify, request, send_file, g
import calendar as cal
from datetime import datetime
import matplotlib.pyplot as plt
import io
import os
import matplotlib
from count_footfall.process import process_video
from flask_cors import CORS

from mysql.connector import MySQLConnection
from app.db.connector import pool
from weather import get_weather_main

matplotlib.use('Agg')

app = Flask(__name__)
CORS(app)

# 影片上傳資料夾
VIDEO_UPLOAD_FOLDER = './clients_video'
#處理完畢後影片的資料夾
OUTPUT_VIDEO_FOLDER = './output'

LAT, LON = 9.5120, 100.0136  # Ko Samui
API_KEY = os.getenv("Weather_API_KEY")

app.config.update({
    'VIDEO_UPLOAD_FOLDER': VIDEO_UPLOAD_FOLDER,
    'OUTPUT_VIDEO_FOLDER': OUTPUT_VIDEO_FOLDER,
})

# 確保上傳資料夾存在
os.makedirs(VIDEO_UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_VIDEO_FOLDER, exist_ok=True)


@app.before_request
def open_db():
    # 1. 先從 pool 拿到 connection
    conn = pool.get_connection()
    # 2. 把 connection & cursor 都存到 g
    g.db_conn = conn
    g.db_cursor = conn.cursor(dictionary=True, buffered=True)

@app.teardown_request
def close_db(exc):
    # 從 g 拿出 cursor & conn
    cursor = getattr(g, 'db_cursor', None)
    conn   = getattr(g, 'db_conn', None)

    if cursor:
        cursor.close()

    if conn:
        # 根據有無 exception 決定 rollback or commit
        if exc:
            conn.rollback()
        else:
            conn.commit()
        conn.close()


# 取得所有人流量數據
@app.route('/api/footfall', methods=['GET'])
def api_get_footfall():
    cursor = g.db_cursor
    # 撈所有日期與對應的時段資料
    cursor.execute("""
        SELECT d.day_date, h.hour_of_day, h.count
        FROM daily_footfall d
        LEFT JOIN hourly_footfall h ON d.id = h.daily_id
        ORDER BY d.day_date, h.hour_of_day
    """)
    rows = cursor.fetchall()

    data = {}
    total = 0
    for row in rows:
        date = row['day_date'].strftime('%Y-%m-%d')
        hour = row['hour_of_day']
        cnt = row['count'] or 0
        if date not in data:
            data[date] = {}
        data[date][str(hour)] = cnt
        total += cnt

    return jsonify({"data": data, "total": total})


# 新增人流量數據
@app.route('/api/footfall', methods=['POST'])
def api_add_footfall():
    data      = request.get_json()
    date_str  = data['date']                   # e.g. "2025-06-19"
    hour      = int(data['hour'])
    footfall  = int(data['footfall'])
    weekday   = datetime.strptime(date_str, "%Y-%m-%d").strftime("%A")
    weather_main = get_weather_main(LAT, LON, API_KEY)

    cursor = g.db_cursor

    # 1. 確保 daily_footfall 有該日期
    cursor.execute(
        """
        INSERT INTO daily_footfall (day_date, weekday, total_count, weather)
        VALUES (%s, %s, 0, %s)
        ON DUPLICATE KEY
          UPDATE id = LAST_INSERT_ID(id)
        """,
        (date_str, weekday, weather_main)
    )
    daily_id = cursor.lastrowid

    # 2. 檢查該小時是否已有資料
    cursor.execute(
        "SELECT 1 FROM hourly_footfall WHERE daily_id = %s AND hour_of_day = %s",
        (daily_id, hour)
    )
    if cursor.fetchone():
        return jsonify({"error": "Footfall data for this date and hour already exists"}), 409

    # 3. 插入新的 hourly_footfall（含 weather）
    cursor.execute(
        """
        INSERT INTO hourly_footfall (daily_id, hour_of_day, count, weather)
        VALUES (%s, %s, %s, %s)
        """,
        (daily_id, hour, footfall, weather_main)
    )

    # 4. 重算並更新 daily_footfall.total_count
    cursor.execute(
        """
        UPDATE daily_footfall d
        SET d.total_count = (
          SELECT COALESCE(SUM(h.count), 0)
          FROM hourly_footfall h
          WHERE h.daily_id = d.id
        )
        WHERE d.id = %s
        """,
        (daily_id,)
    )

    # 5. 重算並更新 daily_footfall.weather：
    #    以「小時筆數最多」的 weather 為當日主要天氣
    cursor.execute(
        """
        SELECT weather, COUNT(*) AS hours_count
        FROM hourly_footfall
        WHERE daily_id = %s
        GROUP BY weather
        ORDER BY hours_count DESC
        LIMIT 1
        """,
        (daily_id,)
    )
    main_weather = cursor.fetchone()['weather']
    cursor.execute(
        "UPDATE daily_footfall SET weather = %s WHERE id = %s",
        (main_weather, daily_id)
    )

    return jsonify({
        "message": "Data added successfully",
        "data": data,
        "hourly_weather": weather_main,
        "daily_weather": main_weather
    }), 201

# 刪除特定日期與小時的人流量（完全移除那一筆）
@app.route('/api/footfall/<date>/<hour>', methods=['DELETE'])
def api_delete_footfall(date, hour):
    hour = int(hour)
    cursor = g.db_cursor

    # 1. 找到 daily_id
    cursor.execute(
        "SELECT id FROM daily_footfall WHERE day_date = %s",
        (date,)
    )
    daily = cursor.fetchone()
    if not daily:
        return jsonify({"error": "Date or hour not found"}), 404
    daily_id = daily['id']

    # 2. 確認該小時資料存在
    cursor.execute("""
        SELECT id
        FROM hourly_footfall
        WHERE daily_id = %s AND hour_of_day = %s
    """, (daily_id, hour))
    hr = cursor.fetchone()
    if not hr:
        return jsonify({"error": "Date or hour not found"}), 404

    # 3. 刪除這一筆 hourly_footfall
    cursor.execute(
        "DELETE FROM hourly_footfall WHERE id = %s",
        (hr['id'],)
    )

    # 4. 重算並更新 daily_footfall.total_count
    cursor.execute("""
        SELECT COALESCE(SUM(count), 0) AS total
        FROM hourly_footfall
        WHERE daily_id = %s
    """, (daily_id,))
    total_cnt = cursor.fetchone()['total']
    cursor.execute(
        "UPDATE daily_footfall SET total_count = %s WHERE id = %s",
        (total_cnt, daily_id)
    )

    return jsonify({
        "message": "Data deleted successfully",
        "date": date,
        "hour": hour
    }), 200

# 刪除單日所有人流量資料（含 hourly_footfall）
@app.route('/api/footfall/<date>', methods=['DELETE'])
def api_delete_footfall_by_date(date):
    cursor = g.db_cursor

    # 1. 確認該日期是否存在
    cursor.execute("SELECT id FROM daily_footfall WHERE day_date = %s", (date,))
    daily = cursor.fetchone()
    if not daily:
        return jsonify({"error": "Date not found"}), 404
    daily_id = daily['id']

    # 2. 刪除該日所有 hourly_footfall
    cursor.execute(
        "DELETE FROM hourly_footfall WHERE daily_id = %s",
        (daily_id,)
    )

    # 3. 刪除 daily_footfall 主紀錄
    cursor.execute(
        "DELETE FROM daily_footfall WHERE id = %s",
        (daily_id,)
    )

    return jsonify({
        "message": "All footfall data for the date has been deleted",
        "date": date
    }), 200



# 取得特定日期小時的人流量
@app.route('/api/footfall/<date>/<hour>', methods=['GET'])
def api_get_footfall_by_date_hour(date, hour):
    hour = int(hour)
    cursor = g.db_cursor
    cursor.execute("""
        SELECT h.count
        FROM hourly_footfall h
        JOIN daily_footfall d ON d.id = h.daily_id
        WHERE d.day_date = %s AND h.hour_of_day = %s
    """, (date, hour))
    row = cursor.fetchone()
    if row and row['count'] != 0:
        return jsonify({"date": date, "hour": hour, "footfall": row['count']})
    else:
        return jsonify({"error": "Date or hour not found"}), 404


# 取得特定日期全天的人流量
@app.route('/api/footfall/<date>', methods=['GET'])
def api_get_footfall_by_date_api(date):
    cursor = g.db_cursor
    cursor.execute("""
        SELECT h.hour_of_day, h.count, h.weather
        FROM hourly_footfall h
        JOIN daily_footfall d ON d.id = h.daily_id
        WHERE d.day_date = %s
        ORDER BY h.hour_of_day
    """, (date,))
    rows = cursor.fetchall()
    if not rows:
        return jsonify({"error": "Date not found"}), 404

    # 把每小時的 count 跟 weather 都包進去
    footfall = {
        str(r['hour_of_day']): {
            "count":   r['count'],
            "weather": r['weather']
        }
        for r in rows
    }
    return jsonify({
        "date":     date,
        "footfall": footfall
    })

# 更新特定日期小時的人流量
@app.route('/api/footfall/<date>/<hour>', methods=['PUT'])
def api_update_footfall(date, hour):
    updated_entry = request.get_json()
    hour          = int(hour)
    new_count     = int(updated_entry['footfall'])

    cursor = g.db_cursor

    # 1. 找 daily_id
    cursor.execute("SELECT id FROM daily_footfall WHERE day_date = %s", (date,))
    daily = cursor.fetchone()
    if not daily:
        return jsonify({"error": "Date not found"}), 404
    daily_id = daily['id']

    # 2. 更新該小時 count
    cursor.execute(
        """
        UPDATE hourly_footfall
        SET count = %s
        WHERE daily_id = %s AND hour_of_day = %s
        """,
        (new_count, daily_id, hour)
    )

    # 3. 重算並更新 daily_footfall.total_count
    cursor.execute(
        """
        UPDATE daily_footfall d
        SET d.total_count = (
          SELECT COALESCE(SUM(h.count), 0)
          FROM hourly_footfall h
          WHERE h.daily_id = d.id
        )
        WHERE d.id = %s
        """,
        (daily_id,)
    )

    # 4. 重算並更新 daily_footfall.weather
    cursor.execute(
        """
        SELECT weather, COUNT(*) AS hours_count
        FROM hourly_footfall
        WHERE daily_id = %s
        GROUP BY weather
        ORDER BY hours_count DESC
        LIMIT 1
        """,
        (daily_id,)
    )
    main_weather = cursor.fetchone()['weather']
    cursor.execute(
        "UPDATE daily_footfall SET weather = %s WHERE id = %s",
        (main_weather, daily_id)
    )

    return jsonify({
        "message": "Data updated successfully",
        "date": date,
        "hour": hour,
        "footfall": new_count,
        "daily_weather": main_weather
    }), 200


# 首頁：月曆檢視
@app.route('/')
def index():
    current_date = datetime.now()
    year = int(request.args.get('year', current_date.year))
    month = int(request.args.get('month', current_date.month))

    cursor = g.db_cursor
    cursor.execute("""
        SELECT DAY(day_date) AS day, total_count
        FROM daily_footfall
        WHERE YEAR(day_date) = %s AND MONTH(day_date) = %s
    """, (year, month))
    rows = cursor.fetchall()

    month_data = {r['day']: r['total_count'] for r in rows}

    cal.setfirstweekday(cal.SUNDAY)
    cal_data = cal.monthcalendar(year, month)

    return render_template('index.html', year=year, month=month, data=month_data, cal=cal_data)


# API：依年月日查詢全天資料
@app.route('/api/footfall/<year>/<month>/<day>', methods=['GET'])
def api_get_footfall_by_date(year, month, day):
    date = f"{year}-{str(month).zfill(2)}-{str(day).zfill(2)}"
    return api_get_footfall_by_date_api(date)


# 生成並返回當日小時分佈圖表
@app.route('/footfall_chart/<year>/<month>/<day>.png')
def footfall_chart(year, month, day):
    date = f"{year}-{str(month).zfill(2)}-{str(day).zfill(2)}"
    cursor = g.db_cursor
    cursor.execute("""
        SELECT h.hour_of_day, h.count
        FROM hourly_footfall h
        JOIN daily_footfall d ON d.id = h.daily_id
        WHERE d.day_date = %s
        ORDER BY h.hour_of_day
    """, (date,))
    rows = cursor.fetchall()
    if not rows:
        return jsonify({"error": "Date not found"}), 404

    # 準備資料
    hours = list(range(24))
    footfall = [0]*24
    for r in rows:
        footfall[r['hour_of_day']] = r['count']

    # 畫圖
    plt.figure(figsize=(10, 6))
    plt.bar(hours, footfall)
    plt.xlabel('Hour')
    plt.ylabel('Footfall')
    plt.title(f'Footfall for {date}')
    plt.xticks(hours)

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()

    return send_file(buf, mimetype='image/png')


# 處理影片上傳
@app.route('/api/upload_video', methods=['POST'])
def upload_video():
    if 'video' not in request.files:
        return jsonify({"error": "No video file uploaded"}), 400

    video = request.files['video']
    if video.filename == '':
        return jsonify({"error": "No video file selected"}), 400

    allowed_extensions = {'.mp4', '.avi', '.mov', '.mkv'}
    ext = os.path.splitext(video.filename)[1].lower()
    if ext not in allowed_extensions:
        return jsonify({"error": "Invalid video file format"}), 400

    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    name = os.path.splitext(video.filename)[0]
    new_filename = f"{name}_{ts}{ext}"
    path = os.path.join(app.config['VIDEO_UPLOAD_FOLDER'], new_filename)
    video.save(path)

    try:
        footfall_count, output_path = process_video(path)
    except Exception as e:
        return jsonify({"error": "Video processing failed", "details": str(e)}), 500

    return jsonify({
        "message": "Video uploaded successfully",
        "file_path": path,
        "footfall": footfall_count,
        "download_url": f"/api/download_video/{output_path}"
    }), 201

# 影片下載
@app.route('/api/download_video/<path:filename>')
def download_video(filename):
    return send_file(
        filename,
        mimetype='video/mp4',
        as_attachment=False,
        conditional=True
    )

#處理後的影片下載 filename 目前是result.mp4
@app.route('/api/download_processed_video/<path:filename>')
def download_processed_video(filename):
    output_path = os.path.join(app.config['OUTPUT_VIDEO_FOLDER'], filename)
    if not os.path.exists(output_path):
        return jsonify({"error": "Processed video not found"}), 404

    return send_file(
        output_path,
        mimetype='video/mp4',
        as_attachment=True,
        conditional=True
    )
    


if __name__ == '__main__':
    app.run(debug=True)
