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

if __name__ == "__main__":
    print("todo: implement retraining logic")