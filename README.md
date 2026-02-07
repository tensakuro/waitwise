# WaitWise (QueuePredict)

WaitWise is a real-time queue waiting time prediction system using computer vision.

Instead of asking users to manually report waiting times, the system observes a queue using a camera and estimates:

• Current queue length
• Service rate
• Expected waiting time

## How It Works
Camera → YOLOv8 Person Detection → Tracking → Event API → Queue Engine → Live Dashboard

The dashboard updates automatically when people enter and leave the queue.

## Features
- Live queue monitoring
- Wait-time estimation
- Service rate learning
- Replay simulation mode
- Privacy-friendly (no face storage)

## Run Locally

Install dependencies:
pip install -r requirements.txt

Start backend:
cd backend
python app.py

Run camera simulator:
cd simulator
python camera_simulator.py

Open browser:
http://127.0.0.1:5000
