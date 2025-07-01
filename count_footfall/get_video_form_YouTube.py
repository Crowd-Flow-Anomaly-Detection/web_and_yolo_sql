import subprocess
import datetime
import os

def get_live_stream_url(video_url: str) -> str:
    # 這裡加上你要的 headers
    cmd = [
        'yt-dlp',
        '-g',
        '--add-header', 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        '--add-header', 'Accept-Language: en-US,en;q=0.5',
        video_url
    ]

    try:
        stream_url = subprocess.check_output(cmd, text=True).strip()
        print(f"✅ 取得串流 URL: {stream_url}")
        return stream_url
    except subprocess.CalledProcessError as e:
        print("❌ 無法取得串流 URL：", e)
        return None

def download_stream(stream_url: str, duration: int = 60, output_file: str = "output.mp4"):
    cmd = [
        'ffmpeg',
        '-y',
        '-i', stream_url,
        '-t', str(duration),
        '-c', 'copy',
        output_file
    ]

    print("🎬 正在錄製...")
    try:
        subprocess.run(cmd, check=True)
        print(f"✅ 錄影完成：{output_file}")
    except subprocess.CalledProcessError as e:
        print("❌ 錄影失敗：", e)

if __name__ == '__main__':
    # 🎯 你的直播網址
    youtube_url = 'https://www.youtube.com/watch?v=VR-x3HdhKLQ'

    # 🕒 檔名加時間戳
    now = datetime.datetime.now()
    filename = f"live_{now.strftime('%Y%m%d_%H%M%S')}.mp4"

    # 🔗 取得串流 URL
    stream = get_live_stream_url(youtube_url)
    if stream:
        # 📼 開始錄影一分鐘
        download_stream(stream, duration=60, output_file=filename)
