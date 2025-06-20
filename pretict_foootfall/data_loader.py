# data_loader.py

import pandas as pd

import os, sys

# 把上一層目錄（專案根）加到 sys.path
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root not in sys.path:
    sys.path.append(root)
    
from app.db.connector import pool

def fetch_daily_footfall():
    """
    用連線池從 daily_footfall 撈出 day_date, weekday, weather, total_count
    回傳 pandas.DataFrame
    """
    # 從 pool 拿一條連線
    conn = pool.get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            day_date,
            weekday,
            weather,
            total_count
        FROM daily_footfall
    """)
    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    # 轉成 DataFrame
    df = pd.DataFrame(rows)
    return df
