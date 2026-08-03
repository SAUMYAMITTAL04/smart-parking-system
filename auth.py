import streamlit as st
USERS = {
    "driver": {"password": "user123", "role": "Customer", "name": "Valued Guest"},
    "manager": {"password": "admin123", "role": "Manager", "name": "Operations Manager"},
    "exec": {"password": "exec123", "role": "Executive", "name": "Executive Analyst"}
}

def render_login_page():
    st.title("🚗 Smart Parking Enterprise Portal")
    st.subheader("Sign In to Access Your Portal")

    col_login, col_info = st.columns([1, 1])

    with col_login:
        username_input = st.text_input("Username").strip()
        password_input = st.text_input("Password", type="password").strip()

        if st.button("🔓 Sign In", width="stretch"):
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

def logout():
    st.session_state["logged_in"] = False
    st.session_state["user_role"] = None
    st.session_state["user_name"] = None
    st.rerun()
