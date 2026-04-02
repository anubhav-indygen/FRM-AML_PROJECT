# ============================================
# FRM + AML Auto Threshold Selector
# Precision-first selection
# ============================================

import pandas as pd
import json
import os

print("\nStarting Auto Threshold Selection...\n")

# --------------------------------------------
# Paths
# --------------------------------------------

BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_PATH = os.path.join(BASE_PATH, "outputs")

precision_path = os.path.join(
    OUTPUT_PATH,
    "precision_estimate.csv"
)

df = pd.read_csv(precision_path)

print("Precision table loaded.\n")


# --------------------------------------------
# Filter invalid configs
# --------------------------------------------

df = df[df["alerts"] > 0]

# prefer low alert rate
df = df.sort_values(
    by=["noise_score", "alert_rate"],
    ascending=True
)


best = df.iloc[0]

print("Best threshold found:")
print(best)


# --------------------------------------------
# Save best threshold
# --------------------------------------------

result = {
    "high_threshold": int(best["high_threshold"]),
    "medium_threshold": int(best["medium_threshold"]),
    "alert_rate": float(best["alert_rate"]),
    "noise_score": float(best["noise_score"])
}

output_path = os.path.join(
    OUTPUT_PATH,
    "best_threshold.json"
)

with open(output_path, "w") as f:
    json.dump(result, f, indent=4)

print("\nbest_threshold.json saved.")
print("\nAuto threshold selection completed.\n")