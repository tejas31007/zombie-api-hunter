import pandas as pd
import joblib
import json
import datetime
from sklearn.ensemble import IsolationForest
from .config import DATASET_PATH

# Input/Output paths
FEATURES_PATH = "ml_engine/features.csv"
MODEL_PATH = "ml_engine/model.pkl"
METADATA_PATH = "ml_engine/model_metadata.json"

def train_model():
    print("🧠 Loading features...")
    try:
        df = pd.read_csv(FEATURES_PATH)
    except FileNotFoundError:
        print("❌ Error: features.csv not found. Run feature_extractor first!")
        return

    # Hyperparameters
    params = {
        "n_estimators": 100,
        "contamination": 0.1,
        "random_state": 42
    }

    # 1. Initialize the Brain
    clf = IsolationForest(**params)

    # 2. Train (Fit)
    print(f"🏋️ Training on {len(df)} requests...")
    clf.fit(df)

    # 3. Save the Brain
    joblib.dump(clf, MODEL_PATH)
    
    # 4. Save Metadata (The MLOps part)
    metadata = {
        "timestamp": datetime.datetime.now().isoformat(),
        "algorithm": "IsolationForest",
        "hyperparameters": params,
        "training_samples": len(df),
        "feature_columns": list(df.columns)
    }
    
    with open(METADATA_PATH, "w") as f:
        json.dump(metadata, f, indent=4)
        
    print(f"✅ Model saved to {MODEL_PATH}")
    print(f"✅ Metadata saved to {METADATA_PATH}")

    # --- INSTANT VERIFICATION ---
    print("\n🔎 Sanity Check:")
    
    # Test Case A: Normal Request (Short path, no special chars, GET)
    # Note: We need to use valid column values based on features.csv structure
    # Typically: [path_length, digit_count, special_char_count, body_length, method_code]
    normal_vec = [[15, 0, 0, 0, 0]] 
    try:
        pred_normal = clf.predict(normal_vec)[0]
        print(f"   Normal Vector {normal_vec} -> Prediction: {'✅ Safe (1)' if pred_normal == 1 else '❌ Anomaly (-1)'}")
    except Exception as e:
        print(f"   Sanity check skipped (Columns mismatch?): {e}")

# ==========================================
# 👇 THIS PART IS CRITICAL 👇
# ==========================================
if __name__ == "__main__":
    train_model()