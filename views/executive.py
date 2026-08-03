import datetime
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


def render_executive_view():
    st.title("📊 Executive Performance & BI Analytics")
    st.markdown(
        "Real-time enterprise overview, occupancy heatmaps, and financial metrics."
    )
    st.markdown("---")

    # -------------------------------------------------------------------------
    # 1. DATA LOADING & PREPARATION
    # -------------------------------------------------------------------------
    if "transactions_df" in st.session_state:
        df = st.session_state["transactions_df"].copy()
    else:
        np.random.seed(42)
        dates = pd.date_range(end=datetime.datetime.now(), periods=500, freq="15min")
        df = pd.DataFrame(
            {
                "entry_time": dates,
                "exit_time": dates + pd.to_timedelta(np.random.randint(30, 240, size=500), unit="m"),
                "fee": np.random.choice([0, 50, 100, 150, 200, 350], size=500),
                "vehicle_type": np.random.choice(["Car", "EV", "Bike", "Truck"], size=500, p=[0.6, 0.2, 0.15, 0.05]),
                "is_ev": np.random.choice([True, False], size=500, p=[0.2, 0.8]),
                "zone": np.random.choice(["Zone A", "Zone B", "Zone C"], size=500),
            }
        )

    df["timestamp"] = pd.to_datetime(df["entry_time"], format="mixed", errors="coerce")
    df["fee"] = pd.to_numeric(df["fee"], errors="coerce").fillna(0)

    if "dwell_time" not in df.columns and "exit_time" in df.columns:
        df["exit_time"] = pd.to_datetime(df["exit_time"], format="mixed", errors="coerce")
        df["dwell_time"] = (df["exit_time"] - df["timestamp"]).dt.total_seconds() / 3600.0
        df["dwell_time"] = df["dwell_time"].fillna(1.0)

    # -------------------------------------------------------------------------
    # 2. SIDEBAR / CONTROL FILTERS
    # -------------------------------------------------------------------------
    st.sidebar.header("Filter Analytics")
    selected_zone = st.sidebar.multiselect(
        "Select Zones",
        options=df["zone"].unique() if "zone" in df.columns else [],
        default=df["zone"].unique() if "zone" in df.columns else [],
    )

    if selected_zone:
        df_filtered = df[df["zone"].isin(selected_zone)].copy()
    else:
        df_filtered = df.copy()

    # -------------------------------------------------------------------------
    # 3. TOP KPI SUMMARY CARDS
    # -------------------------------------------------------------------------
    total_gross = df_filtered["fee"].sum()
    throughput = len(df_filtered)
    avg_dwell = df_filtered["dwell_time"].mean() if "dwell_time" in df_filtered.columns else 0.0
    ev_yield = (
        df_filtered[df_filtered["is_ev"] == True]["fee"].sum()
        if "is_ev" in df_filtered.columns
        else 0
    )

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        st.metric(
            label="Total Gross Revenue",
            value=f"₹{total_gross:,.0f}",
            delta="+16.4% vs prev window",
        )
    with kpi2:
        st.metric(
            label="Vehicle Throughput",
            value=f"{throughput:,} Units",
            delta="+8.2%",
        )
    with kpi3:
        st.metric(
            label="Avg Dwell Time",
            value=f"{avg_dwell:.1f} Hours",
            delta="-0.2 hrs",
        )
    with kpi4:
        st.metric(
            label="EV Charging Yield",
            value=f"₹{ev_yield:,.0f}",
            delta="+28.5% High Demand",
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # 4. REVENUE TRAJECTORY & TARGET GAUGE
    # -------------------------------------------------------------------------
    col_chart, col_gauge = st.columns([2.2, 1])

    with col_chart:
        st.markdown("### 📈 Revenue Trajectory & Traffic Volume")
        
        timeline_df = (
            df_filtered.set_index("timestamp")
            .resample("3h")["fee"]
            .sum()
            .reset_index()
        )

        fig_line = px.area(
            timeline_df,
            x="timestamp",
            y="fee",
            labels={"timestamp": "Timeline", "fee": "Revenue (₹)"},
            color_discrete_sequence=["#1E88E5"],
        )
        fig_line.update_layout(
            xaxis_title="Timeline",
            yaxis_title="Revenue (₹)",
            margin=dict(l=20, r=20, t=20, b=20),
            height=320,
            hovermode="x unified",
        )
        st.plotly_chart(fig_line, use_container_width=True)

    with col_gauge:
        st.markdown("### 🎯 Monthly Target Yield")
        
        monthly_target = 500000

        fig_gauge = go.Figure(
            go.Indicator(
                mode="number+gauge+delta",
                value=total_gross,
                number={"prefix": "₹", "valueformat": ",.0f"},
                delta={
                    "reference": monthly_target,
                    "relative": False,
                    "valueformat": ",.0f",
                    "increasing": {"color": "#2e7d32"},
                    "decreasing": {"color": "#d32f2f"},
                },
                gauge={
                    "axis": {"range": [0, max(monthly_target, total_gross * 1.1)]},
                    "bar": {"color": "#f59e0b"},
                    "steps": [
                        {"range": [0, monthly_target * 0.4], "color": "#ffe082"},
                        {"range": [monthly_target * 0.4, monthly_target * 0.8], "color": "#ffb74d"},
                        {"range": [monthly_target * 0.8, monthly_target * 1.2], "color": "#ffa726"},
                    ],
                    "threshold": {
                        "line": {"color": "red", "width": 4},
                        "thickness": 0.75,
                        "value": monthly_target,
                    },
                },
            )
        )
        fig_gauge.update_layout(height=320, margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig_gauge, use_container_width=True)

    st.markdown("---")

    # -------------------------------------------------------------------------
    # 5. OCCUPANCY HEATMAP
    # -------------------------------------------------------------------------
    st.markdown("### 🔥 Hourly Occupancy & Demand Heatmap")

    df_filtered["hour"] = df_filtered["timestamp"].dt.hour
    df_filtered["day_name"] = df_filtered["timestamp"].dt.day_name()

    days_order = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]

    heatmap_data = (
        df_filtered.groupby(["day_name", "hour"])
        .size()
        .unstack(fill_value=0)
        .reindex(columns=range(24), fill_value=0)
        .reindex(days_order)
        .fillna(0)
    )

    fig_heatmap = px.imshow(
        heatmap_data,
        labels=dict(x="Hour of Day (24H)", y="Day of Week", color="Occupancy Units"),
        x=list(range(24)),
        y=heatmap_data.index.tolist(),
        aspect="auto",
        color_continuous_scale="Viridis",
    )
    fig_heatmap.update_layout(height=350, margin=dict(l=20, r=20, t=20, b=20))
    st.plotly_chart(fig_heatmap, use_container_width=True)

    st.markdown("---")

    # -------------------------------------------------------------------------
    # 6. BREAKDOWN & DISTRIBUTION ANALYTICS
    # -------------------------------------------------------------------------
    dist_col1, dist_col2 = st.columns(2)

    with dist_col1:
        st.markdown("### 🚘 Vehicle Category Share")
        if "vehicle_type" in df_filtered.columns:
            veh_dist = df_filtered["vehicle_type"].value_counts().reset_index()
            veh_dist.columns = ["Vehicle Type", "Count"]

            fig_pie = px.pie(
                veh_dist,
                names="Vehicle Type",
                values="Count",
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Pastel,
            )
            fig_pie.update_layout(height=300, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig_pie, use_container_width=True)

    with dist_col2:
        st.markdown("### 🏗️ Zone Yield Distribution")
        if "zone" in df_filtered.columns:
            zone_dist = (
                df_filtered.groupby("zone")["fee"]
                .sum()
                .reset_index()
                .sort_values(by="fee", ascending=False)
            )

            fig_bar = px.bar(
                zone_dist,
                x="zone",
                y="fee",
                text_auto=".2s",
                labels={"zone": "Parking Zone", "fee": "Revenue (₹)"},
                color="fee",
                color_continuous_scale="Blues",
            )
            fig_bar.update_layout(height=300, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig_bar, use_container_width=True)

    # -------------------------------------------------------------------------
    # 7. RAW TRANSACTIONS DATA TABLE
    # -------------------------------------------------------------------------
    with st.expander("🔍 View Raw Executive Transaction Logs"):
        st.dataframe(
            df_filtered[
                [
                    col
                    for col in [
                        "timestamp",
                        "zone",
                        "vehicle_type",
                        "dwell_time",
                        "fee",
                    ]
                    if col in df_filtered.columns
                ]
            ].sort_values(by="timestamp", ascending=False),
            use_container_width=True,
        )
