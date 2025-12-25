import json
import os
import sys
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
            # Ensure request_id exists for the UI
            if 'request_id' not in entry:
                entry['request_id'] = "N/A"
            data.append(entry)
        except json.JSONDecodeError:
            continue
            
    return pd.DataFrame(data)

if st.button("🔄 Refresh Data"):
    st.rerun()

df = load_data()

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