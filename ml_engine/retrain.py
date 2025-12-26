import pandas as pd
import redis
import json
import joblib
import datetime
import os
import sys

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from proxy.config import settings
from proxy.model_metadata import ModelMetadata
from sklearn.ensemble import IsolationForest
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.pipeline import Pipeline

# --- CONFIG ---
ORIGINAL_DATA_PATH = "ml_engine/datasets/normal_traffic.csv"
MODEL_DIR = "proxy/models"
NEW_VERSION = "v2"

def get_redis_client():
    return redis.Redis(
        host=settings.REDIS_HOST, 
        port=settings.REDIS_PORT, 
        decode_responses=True
    )

def fetch_feedback_data(r_client):
    """
    Fetches 'False Positive' reports (Safe requests blocked by mistake)
    from the feedback_queue to add to training data.
    """
    print("🔍 Checking for feedback...")
    
    # 1. Get all feedback IDs
    feedback_entries = r_client.lrange("feedback_queue", 0, -1)
    if not feedback_entries:
        print("   -> No feedback found.")
        return []

    # 2. Get all Traffic Logs to cross-reference
    traffic_logs = r_client.lrange(settings.REDIS_QUEUE_NAME, 0, -1)
    
    # Map Request ID -> Full Log Entry
    traffic_map = {}
    for log in traffic_logs:
        try:
            entry = json.loads(log)
            if 'request_id' in entry:
                traffic_map[entry['request_id']] = entry
        except:
            continue

    # 3. Extract the 'Safe' payloads that were mistakenly blocked
    new_safe_requests = []
    
    for fb_raw in feedback_entries:
        fb = json.loads(fb_raw)
        
        # We only want to retrain on things that ARE actually Safe
        if fb['actual_label'] == 'safe':
            req_id = fb['request_id']
            if req_id in traffic_map:
                log_entry = traffic_map[req_id]
                
                # Reconstruct the feature string: "METHOD /path body"
                full_req = f"{log_entry['method']} {log_entry['path']} {log_entry['body']}"
                new_safe_requests.append(full_req)
                print(f"   -> Found new training sample: {req_id}")

    return new_safe_requests