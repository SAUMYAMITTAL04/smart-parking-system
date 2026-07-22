import streamlit as st
import pandas as pd
from src.database import get_connection

def render_executive_view():
    st.title("📈 Executive Business Intelligence Analytics")
    st.markdown("Historical utilization trends, peak load distributions, and revenue metrics.")
    
    conn = get_connection()
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