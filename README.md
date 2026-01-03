# 🧟 Zombie API Hunter

A Zero-Trust Reverse Proxy powered by AI to protect Legacy APIs.

## 🛡️ Architecture
The system operates as a security mesh around your vulnerable services:
1.  **Interceptor (The Hunter):** FastAPI Reverse Proxy (Port 8000).
2.  **Brain:** Scikit-Learn Isolation Forest & Random Forest (Anomaly Detection).
3.  **Shield:** Redis-based Rate Limiting (DDoS Protection).
4.  **Monitor:** Streamlit Real-time Dashboard.
5.  **Target:** Vulnerable Java Spring Boot Application.

## 🚀 Capabilities
### 🛡️ The Hunter (Proxy Engine)
Built using **FastAPI** for high performance and asynchronous request handling.
* **Traffic Interception:** Captures all incoming HTTP requests before they reach the target.
* **Deep Packet Inspection:**
    * Logs **Request Body** (Payload) to detect SQL Injection/XSS patterns.
    * Logs **Request Duration** to detect Slowloris/DoS attacks.
* **Async Forwarding:** Proxies valid requests to the Target App using a shared HTTP client.

### 🧠 Middleware Pipeline
Traffic flows through these security layers:
1.  **TimingMiddleware:** Measures latency (Time-to-Response).
2.  **TrafficInspector:** Extracts IP, Method, and Payload for the ML Engine.

### 🧠 AI Engine
* **Models:** Isolation Forest (Unsupervised) + Random Forest (Supervised).
* **Features:** Path Length, Special Char Count, SQL Keywords, Entropy.
* **Training:** Self-learning based on "Normal" traffic patterns and user feedback.

---

## 📡 API Reference (New)

### System Health
**GET** `/health`
* Checks if the API and Redis are online.
* **Response:** `{"status": "ok", "redis": "connected"}`

### Submit Feedback
**POST** `/feedback`
* Used by the dashboard to report AI errors (False Positives/Negatives).
* **Body:**
    ```json
    {
      "request_id": "req-123-uuid",
      "actual_label": "safe",
      "comments": "This was a false alarm."
    }
    ```

### Security Headers
Every response includes:
* `X-Request-ID`: Unique UUID for tracing logs.
* `X-Process-Time`: Execution time in seconds.

---

## 🛠️ Tech Stack
* **Framework:** FastAPI
* **ML Engine:** Scikit-Learn (Joblib)
* **Storage:** Redis (Streams & Cache)
* **Client:** HTTPX (Async)
* **Dashboard:** Streamlit

## 🏃‍♂️ How to Run

### Manual Development (Current)
1.  **Start Redis:**
    ```bash
    redis-server
    ```
2.  **Start Proxy (The Hunter):**
    ```bash
    uvicorn proxy.main:app --reload --port 8000
    ```
3.  **Start Dashboard:**
    ```bash
    streamlit run dashboard/app.py
    ```

### Docker (Coming Soon)
The entire system will be containerized for easy deployment via `docker-compose up`.

## System Architecture

```mermaid
graph TD
    User([User]) -->|Interacts| UI[Dashboard (app.py)]
    UI -->|Sends Feedback| Proxy[Hunter Proxy (router.py)]
    User -->|Sends Requests| Proxy
    Proxy -->|Inspects| AI[AI Engine (ai_engine.py)]
    AI -->|Scans & Probes| Target[Target API]
    Target -->|Returns Responses| Proxy
    Proxy -->|Allows/Blocks| User
    Proxy -->|Logs Data| Redis[(Redis Streams)]
    Redis -->|Live Data| UI


👤 Author
Tejas Samir Alawani
Dept. of Computer Science & Engineering Kolhapur Institute of Technology