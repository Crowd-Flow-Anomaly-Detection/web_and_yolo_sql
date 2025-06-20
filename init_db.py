#!/usr/bin/env python3
# init_db.py

import sys
import mysql.connector
from mysql.connector import errorcode
from app.core.config import settings

def main():
    # 1. 從 Settings 取得連線參數
    host     = settings.db_host
    # port     = settings.db_port
    user     = settings.db_user
    password = settings.db_password
    db_name  = settings.db_name

    # 2. 先連到 MySQL Server（不帶 database）
    try:
        cnx = mysql.connector.connect(
            host=host,
            # port=port,
            user=user,
            password=password,
            use_pure=True
        )
    except mysql.connector.Error as err:
        print(f"[錯誤] 無法連線到 MySQL：{err}", file=sys.stderr)
        sys.exit(1)

    cursor = cnx.cursor()

    try:
        # 3. 建資料庫
        cursor.execute(f"""
            CREATE DATABASE IF NOT EXISTS `{db_name}`
            DEFAULT CHARACTER SET utf8mb4
            DEFAULT COLLATE utf8mb4_unicode_ci;
        """)
        print(f"✓ 資料庫 `{db_name}` 已建立或已存在")

        # 4. 切換到該資料庫
        cursor.execute(f"USE `{db_name}`;")

        # 5. 建表 DDL 清單
        ddl_statements = [
            """
            CREATE TABLE IF NOT EXISTS daily_footfall (
              id          INT AUTO_INCREMENT PRIMARY KEY,
              day_date    DATE         NOT NULL UNIQUE,
              weekday     VARCHAR(10)  NOT NULL,
              total_count INT          NOT NULL,
              weather     VARCHAR(50)  NOT NULL,
              created_at  TIMESTAMP    NOT NULL
                           DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """,
            """
            CREATE TABLE IF NOT EXISTS hourly_footfall (
              id          INT AUTO_INCREMENT PRIMARY KEY,
              daily_id    INT          NOT NULL,
              hour_of_day TINYINT      NOT NULL,
              count       INT          NOT NULL,
              weather     VARCHAR(50)  NOT NULL,
              created_at  TIMESTAMP    NOT NULL
                           DEFAULT CURRENT_TIMESTAMP,
              FOREIGN KEY (daily_id)
                REFERENCES daily_footfall(id)
                ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """
        ]

        # 6. 執行每一條 DDL
        for ddl in ddl_statements:
            cursor.execute(ddl)

        cnx.commit()
        print("✓ 表格 daily_footfall, hourly_footfall 已建立或已存在")

    except mysql.connector.Error as err:
        print(f"[錯誤] 建表失敗：{err}", file=sys.stderr)
        cnx.rollback()
        sys.exit(1)

    finally:
        cursor.close()
        cnx.close()

if __name__ == "__main__":
    main()
