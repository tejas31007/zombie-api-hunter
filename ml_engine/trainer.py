import pandas as pd
import joblib
from sklearn.ensemble import IsolationForest
from .config import DATASET_PATH

# Input/Output paths
FEATURES_PATH = "ml_engine/features.csv"
MODEL_PATH = "ml_engine/model.pkl"

def train_model():
    print("🧠 Loading features...")
    try:
        df = pd.read_csv(FEATURES_PATH)
    except FileNotFoundError:
        print("❌ Error: features.csv not found. Run feature_extractor first!")
        return

    # 1. Initialize the Brain
    # contamination=0.1 means we expect roughly 10% of data to be anomalies
    clf = IsolationForest(n_estimators=100, contamination=0.1, random_state=42)

    # 2. Train (Fit)
    print(f"🏋️ Training on {len(df)} requests...")
    clf.fit(df)

    # 3. Save the Brain
    joblib.dump(clf, MODEL_PATH)
    print(f"✅ Model saved to {MODEL_PATH}")

    # --- INSTANT VERIFICATION ---
    print("\n🔎 Sanity Check:")

    # Test Case A: Normal Request (Short path, no special chars, GET)
    normal_vec = [[15, 0, 0, 0, 0]] 
    pred_normal = clf.predict(normal_vec)[0]
    print(f"   Normal Vector {normal_vec} -> Prediction: {'✅ Safe (1)' if pred_normal == 1 else '❌ Anomaly (-1)'}")

    # Test Case B: Attack Request (Long path, special chars, POST)
    attack_vec = [[50, 5, 10, 200, 1]]
    pred_attack = clf.predict(attack_vec)[0]
    print(f"   Attack Vector {attack_vec} -> Prediction: {'✅ Safe (1)' if pred_attack == 1 else '❌ Anomaly (-1)'}")

if __name__ == "__main__":
    train_model()