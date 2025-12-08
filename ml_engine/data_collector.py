import redis
import json
import csv
import os
import sys
from .config import REDIS_HOST, REDIS_PORT, REDIS_QUEUE, DATASET_PATH

def initialize_csv():
    """Creates the CSV file with headers if it doesn't exist."""
    file_exists = os.path.isfile(DATASET_PATH)
    if not file_exists:
        with open(DATASET_PATH, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # These are the columns our AI will learn from
            writer.writerow(["ip", "method", "path", "body_length", "body_content"])
        print(f"📁 Created new dataset at: {DATASET_PATH}")

def start_consumer():
    print("🚜 Harvester started... Waiting for traffic logs...")

    # Connect to Redis
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

    while True:
        # 1. Block and Wait for data (timeout=0 means wait forever)
        # result is a tuple: ('traffic_log', 'json_string')
        _, data_json = r.brpop(REDIS_QUEUE, timeout=0)

        # 2. Parse Data
        log_entry = json.loads(data_json)

        # 3. Extract Features (Simplify data for CSV)
        row = [
            log_entry.get("ip"),
            log_entry.get("method"),
            log_entry.get("path"),
            len(log_entry.get("body", "")), # Feature: Length of payload
            log_entry.get("body", "")       # Feature: The actual payload
        ]

        # 4. Write to Disk
        with open(DATASET_PATH, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(row)

        print(f"💾 Saved request: {log_entry.get('path')}")

if __name__ == "__main__":
    initialize_csv()
    try:
        start_consumer()
    except KeyboardInterrupt:
        print("\n🛑 Harvester stopped.")
        sys.exit(0)