import json
import os
import sys
import time  # <--- Required for Live Mode
import subprocess
import pandas as pd
import plotly.express as px
import redis
import requests
import streamlit as st

# --- PATH SETUP ---
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from proxy.config import settings
from proxy.ai_engine import ai_engine

# --- CONFIGURATION ---
st.set_page_config(page_title="Zombie Hunter War Room", page_icon="🛡️", layout="wide")

# --- CUSTOM CSS ---
st.markdown("""
    <style>
        .stApp { background-color: #0e1117; }
        h1, h2, h3 { color: #00ff41 !important; font-family: 'Courier New', Courier, monospace; }
        div[data-testid="stMetric"] { background-color: #161b22; border: 1px solid #30363d; padding: 10px; border-radius: 5px; }
        /* Style for the Download Button to look like a terminal button */
        div.stDownloadButton > button { 
            color: #00ff41 !important; 
            border-color: #00ff41 !important; 
            background-color: #0e1117 !important; 
        }
    </style>
""", unsafe_allow_html=True)

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

# --- REFRESH CONTROLS (Commit 3) ---
col_r1, col_r2 = st.sidebar.columns(2)
if col_r1.button("🔄 Refresh"):
    st.rerun()
if col_r2.button("🧹 Clear Cache"):
    st.cache_resource.clear()
    st.rerun()

# --- LIVE MODE (Commit 2) ---
live_mode = st.sidebar.toggle("🔴 Live Mode")

st.sidebar.markdown("---")

st.sidebar.subheader("🧠 AI Brain Status")
model_info = ai_engine.get_model_info()
v_col, a_col = st.sidebar.columns(2)
v_col.metric("Version", model_info.get("version", "N/A"))
a_col.metric("Author", model_info.get("author", "Unknown"))
st.sidebar.caption(f"Algorithm: {model_info.get('algorithm', 'Unknown')}")

st.sidebar.markdown("---")

# Feedback Loop
st.sidebar.subheader("📝 Report Mistake")
if "fb_req_id" not in st.session_state: st.session_state["fb_req_id"] = ""
if "fb_comments" not in st.session_state: st.session_state["fb_comments"] = ""

def clear_form():
    st.session_state["fb_req_id"] = ""
    st.session_state["fb_comments"] = ""

with st.sidebar.form("feedback_form"):
    req_id_input = st.text_input("Request ID", key="fb_req_id")
    correct_label = st.selectbox("Actually was:", ["safe", "malicious"])
    comments = st.text_area("Comments", key="fb_comments")
    if st.form_submit_button("Submit"):
        try:
            requests.post("http://localhost:8000/feedback", json={
                "request_id": req_id_input,
                "actual_label": correct_label,
                "comments": comments
            })
            st.success("Sent!")
        except:
            st.error("Failed.")
st.sidebar.button("Reset", on_click=clear_form)

st.sidebar.markdown("---")

# Admin Controls
st.sidebar.subheader("⚙️ Admin Controls")
if st.sidebar.button("🚀 Retrain Model (v2)"):
    with st.spinner("Retraining..."):
        try:
            res = subprocess.run(["python", "ml_engine/retrain.py"], capture_output=True, text=True)
            if res.returncode == 0:
                st.sidebar.success("Done!")
                with st.sidebar.expander("Logs"): st.text(res.stdout)
            else:
                st.sidebar.error("Failed")
                with st.sidebar.expander("Error"): st.text(res.stderr)
        except Exception as e:
            st.sidebar.error(str(e))

# --- DANGER ZONE (Commit 4) ---
if st.sidebar.button("🗑️ RESET DATABASE", type="primary"):
    redis_client.flushall()
    st.sidebar.warning("💥 Database wiped clean!")
    st.rerun()

st.sidebar.markdown("---")

# --- MAIN PAGE DATA LOADING ---
def load_data():
    raw_logs = redis_client.lrange(settings.REDIS_QUEUE_NAME, 0, -1)
    if not raw_logs:
        return pd.DataFrame() 
    
    data = []
    for log in raw_logs:
        try:
            entry = json.loads(log)
            if 'request_id' not in entry: entry['request_id'] = "N/A"
            entry['risk_score'] = float(entry.get('risk_score', 0.0))
            data.append(entry)
        except json.JSONDecodeError:
            continue
            
    df = pd.DataFrame(data)
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df

# Helper for GeoIP
def mock_geoip(ip_address):
    hash_val = hash(ip_address)
    lat = (hash_val % 180) - 90
    lon = (hash_val % 360) - 180
    return lat, lon

# Load Data
df = load_data()

st.title("🛡️ Zombie API Hunter | War Room")

if df.empty:
    st.warning("⚠️ No traffic data found. Waiting for targets...")
    st.stop()

# --- FILTERS ---
st.sidebar.header("🔍 Forensics Filters")

# Filter IP
all_ips = ["All"] + list(df["ip"].unique())
sel_ip = st.sidebar.selectbox("Filter IP:", all_ips)
if sel_ip != "All": df = df[df["ip"] == sel_ip]

# --- RISK SLIDER (Commit 3) ---
min_risk = st.sidebar.slider("Minimum Risk Score", 0.0, 1.0, 0.0)
df = df[df["risk_score"] >= min_risk]

# --- METRICS ---
c1, c2, c3 = st.columns(3)
c1.metric("Total Intercepts", len(df))
c2.metric("Unique Attackers", df["ip"].nunique())
c3.metric("Top Target", df["path"].mode()[0] if not df.empty else "N/A")

st.markdown("---")

# --- VISUALIZATIONS ---
st.subheader("📈 Traffic Velocity")
if 'timestamp' in df.columns and not df.empty:
    ts_df = df.set_index('timestamp').resample('1T').size().reset_index(name='requests')
    fig_time = px.area(ts_df, x='timestamp', y='requests', template="plotly_dark", color_discrete_sequence=["#00FF00"])
    st.plotly_chart(fig_time, use_container_width=True)

col_left, col_right = st.columns(2)
with col_left:
    st.subheader("🛡️ Action Breakdown")
    if "action" in df.columns:
        fig_pie = px.pie(df, names="action", color="action", 
                         color_discrete_map={"ALLOWED":"#22c55e", "BLOCKED_AI":"#ef4444", "BLOCKED_RATE":"#eab308"},
                         template="plotly_dark")
        st.plotly_chart(fig_pie, use_container_width=True)

with col_right:
    st.subheader("🎯 Target Analysis")
    fig_bar = px.bar(df["path"].value_counts().reset_index(name="count"), 
                     x="count", y="path", orientation="h", template="plotly_dark")
    st.plotly_chart(fig_bar, use_container_width=True)

st.subheader("📊 Anomaly Score Distribution")
if "risk_score" in df.columns:
    fig_hist = px.histogram(df, x="risk_score", nbins=20, title="Risk Score Spread", 
                            color_discrete_sequence=["#FF5500"], template="plotly_dark")
    st.plotly_chart(fig_hist, use_container_width=True)

st.subheader("🌍 Live Attack Map")
if not df.empty:
    coords = df['ip'].apply(mock_geoip)
    df['lat'] = coords.apply(lambda x: x[0])
    df['lon'] = coords.apply(lambda x: x[1])
    st.map(df, latitude='lat', longitude='lon', size=20, color='#FF0000')

# --- LOGS & EXPORT ---
st.subheader("📝 Intercept Logs")

# --- EXPORT BUTTON (Commit 1) ---
csv = df.to_csv(index=False).encode('utf-8')
st.download_button(
    "⬇️ Download Logs as CSV",
    csv,
    "zombie_traffic_logs.csv",
    "text/csv",
    key='download-csv'
)

st.dataframe(df[["timestamp", "request_id", "action", "ip", "path", "risk_score"]].sort_values("timestamp", ascending=False), use_container_width=True)