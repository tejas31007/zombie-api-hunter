import joblib
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from .utils import get_logger

MODEL_PATH = "ml_engine/model.pkl"
logger = get_logger("ai_brain")

class AIEngine:
    def __init__(self):
        self.model = None
        self.load_model()

    def load_model(self):
        """Loads the trained .pkl model from disk."""
        try:
            self.model = joblib.load(MODEL_PATH)
            logger.info(f"🧠 AI Brain loaded successfully from {MODEL_PATH}")
        except Exception as e:
            logger.error(f"❌ Failed to load AI Brain: {e}")
            self.model = None

    def extract_features(self, path: str, method: str, body: str) -> list:
        """
        Converts request data into the exact vector format the model expects.
        Must match feature_extractor.py logic!
        """
        # 1. Path Length
        path_len = len(path)

        # 2. Digit Count
        digit_count = sum(c.isdigit() for c in path)

        # 3. Special Char Count
        special_chars = set(['\'', '"', '-', '<', '>', ';', '%', '(', ')'])
        special_count = sum(1 for c in path if c in special_chars)

        # 4. Body Length (Safe conversion)
        body_len = len(body) if body else 0

        # 5. Method Code (GET=0, POST=1, etc. - Simplified mapping)
        method_map = {"GET": 0, "POST": 1, "PUT": 2, "DELETE": 3}
        method_code = method_map.get(method.upper(), 0)

        # Return as a 2D array (1 row, 5 columns)
        return [[path_len, digit_count, special_count, body_len, method_code]]

    def predict(self, path: str, method: str, body: str) -> int:
        """
        Returns:
            1  = Safe
            -1 = Malicious (Anomaly)
        """
        if not self.model:
            return 1 # Fail safe: If no brain, let traffic through

        features = self.extract_features(path, method, body)

        try:
            # We catch warnings about feature names since we pass a raw list
            prediction = self.model.predict(features)[0]
            return prediction
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            return 1 # Fail safe

# Global instance
ai_engine = AIEngine()