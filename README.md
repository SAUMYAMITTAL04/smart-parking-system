# 🚗 Smart Parking Management & ANPR Monitoring System

An end-to-end, real-time parking management and analytics dashboard built with **Python**, **OpenCV**, **EasyOCR**, and **Streamlit**. The system integrates live Computer Vision for parking space occupancy detection alongside Automatic Number Plate Recognition (ANPR) for automated entry/exit logging, multi-role views, and revenue analytics.

---

## ✨ Features

- **📹 Real-Time ANPR Gate Scanning**: Detects and reads license plates from video streams using OpenCV and EasyOCR to automate vehicle check-ins.
- **🖼️ Manual Image OCR & Gate Entry**: Allows operators to upload plate photos or capture webcam images for manual check-ins.
- **🅿️ Parking Slot Occupancy Detector**: Processes live camera feeds against slot coordinates (`data/slots.json`) defined via the slot picker utility (`src/picker.py`).
- **👥 Multi-Role Dashboard Views**:
  - **Manager View**: Live video feeds, ANPR gate scanner, capacity monitoring, checkout processing, and operations table.
  - **Executive View**: Higher-level analytics, revenue trends, and system load summaries.
  - **Customer View**: Driver-facing portal to check real-time spot availability.
- **🔐 User Authentication**: Secured login flow using `auth.py`.
- **📊 Dynamic Analytics**: Interactive real-time load charts with filterable time windows (`Last 15`, `Last 30`, `Full Session`).
- **📋 Persistent Database**: Database integration (`parking_analytics.db`) to record vehicle check-in/check-out logs and track fees.

---

## 📁 Project Structure

```text
├── data/
│   ├── anpr_video.mp4        # Sample video feed for ANPR gate scanning
│   ├── parking_video.mp4     # Sample video feed for parking lot occupancy
│   ├── parking_analytics.db  # Database copy stored in data directory
│   └── slots.json            # Parking spot bounding box coordinates
├── src/
│   ├── __init__.py
│   ├── anpr.py               # ANPR detection pipeline & OCR logic
│   ├── detector.py           # Parking spot occupancy detection engine
│   └── picker.py             # Utility tool to draw and define parking spot coordinates
├── views/
│   ├── __init__.py
│   ├── customer.py           # Driver-facing slot availability view
│   ├── executive.py          # High-level analytics and revenue dashboard
│   └── manager.py           # Operations center & live stream monitoring view
├── .gitignore
├── app.py                    # Main Streamlit application entry point
├── auth.py                   # User authentication & access control
├── parking_analytics.db      # Main SQLite database for parking logs
├── requirements.txt          # Required Python packages
└── README.md                 # Project documentation
