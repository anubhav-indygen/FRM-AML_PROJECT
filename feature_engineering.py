# ============================================
# FRM + AML Feature Engineering Script
# Fully Stable Version (No account_id Loss)
# ============================================

import pandas as pd
import numpy as np
import os

print("\nStarting Feature Engineering...\n")

# --------------------------------------------
# Paths
# --------------------------------------------

BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_PATH = os.path.join(BASE_PATH, "outputs")

# --------------------------------------------
# Load Data
# --------------------------------------------

login = pd.read_csv(os.path.join(OUTPUT_PATH, "login_clean.csv"), low_memory=False)
mandate = pd.read_csv(os.path.join(OUTPUT_PATH, "mandate_clean.csv"), low_memory=False)
fd = pd.read_csv(os.path.join(OUTPUT_PATH, "fd_clean.csv"), low_memory=False)

print("Clean datasets loaded.\n")

# --------------------------------------------
# Normalize Column Names
# --------------------------------------------

login.columns = login.columns.str.strip().str.lower()
mandate.columns = mandate.columns.str.strip().str.lower()
fd.columns = fd.columns.str.strip().str.lower()

# --------------------------------------------
# Detect Account Column
# --------------------------------------------

possible_account_cols = [
    "account_hash",
    "dbtr_accno",
    "linked_fino_account",
    "account_no",
    "account_id"
]

ACCOUNT_COL = next((col for col in possible_account_cols if col in mandate.columns), None)

if ACCOUNT_COL is None:
    print("Columns available in mandate:", mandate.columns.tolist())
    raise ValueError("No account identifier column found.")

if ACCOUNT_COL != "account_id":
    mandate.rename(columns={ACCOUNT_COL: "account_id"}, inplace=True)

print("Using 'account_id' as account identifier.\n")

# --------------------------------------------
# Validate Required Columns
# --------------------------------------------

required = ["account_id", "credttm", "colltnamt"]
for col in required:
    if col not in mandate.columns:
        raise ValueError(f"Missing required column: {col}")

# --------------------------------------------
# Data Preparation
# --------------------------------------------

mandate["credttm"] = pd.to_datetime(mandate["credttm"], errors="coerce")
mandate["colltnamt"] = pd.to_numeric(mandate["colltnamt"], errors="coerce")

mandate = mandate.dropna(subset=["account_id", "credttm", "colltnamt"])
mandate = mandate.sort_values(["account_id", "credttm"]).reset_index(drop=True)

# --------------------------------------------
# Time-Based Features
# --------------------------------------------

print("Creating transaction-level features...")

mandate["transaction_hour"] = mandate["credttm"].dt.hour
mandate["day_of_week"] = mandate["credttm"].dt.dayofweek
mandate["is_weekend"] = (mandate["day_of_week"] >= 5).astype(int)

# --------------------------------------------
# Velocity Features (NO groupby+apply)
# --------------------------------------------

print("Creating velocity features...")

mandate = mandate.set_index("credttm")

mandate["txn_count_24h"] = (
    mandate.groupby("account_id")["colltnamt"]
    .rolling("24h")
    .count()
    .reset_index(level=0, drop=True)
)

mandate["txn_count_7d"] = (
    mandate.groupby("account_id")["colltnamt"]
    .rolling("7d")
    .count()
    .reset_index(level=0, drop=True)
)

mandate = mandate.reset_index()

# --------------------------------------------
# Amount Behavior Features
# --------------------------------------------

mandate["user_mean_amt"] = (
    mandate.groupby("account_id")["colltnamt"]
    .transform("mean")
)

mandate["user_std_amt"] = (
    mandate.groupby("account_id")["colltnamt"]
    .transform("std")
    .fillna(0)
)

mandate["amount_deviation"] = (
    mandate["colltnamt"] - mandate["user_mean_amt"]
)

mandate["amount_zscore"] = np.where(
    mandate["user_std_amt"] > 0,
    mandate["amount_deviation"] / mandate["user_std_amt"],
    0
)

mandate["amount_ratio"] = np.where(
    mandate["user_mean_amt"] > 0,
    mandate["colltnamt"] / mandate["user_mean_amt"],
    1
)

print("Transaction features created.\n")

# --------------------------------------------
# Behavioral Features
# --------------------------------------------

print("Creating behavioral features...")

behavioral_features = pd.DataFrame()

if "usr_id" in login.columns:

    device_counts = (
        login.groupby("usr_id")["lst_lgin_dev_id"]
        .nunique()
        .reset_index(name="device_count")
        if "lst_lgin_dev_id" in login.columns
        else pd.DataFrame()
    )

    login_counts = (
        login.groupby("usr_id")
        .size()
        .reset_index(name="total_logins")
    )

    behavioral_features = (
        pd.merge(device_counts, login_counts, on="usr_id", how="outer")
        if not device_counts.empty
        else login_counts
    )

print("Behavioral features created.\n")

# --------------------------------------------
# Financial Profile Features
# --------------------------------------------

print("Creating financial profile features...")

fd_summary = pd.DataFrame()

if "fd_amount" in fd.columns:

    fd_account_col = next((col for col in possible_account_cols if col in fd.columns), None)

    if fd_account_col:

        if fd_account_col != "account_id":
            fd.rename(columns={fd_account_col: "account_id"}, inplace=True)

        fd["fd_amount"] = pd.to_numeric(fd["fd_amount"], errors="coerce")

        fd_summary = (
            fd.groupby("account_id")
            .agg(
                total_fd_amount=("fd_amount", "sum"),
                avg_fd_amount=("fd_amount", "mean"),
                fd_count=("fd_amount", "count")
            )
            .reset_index()
        )

print("Financial features created.\n")

# --------------------------------------------
# Regulatory Flags
# --------------------------------------------

print("Creating regulatory flags...")

threshold = 200000

mandate["high_value_flag"] = (mandate["colltnamt"] > threshold).astype(int)

mandate["time_diff_minutes"] = (
    mandate.groupby("account_id")["credttm"]
    .diff()
    .dt.total_seconds() / 60
)

mandate["rapid_repeat_flag"] = np.where(
    mandate["time_diff_minutes"].between(0, 10, inclusive="left"),
    1,
    0
)

mandate["days_since_last_txn"] = (
    mandate.groupby("account_id")["credttm"]
    .diff()
    .dt.days
)

mandate["dormant_flag"] = np.where(
    mandate["days_since_last_txn"] > 180,
    1,
    0
)

print("Regulatory flags created.\n")

# --------------------------------------------
# Merge Features
# --------------------------------------------

print("Merging features...")

if not fd_summary.empty:
    mandate = mandate.merge(fd_summary, on="account_id", how="left")

if not behavioral_features.empty and "usr_id" in mandate.columns:
    mandate = mandate.merge(behavioral_features, on="usr_id", how="left")

print("Merging complete.\n")



mandate.replace([np.inf, -np.inf], np.nan, inplace=True)

numeric_cols = mandate.select_dtypes(include=np.number).columns
mandate[numeric_cols] = mandate[numeric_cols].fillna(0)

# --------------------------------------------
# Save Dataset
# --------------------------------------------

output_path = os.path.join(OUTPUT_PATH, "fraud_feature_dataset.csv")
mandate.to_csv(output_path, index=False)

print("Feature dataset saved as 'fraud_feature_dataset.csv'")
print("Feature Engineering Completed Successfully.\n")