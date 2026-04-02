

import pandas as pd
import numpy as np
import os
from datetime import datetime

print("\nStarting Alert Feedback Loop...\n")



BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_PATH = os.path.join(BASE_PATH, "outputs")

alerts_path = os.path.join(
    OUTPUT_PATH,
    "alerts.csv"
)



alerts = pd.read_csv(alerts_path, low_memory=False)

print("Alerts loaded.\n")


# --------------------------------------------
# Create Alert ID
# --------------------------------------------

alerts["alert_id"] = (
    "ALERT_" +
    alerts.index.astype(str).str.zfill(6)
)


# --------------------------------------------
# Transaction ID (fallback if missing)
# --------------------------------------------

if "transactionid" not in alerts.columns:

    alerts["transactionid"] = alerts.index


# --------------------------------------------
# Trigger Rules Column
# --------------------------------------------

rule_cols = [
    "rule_high_value",
    "rule_rapid_repeat",
    "rule_dormant",
    "rule_amount_spike",
    "rule_velocity"
]

existing_rules = [c for c in rule_cols if c in alerts.columns]

def get_rules(row):

    fired = []

    for r in existing_rules:
        if row[r] == 1:
            fired.append(r)

    return ",".join(fired)

alerts["trigger_rules"] = alerts.apply(
    get_rules,
    axis=1
)


# --------------------------------------------
# Created Time
# --------------------------------------------

alerts["created_at"] = datetime.now()


# --------------------------------------------
# Analyst Decision (initially unknown)
# --------------------------------------------

alerts["analyst_decision"] = "PENDING"


# --------------------------------------------
# Customer Confirmation
# --------------------------------------------

alerts["customer_confirmation"] = "UNKNOWN"


# --------------------------------------------
# Final Label
# --------------------------------------------

alerts["final_label"] = "unknown_pending"


# --------------------------------------------
# Select Required Fields
# --------------------------------------------

cols = [
    "alert_id",
    "transactionid",
    "trigger_rules",
    "risk_score",
    "created_at",
    "analyst_decision",
    "customer_confirmation",
    "final_label"
]

existing_cols = [c for c in cols if c in alerts.columns]

alert_outcomes = alerts[existing_cols].copy()


# --------------------------------------------
# Save
# --------------------------------------------

output_path = os.path.join(
    OUTPUT_PATH,
    "alert_outcomes.csv"
)

alert_outcomes.to_csv(output_path, index=False)

print("alert_outcomes.csv created.")
print("\nFeedback loop initialized.\n")