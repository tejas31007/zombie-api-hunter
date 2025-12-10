# 🧠 ML Inference Engine
This module will contain the PyTorch models for anomaly detection.
- **Model:** Isolation Forest / Autoencoder
- **Input:** Request metadata from Redis


## ⚙️ Feature Engineering
To train the Isolation Forest model, raw log data is converted into the following numerical features:

| Feature | Description | Rationale |
| :--- | :--- | :--- |
| `path_length` | Length of the URL string | Attack payloads (SQLi) often result in unusually long paths. |
| `digit_count` | Number of digits in the path | High digit counts suggest ID enumeration (BOLA attacks). |
| `special_char_count` | Count of chars like `' " < >` | Indicates potential XSS or Injection attempts. |
| `body_length` | Size of the request body | Large bodies may indicate Buffer Overflow or data exfiltration attempts. |
| `method_code` | Categorical encoding (GET=0, POST=1) | Different methods carry different risk profiles. |