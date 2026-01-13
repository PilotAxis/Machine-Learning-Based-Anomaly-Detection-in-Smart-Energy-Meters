import requests
import time
import random

API_URL = "http://127.0.0.1:8000/ingest"   # change port if needed

def generate_telemetry():
    return {
        "temperature": round(random.uniform(25, 80), 2),
        "vibration": round(random.uniform(0.1, 2.5), 2),
        "pressure": round(random.uniform(90, 120), 2)
    }

while True:
    data = generate_telemetry()
    try:
        response = requests.post(API_URL, json=data)
        print(f"Sent: {data} | Response: {response.status_code}")
    except Exception as e:
        print("Error sending data:", e)

    time.sleep(2)   # send data every 2 seconds