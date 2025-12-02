# 🧟 Zombie API Hunter (Sentinel)

> **An AI-Powered API Security Gateway acting as a defense against Zombie APIs, BOLA attacks, and Anomaly Traffic.**

## 📖 Overview
**Zombie API Hunter** is a research-grade security platform designed to detect and block advanced API attacks that traditional WAFs (Web Application Firewalls) miss. 

Unlike signature-based firewalls, this system uses **Unsupervised Machine Learning (Isolation Forest)** to learn "normal" traffic patterns and flag behavioral anomalies in real-time.

### 🎯 The Problem
1. **Zombie APIs:** Old, deprecated endpoints (e.g., `/v1/login`) often remain active and unpatched, becoming easy targets for hackers.
2. **BOLA (Broken Object Level Authorization):** Attackers manipulating IDs (e.g., changing `/user/100` to `/user/101`) to access unauthorized data.
3. **Anomaly Traffic:** Scraping, Brute-force, and non-standard usage patterns.

## 🏗 Architecture  
The system follows a Microservices event-driven architecture:

graph TD
    User[Attacker/User] -->|HTTP Request| Proxy(FastAPI Gateway)
    Proxy -->|1. Log Request| Redis[(Redis Queue)]
    Proxy -->|2. Forward Request| Victim(Spring Boot App)
    
    subgraph "Async Security Engine"
        Redis -->|Pop Log| ML[PyTorch Inference Engine]
        ML -->|3. Analyze| Model{Anomaly?}
        Model -->|Yes| BlockList[Redis Blocklist]
        Model -->|No| Safe[Log Stats]
    end
    
    Proxy -->|4. Check Blocklist| BlockList

🛠 Tech Stack
Proxy (The Hunter): Python (FastAPI, Asyncio)
Target App (The Victim): Java (Spring Boot)
Message Broker: Redis
ML Engine: PyTorch, Scikit-Learn (Isolation Forest)
Dashboard: React.js, Tailwind CSS

🗓 Project Roadmap
[ ] Phase 1: Async Proxy Setup (FastAPI)
[ ] Phase 2: Vulnerable Target App (Spring Boot)
[ ] Phase 3: Data Pipeline & Event Queue (Redis)
[ ] Phase 4: ML Anomaly Detection (PyTorch)
[ ] Phase 5: Threat Dashboard (React)


## 📄 License
This project is open-source and available under the [MIT License](LICENSE).

Created by Tejas Alawani