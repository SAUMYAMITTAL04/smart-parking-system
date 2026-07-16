import streamlit as st
import cv2
import os
import time
from src.detector import ParkingDetector

st.set_page_config(page_title="Smart Parking Vision Dashboard", layout="wide")

st.title("🚗 Smart Parking Automated Infrastructure Analytics")
st.markdown("Real-time edge computer vision parking metrics engine powered by YOLOv8.")

# Sidebar Controls
st.sidebar.header("System Settings")
video_source = st.sidebar.text_input("Video Feed Path", "data/parking_video.mp4")

# Initialize Pipeline Engine Components
if os.path.exists("data/slots.json"):
    detector = ParkingDetector("data/slots.json")
    
    # Dynamic Stat Metrics Cards Component Setup
    col1, col2, col3 = st.columns(3)
    available_metric = col1.metric("Available Slots", "0")
    occupied_metric = col2.metric("Occupied Slots", "0")
    occupancy_rate = col3.metric("System Load", "0%")
    
    # Real-time Video Stream Window Layout Target Setup
    st_frame = st.image([])

    cap = cv2.VideoCapture(video_source)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            # Restart loop if stock demo video finishes streaming
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue
            
        # Execute Frame Processing Calculations
        output_frame, empty, occupied = detector.process_frame(frame)
        
        # Calculate rates dynamically for analytical data displays
        total = empty + occupied
        rate_val = int((occupied / total) * 100) if total > 0 else 0
        
        # Refresh Display Metrics Elements dynamically without page reloads
        available_metric.metric("Available Slots", str(empty))
        occupied_metric.metric("Occupied Slots", str(occupied))
        occupancy_rate.metric("System Load", f"{rate_val}%")
        
        # Render processing stream output into Streamlit container frame layout
        st_frame.image(cv2.cvtColor(output_frame, cv2.COLOR_BGR2RGB))
        time.sleep(0.01)

    cap.release()
else:
    st.error("Missing slot map layout initialization asset. Please run `src/picker.py` configurations tool step first.")