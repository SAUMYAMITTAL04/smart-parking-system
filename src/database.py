import sqlite3
import os
from datetime import datetime

DB_PATH = "parking_analytics.db"

def get_connection():
    """Returns a SQLite database connection."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    return conn

def init_db():
    """Initializes the database schema and creates necessary tables."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Table for storing parking transaction logs and ANPR records
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS parking_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_plate TEXT NOT NULL,
            entry_time TEXT NOT NULL,
            exit_time TEXT,
            assigned_space TEXT,
            status TEXT DEFAULT 'Checked-In',
            fee_amount REAL DEFAULT 0.0
        )
    """)
    
    conn.commit()
    conn.close()

def get_next_available_slot():
    """Generates or assigns the next available parking slot ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM parking_logs WHERE status='Checked-In'")
    occupied_count = cursor.fetchone()[0]
    conn.close()
    
    # Assigns sequential slot names (e.g., Slot-A1, Slot-A2)
    return f"Slot-A{occupied_count + 1}"

def is_recently_logged(plate_number, cooldown_seconds=60):
    """
    Checks if a vehicle with the given plate number was recently logged in DB
    to avoid duplicate continuous entries during live video stream scanning.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT entry_time FROM parking_logs WHERE vehicle_plate=? AND status='Checked-In' ORDER BY id DESC LIMIT 1",
        (plate_number,)
    )
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return False  # Not logged recently, safe to insert
        
    entry_t_str = row[0]
    try:
        fmt = "%H:%M:%S"
        now_time = datetime.strptime(datetime.now().strftime(fmt), fmt)
        entry_time = datetime.strptime(entry_t_str, fmt)
        
        time_diff = (now_time - entry_time).total_seconds()
        return time_diff < cooldown_seconds
    except Exception:
        return False