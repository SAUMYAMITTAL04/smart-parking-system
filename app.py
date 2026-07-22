import sys
import asyncio

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import streamlit as st
from src.database import init_db
from auth import render_login_page, logout
from views.customer import render_customer_view
from views.executive import render_executive_view
from views.manager import render_manager_view

st.set_page_config(page_title="Smart Parking Enterprise AI", layout="wide", page_icon="🚗")

# Initialize SQLite tables on startup
init_db()

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    st.session_state["user_role"] = None
    st.session_state["user_name"] = None

# --- ROUTING ENGINE ---
if not st.session_state["logged_in"]:
    render_login_page()
else:
    # Sidebar Session Header
    st.sidebar.markdown(f"### 👤 User: **{st.session_state['user_name']}**")
    st.sidebar.caption(f"Role: **{st.session_state['user_role']}**")
    st.sidebar.button("🚪 Logout", on_click=logout, use_container_width=True)
    st.sidebar.markdown("---")

    # Render View Based on Role
    role = st.session_state["user_role"]
    if role == "Customer":
        render_customer_view()
    elif role == "Executive":
        render_executive_view()
    elif role == "Manager":
        render_manager_view()