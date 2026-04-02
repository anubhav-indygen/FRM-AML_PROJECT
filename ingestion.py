
import pandas as pd
import numpy as np
import os
from datetime import datetime

print("\nStarting Ingestion Process...\n")


BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_PATH, "data")
OUTPUT_PATH = os.path.join(BASE_PATH, "outputs")

os.makedirs(OUTPUT_PATH, exist_ok=True)

print("Project Root:", BASE_PATH)
print("Data Path:", DATA_PATH)

login_path = os.path.join(DATA_PATH, "Login_1.2.xlsx")
mandate_path = os.path.join(DATA_PATH, "Emandate_Data_07082025.xlsx")
fd_path = os.path.join(DATA_PATH, "1147_FD_Report (2).xlsx")

# --------------------------------------------
# Utility Functions
# --------------------------------------------

def standardize_columns(df):
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
        .str.replace(r"[^a-z0-9_]", "", regex=True)
    )
    return df


def validate_required_columns(df, required_cols, dataset_name):
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"{dataset_name} missing required columns: {missing}")


def enforce_types_login(df):
    df["usr_id"] = df["usr_id"].astype(str).str.strip()
    return df


def enforce_types_mandate(df):

    df["account_id"] = df["account_id"].astype(str).str.strip()

    df["credttm"] = pd.to_datetime(df["credttm"], errors="coerce")

    df["colltnamt"] = (
        df["colltnamt"]
        .astype(str)
        .str.replace(",", "", regex=False)
        .str.replace("₹", "", regex=False)
        .str.strip()
    )

    df["colltnamt"] = pd.to_numeric(df["colltnamt"], errors="coerce")

    df = df.dropna(subset=["account_id", "credttm", "colltnamt"])

    return df


def enforce_types_fd(df):
    df["account_id"] = df["account_id"].astype(str).str.strip()
    df["fd_amount"] = pd.to_numeric(df["fd_amount"], errors="coerce")
    return df


def detect_fd_header(path):

    temp = pd.read_excel(path, header=None)

    for i in range(30):

        row = temp.iloc[i].astype(str).str.lower()

        if row.str.contains("fd amount", regex=False).any():
            print(f"Detected FD header at row: {i}")
            return i

        if row.str.contains("fd a c no", regex=False).any():
            print(f"Detected FD header at row: {i}")
            return i

    print("Preview of first rows for debugging:")
    print(temp.head(10))

    raise ValueError("Could not detect header row in FD file.")


def generate_quality_report(df, dataset_name):
    report = pd.DataFrame({
        "dataset": dataset_name,
        "column": df.columns,
        "null_percent": df.isnull().mean() * 100,
        "unique_count": df.nunique(),
        "dtype": df.dtypes.astype(str)
    })
    return report


# --------------------------------------------
# Load Login Dataset
# --------------------------------------------

print("\nLoading Login dataset...")

login = pd.read_excel(login_path)
login = standardize_columns(login)

validate_required_columns(login, ["usr_id"], "Login")

login = enforce_types_login(login)
login.drop_duplicates(inplace=True)
login.sort_values("usr_id", inplace=True)
login.reset_index(drop=True, inplace=True)

print("Login rows loaded:", len(login))


# --------------------------------------------
# Load Mandate Dataset
# --------------------------------------------

print("\nLoading Mandate dataset...")

mandate = pd.read_excel(mandate_path)
mandate = standardize_columns(mandate)

possible_account_cols = ["account_id", "account_hash", "dbtr_accno"]

account_col = next((c for c in possible_account_cols if c in mandate.columns), None)

if account_col is None:
    print("Available mandate columns:", mandate.columns.tolist())
    raise ValueError("No account identifier column found in mandate.")

if account_col != "account_id":
    mandate.rename(columns={account_col: "account_id"}, inplace=True)

validate_required_columns(mandate, ["account_id", "credttm", "colltnamt"], "Mandate")

mandate = enforce_types_mandate(mandate)
mandate.dropna(subset=["account_id", "credttm", "colltnamt"], inplace=True)

if "transactionid" in mandate.columns:
    mandate.drop_duplicates(subset=["transactionid"], inplace=True)

mandate.sort_values(["account_id", "credttm"], inplace=True)
mandate.reset_index(drop=True, inplace=True)

print("Mandate rows loaded:", len(mandate))


# --------------------------------------------
# Load FD Dataset
# --------------------------------------------

print("\nLoading FD dataset...")

header_row = detect_fd_header(fd_path)
fd = pd.read_excel(fd_path, header=header_row)
fd = standardize_columns(fd)

print("Available FD columns:", fd.columns.tolist())

possible_fd_account_cols = [
    "account_id",
    "linked_fino_a_c_no",
    "linked_fino_account"
]

fd_account_col = next((c for c in possible_fd_account_cols if c in fd.columns), None)

if fd_account_col is None:
    raise ValueError("No account identifier column found in FD data.")

if fd_account_col != "account_id":
    fd.rename(columns={fd_account_col: "account_id"}, inplace=True)

validate_required_columns(fd, ["account_id", "fd_amount"], "FD")

fd = enforce_types_fd(fd)
fd.drop_duplicates(inplace=True)
fd.sort_values("account_id", inplace=True)
fd.reset_index(drop=True, inplace=True)

print("FD rows loaded:", len(fd))


# --------------------------------------------
# Data Quality Report
# --------------------------------------------

print("\nGenerating Data Quality Report...")

login_report = generate_quality_report(login, "login")
mandate_report = generate_quality_report(mandate, "mandate")
fd_report = generate_quality_report(fd, "fd")

quality_report = pd.concat(
    [login_report, mandate_report, fd_report],
    ignore_index=True
)

quality_report["generated_at"] = datetime.now()

quality_report.to_csv(
    os.path.join(OUTPUT_PATH, "data_quality_report.csv"),
    index=False
)

print("Data quality report saved.")


# --------------------------------------------
# Save Cleaned Outputs
# --------------------------------------------

login.to_csv(os.path.join(OUTPUT_PATH, "login_clean.csv"), index=False)
mandate.to_csv(os.path.join(OUTPUT_PATH, "mandate_clean.csv"), index=False)
fd.to_csv(os.path.join(OUTPUT_PATH, "fd_clean.csv"), index=False)

print("\nIngestion Completed Successfully.\n")