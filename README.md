# 智慧型人流分析與預測系統

## 目錄結構

```
.
├── app/
│   ├── core/
│   │   └── config.py              # 設定檔
│   ├── db/
│   │   └── connector.py           # MySQL 連線池設定
├── clients_video/                 # 上傳影片暫存資料夾
├── count_footfall/
│   ├── process.py                 # 影片人流計數主程式
│   ├── sort.py                    # 追蹤演算法
│   ├── yolo-coco/                 # YOLO 模型資料夾
├── output/                        # 處理後影片輸出
├── pretict_foootfall/
│   ├── data_loader.py             # 資料讀取
│   ├── fake_data.py               # 假資料生成
│   ├── predict_single.py          # 單一預測示例
│   ├── test_model.py              # 模型測試
│   ├── train_model.py             # 模型訓練
│   ├── ckpt/                      # 模型檢查點
├── static/                        # 靜態資源
│   ├── script.js                  # 前端互動腳本
│   └── style.css                  # 樣式表
├── templates/                     # 頁面模板
│   └── index.html                 # 月曆檢視頁面
├── .env                           # 環境變數
├── flask_app.py                   # Flask 主程式
├── init_db.py                     # 資料庫初始化
├── requirements.txt               # 相依套件
├── weather.py                     # 天氣資料獲取
└── README.md                      # 專案說明文件
```

這是一個整合了**即時人流計數**、**資料視覺化**與**機器學習預測**的完整系統，適用於零售門市、展覽場館、觀光景點等需要精確人流統計的場所。

## 系統架構


- **前端**：Flask Web 應用 + 視覺化圖表
- **後端**：Flask API + MySQL 資料庫
- **模型**：YOLO 目標偵測 + 線性迴歸預測模型
- **外部整合**：[OpenWeatherMap API](https://openweathermap.org/api)

## 主要功能

### 1️⃣ 人流影片分析
- 上傳影片自動計數經過特定區域的人流
- 支援多種影片格式 (`.mp4`, `.avi`, `.mov`, `.mkv`)
- 即時顯示計數結果並儲存至資料庫

### 2️⃣ 人流資料管理
- 完整的 CRUD API 管理人流資料
- 依日期/時段進行資料查詢與統計
- MySQL 連線池確保高效能資料存取

### 3️⃣ 資料視覺化
- 月曆形式檢視每日總人流
- 單日時段分佈圖
- 天氣資訊整合與顯示

### 4️⃣ 機器學習預測
- 基於歷史人流、天氣資料的預測模型
- 支援未來日期的人流量預測
- 模型效能評估與分析

## 安裝指南

### 前置需求
- Python 3.7+
- MySQL 資料庫
- OpenWeatherMap API 金鑰

### 步驟

1. **安裝相依套件**
   ```bash
   pip install -r requirements.txt
   ```

2. **設定環境變數**
   建立 [`.env`](.env ) 檔案並填入以下資訊：
   ```
   DB_HOST=localhost
   DB_USER=root
   DB_PASSWORD=your_password
   DB_NAME=FOOTFALL
   Weather_API_KEY=your_openweather_api_key
   ```

3. **初始化資料庫**
   ```bash
   python init_db.py
   ```

4. **啟動服務**
   ```bash
   python flask_app.py
   ```

   服務預設於 http://127.0.0.1:5000 運行

## API 文件

| 方法 | 路徑 | 說明 |
|------|------|------|
| GET | `/api/footfall` | 取得所有人流資料 |
| POST | `/api/footfall` | 新增單日單時段人流 |
| GET | `/api/footfall/<date>/<hour>` | 查詢指定日期時段 |
| PUT | `/api/footfall/<date>/<hour>` | 更新指定日期時段 |
| DELETE | `/api/footfall/<date>/<hour>` | 刪除指定日期時段 |
| GET | `/api/footfall/<date>` | 查詢指定日期全天 |
| DELETE | `/api/footfall/<date>` | 刪除指定日期資料 |
| GET | `/api/footfall/<year>/<month>/<day>` | 以年/月/日格式查詢全天 |
| GET | `/footfall_chart/<year>/<month>/<day>.png` | 取得單日分佈圖 |
| POST | `/api/upload_video` | 上傳影片並處理 |
| GET | `/api/download_video/<path>` | 下載處理後影片 |

## API 使用範例

```bash
# 1. 取得所有人流資料
curl -X GET "http://127.0.0.1:5000/api/footfall"

# 2. 新增某日某時段人流
curl -X POST "http://127.0.0.1:5000/api/footfall" -H "Content-Type: application/json" -d "{\"date\":\"2025-06-19\",\"hour\":8,\"footfall\":350}"

# 3. 查詢某日某時段人流
curl -X GET "http://127.0.0.1:5000/api/footfall/2025-06-19/14"

# 4. 查詢整日人流分佈
curl -X GET "http://127.0.0.1:5000/api/footfall/2025-06-19"

# 5. 更新某日某時段人流
curl -X PUT "http://127.0.0.1:5000/api/footfall/2025-06-19/8" -H "Content-Type: application/json" -d "{\"footfall\":400}"

# 6. 刪除某日某時段人流
curl -X DELETE "http://127.0.0.1:5000/api/footfall/2025-06-19/14"

# 7. 刪除單日所有人流資料
curl -X DELETE "http://127.0.0.1:5000/api/footfall/2025-06-19"

# 8. 依年/月/日查詢全天資料
curl -X GET "http://127.0.0.1:5000/api/footfall/2025/06/19"

# 9. 取得單日時段長條圖 (PNG)
curl -X GET "http://127.0.0.1:5000/footfall_chart/2025/06/19.png" --output chart.png

# 10. 上傳影片進行人流計數
curl -X POST "http://127.0.0.1:5000/api/upload_video" -F "video=@/path/to/video.mp4"

# 11. 下載處理後影片
curl -X GET "http://127.0.0.1:5000/api/download_video/clients_video/your_video_20250619_123456.mp4"
```

## 預測模型操作

1. **生成假資料進行測試**
   ```bash
   python pretict_foootfall/fake_data.py 2023-01-01 365
   ```

2. **訓練預測模型**
   ```bash
   python pretict_foootfall/train_model.py
   ```

3. **測試模型效能**
   ```bash
   python pretict_foootfall/test_model.py
   ```

4. **單一預測示例**
   ```bash
   python pretict_foootfall/predict_single.py
   ```

<!-- ## 系統截圖

![月曆視圖](figure/calendar_view.png)
![人流圖表](figure/calendar_view.png)
![影片處理](figure/calendar_view.png) -->

## 資料庫結構

### daily_footfall 表
- `id`: INT (主鍵)
- `day_date`: DATE (唯一索引)
- [`weekday`](flask_app.py ): VARCHAR(10)
- `total_count`: INT
- [`weather`](weather.py ): VARCHAR(50)
- `created_at`: TIMESTAMP

### hourly_footfall 表
- `id`: INT (主鍵)
- [`daily_id`](flask_app.py ): INT (外鍵連結到 daily_footfall.id)
- `hour_of_day`: TINYINT
- `count`: INT
- [`weather`](weather.py ): VARCHAR(50)
- `created_at`: TIMESTAMP