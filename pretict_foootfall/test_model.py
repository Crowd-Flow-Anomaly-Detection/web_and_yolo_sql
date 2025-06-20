# test_model.py

import os
import joblib
import pandas as pd
import numpy as np  # 用來計算 sine/cosine
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

from data_loader import fetch_daily_footfall

def prepare_features(df: pd.DataFrame):
    """
    跟 train_model.py 保持一致：
    1. 轉 day_date -> sin_month, cos_month
    2. one-hot weekday, weather
    """
    # 確保 day_date 是 datetime
    df['day_date'] = pd.to_datetime(df['day_date'])

    # 1. 產生月份週期特徵
    df['month'] = df['day_date'].dt.month
    df['sin_month'] = np.sin(2 * np.pi * df['month'] / 12)
    df['cos_month'] = np.cos(2 * np.pi * df['month'] / 12)

    # 2. one-hot weekday, weather（drop_first=True）
    cat = pd.get_dummies(df[['weekday', 'weather']], drop_first=True)

    # 3. 合併所有特徵
    X = pd.concat([cat, df[['sin_month', 'cos_month']]], axis=1)
    y = df['total_count']
    return X, y

def main():
    # 1. 讀原始 daily 資料
    df = fetch_daily_footfall()

    # 2. 準備特徵與目標
    X, y = prepare_features(df)

    # 3. 切出一個測試集（跟 train_model.py 同設定）
    _, X_test, _, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # 4. 載模型
    ckpt_path = os.path.join(os.path.dirname(__file__), 'ckpt', 'daily_footfall_lr_model.pkl')
    model = joblib.load(ckpt_path)
    print(f"Loaded model from {ckpt_path}")

    # 5. 對測試集做預測並評估
    y_pred = model.predict(X_test)
    print(f"Test MSE:  {mean_squared_error(y_test, y_pred):.2f}")
    print(f"Test R²:   {r2_score(y_test, y_pred):.3f}")

    # 6. 如果想看前幾筆預測 vs. 實際
    comp = pd.DataFrame({
        'y_true': y_test.values,
        'y_pred': y_pred
    }, index=y_test.index).head(5)
    print("\n前五筆預測 vs. 實際：")
    print(comp)

if __name__ == '__main__':
    main()
