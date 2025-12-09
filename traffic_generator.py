import requests
import random
import time

PROXY_URL = "http://localhost:8000"

# 1. Normal Behaviors (The Good Guys)
def normal_user_action():
    actions = [
        # Check profile (Valid IDs)
        lambda: requests.get(f"{PROXY_URL}/api/user/{random.randint(1, 3)}"),
        # Secure Transfer (V2)
        lambda: requests.post(f"{PROXY_URL}/api/v2/transfer", json={"amount": random.randint(10, 100), "to": "Merchant"}),
        # Health Check
        lambda: requests.get(f"{PROXY_URL}/health"),
    ]
    action = random.choice(actions)
    try:
        action()
        print("✅ Sent Normal Request")
    except:
        print("❌ Request Failed")

# 2. Attack Behaviors (The Bad Guys)
def attacker_action():
    actions = [
        # Zombie API Attack (Using V1)
        lambda: requests.post(f"{PROXY_URL}/api/v1/transfer", json={"amount": 99999}),
        # BOLA Attack (Scanning IDs)
        lambda: requests.get(f"{PROXY_URL}/api/user/{random.randint(100, 500)}"),
        # SQL Injection / Payload Scan
        lambda: requests.post(f"{PROXY_URL}/api/login", json={"user": "admin' OR 1=1 --", "pass": "1234"}),
        # Path Traversal Probe
        lambda: requests.get(f"{PROXY_URL}/../../etc/passwd"),
    ]
    action = random.choice(actions)
    try:
        action()
        print("⚠️ Sent ATTACK Request")
    except:
        pass

if __name__ == "__main__":
    print("🚀 Starting Traffic Generation...")
    for i in range(200): # Generate 200 requests
        time.sleep(0.1)  # Fast but not instant

        # 80% chance of being Normal, 20% chance of being an Attacker
        if random.random() < 0.8:
            normal_user_action()
        else:
            attacker_action()

    print("🏁 Generation Complete.")