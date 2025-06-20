# train_model.py

import os
import joblib
import pandas as pd
import numpy as np  # 新增
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score

from data_loader import fetch_daily_footfall

def prepare_features(df: pd.DataFrame):
    """
    原本對 weekday、weather 做 one-hot，
    加上從 day_date 拆出的月份週期特徵。
    """
    # 先確保 day_date 是 datetime 型態
    df['day_date'] = pd.to_datetime(df['day_date'])

    # 1. 抽特徵：月、年中第幾天
    df['month']       = df['day_date'].dt.month
    df['day_of_year'] = df['day_date'].dt.dayofyear

    # 2. 用 sine/cosine 處理月份的週期性 (12 個月)
    df['sin_month'] = np.sin(2 * np.pi * df['month'] / 12)
    df['cos_month'] = np.cos(2 * np.pi * df['month'] / 12)

    # 3. 原本的 one-hot (去掉第一個類別作 baseline)
    cat = pd.get_dummies(df[['weekday', 'weather']], drop_first=True)

    # 4. 合併所有特徵
    X = pd.concat([
        cat,
        df[['sin_month', 'cos_month']]
    ], axis=1)

    y = df['total_count']
    return X, y

def main():
    # 1. 讀資料
    df = fetch_daily_footfall()
    print(f"共讀到 {len(df)} 筆資料")
    print(df.head())

    # 2. 準備特徵與目標
    X, y = prepare_features(df)
    print("Feature 欄位：", list(X.columns))

    # 3. 分訓練/測試集
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # 4. 訓練 Linear Regression
    model = LinearRegression()
    model.fit(X_train, y_train)

    # 5. 評估
    y_pred = model.predict(X_test)
    print(f"測試集 MSE：{mean_squared_error(y_test, y_pred):.2f}")
    print(f"測試集 R²：{r2_score(y_test, y_pred):.3f}")

    # 6. 各特徵係數
    coeffs = pd.Series(model.coef_, index=X.columns).sort_values(ascending=False)
    print("各特徵係數：")
    print(coeffs)

    # 7. 存模型到 ckpt 資料夾
    script_dir = os.path.dirname(os.path.abspath(__file__))
    ckpt_dir   = os.path.join(script_dir, 'ckpt')
    os.makedirs(ckpt_dir, exist_ok=True)

    model_path = os.path.join(ckpt_dir, 'daily_footfall_lr_model.pkl')
    joblib.dump(model, model_path)
    print(f"模型已存為 {model_path}")

if __name__ == '__main__':
    main()
