
import pandas as pd
import numpy as np
import os

print("\nStarting Feature Engineering V2...\n")

# -------------------------------------------------
# Paths
# -------------------------------------------------

BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_PATH = os.path.join(BASE_PATH, "outputs")

feature_path = os.path.join(OUTPUT_PATH, "fraud_feature_dataset.csv")
login_path = os.path.join(OUTPUT_PATH, "login_clean.csv")

# -------------------------------------------------
# Load Data
# -------------------------------------------------

df = pd.read_csv(feature_path, low_memory=False)
login = pd.read_csv(login_path, low_memory=False)

print("Datasets loaded.\n")

# -------------------------------------------------
# Prepare Data
# -------------------------------------------------

df["credttm"] = pd.to_datetime(df["credttm"])
df = df.sort_values(["account_id", "credttm"])

# -------------------------------------------------
# Rolling Behavioral Features (Exclude Current Txn)
# -------------------------------------------------

print("Creating rolling behavioral features...")

df["prev_txn_time"] = df.groupby("account_id")["credttm"].shift(1)

df["txn_count_24h_prev"] = (
    df.groupby("account_id")
    .rolling("24h", on="credttm")["colltnamt"]
    .count()
    .reset_index(level=0, drop=True)
)

df["txn_count_7d_prev"] = (
    df.groupby("account_id")
    .rolling("7D", on="credttm")["colltnamt"]
    .count()
    .reset_index(level=0, drop=True)
)

df["txn_count_24h_prev"] = df.groupby("account_id")["txn_count_24h_prev"].shift(1)
df["txn_count_7d_prev"] = df.groupby("account_id")["txn_count_7d_prev"].shift(1)

print("Rolling features created.\n")

# -------------------------------------------------
# Cold Start User Detection
# -------------------------------------------------

print("Detecting cold-start users...")

df["cold_start_user"] = np.where(
    (df["txn_count_24h_prev"].fillna(0) == 0) &
    (df["txn_count_7d_prev"].fillna(0) == 0),
    1,
    0
)

print("Cold-start feature created.\n")

# -------------------------------------------------
# Device Consistency Score
# -------------------------------------------------

print("Calculating device consistency...")

if "lst_lgin_dev_id" in login.columns:

    device_usage = (
        login.groupby(["usr_id", "lst_lgin_dev_id"])
        .size()
        .reset_index(name="device_count")
    )

    print("Calculating device consistency...")

if "lst_lgin_dev_id" in login.columns:

    device_usage = (
        login.groupby("lst_lgin_dev_id")
        .size()
        .reset_index(name="device_count")
    )

    device_consistency = device_usage["device_count"].max()

    df["device_consistency_score"] = device_consistency

else:
    df["device_consistency_score"] = 0

print("Device consistency calculated.\n")

# -------------------------------------------------
# IP Consistency Score
# -------------------------------------------------

print("Calculating IP consistency...")

if "lst_lgin_ip" in login.columns:

    ip_usage = (
        login.groupby(["usr_id", "lst_lgin_ip"])
        .size()
        .reset_index(name="ip_count")
    )

    ip_score = (
        ip_usage.groupby("usr_id")["ip_count"]
        .max()
        .reset_index(name="ip_consistency_score")
    )

    print("Calculating IP consistency...")

if "lst_lgin_ip" in login.columns:

    ip_usage = (
        login.groupby("lst_lgin_ip")
        .size()
        .reset_index(name="ip_count")
    )

    ip_consistency = ip_usage["ip_count"].max()

    df["ip_consistency_score"] = ip_consistency

else:
    df["ip_consistency_score"] = 0

print("IP consistency calculated.\n")

# -------------------------------------------------
# Recurring Amount Pattern
# -------------------------------------------------

print("Detecting recurring amounts...")

amount_frequency = (
    df.groupby(["account_id", "colltnamt"])
    .size()
    .reset_index(name="amount_freq")
)

recurring_amounts = amount_frequency[
    amount_frequency["amount_freq"] > 3
]

recurring_amounts["recurring_amount_flag"] = 1

df = df.merge(
    recurring_amounts[["account_id", "colltnamt", "recurring_amount_flag"]],
    on=["account_id", "colltnamt"],
    how="left"
)

df["recurring_amount_flag"] = df["recurring_amount_flag"].fillna(0)

print("Recurring amount detection completed.\n")

# -------------------------------------------------
# Strong Authentication Proxy
# -------------------------------------------------

print("Calculating strong authentication signal...")

df["strong_auth_flag"] = np.where(
    df["device_consistency_score"].fillna(0) > 3,
    1,
    0
)

print("Strong authentication feature created.\n")

# -------------------------------------------------
# Cleanup
# -------------------------------------------------

df.replace([np.inf, -np.inf], np.nan, inplace=True)

numeric_cols = df.select_dtypes(include=np.number).columns
df[numeric_cols] = df[numeric_cols].fillna(0)

# -------------------------------------------------
# Save Output
# -------------------------------------------------

output_path = os.path.join(
    OUTPUT_PATH,
    "fraud_feature_dataset_v2.csv"
)

df.to_csv(output_path, index=False)

print("Feature Engineering V2 completed successfully.")
print("Dataset saved as 'fraud_feature_dataset_v2.csv'\n")