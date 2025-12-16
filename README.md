# 🧟 Zombie API Hunter

A Zero-Trust Reverse Proxy powered by AI to protect Legacy APIs.

## 🛡️ Architecture
1.  **Interceptor:** FastAPI Reverse Proxy (Port 8000).
2.  **Brain:** Scikit-Learn Isolation Forest (Anomaly Detection).
3.  **Shield:** Redis-based Rate Limiting (DDoS Protection).
4.  **Monitor:** Streamlit Real-time Dashboard.
5.  **Target:** Vulnerable Java Spring Boot Application.

## 🚀 Quick Start
1.  **Start Redis:** `docker start zombie-redis`
2.  **Start Victim:** `cd victim && mvn spring-boot:run`
3.  **Start Proxy:** `uvicorn proxy.main:app --reload`
4.  **Start Dashboard:** `streamlit run dashboard/app.py`

## 🧠 AI Engine
* **Model:** Isolation Forest (Unsupervised Learning).
* **Features:** Path Length, Special Char Count, SQL Keywords, Entropy.
* **Training:** Self-learning based on "Normal" traffic patterns.

## 👤 Author
**Tejas Samir Alawani**
*Dept. of Computer Science & Engineering*
*Kolhapur Institute of Technology*