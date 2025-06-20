import os
from dotenv import load_dotenv
import requests
from datetime import datetime, timezone

# 載入 .env
load_dotenv()
API_KEY = os.getenv("Weather_API_KEY")
if not API_KEY:
    raise RuntimeError("請先在 .env 設定 API_KEY")

LAT, LON = 9.5120, 100.0136  # Ko Samui

def get_current_weather(lat, lon, api_key):
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "lat": lat,
        "lon": lon,
        "appid": api_key,
        "units": "metric",
        "lang": "zh_tw"
    }
    r = requests.get(url, params=params)
    r.raise_for_status()
    return r.json()

def format_weather(data):
    name    = data.get("name","－")
    country = data.get("sys",{}).get("country","")
    ts = data.get("dt", 0)
    dt = datetime.fromtimestamp(ts, tz=timezone.utc) \
                .strftime("%Y-%m-%d %H:%M:%S UTC")
    weather_main = data["weather"][0]["main"]
    m       = data["main"]
    wd      = data.get("wind",{})
    return (
        f"地點：{name} ({country})\n"
        f"觀測時間：{dt}\n"
        f"天氣狀態：{weather_main}\n"
        f"氣溫：{m['temp']}°C，體感：{m['feels_like']}°C\n"
        f"濕度：{m['humidity']}%\n"
        f"氣壓：{m['pressure']} hPa\n"
        f"風速：{wd.get('speed','－')} m/s，風向：{wd.get('deg','－')}°"
    )

def get_weather_main(lat, lon, api_key):
    data = get_current_weather(lat, lon, api_key)
    # weather[0].main 一定是以下其中之一：
    # Thunderstorm, Drizzle, Rain, Snow, Atmosphere, Clear, Clouds
    return data["weather"][0]["main"]

if __name__ == "__main__":
    data = get_current_weather(LAT, LON, API_KEY)
    print(format_weather(data))
