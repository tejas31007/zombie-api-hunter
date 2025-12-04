# 🛡️ The Hunter (API Gateway)

This module acts as the **Reverse Proxy** and primary entry point for the Zombie API Hunter system. It is built using **FastAPI** to ensure high performance and asynchronous handling of requests.

## 🚀 Capabilities
1.  **Traffic Interception:** Captures all incoming HTTP requests.
2.  **Deep Packet Inspection:** - Logs the **Request Body** (Payload) to detect SQL Injection/XSS patterns.
    - Logs **Request Duration** to detect Slowloris/DoS attacks.
3.  **Async Forwarding:** Proxies valid requests to the Target App using a shared HTTP client.

## 🧠 Middleware Pipeline
The traffic flows through these security layers:
1.  **TimingMiddleware:** Measures latency (Time-to-Response).
2.  **TrafficInspector:** Extracts IP, Method, and Payload for the ML Engine.

## 🛠️ Tech Stack
* **Framework:** FastAPI
* **Client:** HTTPX (Async)
* **Logging:** Custom Structured Logger

## 🏃‍♂️ How to Run
```bash
uvicorn proxy.main:app --reload --port 8000