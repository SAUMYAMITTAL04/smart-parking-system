import sys
import asyncio

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import streamlit as st
import cv2
import os
import time
import sqlite3
import pandas as pd
from datetime import datetime
from src.detector import ParkingDetector

st.set_page_config(page_title="Smart Parking Enterprise AI", layout="wide", page_icon="🚗")

# --- DATABASE ENGINE ---
DB_FILE = "data/parking_analytics.db"
os.makedirs("data", exist_ok=True)

def init_db():
    conn = sqlite3.connect(DB_FILE)
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

init_db()

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("🎛️ Navigation Portal")
app_mode = st.sidebar.radio("Select Interface View:", ["📊 Manager Operations Center", "📱 Driver Kiosk Mobile View"])

# Pre-populate sample vehicles if empty
conn = sqlite3.connect(DB_FILE)
df_check = pd.read_sql_query("SELECT * FROM parking_logs", conn)
conn.close()

if df_check.empty:
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO parking_logs (vehicle_plate, entry_time, assigned_space, status, fee_amount) VALUES (?, ?, ?, ?, ?)",
        ("DL3C-AN-4821", datetime.now().strftime("%H:%M:%S"), "Slot 4", "Checked-In", 0.0)
    )
    conn.commit()
    conn.close()

# ==========================================
# 📱 VIEW 1: DRIVER KIOSK MOBILE VIEW
# ==========================================
if app_mode == "📱 Driver Kiosk Mobile View":
    st.title("📲 Real-Time Driver Navigation Portal")
    st.markdown("Automated parking spot locator for incoming drivers.")
    
    if os.path.exists("data/slots.json"):
        detector = ParkingDetector("data/slots.json")
        cap = cv2.VideoCapture("data/parking_video.mp4")
        ret, frame = cap.read()
        cap.release()
        
        if ret:
            _, empty, occupied = detector.process_frame(frame)
            
            # Big Driver Kiosk Banner
            if empty > 0:
                st.success(f"🟢 **PARKING AVAILABLE: {empty} SPOTS OPEN**")
            else:
                st.error("🔴 **PARKING LOT FULL**")
                
            st.markdown("---")
            kios_col1, kios_col2 = st.columns(2)
            
            with kios_col1:
                st.metric("Total Free Spaces", f"{empty} Slots")
                st.info("💡 **Driver Tip:** Recommended entrance lane: **Zone A (Slots 0-5)**")
                
            with kios_col2:
                st.metric("Current Rate", "₹50 / Hour")
                st.caption("Contactless RFID & ANPR billing active at barrier exit.")
    else:
        st.error("Missing slot map layout initialization asset. Please run `src/picker.py` first.")

# ==========================================
# 📊 VIEW 2: MANAGER OPERATIONS CENTER
# ==========================================
else:
    st.title("🚗 Smart Parking Enterprise Operations Center")
    st.markdown("Real-time computer vision metrics engine powered by localized spatial variance analysis.")

    # --- SIDEBAR: AUTOMATED CHECKOUT & BILLING (OPTION 1) ---
    st.sidebar.markdown("---")
    st.sidebar.subheader("💳 Barrier Exit & Billing Simulator")
    
    conn = sqlite3.connect(DB_FILE)
    active_vehicles = pd.read_sql_query("SELECT vehicle_plate FROM parking_logs WHERE status='Checked-In'", conn)
    conn.close()
    
    if not active_vehicles.empty:
        selected_plate = st.sidebar.selectbox("Select Vehicle at Exit Gate:", active_vehicles["vehicle_plate"])
        
        if st.sidebar.button("🚪 Process Exit & Generate Bill"):
            exit_time_str = datetime.now().strftime("%H:%M:%S")
            
            # Simple flat fee billing rule (₹50 base rate)
            fee = 50.00 
            
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE parking_logs SET exit_time=?, status='Checked-Out', fee_amount=? WHERE vehicle_plate=? AND status='Checked-In'",
                (exit_time_str, fee, selected_plate)
            )
            conn.commit()
            conn.close()
            st.sidebar.success(f"Vehicle {selected_plate} Checked Out! Fee Collected: ₹{fee}")
            st.rerun()
    else:
        st.sidebar.info("No active vehicles inside for checkout.")

    # Main Manager UI Execution Loop
    if os.path.exists("data/slots.json"):
        detector = ParkingDetector("data/slots.json")
        
        # Calculate Total Revenue Collected
        conn = sqlite3.connect(DB_FILE)
        rev_df = pd.read_sql_query("SELECT SUM(fee_amount) as total_rev FROM parking_logs", conn)
        total_revenue = rev_df["total_rev"].iloc[0] if rev_df["total_rev"].iloc[0] is not None else 0.0
        conn.close()

        col1, col2, col3, col4 = st.columns(4)
        available_metric = col1.metric("Available Slots", "0")
        occupied_metric = col2.metric("Occupied Slots", "0")
        occupancy_rate = col3.metric("System Load", "0%")
        revenue_metric = col4.metric("Total Revenue", f"₹{total_revenue:.2f}")
        
        st_frame = st.image([])
        st.markdown("---")
        
        table_col, chart_col = st.columns([1, 1])
        
        with table_col:
            st.subheader("📊 Live Enterprise Database Transaction Ledger")
            log_table = st.empty()

        with chart_col:
            st.subheader("📈 Real-Time Lot Load Analytics")
            chart_placeholder = st.empty()

        if "chart_data" not in st.session_state:
            st.session_state.chart_data = pd.DataFrame(columns=["Time", "Occupied"])

        cap = cv2.VideoCapture("data/parking_video.mp4")
        last_chart_update = time.time()

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue
                
            output_frame, empty, occupied = detector.process_frame(frame)
            
            total = empty + occupied
            rate_val = int((occupied / total) * 100) if total > 0 else 0
            
            available_metric.metric("Available Slots", str(empty))
            occupied_metric.metric("Occupied Slots", str(occupied))
            occupancy_rate.metric("System Load", f"{rate_val}%")

            conn = sqlite3.connect(DB_FILE)
            df = pd.read_sql_query("SELECT vehicle_plate as 'Vehicle Plate', entry_time as 'Entry Time', exit_time as 'Exit Time', assigned_space as 'Space', status as 'Status', fee_amount as 'Fee (₹)' FROM parking_logs ORDER BY id DESC LIMIT 10", conn)
            conn.close()
            log_table.dataframe(df, use_container_width=True)

            if time.time() - last_chart_update > 1.0:
                current_time = datetime.now().strftime("%H:%M:%S")
                new_row = pd.DataFrame([{"Time": current_time, "Occupied": occupied}])
                st.session_state.chart_data = pd.concat([st.session_state.chart_data, new_row], ignore_index=True).tail(20)
                last_chart_update = time.time()

            if not st.session_state.chart_data.empty:
                chart_placeholder.line_chart(
                    st.session_state.chart_data.set_index("Time"),
                    use_container_width=True
                )

            st_frame.image(cv2.cvtColor(output_frame, cv2.COLOR_BGR2RGB))
            time.sleep(0.01)

        cap.release()
    else:
        st.error("Missing slot map layout initialization asset. Please run `src/picker.py` configuration tool step first.")