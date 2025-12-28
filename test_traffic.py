import requests
import time
import random
import redis
import json
import uuid
from datetime import datetime

# --- CONFIG ---
PROXY_URL = "http://localhost:8000/api/v1/resource" # Adjust if your target path is different
REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_QUEUE = "traffic_logs"

# Connect to Redis for "Simulation Mode" (Fake IPs)
r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

def send_real_request(type="safe"):
    """Sends actual HTTP requests to your Proxy."""
    try:
        if type == "safe":
            # Normal JSON payload
            payload = {"user_id": 123, "action": "login", "timestamp": time.time()}
            requests.post(PROXY_URL, json=payload)
            print("🟢 Sent SAFE Request")
            
        elif type == "malicious":
            # Typical SQL Injection or huge payload patterns
            # Note: This depends on what your Isolation Forest learned as 'anomaly'
            # We simulate a "weird" request by sending a massive string
            payload = {"data": "A" * 10000, "attack": "' OR '1'='1"} 
            requests.post(PROXY_URL, json=payload)
            print("🔴 Sent MALICIOUS Request")
            
        elif type == "spam":
            # Fast requests to trigger Rate Limiter
            for _ in range(5):
                requests.get(PROXY_URL)
                print("🟡 Sent SPAM Request")
                
    except Exception as e:
        print(f"Request failed: {e}")

def simulate_global_traffic(count=10):
    """
    Directly pushes logs to Redis with RANDOM IPs.
    This is necessary because localhost only has one IP (127.0.0.1).
    This tricks the dashboard into showing a cool map.
    """
    print(f"\n🌍 Simulating {count} attacks from around the world...")
    
    actions = ["ALLOWED", "BLOCKED_AI", "BLOCKED_RATE"]
    paths = ["/api/login", "/admin", "/payment", "/v1/data"]
    
    for _ in range(count):
        # Generate random IP
        fake_ip = f"{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}"
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "ip": fake_ip,
            "method": random.choice(["GET", "POST"]),
            "path": random.choice(paths),
            "headers": {"User-Agent": "Simulation-Script"},
            "body": "simulated_traffic_payload",
            "action": random.choice(actions),
            "risk_score": random.random(), # Random float 0.0 - 1.0
            "request_id": str(uuid.uuid4())
        }
        
        # Push to Redis
        r.lpush(REDIS_QUEUE, json.dumps(log_entry))
        time.sleep(0.1)
    
    print("✅ Simulation complete! Check the Map.")

if __name__ == "__main__":
    print("--- 🧟 ZOMBIE HUNTER TEST SUITE ---")
    print("1. Sending REAL traffic (Triggers Charts & Metrics)...")
    
    # 1. Send Safe Traffic
    for _ in range(3): 
        send_real_request("safe")
        time.sleep(0.5)

    # 2. Send Malicious Traffic (Try to trigger AI)
    for _ in range(2):
        send_real_request("malicious")
        time.sleep(0.5)

    # 3. Send Spam Traffic (Trigger Rate Limit)
    # This fires requests as fast as possible
    send_real_request("spam") 

    # 4. Simulate Global Map Data
    simulate_global_traffic(count=20)
    
    print("\n🎉 Done! Go to http://localhost:8501 and hit 'Refresh Data'")