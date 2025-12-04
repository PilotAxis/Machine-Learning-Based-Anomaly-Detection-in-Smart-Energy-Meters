import joblib
import pandas as pd
import numpy as np
import requests
import time
from datetime import datetime
import random

# Load the ML model
model = joblib.load("/Users/ahmedmajid/Desktop/Digital-Twin-for Smart-Energy-Meters/isolation_forest_model.pkl")

# Rolling buffer to compute rolling features
history = {
    "temperature": [],
    "vibration": [],
    "pressure": []
}
WINDOW = 5  # rolling window size

# API where edge device sends summarized health data
API_URL = "http://127.0.0.1:8000/edge_health"

# === FUNCTIONS ===

def generate_sensor_data():
    """Simulate real sensor data (replace with real sensors later)."""
    return {
        "temperature": round(random.uniform(30, 80), 2),
        "vibration": round(random.uniform(0.1, 2.5), 2),
        "pressure": round(random.uniform(90, 120), 2)
    }

def compute_sensor_risk(temp, vib, pres):
    temp_risk = 0 if temp < 60 else (0.4 if temp < 70 else 1.0)
    vib_risk = 0 if vib < 1.5 else (0.5 if vib < 2.0 else 1.0)
    pres_risk = 0 if 95 < pres < 115 else 1.0
    return temp_risk, vib_risk, pres_risk

def compute_mhi(data, ml_anomaly):
    temp, vib, pres = data["temperature"], data["vibration"], data["pressure"]

    temp_risk, vib_risk, pres_risk = compute_sensor_risk(temp, vib, pres)
    sensor_risk = (temp_risk + vib_risk + pres_risk) / 3

    ml_risk = float(ml_anomaly)

    # Edge-calculated MHI
    MHI = 100 * (1 - (0.4*sensor_risk + 0.3*0 + 0.3*ml_risk))
    return max(0, min(100, MHI))

# === MAIN LOOP ===

while True:
    # Step 1: Collect sensor readings
    data = generate_sensor_data()

    # Update rolling history
    history["temperature"].append(data["temperature"])
    history["vibration"].append(data["vibration"])
    history["pressure"].append(data["pressure"])

    # Keep only the last WINDOW readings
    for key in history:
        if len(history[key]) > WINDOW:
            history[key] = history[key][-WINDOW:]

    # Step 2: ML anomaly detection
    # Compute rolling features
    temp_roll_mean = np.mean(history["temperature"])
    temp_roll_std = np.std(history["temperature"])
    vib_roll_mean = np.mean(history["vibration"])
    vib_roll_std = np.std(history["vibration"])
    pres_roll_mean = np.mean(history["pressure"])
    pres_roll_std = np.std(history["pressure"])

    # Build full feature set required by the model
    full_features = {
        "temperature": data["temperature"],
        "vibration": data["vibration"],
        "pressure": data["pressure"],
        "temp_roll_mean": temp_roll_mean,
        "temp_roll_std": temp_roll_std,
        "vib_roll_mean": vib_roll_mean,
        "vib_roll_std": vib_roll_std,
        "pres_roll_mean": pres_roll_mean,
        "pres_roll_std": pres_roll_std
    }

    df = pd.DataFrame([full_features])

    ml_pred = model.predict(df)[0]
    ml_anomaly = 1 if ml_pred == -1 else 0

    # Step 3: Compute health score
    MHI = compute_mhi(data, ml_anomaly)

    # Step 4: Prepare edge packet
    packet = {
        "timestamp": datetime.utcnow().isoformat(),
        "temperature": data["temperature"],
        "vibration": data["vibration"],
        "pressure": data["pressure"],
        "ml_anomaly": ml_anomaly,
        "MHI": MHI
    }

    print("EDGE PACKET:", packet)

    # Step 5: Send to cloud API
    try:
        requests.post(API_URL, json=packet)
    except:
        print("Could not send to cloud")

    time.sleep(3)