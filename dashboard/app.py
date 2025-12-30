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
# NEW IMPORT (Commit 2)
from dashboard.auth import login_form 

# --- CONFIGURATION ---
st.set_page_config(page_title="Zombie Hunter War Room", page_icon="🛡️", layout="wide")

# --- AUTHENTICATION CHECK (Commit 2 & 3) ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    # Show Login Form and STOP execution if not logged in
    login_form()
    st.stop()

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

# --- LOGOUT BUTTON (Commit 4) ---
if st.sidebar.button("🔒 Logout"):
    st.session_state["authenticated"] = False
    st.rerun()

# --- REFRESH CONTROLS (Commit 3) ---
col_r1, col_r2 = st.sidebar.columns(2)
if col_r1.button("🔄 Refresh"):
    st.rerun()
if col_r2.button("🧹 Clear Cache"):
    st.cache_resource.clear()
    st.rerun()

# --- LIVE MODE (Commit 2) ---
live_mode = st.sidebar.toggle("🔴 Live Mode")
if live_mode:
    time.sleep(2) # Refresh every 2 seconds
    st.rerun()

st.sidebar.markdown("---")

st.sidebar.subheader("🧠 AI Brain Status")
model_info = ai_engine.get_model_info()
v_col, a_col = st.sidebar.columns(2)
v_col.metric("Version", model_info.get("version", "N/A"))
a_col.metric("Author", model_info.get("author", "Unknown"))
st.sidebar.caption(f"Algorithm: {model_info.get('algorithm', 'Unknown')}")

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

# --- EXPORT BUTTONS (Commit 1 & 4) ---
col_d1, col_d2 = st.columns(2)

# CSV Export
csv = df.to_csv(index=False).encode('utf-8')
col_d1.download_button(
    "⬇️ Download CSV",
    csv,
    "zombie_logs.csv",
    "text/csv",
    key='download-csv'
)

# JSON Export (Commit 4)
json_str = df.to_json(orient="records")
col_d2.download_button(
    "⬇️ Download JSON",
    json_str,
    "zombie_logs.json",
    "application/json",
    key='download-json'
)

st.dataframe(df[["timestamp", "request_id", "action", "ip", "path", "risk_score"]].sort_values("timestamp", ascending=False), use_container_width=True)