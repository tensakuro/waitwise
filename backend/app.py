from flask import Flask, request, jsonify, render_template
import sqlite3

app = Flask(__name__, template_folder="templates")

DB = "../data/queue.db"

# ---------------- DATABASE INIT ----------------

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS events(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        location_id TEXT,
        event_type TEXT,
        timestamp REAL
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ---------------- LIVE QUEUE ENGINE ----------------

queue_length = 0
last_service_time = None
avg_service_time = 20.0
service_samples = []

def process_event(event_type, ts):
    global queue_length, last_service_time, avg_service_time, service_samples

    # person joins queue
    if event_type == "arrival":
        queue_length += 1
        print("ARRIVAL received | Queue:", queue_length)

    # person served
    elif event_type == "served":

        if queue_length > 0:
            queue_length -= 1

        # learn service speed
        if last_service_time is not None:
            gap = ts - last_service_time

            # ignore impossible timings (video glitches)
            if 2 < gap < 120:
                service_samples.append(gap)

        last_service_time = ts

        # moving average of service speed
        if len(service_samples) > 3:
            recent = service_samples[-10:]
            avg_service_time = sum(recent) / len(recent)

        print("SERVED received | Queue:", queue_length)


# ---------------- DASHBOARD PAGE ----------------

@app.route("/")
def home():
    return render_template("index.html")


# ---------------- EVENT API (simulator uses this) ----------------

@app.route("/event", methods=["POST"])
def event():
    data = request.json

    location = data["location_id"]
    event_type = data["event"]
    ts = float(data["timestamp"])

    # store raw event
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute(
        "INSERT INTO events(location_id,event_type,timestamp) VALUES (?,?,?)",
        (location, event_type, ts)
    )

    conn.commit()
    conn.close()

    # update real-time queue
    process_event(event_type, ts)

    return {"status": "ok"}


# ---------------- STATUS API (dashboard polls this) ----------------

@app.route("/status")
def status():
    wait_time = queue_length * avg_service_time

    return jsonify({
        "queue_length": int(queue_length),
        "estimated_wait": round(wait_time, 1),
        "avg_service_time": round(avg_service_time, 1)
    })


# ---------------- RESET BUTTON ----------------

@app.route("/reset", methods=["POST"])
def reset():
    global queue_length, last_service_time, avg_service_time, service_samples

    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("DELETE FROM events")
    conn.commit()
    conn.close()

    queue_length = 0
    last_service_time = None
    avg_service_time = 20.0
    service_samples = []

    print("System reset.")

    return {"status": "reset"}


# ---------------- RUN SERVER ----------------

if __name__ == "__main__":
    # IMPORTANT: disable reloader & debug
    app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)
