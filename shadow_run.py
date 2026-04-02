# ============================================
# FRM + AML Shadow Run + Threshold Tuning
# ============================================

import pandas as pd
import numpy as np
import os

print("\nStarting Shadow Run...\n")

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
# Thresholds (tunable)
# --------------------------------------------

HIGH_THRESHOLD = 6
MEDIUM_THRESHOLD = 3

print("Using thresholds:")
print("HIGH >=", HIGH_THRESHOLD)
print("MEDIUM >=", MEDIUM_THRESHOLD)


# --------------------------------------------
# Recalculate Risk Levels (Shadow Mode)
# --------------------------------------------

conditions = [
    alerts["risk_score"] >= HIGH_THRESHOLD,
    alerts["risk_score"] >= MEDIUM_THRESHOLD,
    alerts["risk_score"] < MEDIUM_THRESHOLD
]

choices = [
    "HIGH",
    "MEDIUM",
    "LOW"
]

alerts["shadow_risk_level"] = np.select(
    conditions,
    choices,
    default="LOW"
)


# --------------------------------------------
# Shadow Action (No blocking)
# --------------------------------------------

alerts["shadow_action"] = np.where(
    alerts["shadow_risk_level"] == "HIGH",
    "LOG_ONLY",
    np.where(
        alerts["shadow_risk_level"] == "MEDIUM",
        "LOG_ONLY",
        "ALLOW"
    )
)


# --------------------------------------------
# Save shadow alerts
# --------------------------------------------

shadow_path = os.path.join(
    OUTPUT_PATH,
    "shadow_alerts.csv"
)

alerts.to_csv(shadow_path, index=False)

print("shadow_alerts.csv saved.\n")


# --------------------------------------------
# Summary Metrics
# --------------------------------------------

summary = {}

summary["total_txn"] = len(alerts)

summary["high_alerts"] = (
    alerts["shadow_risk_level"] == "HIGH"
).sum()

summary["medium_alerts"] = (
    alerts["shadow_risk_level"] == "MEDIUM"
).sum()

summary["low_alerts"] = (
    alerts["shadow_risk_level"] == "LOW"
).sum()

summary["alert_rate"] = (
    (summary["high_alerts"] + summary["medium_alerts"])
    / summary["total_txn"]
)

summary_df = pd.DataFrame([summary])

summary_path = os.path.join(
    OUTPUT_PATH,
    "shadow_summary.csv"
)

summary_df.to_csv(summary_path, index=False)

print("shadow_summary.csv saved.\n")

print("Shadow Run Completed.\n")