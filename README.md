# FRM & AML System

## Overview

This project implements a **production-style Fraud Risk Management (FRM) and Anti-Money Laundering (AML) system** designed with a **false-positive-first approach**.

The system ingests raw financial datasets, performs identity resolution, engineers behavioral features, detects anomalies, applies rule-based scoring with suppressors, and generates **explainable fraud alerts**. It further includes **shadow-mode evaluation, threshold tuning, and automated production configuration**.

---

## Objectives

* Minimize false positives (analyst noise)
* Generate explainable fraud alerts
* Enable feedback-driven improvement
* Simulate real-world FRM system architecture

---

## System Architecture

```
Raw Data
   ↓
Ingestion Layer
   ↓
Identity Resolution
   ↓
Feature Engineering (v1 + v2)
   ↓
Anomaly Detection (Isolation Forest)
   ↓
Rule-Based Alert Engine
   ↓
Suppressor Logic (False-Positive Reduction)
   ↓
Feedback Loop (Labeling)
   ↓
Shadow Run & Threshold Tuning
   ↓
Production Alert Generation
```

---

## Project Structure

```
frm_aml_project/
│
├── app.py                         # Streamlit UI
├── data/                          # Input datasets
├── outputs/                       # Generated outputs
│
├── src/
│   ├── ingestion.py
│   ├── identity_resolution.py
│   ├── feature_engineering.py
│   ├── feature_engineering_v2.py
│   ├── anomaly_model.py
│   ├── alert_engine.py
│   ├── alert_feedback.py
│   ├── shadow_run.py
│   ├── threshold_experiments.py
│   ├── precision_estimator.py
│   ├── auto_threshold_selector.py
│   └── production_config_loader.py
│
└── venv/
```

---

## Input Data

The system expects three datasets:

### 1. Login Dataset

* `usr_id`, device info, IP, timestamps

### 2. Transaction (Mandate) Dataset

* `account_id`, `credttm`, `colltnamt`

### 3. FD / Customer Dataset

* `linked_fino_a_c_no`, `fd_amount`, `cif`

---

## Output

### Final Output

```
outputs/alerts_production.csv
```

Contains:

* `account_id`
* `risk_score`
* `risk_level` (HIGH / MEDIUM / LOW)
* `action` (BLOCK / REVIEW / ALLOW)

---

## How It Works

### 1. Ingestion

* Cleans data, standardizes schema
* Detects FD headers dynamically
* Generates data quality reports

### 2. Identity Resolution

* Maps `usr_id`, `account_id`, and `cif`
* Creates `canonical_customer_id`

### 3. Feature Engineering

* Transaction features (time, velocity)
* Behavioral features (device, login)
* Financial features (FD profile)
* Regulatory flags

### 4. Advanced Features (v2)

* Rolling windows (no data leakage)
* Cold-start detection
* Suppressor features:

  * Device consistency
  * IP consistency
  * Recurring patterns
  * Strong authentication

### 5. Anomaly Detection

* Isolation Forest (unsupervised)
* Detects behavioral deviations

### 6. Alert Engine

* Weighted rule-based scoring
* Suppressor-based risk reduction

### 7. Risk Score Formula

```
risk_score =
    (3 × high_value)
  + (3 × rapid_repeat)
  + (2 × dormant)
  + (3 × amount_spike)
  + (2 × velocity)
  − suppressors
```

### 8. Risk Classification

| Score              | Risk Level |
| ------------------ | ---------- |
| ≥ HIGH_THRESHOLD   | HIGH       |
| ≥ MEDIUM_THRESHOLD | MEDIUM     |
| < MEDIUM_THRESHOLD | LOW        |

---

## Feedback Loop

* Stores analyst decisions in `alert_outcomes.csv`
* Enables future supervised learning

---

## Shadow Mode & Threshold Tuning

* Runs system without impacting users
* Evaluates:

  * Alert rate
  * Analyst workload
  * Noise score

Outputs:

* `shadow_summary.csv`
* `threshold_results.csv`
* `precision_estimate.csv`

---

## ⚡ Auto Threshold Selection

Automatically selects optimal thresholds:

```
outputs/best_threshold.json
```

Based on:

* Lowest noise score
* Reduced false positives

---

## Production Run

Final alerts generated using tuned thresholds:

```
outputs/alerts_production.csv
```

---

## Running the Project

### 1. Activate Environment

```
source venv/bin/activate
```

### 2. Run Streamlit App

```
streamlit run app.py
```

### 3. Upload Datasets and Click "Run Analysis"

---

## Techniques Used

* Data Preprocessing & Schema Normalization
* Identity Resolution (Entity Matching)
* Feature Engineering (Behavioral + Financial)
* Rolling Window Analysis
* Unsupervised Learning (Isolation Forest)
* Rule-Based Risk Scoring
* False Positive Suppression
* Threshold Optimization
* Precision-First Tuning

---

## Key Features

✔ False-positive-first design
✔ Explainable alerts
✔ Hybrid (rules + ML) system
✔ Feedback-driven improvement
✔ Shadow deployment simulation
✔ Production-ready pipeline

---

## Limitations

* Requires predefined schema (not schema-agnostic)
* Batch processing (not real-time)
* No UI dashboard beyond Streamlit

---

## Future Improvements

* Real-time streaming pipeline
* ML-based supervised fraud classifier
* API deployment (FastAPI)
* Dashboard (React / Plotly)
* Auto schema detection

---

## Conclusion

This project simulates a **real-world fraud detection system** used in banking and fintech, combining:

* Data engineering
* Machine learning
* Rule-based systems
* Risk optimization

It goes beyond traditional ML projects by implementing a **complete FRM pipeline**.

---

## Author

Anubhav Sharda

---

