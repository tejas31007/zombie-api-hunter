import joblib
import os
import json
from typing import Any, Optional, List, Dict
from .utils import get_logger
from .model_metadata import ModelMetadata  # <--- NEW IMPORT

logger = get_logger("ai_brain")

class AIEngine:
    def __init__(self, model_version: str = "v1") -> None:
        self.model_version = model_version
        self.model: Optional[Any] = None
        self.metadata: Optional[ModelMetadata] = None # <--- NEW STORE
        
        self.load_model()
        self.load_metadata() # <--- NEW CALL

    def load_model(self) -> None:
        """Loads the specific version of the model from the models/ directory."""
        model_path = f"proxy/models/model_{self.model_version}.pkl"
        
        try:
            if os.path.exists(model_path):
                self.model = joblib.load(model_path)
                logger.info(f"🧠 AI Brain loaded: {model_path}")
            else:
                logger.warning(f"⚠️ Model file not found: {model_path}. Running in Fail-Open mode.")
                self.model = None
        except Exception as e:
            logger.error(f"❌ Failed to load AI Brain: {e}")
            self.model = None

    def load_metadata(self) -> None:
        """Loads the corresponding JSON ID card for the model."""
        meta_path = f"proxy/models/model_{self.model_version}.json"
        
        try:
            if os.path.exists(meta_path):
                with open(meta_path, "r") as f:
                    data = json.load(f)
                    self.metadata = ModelMetadata(**data)
                logger.info(f"📄 Metadata loaded: {self.metadata.algorithm} by {self.metadata.author}")
            else:
                logger.warning(f"⚠️ Metadata not found: {meta_path}")
                self.metadata = None
        except Exception as e:
            logger.error(f"❌ Failed to load Metadata: {e}")
            self.metadata = None

    def _preprocess(self, path: str, method: str, body: str) -> List[str]:
        """Combines request parts into a single string for the AI Pipeline."""
        full_request = f"{method} {path} {body}"
        return [full_request]

    def predict(self, path: str, method: str, body: str) -> int:
        """
        Returns: 1 (Safe), -1 (Malicious)
        """
        if not self.model:
            return 1  # Fail open

        input_data = self._preprocess(path, method, body)

        try:
            prediction = self.model.predict(input_data)[0]
            if prediction == 1:
                return -1 # BLOCK
            return 1      # ALLOW
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            return 1

    def get_risk_score(self, path: str, method: str, body: str) -> float:
        """Returns probability of attack (0.0 to 1.0)."""
        if not self.model:
            return 0.0

        input_data = self._preprocess(path, method, body)
        try:
            probs = self.model.predict_proba(input_data)[0]
            return float(probs[1])
        except Exception:
            return 0.0
    
    def get_model_info(self) -> Dict[str, Any]:
        """Returns a summary of the current model for the UI."""
        if self.metadata:
            return self.metadata.model_dump()
        return {"version": "unknown", "description": "No metadata available"}

# Global instance
ai_engine = AIEngine(model_version="v1")