from flask import Flask, request, jsonify
import sqlite3
from datetime import datetime

app = Flask(__name__)
DB_NAME = "database.db"

# ---------------- DATABASE SETUP ---------------- #

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS hosts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        location TEXT,
        rate REAL
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS parking_spots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        host_id INTEGER,
        location TEXT,
        available_from TEXT,
        available_to TEXT,
        is_booked INTEGER DEFAULT 0,
        FOREIGN KEY(host_id) REFERENCES hosts(id)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        spot_id INTEGER,
        hours INTEGER,
        total_cost REAL,
        booking_time TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ---------------- HOST REGISTRATION ---------------- #

@app.route("/host/register", methods=["POST"])
def register_host():
    data = request.json
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO hosts (name, location, rate) VALUES (?, ?, ?)",
        (data["name"], data["location"], data["rate"])
    )
    conn.commit()
    conn.close()

    return jsonify({"message": "Host registered successfully"})

# ---------------- ADD PARKING SPACE ---------------- #

@app.route("/host/add-space", methods=["POST"])
def add_space():
    data = request.json
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO parking_spots (host_id, location, available_from, available_to)
        VALUES (?, ?, ?, ?)
    """, (
        data["host_id"],
        data["location"],
        data["available_from"],
        data["available_to"]
    ))

    conn.commit()
    conn.close()
    return jsonify({"message": "Parking space added"})

# ---------------- SEARCH & ROUTING LOGIC ---------------- #

@app.route("/search", methods=["GET"])
def search_parking():
    area = request.args.get("location")
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT * FROM parking_spots
        WHERE location = ? AND is_booked = 0
    """, (area,))
    spots = cur.fetchall()

    if not spots:
        # Re-route logic
        cur.execute("""
            SELECT * FROM parking_spots
            WHERE location != ? AND is_booked = 0
        """, (area,))
        alternative = cur.fetchall()

        return jsonify({
            "status": "HIGH TRAFFIC / BLOCKED",
            "suggested_spots": [dict(s) for s in alternative]
        })

    return jsonify({
        "status": "AVAILABLE",
        "spots": [dict(s) for s in spots]
    })

# ---------------- BOOKING ENGINE ---------------- #

@app.route("/book", methods=["POST"])
def book_spot():
    data = request.json
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT is_booked FROM parking_spots WHERE id = ?", (data["spot_id"],))
    spot = cur.fetchone()

    if spot["is_booked"] == 1:
        return jsonify({"error": "Spot already booked"}), 400

    cur.execute("""
        UPDATE parking_spots
        SET is_booked = 1
        WHERE id = ?
    """, (data["spot_id"],))

    total_cost = data["hours"] * data["rate"]

    cur.execute("""
        INSERT INTO bookings (spot_id, hours, total_cost, booking_time)
        VALUES (?, ?, ?, ?)
    """, (
        data["spot_id"],
        data["hours"],
        total_cost,
        datetime.now()
    ))

    conn.commit()
    conn.close()

    return jsonify({
        "message": "Booking confirmed",
        "total_cost": total_cost
    })

# ---------------- HOST EARNINGS DASHBOARD ---------------- #

@app.route("/host/earnings/<int:host_id>", methods=["GET"])
def host_earnings(host_id):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT SUM(b.total_cost) AS earnings
        FROM bookings b
        JOIN parking_spots p ON b.spot_id = p.id
        WHERE p.host_id = ?
    """, (host_id,))

    earnings = cur.fetchone()["earnings"] or 0
    conn.close()

    return jsonify({
        "host_id": host_id,
        "total_earnings": earnings
    })

# ---------------- RUN SERVER ---------------- #

if __name__ == "__main__":
    app.run(debug=True)
