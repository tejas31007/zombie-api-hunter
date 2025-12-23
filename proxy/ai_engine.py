import joblib
import os
from typing import Any, Optional, List
from .utils import get_logger

logger = get_logger("ai_brain")

class AIEngine:
    def __init__(self, model_version: str = "v1") -> None:
        self.model_version = model_version
        self.model: Optional[Any] = None
        self.load_model()

    def load_model(self) -> None:
        """Loads the specific version of the model from the models/ directory."""
        # DYNAMIC PATH: proxy/models/model_v1.pkl
        model_path = f"proxy/models/model_{self.model_version}.pkl"
        
        try:
            if os.path.exists(model_path):
                self.model = joblib.load(model_path)
                logger.info(f"🧠 AI Brain loaded: {model_path} (Version: {self.model_version})")
            else:
                logger.warning(f"⚠️ Model file not found: {model_path}. Running in Fail-Open mode.")
                self.model = None
        except Exception as e:
            logger.error(f"❌ Failed to load AI Brain: {e}")
            self.model = None

    def _preprocess(self, path: str, method: str, body: str) -> List[str]:
        """
        Combines request parts into a single string for the AI Pipeline.
        The new model (TfidfVectorizer) expects a list of strings.
        """
        # Example: "GET /dashboard user=admin"
        full_request = f"{method} {path} {body}"
        return [full_request]

    def predict(self, path: str, method: str, body: str) -> int:
        """
        Returns:
            1  = Safe (Allow)
            -1 = Malicious (Block)
        """
        if not self.model:
            return 1  # Fail open if no model

        input_data = self._preprocess(path, method, body)

        try:
            # The Training Script used: 1=Attack, 0=Safe
            # We need to map this to Proxy Logic: -1=Block, 1=Allow
            prediction = self.model.predict(input_data)[0]
            
            if prediction == 1:
                return -1 # BLOCK (It's an attack)
            return 1      # ALLOW (It's safe)
            
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            return 1  # Fail open

    def get_risk_score(self, path: str, method: str, body: str) -> float:
        """
        Returns probability of attack (0.0 to 1.0).
        """
        if not self.model:
            return 0.0

        input_data = self._preprocess(path, method, body)
        try:
            # RandomForest supports predict_proba
            # Returns [[prob_safe, prob_attack]]
            probs = self.model.predict_proba(input_data)[0]
            attack_prob = probs[1] 
            return float(attack_prob)
        except Exception:
            return 0.0

# Global instance defaults to v1
ai_engine = AIEngine(model_version="v1")