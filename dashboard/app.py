import json
import os
import sys
import subprocess  # <--- Added for running the retrain script
import pandas as pd
import plotly.express as px
import redis
import requests  # To talk to the Proxy API
import streamlit as st

# --- PATH SETUP ---
# Allows importing from the sibling 'proxy' directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from proxy.config import settings
from proxy.ai_engine import ai_engine

# --- CONFIGURATION ---
st.set_page_config(page_title="Zombie Hunter Dashboard", page_icon="🛡️", layout="wide")

# Connect to Redis
@st.cache_resource
def get_redis_client():
    return redis.Redis(
        host=settings.REDIS_HOST, 
        port=settings.REDIS_PORT, 
        decode_responses=True
    )

try:
    redis_client = get_redis_client()
    redis_client.ping()
except redis.ConnectionError:
    st.error("🚨 Redis is DOWN! Start Docker: `docker start zombie-redis`")
    st.stop()

# --- SIDEBAR: AI STATUS ---
st.sidebar.title("🧟 Zombie Hunter")
st.sidebar.markdown("Monitoring real-time traffic.")
st.sidebar.markdown("---")

st.sidebar.subheader("🧠 AI Brain Status")
model_info = ai_engine.get_model_info()

version_col, author_col = st.sidebar.columns(2)
version_col.metric("Version", model_info.get("version", "N/A"))
author_col.metric("Author", model_info.get("author", "Unknown"))

st.sidebar.info(f"**Algorithm:**\n{model_info.get('algorithm', 'Unknown')}")
if 'trained_at' in model_info:
    st.sidebar.caption(f"📅 Trained: {model_info['trained_at'][:10]}")

st.sidebar.markdown("---")

# --- SIDEBAR: FEEDBACK LOOP ---
st.sidebar.subheader("📝 Report Mistake")

# Initialize Session State
if "fb_req_id" not in st.session_state:
    st.session_state["fb_req_id"] = ""
if "fb_comments" not in st.session_state:
    st.session_state["fb_comments"] = ""

def clear_form():
    st.session_state["fb_req_id"] = ""
    st.session_state["fb_comments"] = ""

with st.sidebar.form("feedback_form"):
    st.markdown("Found a False Positive?")
    
    req_id_input = st.text_input("Request ID (Copy from table)", key="fb_req_id")
    correct_label = st.selectbox("Actually was:", ["safe", "malicious"])
    comments = st.text_area("Comments", key="fb_comments")
    
    submitted = st.form_submit_button("Submit Feedback")
    
    if submitted and req_id_input:
        try:
            api_url = "http://localhost:8000/feedback"
            payload = {
                "request_id": req_id_input,
                "actual_label": correct_label,
                "comments": comments
            }
            
            response = requests.post(api_url, json=payload)
            
            if response.status_code == 200:
                st.success("✅ Feedback Sent!")
            else:
                st.error(f"❌ Failed: {response.text}")
        except Exception as e:
            st.error(f"❌ Error connecting to Proxy: {e}")

st.sidebar.button("Reset Form", on_click=clear_form)
st.sidebar.markdown("---")

# --- SIDEBAR: ADMIN CONTROLS (NEW) ---
st.sidebar.subheader("⚙️ Admin Controls")
if st.sidebar.button("🚀 Retrain Model (v2)"):
    with st.spinner("Retraining AI Brain... this may take a moment."):
        try:
            # Run the retrain script
            # We use 'python' assuming it's in the path, or 'python3' depending on your OS
            result = subprocess.run(
                ["python", "ml_engine/retrain.py"], 
                capture_output=True, 
                text=True
            )
            
            if result.returncode == 0:
                st.sidebar.success("✅ Retrained Successfully!")
                # Show the output logs in a small expander
                with st.sidebar.expander("See Logs"):
                    st.text(result.stdout)
            else:
                st.sidebar.error("❌ Retraining Failed")
                with st.sidebar.expander("See Error"):
                    st.text(result.stderr)
                    
        except Exception as e:
            st.sidebar.error(f"Error launching script: {e}")

st.sidebar.markdown("---")


# --- SIDEBAR FILTERS ---
st.sidebar.header("🔍 Forensics Filters")

# --- DATA LOADING ---
def load_data():
    raw_logs = redis_client.lrange(settings.REDIS_QUEUE_NAME, 0, -1)
    if not raw_logs:
        return pd.DataFrame() 
    
    data = []
    for log in raw_logs:
        try:
            entry = json.loads(log)
            # Ensure request_id exists
            if 'request_id' not in entry:
                entry['request_id'] = "N/A"
            
            # NEW: Ensure risk_score is float (handle missing values)
            entry['risk_score'] = float(entry.get('risk_score', 0.0))
            
            data.append(entry)
        except json.JSONDecodeError:
            continue
            
    df = pd.DataFrame(data)
    
    # NEW: Convert timestamp to datetime objects
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
    return df


# Helper for Commit 3
def mock_geoip(ip_address):
    """
    Deterministically generates a fake Lat/Lon based on the IP string.
    Real production apps would use a GeoIP database here.
    """
    # Simple hash of the IP to get numbers
    hash_val = hash(ip_address)
    # Map hash to valid Lat (-90 to 90) and Lon (-180 to 180)
    lat = (hash_val % 180) - 90
    lon = (hash_val % 360) - 180
    return lat, lon



# --- MAIN CONTENT ---
st.title("🛡️ Zombie API Hunter | Live Traffic")

if df.empty:
    st.warning("⚠️ No traffic data found yet. Send some requests!")
    st.stop()

# Filter Logic
all_ips = ["All"] + list(df["ip"].unique())
selected_ip = st.sidebar.selectbox("Filter by IP:", all_ips)

if "action" in df.columns:
    all_actions = ["All"] + list(df["action"].unique())
    selected_action = st.sidebar.selectbox("Filter by Outcome:", all_actions)
else:
    selected_action = "All"

if selected_ip != "All":
    df = df[df["ip"] == selected_ip]

if selected_action != "All":
    df = df[df["action"] == selected_action]

# --- KPI METRICS ---
m_col1, m_col2, m_col3 = st.columns(3)

with m_col1:
    st.metric("Total Requests", len(df))

with m_col2:
    unique_ips = df["ip"].nunique()
    st.metric("Unique Attackers (IPs)", unique_ips)

with m_col3:
    top_path = df["path"].mode()[0] if not df.empty else "N/A"
    st.metric("Top Target Path", top_path)

st.markdown("---")


# --- TIME SERIES CHART (Commit 1) ---
st.subheader("📈 Traffic Velocity (Requests/Minute)")
if not df.empty and 'timestamp' in df.columns:
    # Resample data by minute to count requests
    # Set timestamp as index temporarily for resampling
    ts_df = df.set_index('timestamp').resample('1T').size().reset_index(name='requests')
    
    fig_time = px.area(
        ts_df, 
        x='timestamp', 
        y='requests',
        template="plotly_dark",
        color_discrete_sequence=["#00FF00"] # Hacker Green
    )
    st.plotly_chart(fig_time, use_container_width=True)


# --- CHARTS ---
chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.subheader("🛡️ Threat Detection Status")
    if "action" in df.columns:
        fig_action = px.pie(
            df,
            names="action",
            title="Blocked vs Allowed Traffic",
            color="action",
            color_discrete_map={
                "ALLOWED": "#22c55e",       # Green
                "BLOCKED_AI": "#ef4444",    # Red
                "BLOCKED_RATE": "#eab308",  # Yellow
            },
        )
        st.plotly_chart(fig_action, use_container_width=True)
    else:
        st.info("Waiting for new telemetry data...")

with chart_col2:
    st.subheader("🎯 Top Targeted Paths")
    path_counts = df["path"].value_counts().reset_index()
    path_counts.columns = ["Path", "Count"]
    fig_path = px.bar(
        path_counts, x="Count", y="Path", orientation="h", title="Most Hit Endpoints"
    )
    st.plotly_chart(fig_path, use_container_width=True)


# --- SCORE DISTRIBUTION (Commit 2) ---
st.subheader("📊 Anomaly Score Distribution")
if not df.empty and "risk_score" in df.columns:
    fig_hist = px.histogram(
        df, 
        x="risk_score", 
        nbins=20,
        title="Risk Score Spread (0=Safe, 1=Malicious)",
        color_discrete_sequence=["#FF5500"], # Hacker Orange
        template="plotly_dark"
    )
    st.plotly_chart(fig_hist, use_container_width=True)

# --- RAW DATA TABLE ---
st.subheader("📝 Recent Traffic Logs")
st.caption("Copy the 'request_id' to report False Positives in the sidebar.")

cols_to_show = ["ip", "method", "path", "body"]

if "action" in df.columns:
    cols_to_show.insert(0, "action")
if "timestamp" in df.columns:
    cols_to_show.insert(0, "timestamp")
if "request_id" in df.columns:
    cols_to_show.insert(1, "request_id")

st.dataframe(
    df[cols_to_show].sort_values(by=cols_to_show[0] if "timestamp" in cols_to_show else "path", ascending=False), 
    use_container_width=True
)


# --- ATTACK MAP (Commit 3) ---
st.subheader("🌍 Live Attack Map")
if not df.empty:
    # Create new columns for lat/lon
    # Apply the mock function to every IP in the dataframe
    coords = df['ip'].apply(mock_geoip)
    df['lat'] = coords.apply(lambda x: x[0])
    df['lon'] = coords.apply(lambda x: x[1])

    # Display the map
    st.map(df, latitude='lat', longitude='lon', size=20, color='#FF0000')