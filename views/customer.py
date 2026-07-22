import streamlit as st
import os
import cv2
from src.detector import ParkingDetector

def render_customer_view():
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
        st.error("Missing slot map layout initialization asset. Run `src/picker.py` first.")