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

def retrain_model():
    print(f"🚀 Starting Retraining Process ({NEW_VERSION})...")
    r = get_redis_client()

    # 1. Load Original Data (Prevent Catastrophic Forgetting)
    if os.path.exists(ORIGINAL_DATA_PATH):
        df = pd.read_csv(ORIGINAL_DATA_PATH)
        # Assuming CSV has 'method', 'path', 'body'
        # We combine them into a single string column for the vectorizer
        base_data = (df['method'] + " " + df['url'] + " " + df['body']).tolist()
        print(f"✅ Loaded {len(base_data)} original samples.")
    else:
        print("⚠️ Original dataset not found. Starting empty (Risky!)")
        base_data = []

    # 2. Fetch New Data from Feedback
    new_data = fetch_feedback_data(r)
    print(f"✅ Loaded {len(new_data)} new samples from feedback.")

    if not new_data and not base_data:
        print("❌ No data to train on. Aborting.")
        return

    # 3. Combine Data
    training_data = base_data + new_data

    # 4. Train Pipeline (Vectorizer + Isolation Forest)
    # Using HashingVectorizer for fixed memory usage
    model_pipeline = Pipeline([
        ("vectorizer", HashingVectorizer(n_features=1000, norm=None)),
        ("anomaly_detector", IsolationForest(contamination=0.05, random_state=42))
    ])

    print("🧠 Fitting model...")
    model_pipeline.fit(training_data)

    # 5. Save Model
    model_path = os.path.join(MODEL_DIR, f"model_{NEW_VERSION}.pkl")
    joblib.dump(model_pipeline, model_path)
    print(f"💾 Model saved to {model_path}")

    # 6. Save Metadata
    meta = ModelMetadata(
        version=NEW_VERSION,
        algorithm="IsolationForest + HashingVectorizer",
        author="ZombieHunter Auto-Retrain",
        accuracy=0.95, # Placeholder
        trained_at=datetime.datetime.now().isoformat()
    )
    
    meta_path = os.path.join(MODEL_DIR, f"model_{NEW_VERSION}.json")
    with open(meta_path, "w") as f:
        json.dump(meta.model_dump(), f)
    
    print("✅ Retraining Complete! Update AI Engine version to apply.")

if __name__ == "__main__":
    retrain_model()