import sys
import asyncio

# Fix for Windows asyncio ConnectionResetError bug
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import streamlit as st
import sqlite3
import os

# Set main Streamlit page configuration (must only be called once globally)
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

# --- IMPORT VIEW RENDERERS ---
from views.login import render_login_page, logout
from views.customer import render_customer_view
from views.manager import render_manager_view
from views.executive import render_executive_view

# Initialize Session State
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    st.session_state["user_role"] = None
    st.session_state["user_name"] = None

# ==========================================
# 🔑 AUTHENTICATION CHECK
# ==========================================
if not st.session_state["logged_in"]:
    render_login_page()
    st.stop()

# ==========================================
# 📊 DASHBOARD ROUTER (AFTER LOGGING IN)
# ==========================================

# Sidebar Navigation Header
st.sidebar.markdown(f"### 👤 User: **{st.session_state['user_name']}**")
st.sidebar.caption(f"Role: **{st.session_state['user_role']}**")
st.sidebar.button("🚪 Logout", on_click=logout, use_container_width=True)
st.sidebar.markdown("---")

# Route user based on their authenticated role
if st.session_state["user_role"] == "Customer":
    render_customer_view()

elif st.session_state["user_role"] == "Executive":
    render_executive_view()

elif st.session_state["user_role"] == "Manager":
    render_manager_view()
