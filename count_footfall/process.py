# 更新 YOLOv3 推論程式，使用 Ultralytics YOLO（YOLOv8 ~ YOLOv12）

import os
import cv2
import time
import glob
import numpy as np
from tqdm import tqdm
from ultralytics import YOLO
# from sort import Sort  # 你的追蹤器程式
from count_footfall.sort import Sort
from datetime import datetime
import requests

def process_video(video_path, model_path='count_footfall/yolo-coco/best.pt'):
    os.makedirs("output", exist_ok=True)

    for f in glob.glob('output/*.png'):
        os.remove(f)

    tracker = Sort()
    memory = {}
    line = [(369, 312), (800, 364)]
    counter = 0

    COLORS = np.random.randint(0, 255, size=(200, 3), dtype="uint8")

    def intersect(A, B, C, D):
        return ccw(A, C, D) != ccw(B, C, D) and ccw(A, B, C) != ccw(A, B, D)

    def ccw(A, B, C):
        return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])

    print("[INFO] loading Ultralytics model...")
    model = YOLO(model_path)

    vs = cv2.VideoCapture(video_path)
    writer = None
    total = int(vs.get(cv2.CAP_PROP_FRAME_COUNT))

    for frameIndex in tqdm(range(total), desc="處理影格"):
        grabbed, frame = vs.read()
        if not grabbed:
            break

        H, W = frame.shape[:2]
        start = time.time()
        results = model(frame, verbose=False)[0]  # 取得第一個 batch 的結果
        end = time.time()

        dets = []
        for box in results.boxes:
            if box.conf < 0.5:
                continue

            x1, y1, x2, y2 = box.xyxy[0].tolist()
            cls = int(box.cls)
            conf = float(box.conf)

            # 只針對特定類別，例如 person
            if cls == 0:
                dets.append([x1, y1, x2, y2, conf])

        dets = np.array(dets)
        tracks = tracker.update(dets)

        boxes = []
        indexIDs = []
        previous = memory.copy()
        memory = {}

        for track in tracks:
            x1, y1, x2, y2, track_id = track
            boxes.append([x1, y1, x2, y2])
            indexIDs.append(int(track_id))
            memory[int(track_id)] = [x1, y1, x2, y2]

        for i, box in enumerate(boxes):
            x1, y1, x2, y2 = map(int, box)
            color = [int(c) for c in COLORS[indexIDs[i] % len(COLORS)]]
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

            if indexIDs[i] in previous:
                x2_prev, y2_prev, x4_prev, y4_prev = previous[indexIDs[i]]
                p0 = (int((x1 + x2) / 2), int((y1 + y2) / 2))
                p1 = (int((x2_prev + x4_prev) / 2), int((y2_prev + y4_prev) / 2))
                cv2.line(frame, p0, p1, color, 3)
                if intersect(p0, p1, line[0], line[1]):
                    counter += 1
                    print("目前計數:", counter)

            cv2.putText(frame, str(indexIDs[i]), (x1, y1 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        cv2.line(frame, line[0], line[1], (0, 255, 255), 5)
        cv2.putText(frame, str(counter), (100, 200),
                    cv2.FONT_HERSHEY_DUPLEX, 5.0, (0, 255, 255), 10)

        out_path = f"count_footfall/output/frame-{frameIndex}.png"
        cv2.imwrite(out_path, frame)

        if writer is None:
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            writer = cv2.VideoWriter("output/result.mp4", fourcc, 30, (W, H), True)

            elap = end - start
            print(f"[INFO] single frame took {elap:.4f} seconds")
            print(f"[INFO] estimated total time: {elap * total:.4f} seconds")

        writer.write(frame)

    vs.release()
    writer.release()

    now = datetime.now()
    data = {
        "date": now.strftime("%Y-%m-%d"),
        "hour": now.hour,
        "footfall": counter
    }

    response = requests.post("http://127.0.0.1:5000/api/footfall",
                             json=data,
                             headers={"Content-Type": "application/json"})
    print("API response:", response.status_code, response.text)

    return counter, "output/result.mp4"

if __name__ == "__main__":
    video_path = "input/record_2025-07-01_20-20-41.mp4"
    model_path = "yolo-coco/best.pt"  # 或 yolov12n.pt
    process_video(video_path, model_path)