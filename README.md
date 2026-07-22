# 🚗 Smart Parking Enterprise AI

An intelligent, real-time parking management and monitoring platform powered by **OpenCV**, **EasyOCR**, and **Streamlit**. 

This enterprise solution integrates automated entrance gate vehicle tracking via **Number Plate Recognition** with continuous **Parking Spot Occupancy Analytics** to streamline operations, compute dynamic billing, and visualize live system loads.

---

## 🌟 Key Features

* **🎥 Entrance Gate Number Plate Recognition (ANPR):** Real-time computer vision engine that detects vehicles, localizes license plates via contour analysis, and extracts plate text using EasyOCR.
* **🅿️ Real-Time Parking Spot Occupancy Detector:** Uses ROI (Region of Interest) image processing and background masking to identify open vs. occupied slots in real time.
* **📈 Live Load Analytics:** Interactive dashboard monitoring system occupancy, active vehicle count, and gross revenue metrics.
* **📋 Active Vehicle Log & Checkout:** Instant tracking of active vehicles, entrance timestamps, slot allocations, dynamic fee calculation, and payment checkout processing.
* **🖼️ Manual Image / Camera Upload:** Secondary input mode to upload photos or take camera snapshots for manual plate registration.
* **🔍 Full Database Search & Analytics:** Historical vehicle log browser with live filtering by license plate number.

---

## 📁 Repository Structure

```text
smart-parking-system/
├── app.py                   # Main application entry point & navigation
├── auth.py                  # User authentication & role management
├── requirements.txt         # Project dependencies
├── data/                    # Video feeds, database, and slot configurations
│   ├── parking_analytics.db # SQLite database storing vehicle logs
│   ├── slots.json           # Defined ROI coordinates for parking spots
│   └── parking_video.mp4    # Sample feed for slot detection
├── src/                     # Core computer vision & logic modules
│   ├── anpr.py              # Number plate detection & OCR processing
│   ├── database.py          # Database queries & SQLite connections
│   └── detector.py          # Parking spot occupancy analysis
└── views/                   # Dashboard role-based interfaces
    ├── manager.py           # Operations Center & Live ANPR Dashboard
    ├── executive.py         # Management reporting & analytics
    └── customer.py          # Customer slot availability view
