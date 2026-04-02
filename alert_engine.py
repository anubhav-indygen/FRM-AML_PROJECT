
import pandas as pd
import numpy as np
import os

print("\nStarting Alert Engine...\n")


BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_PATH = os.path.join(BASE_PATH, "outputs")

feature_path = os.path.join(
    OUTPUT_PATH,
    "fraud_feature_dataset_v2.csv"
)

df = pd.read_csv(feature_path, low_memory=False)

print("Feature dataset loaded.\n")



print("Stage 1: Generating candidate alerts...")

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

print("Candidate rules created.\n")


# --------------------------------------------
# Risk Score (Stage 1)
# --------------------------------------------

print("Calculating base risk score...")

df["risk_score"] = (
    df["rule_high_value"] * 3 +
    df["rule_rapid_repeat"] * 3 +
    df["rule_dormant"] * 2 +
    df["rule_amount_spike"] * 3 +
    df["rule_velocity"] * 2
)

print("Base risk score calculated.\n")


# --------------------------------------------
# Stage 2 — False Positive Suppression
# --------------------------------------------

print("Stage 2: Applying suppressors...")

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

df["suppress_score"] = (
    df["suppress_device"] +
    df["suppress_ip"] +
    df["suppress_recurring"] +
    df["suppress_auth"]
)

df["risk_score"] = df["risk_score"] - df["suppress_score"]

df["risk_score"] = df["risk_score"].clip(lower=0)

print("Suppressors applied.\n")


# --------------------------------------------
# Risk Level Classification
# --------------------------------------------

print("Assigning risk levels...")

conditions = [
    df["risk_score"] >= 6,
    df["risk_score"] >= 3,
    df["risk_score"] < 3
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

print("Risk levels assigned.\n")


# --------------------------------------------
# Action Policy
# --------------------------------------------

print("Assigning actions...")

df["action"] = np.where(
    df["risk_level"] == "HIGH",
    "STEP_UP_OR_BLOCK",
    np.where(
        df["risk_level"] == "MEDIUM",
        "MANUAL_REVIEW",
        "ALLOW"
    )
)

print("Actions assigned.\n")


# --------------------------------------------
# Keep Alert Columns
# --------------------------------------------

alert_cols = [
    "account_id",
    "credttm",
    "colltnamt",
    "risk_score",
    "risk_level",
    "action",
    "rule_high_value",
    "rule_rapid_repeat",
    "rule_dormant",
    "rule_amount_spike",
    "rule_velocity",
    "suppress_device",
    "suppress_ip",
    "suppress_recurring",
    "suppress_auth"
]

existing_cols = [c for c in alert_cols if c in df.columns]

alerts = df[existing_cols].copy()


# --------------------------------------------
# Save Alerts
# --------------------------------------------

output_path = os.path.join(
    OUTPUT_PATH,
    "alerts.csv"
)

alerts.to_csv(output_path, index=False)

print("Alerts saved as alerts.csv")
print("\nAlert Engine Completed Successfully.\n")