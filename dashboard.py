# dashboard.py - Fixed version
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
import random
import time

# Page config
st.set_page_config(
    page_title="Vehicle Condition Monitoring System",
    page_icon="🚗",
    layout="wide"
)

# Initialize session state
if 'sensor_data' not in st.session_state:
    st.session_state.sensor_data = []
if 'anomalies' not in st.session_state:
    st.session_state.anomalies = []
if 'alerts' not in st.session_state:
    st.session_state.alerts = []
if 'monitoring_active' not in st.session_state:
    st.session_state.monitoring_active = False
if 'vehicle_ids' not in st.session_state:
    st.session_state.vehicle_ids = ["VEH001", "VEH002", "VEH003"]

# Function to generate sensor data
def generate_sensor_data():
    sensors = ["engine_temp", "oil_pressure", "rpm", "speed", 
               "fuel_level", "battery_voltage", "coolant_temp"]
    
    for vehicle_id in st.session_state.vehicle_ids:
        timestamp = datetime.now()
        
        reading = {
            "vehicle_id": vehicle_id,
            "timestamp": timestamp,
            "engine_temp": round(90 + np.random.normal(0, 2), 1),
            "oil_pressure": round(40 + np.random.normal(0, 3), 1),
            "rpm": round(2500 + np.random.normal(0, 200), 0),
            "speed": round(60 + np.random.normal(0, 10), 1),
            "fuel_level": round(65 + np.random.normal(0, 1), 1),
            "battery_voltage": round(12.6 + np.random.normal(0, 0.1), 2),
            "coolant_temp": round(85 + np.random.normal(0, 1.5), 1)
        }
        
        # Random anomaly (5% chance)
        if random.random() < 0.05:
            sensor = random.choice(sensors)
            old_value = reading[sensor]
            reading[sensor] = round(old_value + random.choice([30, -20]), 1)
            
            st.session_state.anomalies.append({
                "vehicle_id": vehicle_id,
                "timestamp": timestamp,
                "sensor": sensor,
                "normal_value": old_value,
                "anomaly_value": reading[sensor]
            })
            
            # Keep only last 50 anomalies
            if len(st.session_state.anomalies) > 50:
                st.session_state.anomalies = st.session_state.anomalies[-50:]
            
            # Create alert
            st.session_state.alerts.append({
                "vehicle_id": vehicle_id,
                "timestamp": timestamp.strftime("%H:%M:%S"),
                "severity": random.choice(["HIGH", "MEDIUM"]),
                "message": f"⚠️ Anomaly: {sensor} = {reading[sensor]} (normal: {old_value})"
            })
            
            if len(st.session_state.alerts) > 50:
                st.session_state.alerts = st.session_state.alerts[-50:]
        
        st.session_state.sensor_data.append(reading)
    
    # Keep only last 100 readings
    if len(st.session_state.sensor_data) > 100:
        st.session_state.sensor_data = st.session_state.sensor_data[-100:]

# Title
st.title("🚗 Vehicle Condition Monitoring System")
st.markdown("### AI-Powered Real-Time Vehicle Health Monitoring")

# Sidebar
with st.sidebar:
    st.header("Control Panel")
    
    if st.button("▶️ Start Monitoring", disabled=st.session_state.monitoring_active, type="primary", use_container_width=True):
        st.session_state.monitoring_active = True
    
    if st.button("⏹️ Stop Monitoring", disabled=not st.session_state.monitoring_active, use_container_width=True):
        st.session_state.monitoring_active = False
    
    if st.button("🔄 Reset Data", use_container_width=True):
        st.session_state.sensor_data = []
        st.session_state.anomalies = []
        st.session_state.alerts = []
    
    st.divider()
    
    selected_vehicle = st.selectbox("Select Vehicle", ["All"] + st.session_state.vehicle_ids)
    
    st.divider()
    st.subheader("System Status")
    if st.session_state.monitoring_active:
        st.success("● Active - Monitoring 3 vehicles")
    else:
        st.info("● Inactive - Click Start to begin")

# Generate data if monitoring
if st.session_state.monitoring_active:
    generate_sensor_data()

# Main content tabs
tab1, tab2, tab3 = st.tabs(["📊 Real-Time Monitoring", "🔍 Anomaly Detection", "🚨 Alerts"])

with tab1:
    st.header("Real-Time Sensor Data")
    
    if st.session_state.sensor_data:
        df = pd.DataFrame(st.session_state.sensor_data)
        
        # Filter by vehicle
        if selected_vehicle != "All":
            df = df[df["vehicle_id"] == selected_vehicle]
        
        # Metrics row
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Active Vehicles", len(st.session_state.vehicle_ids), delta="Online")
        with col2:
            st.metric("Total Readings", len(st.session_state.sensor_data))
        with col3:
            anomaly_count = len(st.session_state.anomalies)
            st.metric("Anomalies", anomaly_count, delta=f"{anomaly_count} total" if anomaly_count > 0 else None)
        with col4:
            alert_count = len(st.session_state.alerts)
            st.metric("Alerts", alert_count)
        
        st.divider()
        
        # Latest readings table
        st.subheader("📋 Latest Sensor Readings")
        cols_to_show = ["vehicle_id", "timestamp", "engine_temp", "oil_pressure", "rpm", "speed", "battery_voltage"]
        available_cols = [c for c in cols_to_show if c in df.columns]
        st.dataframe(df[available_cols].tail(10), use_container_width=True, hide_index=True)
        
        st.divider()
        
        # Charts
        st.subheader("📈 Sensor Trends")
        
        if not df.empty and "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            
            # Create two charts side by side
            col1, col2 = st.columns(2)
            
            with col1:
                # Engine Temperature Chart
                fig1 = go.Figure()
                for vehicle in df["vehicle_id"].unique():
                    vdf = df[df["vehicle_id"] == vehicle].tail(30)
                    fig1.add_trace(go.Scatter(
                        x=vdf["timestamp"],
                        y=vdf["engine_temp"],
                        mode="lines+markers",
                        name=vehicle,
                        line=dict(width=2)
                    ))
                fig1.update_layout(
                    title="Engine Temperature (°C)",
                    height=300,
                    margin=dict(l=0, r=0, t=30, b=0)
                )
                st.plotly_chart(fig1, use_container_width=True)
            
            with col2:
                # Oil Pressure Chart
                fig2 = go.Figure()
                for vehicle in df["vehicle_id"].unique():
                    vdf = df[df["vehicle_id"] == vehicle].tail(30)
                    fig2.add_trace(go.Scatter(
                        x=vdf["timestamp"],
                        y=vdf["oil_pressure"],
                        mode="lines+markers",
                        name=vehicle,
                        line=dict(width=2)
                    ))
                fig2.update_layout(
                    title="Oil Pressure (PSI)",
                    height=300,
                    margin=dict(l=0, r=0, t=30, b=0)
                )
                st.plotly_chart(fig2, use_container_width=True)
            
            # RPM and Speed charts
            col3, col4 = st.columns(2)
            
            with col3:
                fig3 = go.Figure()
                for vehicle in df["vehicle_id"].unique():
                    vdf = df[df["vehicle_id"] == vehicle].tail(30)
                    fig3.add_trace(go.Scatter(
                        x=vdf["timestamp"],
                        y=vdf["rpm"],
                        mode="lines+markers",
                        name=vehicle,
                        line=dict(width=2)
                    ))
                fig3.update_layout(
                    title="Engine RPM",
                    height=300,
                    margin=dict(l=0, r=0, t=30, b=0)
                )
                st.plotly_chart(fig3, use_container_width=True)
            
            with col4:
                fig4 = go.Figure()
                for vehicle in df["vehicle_id"].unique():
                    vdf = df[df["vehicle_id"] == vehicle].tail(30)
                    fig4.add_trace(go.Scatter(
                        x=vdf["timestamp"],
                        y=vdf["speed"],
                        mode="lines+markers",
                        name=vehicle,
                        line=dict(width=2)
                    ))
                fig4.update_layout(
                    title="Vehicle Speed (km/h)",
                    height=300,
                    margin=dict(l=0, r=0, t=30, b=0)
                )
                st.plotly_chart(fig4, use_container_width=True)
    else:
        st.info("👆 Click **Start Monitoring** in the sidebar to begin collecting vehicle data")
        st.markdown("""
        Once started, you'll see:
        - 📊 Real-time sensor readings from 3 vehicles
        - 📈 Live charts showing temperature, pressure, RPM, and speed
        - 🔍 Automatic anomaly detection
        - 🚨 Instant alerts for any issues
        """)

with tab2:
    st.header("🔍 Anomaly Detection Results")
    
    if st.session_state.anomalies:
        st.warning(f"⚠️ **{len(st.session_state.anomalies)}** anomalies detected across all vehicles")
        
        st.subheader("Recent Anomalies")
        anomaly_df = pd.DataFrame(st.session_state.anomalies[-20:])
        
        # Rename columns for display
        anomaly_df.columns = ["Vehicle ID", "Timestamp", "Sensor", "Normal Value", "Anomaly Value"]
        st.dataframe(anomaly_df, use_container_width=True, hide_index=True)
        
        # Anomaly statistics
        st.subheader("Anomaly by Sensor")
        sensor_counts = {}
        for a in st.session_state.anomalies:
            sensor = a["sensor"]
            sensor_counts[sensor] = sensor_counts.get(sensor, 0) + 1
        
        if sensor_counts:
            fig = go.Figure([go.Bar(x=list(sensor_counts.keys()), y=list(sensor_counts.values()))])
            fig.update_layout(title="Anomalies by Sensor Type", height=300)
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("✅ No anomalies detected yet. The system is monitoring for unusual patterns.")

with tab3:
    st.header("🚨 Alert Management")
    
    if st.session_state.alerts:
        st.subheader(f"Active Alerts ({len(st.session_state.alerts)} total)")
        
        for alert in reversed(st.session_state.alerts[-10:]):
            severity = alert.get("severity", "LOW")
            if severity == "CRITICAL":
                bg_color = "#ff4444"
                emoji = "🔴"
            elif severity == "HIGH":
                bg_color = "#ff8800"
                emoji = "🟠"
            else:
                bg_color = "#ffbb33"
                emoji = "🟡"
            
            st.markdown(f"""
            <div style="background-color: {bg_color}22; padding: 10px; border-left: 5px solid {bg_color}; margin: 5px 0; border-radius: 5px;">
                {emoji} <strong>{severity}</strong> | <strong>{alert['vehicle_id']}</strong> | {alert['timestamp']}<br>
                {alert['message']}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("📭 No alerts generated yet. Alerts appear when anomalies are detected.")

# Auto-refresh
if st.session_state.monitoring_active:
    time.sleep(1)
    st.rerun()