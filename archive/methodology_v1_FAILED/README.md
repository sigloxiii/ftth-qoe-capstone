# FTTH QoE Risk & Support Cost Optimization
> **From Network Telemetry to Churn Prevention and OPEX Reduction**

[![License: MIT](https://img.shields.io/badge/Code_License-MIT-yellow.svg)](LICENSE)
[![Data Source: FCC MBA](https://img.shields.io/badge/Data_Source-FCC_MBA_2023--2024-blue.svg)](https://www.fcc.gov/general/measuring-broadband-america)
[![Python](https://img.shields.io/badge/Python-3.10%2B-brightgreen.svg)](https://www.python.org/)
[![Tableau](https://img.shields.io/badge/Tableau-Public_Profile-orange.svg)](https://public.tableau.com/app/profile/rafael.cansigno/vizzes)

---
**September 2026 - Ing. Rafael Cansigno Peláez**

### 🌐 Overview
* **Project Type:** Google Data Analytics Capstone | **Track B (Self-directed Project)**
* **Author:** **Ing. Rafael Cansigno Peláez** *(Telecom Engineer | CCNA 2003 → Telecom Data Analyst 2026)*
* **Tableau Public:** [rafael.cansigno](https://public.tableau.com/app/profile/rafael.cansigno/vizzes)
* **Languages:** English | [Español](./README_ES.md)

---

### 🎯 Business Task
FTTH (Fiber to the Home) operators face silent subscriber churn caused by unmonitored service degradation during peak usage hours (19:00 - 23:00). Concurrently, unnecessary field technician dispatches (*truck rolls*) generate high OPEX ($120–$150 USD direct cost).

**Objective:** Quantify subscriber risk through a technical proxy (`risk_flag`) based on network telemetry and model operational savings to shift NOC operations from reactive to proactive.

---

### 🛠️ Tech Stack & Skills
* **Data Processing & Analysis:** Python (`Pandas`, `NumPy`), SQL, Excel
* **Data Visualization:** Tableau Public
* **Domain Knowledge:** FTTH / GPON, QoS/QoE Metrics, Time-Series, SLA Compliance

---

### 📊 Dataset Information
* **Source:** [FCC Measuring Broadband America (MBA) 2023-2024](https://www.fcc.gov/general/measuring-broadband-america)
* **Scope / Filter:** `technology = FIBER (FTTH)` - 285 units
* **Note on Raw Data:** Raw CSVs (>2.5 GB/month) are excluded. See [`/data/`](./data/) for reproduction instructions.

---

### 🔄 Google Data Analytics Methodology
| Phase | Description & Execution |
| :--- | :--- |
| **1. Ask** | Defined business rules and engineered the technical proxy: <br>$$\text{risk\_flag} = (\text{P95 Latency} > 80\text{ms}) \lor (\text{Packet Loss} > 1.5\%\text{ during peak hours})$$ |
| **2. Prepare** | Ingested multi-million time-series logs from the FCC MBA platform; filtered for FTTH units and normalized timestamps. |
| **3. Process** | Computed 95th percentile ($P_{95}$) RTT latency, handled missing packet counts, and flagged peak window (19:00 - 23:00). |
| **4. Analyze** | Evaluated degradation clusters and modeled financial ROI: <br>$$\text{Potential Savings} = \text{At-Risk Customers} \times \text{Expected Retention Rate} \times \text{Truck Roll Cost}$$ |
| **5. Share** | Designed interactive dashboards in **Tableau** tailoring views for Executives and NOC Engineers. |
| **6. Act** | Proposed automated alert protocols for NOC teams and a remote triage workflow. |

---

### 📁 Repository Structure
```bash
├── data/              # Data dictionary and reproduction steps
├── notebooks/         # 01_ingest, 02_process_p95, 03_analyze_risk
├── sql/               # Aggregation and P95 queries
├── dashboards/        # Tableau .twbx files and screenshots
├── docs/              # Detailed methodology and evidence
└── README.md
