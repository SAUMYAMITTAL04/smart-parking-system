import streamlit as st
import cv2
import os
import time
import pandas as pd
from datetime import datetime
from src.detector import ParkingDetector
from src.database import get_connection, get_next_available_slot, is_recently_logged
from src.anpr import detect_and_draw_plates, extract_license_plate_from_bytes

def render_manager_view():
    st.title("🚗 Operations Center & Monitoring Dashboard")
    st.markdown("Independent Real-Time ANPR Gate Scanner and Parking Spot Occupancy Detector.")

    # --- TOP METRICS OVERVIEW ---
    col1, col2, col3, col4 = st.columns(4)
    available_metric = col1.metric("Available Slots", "0")
    occupied_metric = col2.metric("Occupied Slots", "0")
    occupancy_rate = col3.metric("System Load", "0%")
    
    conn = get_connection()
    rev_df = pd.read_sql_query("SELECT SUM(fee_amount) as total_rev FROM parking_logs", conn)
    total_revenue = rev_df["total_rev"].iloc[0] if rev_df["total_rev"].iloc[0] is not None else 0.0
    conn.close()
    col4.metric("Total Revenue", f"₹{total_revenue:.2f}")

    st.markdown("---")

    # --- MAIN DASHBOARD COLUMNS ---
    anpr_col, slot_col = st.columns(2)

    # =========================================================
    # COLUMN 1: AUTOMATIC NUMBER PLATE RECOGNITION (ANPR)
    # =========================================================
    with anpr_col:
        st.subheader("📹 Entrance Gate Number Plate Recognition")
        
        auto_anpr = st.toggle("Enable Live ANPR Auto-Scan", value=True)

        anpr_input_mode = st.tabs(["🎥 Live ANPR Video", "🖼️ Snap / Upload Image"])

        with anpr_input_mode[1]:
            img_file = st.file_uploader("Upload Image", type=["jpg", "png", "jpeg"], key="anpr_upload")
            cam_file = st.camera_input("Take Photo", key="anpr_camera")
            target_file = img_file if img_file is not None else cam_file
            
            if target_file is not None:
                with st.spinner("Scanning plate via OCR..."):
                    detected_plate = extract_license_plate_from_bytes(target_file)
                    
                st.success(f"Detected Plate: **{detected_plate}**")
                if st.button("Register Entry", use_container_width=True, key="reg_manual_entry"):
                    entry_time_str = datetime.now().strftime("%H:%M:%S")
                    assigned_slot = get_next_available_slot()
                    
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO parking_logs (vehicle_plate, entry_time, assigned_space, status, fee_amount) VALUES (?, ?, ?, ?, ?)",
                        (detected_plate, entry_time_str, assigned_slot, "Checked-In", 0.0)
                    )
                    conn.commit()
                    conn.close()
                    st.toast(f"✅ Registered: {detected_plate} -> {assigned_slot}", icon="🚗")
                    st.rerun()

        with anpr_input_mode[0]:
            # Live Banner displaying the latest scanned vehicle plate
            detection_banner = st.empty()
            st_anpr_frame = st.image([])

        with st.expander("💳 Process Vehicle Exit"):
            conn = get_connection()
            active_vehicles = pd.read_sql_query("SELECT vehicle_plate FROM parking_logs WHERE status='Checked-In'", conn)
            conn.close()
            
            if not active_vehicles.empty:
                selected_plate = st.selectbox("Select Vehicle at Exit:", active_vehicles["vehicle_plate"], key="exit_select")
                if st.button("Checkout & Collect Payment", use_container_width=True, key="btn_checkout"):
                    exit_time_str = datetime.now().strftime("%H:%M:%S")
                    fee = 50.00
                    
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute(
                        "UPDATE parking_logs SET exit_time=?, status='Checked-Out', fee_amount=? WHERE vehicle_plate=? AND status='Checked-In'",
                        (exit_time_str, fee, selected_plate)
                    )
                    conn.commit()
                    conn.close()
                    st.success(f"Vehicle {selected_plate} Checked Out!")
                    st.rerun()
            else:
                st.info("No active vehicles inside.")

    # =========================================================
    # COLUMN 2: PARKING SPOT OCCUPANCY DETECTOR
    # =========================================================
    with slot_col:
        st.subheader("🅿️ Parking Lot Occupancy Feed")
        st_slot_frame = st.image([])

        st.subheader("📈 Live Load Analytics")
        chart_placeholder = st.empty()

    st.markdown("---")

    # =========================================================
    # FULL DETECTED CAR PLATES LOG TABLE
    # =========================================================
    st.subheader("📋 Detected Car Plates Log")
    
    log_tab_live, log_tab_full = st.tabs(["⚡ Active Stream Feed", "🔍 Full Database Search & Export"])
    
    with log_tab_live:
        anpr_log_table = st.empty()

    with log_tab_full:
        conn = get_connection()
        df_full_logs = pd.read_sql_query(
            """
            SELECT 
                id AS 'ID',
                vehicle_plate AS 'License Plate',
                entry_time AS 'Detected/Entry Time',
                exit_time AS 'Exit Time',
                assigned_space AS 'Assigned Slot',
                status AS 'Status',
                fee_amount AS 'Fee (₹)'
            FROM parking_logs 
            ORDER BY id DESC
            """, 
            conn
        )
        conn.close()

        search_query = st.text_input("Search Plate Number:", placeholder="e.g. GX15 OGJ", key="search_plate")
        
        if search_query:
            filtered_df = df_full_logs[df_full_logs['License Plate'].str.contains(search_query.upper(), na=False)]
            st.dataframe(filtered_df, use_container_width=True, hide_index=True)
        else:
            st.dataframe(df_full_logs, use_container_width=True, hide_index=True)

    # Session State Management
    if "chart_data" not in st.session_state:
        st.session_state.chart_data = pd.DataFrame(columns=["Time", "Occupied"])

    if "last_detected_plate" not in st.session_state:
        st.session_state.last_detected_plate = "None"

    # =========================================================
    # DUAL VIDEO PROCESSING LOOP
    # =========================================================
    anpr_video_path = "data/Traffic Control CCTV.mp4"
    if not os.path.exists(anpr_video_path):
        anpr_video_path = "data/Automatic Number Plate Recognition (ANPR) _ Vehicle Number Plate Recognition (1).mp4"
    if not os.path.exists(anpr_video_path):
        anpr_video_path = "data/parking_video.mp4"

    slot_video_path = "data/parking_video.mp4"

    if os.path.exists(anpr_video_path) and os.path.exists(slot_video_path) and os.path.exists("data/slots.json"):
        cap_anpr = cv2.VideoCapture(anpr_video_path)
        cap_slot = cv2.VideoCapture(slot_video_path)
        detector = ParkingDetector("data/slots.json")

        last_chart_update = time.time()

        while cap_anpr.isOpened() and cap_slot.isOpened():
            ret_anpr, frame_anpr = cap_anpr.read()
            ret_slot, frame_slot = cap_slot.read()

            if not ret_anpr:
                cap_anpr.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue
            if not ret_slot:
                cap_slot.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue

            # ----------------------------------------------------
            # 1. MULTI-CAR ANPR SCAN & BOUNDING BOX ANNOTATION
            # ----------------------------------------------------
            if auto_anpr:
                # Detect ALL visible plates and draw green bounding boxes on frame
                annotated_frame, found_plates = detect_and_draw_plates(frame_anpr)

                for detected_plate in found_plates:
                    if detected_plate and not is_recently_logged(detected_plate):
                        st.session_state.last_detected_plate = detected_plate
                        entry_time_str = datetime.now().strftime("%H:%M:%S")
                        assigned_slot = get_next_available_slot()
                        
                        conn = get_connection()
                        cursor = conn.cursor()
                        cursor.execute(
                            "INSERT INTO parking_logs (vehicle_plate, entry_time, assigned_space, status, fee_amount) VALUES (?, ?, ?, ?, ?)",
                            (detected_plate, entry_time_str, assigned_slot, "Checked-In", 0.0)
                        )
                        conn.commit()
                        conn.close()
                        st.toast(f"🚘 Detected Plate: {detected_plate}", icon="🔍")
            else:
                annotated_frame = frame_anpr

            # Update live header banner
            if st.session_state.last_detected_plate != "None":
                detection_banner.info(f"🚘 **Last Detected Plate:** `{st.session_state.last_detected_plate}`")
            else:
                detection_banner.caption("Scanning stream for vehicle plates...")

            # Render ANPR frame with bounding boxes overlaid
            st_anpr_frame.image(cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB))

            # ----------------------------------------------------
            # 2. PROCESS PARKING SLOT DETECTION FRAME
            # ----------------------------------------------------
            output_slot_frame, empty, occupied = detector.process_frame(frame_slot)
            total = empty + occupied
            rate_val = int((occupied / total) * 100) if total > 0 else 0

            # Render Slot stream
            st_slot_frame.image(cv2.cvtColor(output_slot_frame, cv2.COLOR_BGR2RGB))

            # Update top metrics
            available_metric.metric("Available Slots", str(empty))
            occupied_metric.metric("Occupied Slots", str(occupied))
            occupancy_rate.metric("System Load", f"{rate_val}%")

            # Update live active vehicle log table
            conn = get_connection()
            df_logs = pd.read_sql_query(
                "SELECT vehicle_plate as 'Plate', entry_time as 'Detected Time', assigned_space as 'Slot', status as 'Status' FROM parking_logs ORDER BY id DESC LIMIT 10", 
                conn
            )
            conn.close()
            anpr_log_table.dataframe(df_logs, use_container_width=True, hide_index=True)

            # Update load graph
            if time.time() - last_chart_update > 1.0:
                current_time = datetime.now().strftime("%H:%M:%S")
                new_row = pd.DataFrame([{"Time": current_time, "Occupied": occupied}])
                st.session_state.chart_data = pd.concat([st.session_state.chart_data, new_row], ignore_index=True).tail(15)
                last_chart_update = time.time()

            if not st.session_state.chart_data.empty:
                chart_placeholder.line_chart(st.session_state.chart_data.set_index("Time"), use_container_width=True)

            time.sleep(0.01)

        cap_anpr.release()
        cap_slot.release()
    else:
        st.error("Missing required video or JSON configuration files in `data/` directory.")