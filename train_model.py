import pickle
import json
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline

# --- NEW IMPORT ---
# (Make sure to run this script from the root folder so it finds the module)
import sys
sys.path.append(".") 
from proxy.model_metadata import ModelMetadata

# 1. Create Dummy Data
X_train = [
    "SELECT * FROM users", 
    "OR 1=1", 
    "DROP TABLE users", 
    "/dashboard", 
    "/login", 
    "user_id=5", 
    "search=apple", 
    "<script>alert(1)</script>" 
]
y_train = [1, 1, 1, 0, 0, 0, 0, 1] 

# 2. Build Pipeline
print("🧠 Training Model v1...")
model = Pipeline([
    ('tfidf', TfidfVectorizer()),
    ('clf', RandomForestClassifier())
])

model.fit(X_train, y_train)

# 3. Save Model AND Metadata
models_dir = "proxy/models"
os.makedirs(models_dir, exist_ok=True)

# A. Save the Brain (.pkl)
pkl_path = f"{models_dir}/model_v1.pkl"
with open(pkl_path, "wb") as f:
    pickle.dump(model, f)

# B. Save the ID Card (.json) <--- NEW PART
meta = ModelMetadata.create(
    version="v1",
    algorithm="RandomForest + TF-IDF",
    author="Tejas"
)

json_path = f"{models_dir}/model_v1.json"
with open(json_path, "w") as f:
    f.write(meta.model_dump_json(indent=4))

print(f"✅ Model saved:    {pkl_path}")
print(f"✅ Metadata saved: {json_path}")