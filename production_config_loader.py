# ============================================
# FRM + AML Production Alert Run
# Uses best_threshold.json
# ============================================

import pandas as pd
import numpy as np
import json
import os

print("\nStarting Production Alert Run...\n")

# --------------------------------------------
# Paths
# --------------------------------------------

BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_PATH = os.path.join(BASE_PATH, "outputs")

feature_path = os.path.join(
    OUTPUT_PATH,
    "fraud_feature_dataset_v2.csv"
)

config_path = os.path.join(
    OUTPUT_PATH,
    "best_threshold.json"
)

df = pd.read_csv(feature_path, low_memory=False)

with open(config_path, "r") as f:
    config = json.load(f)

HIGH_THRESHOLD = config["high_threshold"]
MEDIUM_THRESHOLD = config["medium_threshold"]

print("Using thresholds:")
print("HIGH >=", HIGH_THRESHOLD)
print("MEDIUM >=", MEDIUM_THRESHOLD)


# --------------------------------------------
# Stage 1 Rules
# --------------------------------------------

df["rule_high_value"] = np.where(
    df.get("high_value_flag", 0) == 1,
    1,
    0
)

df["rule_rapid_repeat"] = np.where(
    df.get("rapid_repeat_flag", 0) == 1,
    1,
    0
)

df["rule_dormant"] = np.where(
    df.get("dormant_flag", 0) == 1,
    1,
    0
)

df["rule_amount_spike"] = np.where(
    df.get("amount_zscore", 0) > 3,
    1,
    0
)

df["rule_velocity"] = np.where(
    df.get("txn_count_24h_prev", 0) > 3,
    1,
    0
)


# --------------------------------------------
# Base Risk Score
# --------------------------------------------

df["risk_score"] = (
    df["rule_high_value"] * 3 +
    df["rule_rapid_repeat"] * 3 +
    df["rule_dormant"] * 2 +
    df["rule_amount_spike"] * 3 +
    df["rule_velocity"] * 2
)


# --------------------------------------------
# Suppressors
# --------------------------------------------

df["suppress_device"] = np.where(
    df.get("device_consistency_score", 0) > 5,
    1,
    0
)

df["suppress_ip"] = np.where(
    df.get("ip_consistency_score", 0) > 5,
    1,
    0
)

df["suppress_recurring"] = np.where(
    df.get("recurring_amount_flag", 0) == 1,
    1,
    0
)

df["suppress_auth"] = np.where(
    df.get("strong_auth_flag", 0) == 1,
    1,
    0
)

df["risk_score"] = (
    df["risk_score"]
    - df["suppress_device"]
    - df["suppress_ip"]
    - df["suppress_recurring"]
    - df["suppress_auth"]
)

df["risk_score"] = df["risk_score"].clip(lower=0)


# --------------------------------------------
# Apply thresholds from config
# --------------------------------------------

conditions = [
    df["risk_score"] >= HIGH_THRESHOLD,
    df["risk_score"] >= MEDIUM_THRESHOLD,
    df["risk_score"] < MEDIUM_THRESHOLD
]

choices = [
    "HIGH",
    "MEDIUM",
    "LOW"
]

df["risk_level"] = np.select(
    conditions,
    choices,
    default="LOW"
)


# --------------------------------------------
# Action policy
# --------------------------------------------

df["action"] = np.where(
    df["risk_level"] == "HIGH",
    "STEP_UP_OR_BLOCK",
    np.where(
        df["risk_level"] == "MEDIUM",
        "MANUAL_REVIEW",
        "ALLOW"
    )
)


# --------------------------------------------
# Save production alerts
# --------------------------------------------

output_path = os.path.join(
    OUTPUT_PATH,
    "alerts_production.csv"
)

df.to_csv(output_path, index=False)

print("alerts_production.csv saved.")
print("\nProduction run completed.\n")