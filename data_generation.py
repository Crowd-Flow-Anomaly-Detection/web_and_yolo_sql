import random
import datetime
import json

# 生成資料函式
def generate_data(filename='footfall_data.json'):
    current_date = datetime.datetime.now()
    data = {}
    
    # 生成 1000 天的資料，從最舊到最新
    for i in range(999, -1, -1):
        date = (current_date - datetime.timedelta(days=i)).strftime('%Y-%m-%d')
        hourly_data = {}
        
        for hour in range(24):
            footfall = random.randint(5, 50)  # 隨機生成 5 到 50 之間的數字
            hourly_data[hour] = footfall
        
        data[date] = hourly_data
    
    # 寫入 JSON 
    with open(filename, 'w') as jsonfile:
        json.dump(data, jsonfile, indent=4)
    
    print(f"資料成功生成 存成 {filename}")

if __name__ == "__main__":
    generate_data()
