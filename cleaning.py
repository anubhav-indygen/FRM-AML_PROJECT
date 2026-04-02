
import pandas as pd
import numpy as np
import hashlib
import os

print("Starting data cleaning process...\n")


def hash_id(value):
    """Hash sensitive identifiers using SHA256."""
    if pd.isna(value):
        return np.nan
    return hashlib.sha256(str(value).encode()).hexdigest()


def clean_amount(series):
    """Convert amount column to numeric safely."""
    return (
        series.astype(str)
        .str.replace(",", "", regex=False)
        .str.replace("₹", "", regex=False)
        .str.strip()
        .replace("", np.nan)
        .astype(float)
    )


def standardize_columns(df):
    """Standardize column names."""
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
    return df


# -------------------------------
# Load Data
# -------------------------------

DATA_PATH = "data"

login_path = os.path.join(DATA_PATH, "Login_1.2.xlsx")
mandate_path = os.path.join(DATA_PATH, "Emandate_Data_07082025.xlsx")
fd_path = os.path.join(DATA_PATH, "1147_FD_Report (2).xlsx")

print("Loading datasets...")

login = pd.read_excel(login_path)
mandate = pd.read_excel(mandate_path)
fd = pd.read_excel(fd_path)

print("Datasets loaded successfully.\n")


# -------------------------------
# Standardize Column Names
# -------------------------------

login = standardize_columns(login)
mandate = standardize_columns(mandate)
fd = standardize_columns(fd)

print("Column names standardized.\n")


# -------------------------------
# CLEAN LOGIN DATASET
# -------------------------------

print("Cleaning Login dataset...")

# Combine date + time if present
if "frst_lgin_dte_day" in login.columns and "frst_lgin_tme_day" in login.columns:
    login["login_timestamp"] = pd.to_datetime(
        login["frst_lgin_dte_day"].astype(str) + " " +
        login["frst_lgin_tme_day"].astype(str),
        errors="coerce"
    )

# Handle missing IP / device
if "lst_lgin_ip" in login.columns:
    login["lst_lgin_ip"].fillna("unknown_ip", inplace=True)

if "lst_lgin_dev_id" in login.columns:
    login["lst_lgin_dev_id"].fillna("unknown_device", inplace=True)

# Remove duplicates
login.drop_duplicates(inplace=True)

# Sort chronologically
if "login_timestamp" in login.columns and "usr_id" in login.columns:
    login.sort_values(["usr_id", "login_timestamp"], inplace=True)

print("Login dataset cleaned.\n")


# -------------------------------
# CLEAN MANDATE DATASET
# -------------------------------

print("Cleaning Mandate dataset...")

# Remove sensitive fields
sensitive_cols = ["cvv", "pin", "cardno", "aadhaarno", "expiry"]
mandate.drop(columns=sensitive_cols, errors="ignore", inplace=True)

# Convert timestamp
if "credttm" in mandate.columns:
    mandate["credttm"] = pd.to_datetime(mandate["credttm"], errors="coerce")

# Convert amount columns
if "colltnamt" in mandate.columns:
    mandate["colltnamt"] = clean_amount(mandate["colltnamt"])

if "maxamt" in mandate.columns:
    mandate["maxamt"] = clean_amount(mandate["maxamt"])

# Drop rows missing critical fields
critical_fields = ["colltnamt", "credttm"]
existing_critical = [col for col in critical_fields if col in mandate.columns]
mandate.dropna(subset=existing_critical, inplace=True)

# Remove duplicate transaction IDs
if "transactionid" in mandate.columns:
    mandate.drop_duplicates(subset=["transactionid"], inplace=True)

# Standardize status
if "mnd_status" in mandate.columns:
    mandate["mnd_status"] = mandate["mnd_status"].astype(str).str.upper().str.strip()

# Clean account numbers
if "dbtr_accno" in mandate.columns:
    mandate["dbtr_accno"] = mandate["dbtr_accno"].astype(str).str.strip()
    mandate["account_hash"] = mandate["dbtr_accno"].apply(hash_id)
    mandate.drop(columns=["dbtr_accno"], inplace=True)

# Sort chronologically
if "account_hash" in mandate.columns and "credttm" in mandate.columns:
    mandate.sort_values(["account_hash", "credttm"], inplace=True)

print("Mandate dataset cleaned.\n")


# -------------------------------
# CLEAN FD DATASET
# -------------------------------

print("Cleaning FD dataset...")

# Convert amount columns if present
fd_amount_cols = ["fd_amount", "ledger_balance", "mab"]
for col in fd_amount_cols:
    if col in fd.columns:
        fd[col] = clean_amount(fd[col])

# Convert closure date
if "closure_date" in fd.columns:
    fd["closure_date"] = pd.to_datetime(fd["closure_date"], errors="coerce")

# Clean account number
if "linked_fino_account" in fd.columns:
    fd["linked_fino_account"] = fd["linked_fino_account"].astype(str).str.strip()
    fd["account_hash"] = fd["linked_fino_account"].apply(hash_id)
    fd.drop(columns=["linked_fino_account"], inplace=True)

# Remove duplicates
fd.drop_duplicates(inplace=True)

print("FD dataset cleaned.\n")


# -------------------------------
# Final Validation
# -------------------------------

print("Final validation checks...")

print("Login shape:", login.shape)
print("Mandate shape:", mandate.shape)
print("FD shape:", fd.shape)

print("\nMissing values (Mandate):")
print(mandate.isnull().sum())

print("\nCleaning completed successfully.\n")


# -------------------------------
# Save Cleaned Files
# -------------------------------

OUTPUT_PATH = "outputs"
os.makedirs(OUTPUT_PATH, exist_ok=True)

login.to_csv(os.path.join(OUTPUT_PATH, "login_clean.csv"), index=False)
mandate.to_csv(os.path.join(OUTPUT_PATH, "mandate_clean.csv"), index=False)
fd.to_csv(os.path.join(OUTPUT_PATH, "fd_clean.csv"), index=False)

print("Cleaned datasets saved in /outputs folder.")
print("Process finished successfully.")