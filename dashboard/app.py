import streamlit as st
import pandas as pd
import redis
import json
import plotly.express as px
import time

# --- CONFIGURATION ---
st.set_page_config(
    page_title="Zombie Hunter Dashboard",
    page_icon="🛡️",
    layout="wide"
)

# Connect to Redis (The Brain Memory)
@st.cache_resource
def get_redis_client():
    return redis.Redis(host='localhost', port=6379, decode_responses=True)

try:
    r = get_redis_client()
    r.ping()
except redis.ConnectionError:
    st.error("🚨 Redis is DOWN! Start Docker: `docker start zombie-redis`")
    st.stop()

# --- TITLE & HEADER ---
st.title("🛡️ Zombie API Hunter | Live Traffic")
st.markdown("Monitoring real-time traffic flow through the Python Proxy.")

# --- DATA LOADING ---
def load_data():
    # Fetch all logs from the Redis list 'traffic_logs'
    # lrange(key, start, end) -> 0, -1 means "everything"
    raw_logs = r.lrange("traffic_logs", 0, -1)

    if not raw_logs:
        return pd.DataFrame() # Empty if no data

    # Parse JSON strings into a List of Dicts
    data = [json.loads(log) for log in raw_logs]
    df = pd.DataFrame(data)
    return df

# Refresh Button
if st.button('🔄 Refresh Data'):
    st.rerun()

# Get Data
df = load_data()

if df.empty:
    st.warning("⚠️ No traffic data found yet. Send some requests!")
    st.stop()


# --- SIDEBAR FILTERS ---
    st.sidebar.header("🔍 Forensics Filters")
    
    # Filter by IP
    all_ips = ["All"] + list(df['ip'].unique())
    selected_ip = st.sidebar.selectbox("Filter by IP:", all_ips)

    # Filter by Action
    if 'action' in df.columns:
        all_actions = ["All"] + list(df['action'].unique())
        selected_action = st.sidebar.selectbox("Filter by Outcome:", all_actions)
    else:
        selected_action = "All"

    # Apply Filters
    if selected_ip != "All":
        df = df[df['ip'] == selected_ip]
    
    if selected_action != "All":
        df = df[df['action'] == selected_action]

# --- KPI METRICS ---
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Total Requests", len(df))

with col2:
    # Count unique IPs
    unique_ips = df['ip'].nunique()
    st.metric("Unique Attackers (IPs)", unique_ips)

with col3:
    # Most common path
    top_path = df['path'].mode()[0] if not df.empty else "N/A"
    st.metric("Top Target Path", top_path)

st.markdown("---")

# --- CHARTS ---
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("🛡️ Threat Detection Status")
    # NEW: Visualize Blocked vs Allowed
    if 'action' in df.columns:
        fig_action = px.pie(
            df, 
            names='action', 
            title='Blocked vs Allowed Traffic', 
            color='action',
            color_discrete_map={
                'ALLOWED': '#22c55e',       # Green
                'BLOCKED_AI': '#ef4444',    # Red
                'BLOCKED_RATE': '#eab308'   # Yellow
            }
        )
        st.plotly_chart(fig_action, use_container_width=True)
    else:
        st.info("Waiting for new telemetry data...")

with col_right:
    st.subheader("🎯 Top Targeted Paths")
    path_counts = df['path'].value_counts().reset_index()
    path_counts.columns = ['Path', 'Count']
    fig_path = px.bar(path_counts, x='Count', y='Path', orientation='h', title='Most Hit Endpoints')
    st.plotly_chart(fig_path, use_container_width=True)

# --- RAW DATA TABLE ---
st.subheader("📝 Recent Traffic Logs")
st.dataframe(df[['ip', 'method', 'path', 'body']], use_container_width=True)