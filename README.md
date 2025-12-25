# 🧟 Zombie API Hunter

A Zero-Trust Reverse Proxy powered by AI to protect Legacy APIs.

## 🛡️ Architecture
1.  **Interceptor:** FastAPI Reverse Proxy (Port 8000).
2.  **Brain:** Scikit-Learn Isolation Forest (Anomaly Detection).
3.  **Shield:** Redis-based Rate Limiting (DDoS Protection).
4.  **Monitor:** Streamlit Real-time Dashboard.
5.  **Target:** Vulnerable Java Spring Boot Application.

## 🚀 Quick Start (Docker)

The entire system (Brain, Hunter, Dashboard) is containerized for easy deployment.

1.  **Start the System:**
    ```bash
    docker-compose up --build
    ```
2.  **Access Components:**
    * **Dashboard:** [http://localhost:8501](http://localhost:8501)
    * **Proxy API:** [http://localhost:8000](http://localhost:8000)
3.  **Stop:**
    ```bash
    docker-compose down
    ```

## 🛠️ Manual Development
If you want to run locally without Docker for debugging:
1.  Start Redis: `docker run -p 6379:6379 redis`
2.  Install Dev Tools: `pip install -r requirements-dev.txt`
3.  Start Proxy: `uvicorn proxy.main:app --reload`
4.  Start Dashboard: `streamlit run dashboard/app.py`

## 🧠 AI Engine
* **Model:** Isolation Forest (Unsupervised Learning).
* **Features:** Path Length, Special Char Count, SQL Keywords, Entropy.
* **Training:** Self-learning based on "Normal" traffic patterns.


## System Architecture

```mermaid
graph TD
    User([User]) -->|Interacts| UI[Dashboard (app.py)]
    UI -->|Sends API Specs| AI[AI Engine (ai_engine.py)]
    AI -->|Scans & Probes| Target[Target API]
    Target -->|Returns Responses| AI
    AI -->|Calculates Zombie Score| Logic{Anomaly Detection}
    Logic -->|Results| UI


## 👤 Author
**Tejas Samir Alawani**
*Dept. of Computer Science & Engineering*
*Kolhapur Institute of Technology*