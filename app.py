import sys
import asyncio

# Fix for Windows asyncio ConnectionResetError bug
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

# --- DATABASE SETUP ---
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

# --- MOCK USER DATABASE & AUTHENTICATION ---
USERS = {
    "driver": {"password": "user123", "role": "Customer", "name": "Valued Guest"},
    "manager": {"password": "admin123", "role": "Manager", "name": "Operations Manager"},
    "exec": {"password": "exec123", "role": "Executive", "name": "Executive Analyst"}
}

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    st.session_state["user_role"] = None
    st.session_state["user_name"] = None

def logout():
    st.session_state["logged_in"] = False
    st.session_state["user_role"] = None
    st.session_state["user_name"] = None
    st.rerun()

# ==========================================
# 🔑 LOGIN PAGE
# ==========================================
if not st.session_state["logged_in"]:
    st.title("🚗 Smart Parking Enterprise Portal")
    st.subheader("Sign In to Access Your Portal")

    col_login, col_info = st.columns([1, 1])

    with col_login:
        username_input = st.text_input("Username").strip()
        password_input = st.text_input("Password", type="password").strip()

        if st.button("🔓 Sign In", use_container_width=True):
            if username_input in USERS and USERS[username_input]["password"] == password_input:
                st.session_state["logged_in"] = True
                st.session_state["user_role"] = USERS[username_input]["role"]
                st.session_state["user_name"] = USERS[username_input]["name"]
                st.success(f"Welcome, {USERS[username_input]['name']}!")
                st.rerun()
            else:
                st.error("Invalid username or password.")

    with col_info:
        st.info("""
        **Demo Credentials:**
        * **Customer Kiosk:** User: `driver` | Pass: `user123`
        * **Operations Center:** User: `manager` | Pass: `admin123`
        * **BI Analytics:** User: `exec` | Pass: `exec123`
        """)

# ==========================================
# 📊 DASHBOARDS (AFTER AUTHENTICATION)
# ==========================================
else:
<<<<<<< Updated upstream
    # Sidebar Profile & Logout
    st.sidebar.markdown(f"### 👤 Logged in as: **{st.session_state['user_name']}**")
    st.sidebar.caption(f"Role Level: **{st.session_state['user_role']}**")
    st.sidebar.button("🚪 Logout", on_click=logout, use_container_width=True)
=======
    # Sidebar Session Header
    st.sidebar.markdown(f"### 👤 User: **{st.session_state['user_name']}**")
    st.sidebar.caption(f"Role: **{st.session_state['user_role']}**")
    st.sidebar.button("🚪 Logout", on_click=logout, width="stretch")
>>>>>>> Stashed changes
    st.sidebar.markdown("---")

    # ------------------------------------------
    # 📱 VIEW 1: CUSTOMER DASHBOARD
    # ------------------------------------------
    if st.session_state["user_role"] == "Customer":
        st.title("📲 Real-Time Driver Navigation Portal")
        st.markdown("Automated parking spot locator for incoming drivers.")
        
        if os.path.exists("data/slots.json"):
            detector = ParkingDetector("data/slots.json")
            cap = cv2.VideoCapture("data/parking_video.mp4")
            ret, frame = cap.read()
            cap.release()
            
            if ret:
                _, empty, occupied = detector.process_frame(frame)
                
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

    # ------------------------------------------
    # 📈 VIEW 2: EXECUTIVE BI DASHBOARD
    # ------------------------------------------
    elif st.session_state["user_role"] == "Executive":
        st.title("📈 Executive Business Intelligence Analytics")
        st.markdown("Historical utilization trends, peak load distributions, and revenue metrics.")
        
        conn = sqlite3.connect(DB_FILE)
        df_logs = pd.read_sql_query("SELECT * FROM parking_logs", conn)
        conn.close()
        
        if not df_logs.empty:
            col_bi1, col_bi2 = st.columns(2)
            
            with col_bi1:
                st.subheader("📊 Space Utilization Distribution")
                space_counts = df_logs["assigned_space"].value_counts().reset_index()
                space_counts.columns = ["Space", "Visits"]
                st.bar_chart(space_counts.set_index("Space"))
                
            with col_bi2:
                st.subheader("💳 Revenue Summary by Status")
                rev_summary = df_logs.groupby("status")["fee_amount"].sum().reset_index()
                rev_summary.columns = ["Status", "Total Revenue (₹)"]
                st.dataframe(rev_summary, use_container_width=True)
                
            st.markdown("---")
            st.subheader("⏱️ Peak Traffic Activity")
            df_logs['Hour'] = df_logs['entry_time'].apply(lambda x: str(x).split(":")[0] + ":00" if isinstance(x, str) else "00:00")
            hour_counts = df_logs['Hour'].value_counts().reset_index()
            hour_counts.columns = ["Hour of Day", "Traffic Volume"]
            st.line_chart(hour_counts.set_index("Hour of Day"))
        else:
            st.info("No historical analytics logged yet.")

    # ------------------------------------------
    # 📊 VIEW 3: MANAGER OPERATIONS CENTER
    # ------------------------------------------
    elif st.session_state["user_role"] == "Manager":
        st.title("🚗 Smart Parking Enterprise Operations Center")
        st.markdown("Real-time computer vision metrics engine powered by localized spatial variance analysis.")

        # --- SIDEBAR: AUTOMATED ENTRY / CHECKOUT SIMULATOR ---
        st.sidebar.subheader("🚗 Gate Simulation Controls")
        
        new_plate = st.sidebar.text_input("Simulate Entry Plate:", "KA-01-MJ-9999")
        if st.sidebar.button("🟢 Check-In New Vehicle", use_container_width=True):
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO parking_logs (vehicle_plate, entry_time, assigned_space, status, fee_amount) VALUES (?, ?, ?, ?, ?)",
                (new_plate, datetime.now().strftime("%H:%M:%S"), "Slot 4", "Checked-In", 0.0)
            )
            conn.commit()
            conn.close()
            st.sidebar.success(f"Vehicle {new_plate} Registered!")
            st.rerun()

        st.sidebar.markdown("---")
        st.sidebar.subheader("💳 Exit Gate & Invoice Simulator")
        
        conn = sqlite3.connect(DB_FILE)
        active_vehicles = pd.read_sql_query("SELECT vehicle_plate FROM parking_logs WHERE status='Checked-In'", conn)
        conn.close()
        
        if not active_vehicles.empty:
            selected_plate = st.sidebar.selectbox("Select Vehicle at Exit Gate:", active_vehicles["vehicle_plate"])
            
            if st.sidebar.button("🚪 Process Exit & Generate Invoice", use_container_width=True):
                exit_time_str = datetime.now().strftime("%H:%M:%S")
                fee = 50.00
                
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE parking_logs SET exit_time=?, status='Checked-Out', fee_amount=? WHERE vehicle_plate=? AND status='Checked-In'",
                    (exit_time_str, fee, selected_plate)
                )
                conn.commit()
                
                cursor.execute("SELECT entry_time, assigned_space FROM parking_logs WHERE vehicle_plate=? ORDER BY id DESC LIMIT 1", (selected_plate,))
                rec_row = cursor.fetchone()
                conn.close()
                
                if rec_row:
                    entry_t, space_name = rec_row
                    html_receipt = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body {{ font-family: Arial, sans-serif; background-color: #f8fafc; padding: 30px; }}
  .card {{ background: #ffffff; border: 2px solid #1e3a8a; border-radius: 8px; padding: 24px; max-width: 500px; margin: auto; color: #000; }}
  .header {{ background: #1e3a8a; color: white; padding: 12px; border-radius: 6px; text-align: center; }}
  .row {{ margin: 12px 0; font-size: 14px; border-bottom: 1px solid #e2e8f0; padding-bottom: 6px; }}
  .total {{ font-size: 18px; color: #1e3a8a; font-weight: bold; margin-top: 16px; }}
</style>
</head>
<body>
  <div class="card">
    <div class="header">
      <h2>🚗 SMART PARKING OFFICIAL RECEIPT</h2>
    </div>
    <div class="row"><b>Vehicle Registration:</b> {selected_plate}</div>
    <div class="row"><b>Assigned Parking Bay:</b> {space_name}</div>
    <div class="row"><b>Check-In Time:</b> {entry_t}</div>
    <div class="row"><b>Check-Out Time:</b> {exit_time_str}</div>
    <div class="row"><b>Billing Status:</b> <span style="color:green; font-weight:bold;">PAID & CHECKED-OUT</span></div>
    <div class="total">Total Fee Paid: ₹{fee:.2f}</div>
  </div>
</body>
</html>"""
                    st.session_state["invoice_html"] = html_receipt
                    st.session_state["receipt_plate"] = selected_plate
                
                st.sidebar.success(f"Vehicle {selected_plate} Checked Out!")
                st.rerun()
        else:
            st.sidebar.info("No active vehicles inside for checkout.")

        # --- MAIN MANAGER DASHBOARD EXECUTION ---
        if os.path.exists("data/slots.json"):
            detector = ParkingDetector("data/slots.json")
            
            conn = sqlite3.connect(DB_FILE)
            rev_df = pd.read_sql_query("SELECT SUM(fee_amount) as total_rev FROM parking_logs", conn)
            total_revenue = rev_df["total_rev"].iloc[0] if rev_df["total_rev"].iloc[0] is not None else 0.0
            conn.close()

            col1, col2, col3, col4 = st.columns(4)
            available_metric = col1.metric("Available Slots", "0")
            occupied_metric = col2.metric("Occupied Slots", "0")
            occupancy_rate = col3.metric("System Load", "0%")
            revenue_metric = col4.metric("Total Revenue", f"₹{total_revenue:.2f}")
            
            if "invoice_html" in st.session_state:
                st.markdown("---")
                st.success(f"🎉 Exit processed for **{st.session_state['receipt_plate']}**!")
                st.download_button(
                    label=f"📄 DOWNLOAD OFFICIAL INVOICE FILE ({st.session_state['receipt_plate']}.html)",
                    data=st.session_state["invoice_html"],
                    file_name=f"Official_Invoice_{st.session_state['receipt_plate']}.html",
                    mime="text/html",
                    use_container_width=True
                )

            st_frame = st.image([])
            st.markdown("---")
            
            table_col, chart_col = st.columns([1, 1])
            
            with table_col:
                st.subheader("📊 Live Enterprise Transaction Ledger")
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
            st.error("Missing slot map layout initialization asset. Please run `src/picker.py` first.")