

import pandas as pd
import numpy as np
import os

from sklearn.ensemble import IsolationForest

print("\nStarting Anomaly Model...\n")

# --------------------------------------------
# Paths
# --------------------------------------------

BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_PATH = os.path.join(BASE_PATH, "outputs")

feature_path = os.path.join(
    OUTPUT_PATH,
    "fraud_feature_dataset_v2.csv"
)

df = pd.read_csv(feature_path, low_memory=False)

print("Dataset loaded.\n")


# --------------------------------------------
# Select features for model
# --------------------------------------------

feature_cols = [
    "colltnamt",
    "amount_zscore",
    "txn_count_24h_prev",
    "txn_count_7d_prev",
    "device_consistency_score",
    "ip_consistency_score",
    "total_fd_amount"
]

existing_cols = [c for c in feature_cols if c in df.columns]

X = df[existing_cols].copy()

X = X.fillna(0)


print("Features used:", existing_cols)


# --------------------------------------------
# Train Isolation Forest
# --------------------------------------------

model = IsolationForest(
    n_estimators=100,
    contamination=0.05,
    random_state=42
)

model.fit(X)

scores = model.decision_function(X)
preds = model.predict(X)


# --------------------------------------------
# Save results
# --------------------------------------------

df["anomaly_score"] = scores
df["anomaly_flag"] = np.where(preds == -1, 1, 0)

output_path = os.path.join(
    OUTPUT_PATH,
    "anomaly_scores.csv"
)

df.to_csv(output_path, index=False)

print("anomaly_scores.csv saved.")
print("\nAnomaly model completed.\n")