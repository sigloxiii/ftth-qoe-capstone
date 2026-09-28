# FTTH QoE Risk & Support Cost Optimization
> **From Network Telemetry to Churn Prevention and OPEX Reduction — Methodology v2.0 (Bias-Corrected)**

[[License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[[Data Source: FCC MBA](https://img.shields.io/badge/Data-FCC%20MBA%202023--2024-blue)](https://www.fcc.gov/general/measuring-broadband-america)
[[Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://www.python.org)
[[Status](https://img.shields.io/badge/Status-v2.0%20Corrected-green)](./docs/postmortem_convenience_biasv1.md)

**September 2026 - Eng. Rafael Cansigno Peláez**
**Project Type:** Google Data Analytics Capstone | Track B (Self-directed)

---

### ⚠️ Methodological Reconstruction Note - Why was this project rebuilt?

> **This repository was fully rebuilt on September 27, 2026.**

**Critical Finding (v1 FAILED):** The initial methodology used `df.head(1000)` / `nrows=1000` when reading monthly FCC MBA CSVs.

We discovered this creates a **severe convenience bias**: the first 1000 records in the sorted files systematically correspond to `unit_id` with `enrollment_date` between 2012-2016. These are SamKnows v1 Whiteboxes, with obsolete hardware and legacy plans <100 Mbps.

**Impact:** The `risk_flag` calculated in v1 did not measure real FTTH degradation during peak hours, it measured CPE obsolescence. It overestimated risk by ~3.2x and invalidated the truck roll savings model.

**Corrective Action:** All v1 code was preserved intact in `/data/methodology_v1_FAILED/` as audit evidence. This v2.0 implements stratified probabilistic sampling. See full analysis in [`docs/05_postmortem_convenience_bias.md`](./docs/05_postmortem_convenience_bias.md).

This correction is a core part of the **Prepare & Process** phases of the Google framework.

---

### 🌐 Overview

FTTH operators face silent churn due to unmonitored degradation during peak hours (19:00-23:00) and high OPEX from unnecessary technician dispatches (truck rolls: $120-$150 USD).

**v2 Objective:** Quantify real subscriber risk using a robust technical proxy and model operational savings, shifting from reactive to proactive NOC, with a representative sample of the current FTTH fleet.

### 🎯 Business Task

Quantify `risk_flag` in modern FTTH (2023-2024) and model:
`Potential Savings = At-Risk Customers * Retention Rate * Truck Roll Cost`

### 🛠️ Tech Stack

- **Data Processing:** Python (Pandas, NumPy), SQL (P95 with PERCENTILE_CONT)
- **Methodology:** Stratified Sampling, Temporal Bias Control
- **Viz:** Tableau Public
- **Domain:** FTTH/GPON, QoS/QoE, SLA Compliance

### 📊 Dataset - FCC MBA 2023-2024

- **Source:** FCC Measuring Broadband America
- **Scope:** `technology = FIBER` - 285 unique units (full population, not row sample)
- **v2 Correction:**
    - Sampling unit = full `unit_id`, not row.
    - Sampling = Stratified by ISP + Speed Tier + Enrollment Year.
    - Temporal = `sample(frac=0.1, random_state=42)` within peak, never `head()`.
    - Reproducibility = `data/methodology_v2_CORRECTED/sampling_manifest.csv` with seed=42.

Raw CSVs >2.5GB/month excluded. See `data/README.md` for reproduction steps.

### 🔄 Google Data Analytics Methodology v2.0

| Phase | v1 (Failed) | v2 (Corrected) - Current |
| :--- | :--- | :--- |
| **1. Ask** | `risk_flag = (P95>80ms) OR (Loss>1.5% peak)` | **Same proxy, but adding control:** Report `risk_flag` separated by equipment age cohort. |
| **2. Prepare** | `pd.read_csv(..., nrows=1000)` | **Fix:** Ingest full inventory `units.csv`. Filter `tech=FIBER`. Validate `enrollment_date`. Probabilistic sampling of units. |
| **3. Process** | P95 over 1000 old rows | **Fix:** P95 per `unit_id` per month `PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY rtt)`. Peak window 19-23 local. Handle packet loss nulls. Log age distribution. |
| **4. Analyze** | Inflated risk | **Fix:** v1 vs v2 comparison. Real degradation clustering. ROI with conservative retention rate (15-25%). |
| **5. Share** | Biased dashboard | **Fix:** Dashboard with filter `Excluding legacy whiteboxes <2018` and bias audit page. |
| **6. Act** | NOC alert | **Fix:** Remote triage workflow + protocol to discard obsolete CPE before truck roll. |

### 📁 Repository Structure v2.0
```text
├── README.md
├── README_ES.md
├── data/
│   ├── methodology_v1_FAILED/      # EVIDENCE - Original biased code
│   │   └── README.md
│   └── methodology_v2_CORRECTED/
│       ├── sampling_manifest.csv   # 285 unit_id + seed=42
│       └── data_dictionary.md
├── notebooks/
│   ├── 01_ingest_v2_corrected.ipynb
│   ├── 02_process_p95_v2.ipynb
│   └── 03_analyze_risk_v2.ipynb
├── sql/
│   ├── p95_per_unit_corrected.sql
│   └── enrollment_age_audit.sql
├── docs/
│   ├── 04_methodology_v2.md
│   ├── 05_postmortem_convenience_bias.md  # MAIN FINDING
│   └── evidence/
│       ├── dist_enrollment_v1_vs_v2.png
│       └── p95_comparison.png
├── dashboards/
│   └── FTTH_QoE_v2.twbx
└── python/
    └── corrected_ingest.py
```