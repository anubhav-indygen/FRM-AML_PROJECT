
import pandas as pd
import os

print("\nStarting Identity Resolution...\n")

# --------------------------------------------
# Paths
# --------------------------------------------

BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_PATH = os.path.join(BASE_PATH, "outputs")

login_path = os.path.join(OUTPUT_PATH, "login_clean.csv")
mandate_path = os.path.join(OUTPUT_PATH, "mandate_clean.csv")
fd_path = os.path.join(OUTPUT_PATH, "fd_clean.csv")

# --------------------------------------------
# Load Cleaned Datasets
# --------------------------------------------

login = pd.read_csv(login_path, low_memory=False)
mandate = pd.read_csv(mandate_path, low_memory=False)
fd = pd.read_csv(fd_path, low_memory=False)

print("Datasets loaded.\n")

# --------------------------------------------
# Extract Identifiers
# --------------------------------------------

login_ids = pd.DataFrame()

if "usr_id" in login.columns:
    login_ids = login[["usr_id"]].drop_duplicates()

mandate_ids = pd.DataFrame()

if "account_id" in mandate.columns:
    mandate_ids = mandate[["account_id"]].drop_duplicates()

fd_ids = pd.DataFrame()

fd_account_col = None
fd_cif_col = None

if "linked_fino_a_c_no" in fd.columns:
    fd_account_col = "linked_fino_a_c_no"

if "linked_fino_a_c_cif" in fd.columns:
    fd_cif_col = "linked_fino_a_c_cif"

if fd_account_col:
    cols = [fd_account_col]

    if fd_cif_col:
        cols.append(fd_cif_col)

    fd_ids = fd[cols].drop_duplicates()

print("Identifiers extracted.\n")

# --------------------------------------------
# Build Identity Mapping Table
# --------------------------------------------

identity_map = pd.DataFrame()

if not mandate_ids.empty:

    identity_map = mandate_ids.copy()

    identity_map["canonical_customer_id"] = (
        "CUST_" + identity_map.index.astype(str).str.zfill(6)
    )

    identity_map["confidence"] = "HIGH"

else:

    identity_map = pd.DataFrame({
        "canonical_customer_id": ["CUST_000000"]
    })

print("Base identity map created.\n")

# --------------------------------------------
# Merge FD Accounts
# --------------------------------------------

if not fd_ids.empty and fd_account_col:

    fd_ids = fd_ids.rename(columns={
        fd_account_col: "account_id"
    })

    identity_map = identity_map.merge(
        fd_ids,
        on="account_id",
        how="left"
    )

print("FD accounts merged.\n")

# --------------------------------------------
# Attach Login Users
# --------------------------------------------

if not login_ids.empty:

    login_ids = login_ids.reset_index(drop=True)

    login_ids["canonical_customer_id"] = (
        "CUST_" + login_ids.index.astype(str).str.zfill(6)
    )

    identity_map = identity_map.merge(
        login_ids,
        on="canonical_customer_id",
        how="left"
    )

print("Login users merged.\n")

# --------------------------------------------
# Final Cleanup
# --------------------------------------------

identity_map.fillna("UNKNOWN", inplace=True)

final_columns = [
    "canonical_customer_id",
    "usr_id",
    "account_id",
    "linked_fino_a_c_cif",
    "confidence"
]

existing_columns = [c for c in final_columns if c in identity_map.columns]

identity_map = identity_map[existing_columns]

identity_map = identity_map.drop_duplicates()

# --------------------------------------------
# Save Identity Map
# --------------------------------------------

output_path = os.path.join(
    OUTPUT_PATH,
    "customer_identity_map.csv"
)

identity_map.to_csv(output_path, index=False)

print("Identity map saved as 'customer_identity_map.csv'")
print("\nIdentity Resolution Completed Successfully.\n")