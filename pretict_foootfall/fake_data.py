#!/usr/bin/env python3
# fake_data_generator.py

import sys
import random
from datetime import datetime, timedelta

import mysql.connector
from mysql.connector import errorcode

import os, sys

# 把上一層目錄（專案根）加到 sys.path
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root not in sys.path:
    sys.path.append(root)

from app.db.connector import pool

# 假設你的天氣種類
WEATHER_OPTIONS = ['Clear', 'Clouds', 'Rain', 'Snow', 'Drizzle', 'Thunderstorm']

def generate_fake_data(start_date: datetime, days: int):
    """
    從 start_date（含）開始往後 days 天，
    每天 0–23 小時插入一筆 hourly_footfall（隨機 count＋weather），
    若 daily_footfall 不存在，先 insert。
    Trigger 會自動幫你更新 daily_footfall.total_count & weather。
    """
    conn = pool.get_connection()
    cursor = conn.cursor()

    for i in range(days):
        d = start_date + timedelta(days=i)
        date_str = d.strftime('%Y-%m-%d')
        weekday  = d.strftime('%A')

        # 1. 確保 daily_footfall 有這天的紀錄
        cursor.execute("""
            INSERT INTO daily_footfall (day_date, weekday, total_count, weather)
            VALUES (%s, %s, 0, '')
            ON DUPLICATE KEY
              UPDATE id = LAST_INSERT_ID(id)
        """, (date_str, weekday))
        # 取回剛剛插入或已存在的 id
        daily_id = cursor.lastrowid

        # 2. 針對每個小時插入一筆隨機資料
        for hr in range(24):
            cnt     = random.randint(0, 500)
            weather = random.choice(WEATHER_OPTIONS)
            try:
                cursor.execute("""
                    INSERT INTO hourly_footfall
                      (daily_id, hour_of_day, count, weather)
                    VALUES (%s, %s, %s, %s)
                """, (daily_id, hr, cnt, weather))
            except mysql.connector.Error as e:
                # 如果已經存在（duplicate），就跳過
                if e.errno == errorcode.ER_DUP_ENTRY:
                    continue
                else:
                    raise

    conn.commit()
    cursor.close()
    conn.close()
    print(f"✅ 已為 {start_date.strftime('%Y-%m-%d')} 起算 {days} 天，生成假資料。")

if __name__ == '__main__':
    # 允許從命令列帶入起始日期與天數
    # 用法： python fake_data_generator.py 2025-01-01 90
    if len(sys.argv) >= 3:
        sd = datetime.strptime(sys.argv[1], '%Y-%m-%d')
        nd = int(sys.argv[2])
    else:
        sd = datetime.today() - timedelta(days=2000)
        nd = 2000

    generate_fake_data(sd, nd)
