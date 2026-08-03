import os
import cv2
import io
import streamlit as st
import pandas as pd
from datetime import datetime
from src.detector import ParkingDetector

def generate_qr_image(data_str: str):
    """Generates an in-memory QR code image byte buffer."""
    try:
        import qrcode
        qr = qrcode.QRCode(version=1, box_size=6, border=2)
        qr.add_data(data_str)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
    except ImportError:
        return None

def render_customer_view():
    col_head1, col_head2 = st.columns([3, 1])
    with col_head1:
        st.title("📲 Live Driver Navigation & Parking Portal")
        st.caption("Real-time spot availability, zone guidance, and digital kiosk services.")
    with col_head2:
        st.markdown("<br>", unsafe_allow_html=True)
        st.success("🟢 Barrier Gate Status: Active")

    st.markdown("---")

    # Slot detection check
    if os.path.exists("data/slots.json"):
        detector = ParkingDetector("data/slots.json")
        cap = cv2.VideoCapture("data/parking_video.mp4")
        ret, frame = cap.read()
        cap.release()
        
        if ret:
            _, empty, occupied = detector.process_frame(frame)
        else:
            empty, occupied = 18, 42
    else:
        empty, occupied = 12, 48

    total_slots = empty + occupied
    occupancy_pct = int((occupied / total_slots) * 100) if total_slots > 0 else 0

    # Banner Alert
    if empty > 5:
        st.success(f"### 🟢 PARKING AVAILABLE: {empty} SPOTS OPEN (Occupancy: {occupancy_pct}%)")
    elif 0 < empty <= 5:
        st.warning(f"### 🟡 LIMITED PARKING: ONLY {empty} SPOTS REMAINING!")
    else:
        st.error("### 🔴 PARKING LOT FULL - NEXT AVAILABLE ENTRY ESTIMATED IN 10 MINS")

    st.markdown("---")

    # Live Metrics Bar
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Available Spaces", f"{empty} Slots", delta=f"{empty} Open", delta_color="normal")
    m2.metric("Occupied Spaces", f"{occupied} Slots")
    m3.metric("Standard Parking Rate", "₹50 / Hr", "Contactless Enabled")
    m4.metric("EV Charging Rate", "₹80 / Hr", "Fast Charger 50kW")

    st.markdown("<br>", unsafe_allow_html=True)

    # Main Interactive Navigation Section
    nav_col1, nav_col2 = st.columns([3, 2])

    with nav_col1:
        st.subheader("🗺️ Real-Time Zone Breakdown & Spot Allocation")
        
        zones_data = [
            {"Zone": "Zone A (Ground Floor - North)", "Type": "Standard", "Open": max(0, int(empty * 0.4)), "Total": 20, "Status": "Open"},
            {"Zone": "Zone B (Ground Floor - South)", "Type": "Standard", "Open": max(0, int(empty * 0.3)), "Total": 20, "Status": "Open"},
            {"Zone": "Zone C (EV Charging Bays)", "Type": "EV Only", "Open": max(0, int(empty * 0.2)), "Total": 10, "Status": "Charging Available"},
            {"Zone": "Zone D (Accessible / VIP)", "Type": "Priority", "Open": max(0, int(empty * 0.1)), "Total": 10, "Status": "Permit Required"},
        ]
        df_zones = pd.DataFrame(zones_data)
        
        st.dataframe(
            df_zones,
            column_config={
                "Zone": st.column_config.TextColumn("Parking Zone", help="Zone Location"),
                "Type": st.column_config.TextColumn("Category"),
                "Open": st.column_config.ProgressColumn(
                    "Free Bays",
                    help="Number of free slots available",
                    format="%d Open",
                    min_value=0,
                    max_value=20,
                ),
                "Status": st.column_config.TextColumn("Zone Status"),
            },
            width="stretch",
            hide_index=True
        )

        st.info("💡 **Smart Wayfinding Tip:** Head to **Zone A** for shortest walking distance to Main Mall Elevator Entrance.")

    with nav_col2:
        st.subheader("💳 Parking Fee Estimator")
        with st.container(border=True):
            v_type = st.selectbox("Vehicle Type", ["Car / SUV", "Two-Wheeler", "EV (Fast Charge)", "Commercial Vehicle"])
            duration = st.slider("Expected Parking Duration (Hours)", 1, 12, 2)
            
            rate_map = {"Car / SUV": 50, "Two-Wheeler": 20, "EV (Fast Charge)": 80, "Commercial Vehicle": 100}
            total_est = duration * rate_map[v_type]
            
            st.markdown(f"### Estimated Total: **₹{total_est}**")
            st.caption("Includes automated ANPR ticketless entry & exit grace period (15 mins).")

            if st.button("🎫 Generate Digital Express Entry Pass", width="stretch"):
                pass_code = f"PARK-EXPRESS-{datetime.now().strftime('%Y%m%d%H%M')}"
                st.success("Pass Generated! Scan your vehicle registration at barrier entrance.")
                
                qr_bytes = generate_qr_image(pass_code)
                if qr_bytes:
                    st.image(qr_bytes, caption=f"Express Entry Pass Code: {pass_code}", width=220)
                else:
                    st.code(pass_code, language="text")

    st.markdown("---")
    st.caption("Smart Parking Enterprise System • ANPR & RFID Active Gates • Live Support: +91 1800-PARK-NOW")
