# ============================================
# FRM + AML Precision / Analyst Load Estimator
# ============================================

import pandas as pd
import numpy as np
import os

print("\nStarting Precision Estimation...\n")

# --------------------------------------------
# Paths
# --------------------------------------------

BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_PATH = os.path.join(BASE_PATH, "outputs")

alerts_path = os.path.join(
    OUTPUT_PATH,
    "alerts.csv"
)

threshold_path = os.path.join(
    OUTPUT_PATH,
    "threshold_results.csv"
)

alerts = pd.read_csv(alerts_path, low_memory=False)
thresholds = pd.read_csv(threshold_path)

print("Data loaded.\n")


results = []


# --------------------------------------------
# Loop over threshold configs
# --------------------------------------------

for _, row in thresholds.iterrows():

    high = row["high_threshold"]
    medium = row["medium_threshold"]

    temp = alerts.copy()

    conditions = [
        temp["risk_score"] >= high,
        temp["risk_score"] >= medium,
        temp["risk_score"] < medium
    ]

    choices = [
        "HIGH",
        "MEDIUM",
        "LOW"
    ]

    temp["risk_level"] = np.select(
        conditions,
        choices,
        default="LOW"
    )

    total = len(temp)

    high_alerts = (temp["risk_level"] == "HIGH").sum()
    medium_alerts = (temp["risk_level"] == "MEDIUM").sum()

    alerts_total = high_alerts + medium_alerts

    alert_rate = alerts_total / total

    # analyst workload = medium alerts
    analyst_reviews = medium_alerts

    # noise score (heuristic)
    noise_score = alert_rate + (analyst_reviews / total)

    results.append({
        "high_threshold": high,
        "medium_threshold": medium,
        "total_txn": total,
        "alerts": alerts_total,
        "high_alerts": high_alerts,
        "medium_alerts": medium_alerts,
        "alert_rate": alert_rate,
        "analyst_reviews": analyst_reviews,
        "noise_score": noise_score
    })


# --------------------------------------------
# Save
# --------------------------------------------

df = pd.DataFrame(results)

output_path = os.path.join(
    OUTPUT_PATH,
    "precision_estimate.csv"
)

df.to_csv(output_path, index=False)

print("precision_estimate.csv saved.")
print("\nPrecision estimation completed.\n")