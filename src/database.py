import sqlite3
import os
from datetime import datetime, timedelta

DB_FILE = os.path.join("data", "parking_analytics.db")

def get_connection():
    """Establishes and returns a connection to the SQLite database."""
    os.makedirs("data", exist_ok=True)
    return sqlite3.connect(DB_FILE)

def init_db():
    """Initializes the database schema if it doesn't already exist."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS parking_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_plate TEXT NOT NULL,
            entry_time TEXT NOT NULL,
            exit_time TEXT,
            assigned_space TEXT NOT NULL,
            status TEXT NOT NULL,
            fee_amount REAL DEFAULT 0.0
        )
    ''')
    conn.commit()
    conn.close()

# Ensure database table exists on module import
init_db()

def get_next_available_slot():
    """Assigns the next available slot based on current checked-in vehicles."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT assigned_space FROM parking_logs WHERE status='Checked-In'")
    occupied_slots = {row[0] for row in cursor.fetchall()}
    conn.close()

    # Pre-defined parking slots (Slot 1 to Slot 12)
    all_slots = [f"Slot {i}" for i in range(1, 13)]
    for slot in all_slots:
        if slot not in occupied_slots:
            return slot
    return "Overflow Area"

def is_recently_logged(plate, cooldown_seconds=30):
    """Prevents duplicate logging of the same license plate within a short time window."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT entry_time FROM parking_logs WHERE vehicle_plate=? AND status='Checked-In' ORDER BY id DESC LIMIT 1",
        (plate,)
    )
    row = cursor.fetchone()
    conn.close()

    if row:
        try:
            last_entry = datetime.strptime(row[0], "%H:%M:%S")
            now = datetime.now()
            last_entry_today = datetime.combine(now.date(), last_entry.time())
            if (now - last_entry_today) < timedelta(seconds=cooldown_seconds):
                return True
        except ValueError:
            pass
    return False