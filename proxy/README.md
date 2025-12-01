# 🛡️ The Hunter (API Gateway)

This module acts as the **Reverse Proxy** and primary entry point for the Zombie API Hunter system. It is built using **FastAPI** to ensure high performance and asynchronous handling of requests.

## 🚀 Responsibilities
1.  **Intercept Traffic:** Receives all incoming HTTP requests from the client.
2.  **Log Data:** Captures request metadata (headers, body, timestamps) for analysis.
3.  **Enforce Security:** Checks the Redis Blocklist to reject malicious IPs.
4.  **Forward Traffic:** Asynchronously proxies valid requests to the Victim App (Spring Boot).

## 🛠️ Tech Stack
* **Framework:** FastAPI (Python)
* **Server:** Uvicorn (ASGI)
* **HTTP Client:** HTTPX (Async)

## 🏃‍♂️ How to Run
Ensure you are in the root directory and your virtual environment is active.

```bash
# Start the server with hot-reload enabled
uvicorn proxy.main:app --reload --port 8000