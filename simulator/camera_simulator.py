import cv2
import numpy as np
from ultralytics import YOLO
import requests
import time
from norfair import Detection, Tracker

# ---------------- CONFIG ----------------

# IMPORTANT: use raw string (r"...") OR forward slashes
VIDEO = r"C:\Users\kaise\OneDrive\Desktop\waitwise\queuepredict\queue1.mp4"

API = "http://127.0.0.1:5000/event"

# ----------------------------------------

print("Loading YOLO model...")
model = YOLO("yolov8n.pt")

tracker = Tracker(distance_function="euclidean", distance_threshold=60)

cap = cv2.VideoCapture(VIDEO)

if not cap.isOpened():
    print("❌ ERROR: Video file not found. Check VIDEO path.")
    exit()

# get video resolution automatically
width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

print("Video Resolution:", width, "x", height)

# virtual sensor lines (auto-scale for any video)
ENTRY_Y = int(height * 0.45)
EXIT_Y  = int(height * 0.70)

print("Entry line at:", ENTRY_Y)
print("Exit line at:", EXIT_Y)

crossed_entry = set()
crossed_exit = set()

print("Starting queue sensor...\n")

while True:
    ret, frame = cap.read()
    if not ret:
        print("Video finished.")
        break

    # detect persons
    results = model(frame, conf=0.25, verbose=False)[0]

    detections = []

    for box in results.boxes:
        if int(box.cls[0]) != 0:   # class 0 = person
            continue

        x1, y1, x2, y2 = map(int, box.xyxy[0])

        cx = (x1 + x2) // 2
        cy = (y1 + y2) // 2

        detections.append(Detection(points=np.array([[cx, cy]])))

        # draw bounding box
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0,255,0), 2)

    # tracking
    tracked_objects = tracker.update(detections=detections)

    for obj in tracked_objects:
        tid = obj.id
        cx, cy = obj.estimate[0].astype(int)

        # draw center point
        cv2.circle(frame, (cx, cy), 5, (255,0,0), -1)

        # ---------- ARRIVAL ----------
        if cy > ENTRY_Y and tid not in crossed_entry:
            crossed_entry.add(tid)
            print("ARRIVAL detected ID:", tid)

            try:
                r = requests.post(API, json={
                    "location_id": "canteen_demo",
                    "event": "arrival",
                    "timestamp": time.time()
                })
                print("ARRIVAL SENT ->", r.status_code)
            except Exception as e:
                print("ARRIVAL ERROR:", e)

        # ---------- SERVED ----------
        if cy > EXIT_Y and tid not in crossed_exit:
            crossed_exit.add(tid)
            print("SERVED detected ID:", tid)

            try:
                r = requests.post(API, json={
                    "location_id": "canteen_demo",
                    "event": "served",
                    "timestamp": time.time()
                })
                print("SERVED SENT ->", r.status_code)
            except Exception as e:
                print("SERVED ERROR:", e)

    # draw sensor lines
    cv2.line(frame, (0, ENTRY_Y), (width, ENTRY_Y), (0,255,0), 3)
    cv2.line(frame, (0, EXIT_Y),  (width, EXIT_Y),  (0,0,255), 3)

    cv2.putText(frame, "ENTRY LINE", (20, ENTRY_Y-10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)

    cv2.putText(frame, "SERVICE LINE", (20, EXIT_Y-10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,255), 2)

    cv2.imshow("QueuePredict Edge Camera", frame)

    if cv2.waitKey(1) == 27:  # ESC to exit
        break

cap.release()
cv2.destroyAllWindows()
