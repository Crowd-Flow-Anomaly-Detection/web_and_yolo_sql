
import os
import joblib
import pandas as pd
import numpy as np

# 1. 構造一筆特徵資料
single = pd.DataFrame([{
    'day_date': '2025-09-01',
    'weekday':  'Monday',
    'weather':  'Clouds'
}])

# 2. 先把 day_date 轉成 datetime，做出季節性特徵 sin_month / cos_month
single['day_date'] = pd.to_datetime(single['day_date'])
single['month']    = single['day_date'].dt.month
single['sin_month'] = np.sin(2 * np.pi * single['month'] / 12)
single['cos_month'] = np.cos(2 * np.pi * single['month'] / 12)

# 3. one-hot 編碼 weekday, weather（drop_first=True）
cat = pd.get_dummies(single[['weekday','weather']], drop_first=True)

# 4. 合併所有特徵
X_single = pd.concat([cat, single[['sin_month','cos_month']]], axis=1)

# 5. 把缺少的 dummy 欄位補 0，並按照訓練時的順序排列
feature_list = [
    'weekday_Monday','weekday_Saturday','weekday_Sunday',
    'weekday_Thursday','weekday_Tuesday','weekday_Wednesday',
    'weather_Clouds','weather_Drizzle','weather_Rain',
    'weather_Snow','weather_Thunderstorm',
    'sin_month','cos_month'
]
for feat in feature_list:
    if feat not in X_single.columns:
        X_single[feat] = 0
X_single = X_single[feature_list]

# 6. 載模型並預測
ckpt_path = os.path.join(os.path.dirname(__file__), 'ckpt', 'daily_footfall_lr_model.pkl')
model = joblib.load(ckpt_path)

pred = model.predict(X_single)[0]
print(f"預測 2025-07-01 (Tuesday, Clouds) 的 total_count ≈ {pred:.0f}")