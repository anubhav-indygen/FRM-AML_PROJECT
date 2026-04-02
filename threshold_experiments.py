# ============================================
# FRM + AML Threshold Experiments
# Precision-first tuning
# ============================================

import pandas as pd
import numpy as np
import os

print("\nStarting Threshold Experiments...\n")

# --------------------------------------------
# Paths
# --------------------------------------------

BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_PATH = os.path.join(BASE_PATH, "outputs")

alerts_path = os.path.join(
    OUTPUT_PATH,
    "alerts.csv"
)

alerts = pd.read_csv(alerts_path, low_memory=False)

print("Alerts loaded.\n")


# --------------------------------------------
# Threshold ranges to test
# --------------------------------------------

HIGH_VALUES = [5, 6, 7, 8, 9]
MEDIUM_VALUES = [2, 3, 4, 5]

results = []


# --------------------------------------------
# Loop over thresholds
# --------------------------------------------

for high in HIGH_VALUES:

    for medium in MEDIUM_VALUES:

        if medium >= high:
            continue

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

        high_count = (temp["risk_level"] == "HIGH").sum()
        med_count = (temp["risk_level"] == "MEDIUM").sum()
        low_count = (temp["risk_level"] == "LOW").sum()

        alert_rate = (high_count + med_count) / total

        results.append({
            "high_threshold": high,
            "medium_threshold": medium,
            "total_txn": total,
            "high_alerts": high_count,
            "medium_alerts": med_count,
            "low": low_count,
            "alert_rate": alert_rate
        })


# --------------------------------------------
# Save results
# --------------------------------------------

df = pd.DataFrame(results)

output_path = os.path.join(
    OUTPUT_PATH,
    "threshold_results.csv"
)

df.to_csv(output_path, index=False)

print("threshold_results.csv saved.")
print("\nThreshold experiments completed.\n")