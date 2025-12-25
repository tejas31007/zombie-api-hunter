import joblib
import os
import json
from typing import Any, Optional, List, Dict
from .utils import get_logger
from .model_metadata import ModelMetadata

logger = get_logger("ai_brain")

class AIEngine:
    """
    The central AI controller for the Zombie API Hunter.
    
    This class handles the lifecycle of the Machine Learning model, including:
    1. Loading the serialized model (.pkl) and its metadata (.json).
    2. Preprocessing incoming HTTP request data.
    3. Generating predictions (Safe vs. Malicious) and risk scores.
    """

    def __init__(self, model_version: str = "v1") -> None:
        """
        Initialize the AI Engine.

        Args:
            model_version (str): The version tag of the model to load (default: "v1").
                                 Expects files named 'model_v1.pkl' and 'model_v1.json'.
        """
        self.model_version = model_version
        self.model: Optional[Any] = None
        self.metadata: Optional[ModelMetadata] = None 
        
        self.load_model()
        self.load_metadata()

    def load_model(self) -> None:
        """
        Loads the serialized machine learning model from disk using joblib.
        
        If the model file is missing or corrupt, it logs a warning and sets
        the engine to 'Fail-Open' mode (where all traffic is allowed) to prevent
        blocking legitimate traffic due to system error.
        """
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
        """
        Loads the JSON metadata 'ID card' associated with the model.
        
        This includes information like the algorithm used, the author, accuracy metrics,
        and the creation date, which is useful for the Dashboard UI.
        """
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
        """
        Prepares raw HTTP request data for the ML model.

        Combines the HTTP method, URL path, and body content into a single string
        format that matches the training data structure.

        Args:
            path (str): The endpoint URL (e.g., "/api/v1/login").
            method (str): The HTTP method (e.g., "POST").
            body (str): The content of the request body.

        Returns:
            List[str]: A list containing the single formatted string, ready for vectorization.
        """
        full_request = f"{method} {path} {body}"
        return [full_request]

    def predict(self, path: str, method: str, body: str) -> int:
        """
        Analyzes a request and determines if it should be blocked.

        Args:
            path (str): The request URL path.
            method (str): The HTTP method.
            body (str): The request body.

        Returns:
            int: 
                1 : ALLOW (Safe request)
               -1 : BLOCK (Malicious/Zombie request)
        """
        if not self.model:
            return 1  # Fail open

        input_data = self._preprocess(path, method, body)

        try:
            prediction = self.model.predict(input_data)[0]
            # Adjust logic based on your specific model training labels
            if prediction == 1:
                return -1 # BLOCK
            return 1      # ALLOW
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            return 1

    def get_risk_score(self, path: str, method: str, body: str) -> float:
        """
        Calculates the probability that a request is a 'Zombie' API call.

        Args:
            path (str): The request URL path.
            method (str): The HTTP method.
            body (str): The request body.

        Returns:
            float: A score between 0.0 (Safe) and 1.0 (High Risk).
                   Returns 0.0 if the model does not support probability prediction.
        """
        if not self.model:
            return 0.0

        input_data = self._preprocess(path, method, body)
        try:
            # Assumes index 1 is the 'positive' class for the anomaly
            probs = self.model.predict_proba(input_data)[0]
            return float(probs[1])
        except Exception:
            return 0.0
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Retrieves the loaded model's metadata for display purposes.

        Returns:
            Dict[str, Any]: A dictionary of metadata (algorithm, metrics, etc.),
                            or a default dictionary if no metadata is loaded.
        """
        if self.metadata:
            return self.metadata.model_dump()
        return {"version": "unknown", "description": "No metadata available"}

# Global instance
ai_engine = AIEngine(model_version="v1")