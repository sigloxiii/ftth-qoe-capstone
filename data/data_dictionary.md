# Data Dictionary - Methodology v2.0 CORRECTED

> **Location:** `data/methodology_v2_CORRECTED/`  
> **Primary Files:** `fiber_units.csv`, `sampling_manifest.csv`, `ftth_clean_for_sql.csv`, `curr_udplatency.csv`  
> **Seed:** 42 (all random operations)  
> **Author:** Eng. Rafael Cansigno Peláez

This document defines every field used in v2.0. It corrects the critical omission of v1: `unit_id` is sequential by enrollment_date, not random. This caused convenience bias when using `head(1000)`.

---

### 1. fiber_units.csv - Population Inventory (Source of Truth)

**File:** `data/fiber_units.csv` (5MB, committed)  
**Granularity:** 1 row = 1 SamKnows Whitebox = 1 subscriber home  
**Role:** Defines population BEFORE any measurement is read. v1 skipped this.

| Column | Type | Example | Description | Key for v2? |
| :--- | :--- | :--- | :--- | :--- |
| `unit_id` | int | 10231 | **PK.** Whitebox ID. **Sequential, NOT random.** Low IDs = 2012-2014, High IDs = 2020+. Root cause of bias. | YES |
| `technology` | string | FIBER | FIBER, CABLE, DSL. v2 filters `== FIBER` only. | YES |
| `isp` | int/string | 4 | Anonymized ISP ID. Stratification variable. | YES |
| `advertised_down` | int | 300 | Mbps tier (50, 100, 300, 1000). Different P95 baseline. | YES |
| `enrollment_date` | date | 2019-03-15 | **Date Whitebox activated.** <2018-01-01 = Whitebox v1-v7 (CPU bottleneck). >=2018 = WB8+ (valid). **Confounding var missed in v1.** | YES |
| `hardware_version` | string | SK-WB8 | SK-WB8, SK-WB8v2, SK-WB7 legacy. WB7 inflates P95 >80ms falsely. | YES |

**v2 Rule:** `enrollment_date >= '2018-01-01'` AND `hardware_version LIKE 'SK-WB8%'`

### 2. sampling_manifest.csv - Reproducibility Core

**File:** `data/methodology_v2_CORRECTED/sampling_manifest.csv`  
**Rows:** ~285 | **Generation:** `python/corrected_ingest.py`

| Column | Type | Example | Description |
| :--- | :--- | :--- | :--- |
| `unit_id` | int | 45218 | FK, only modern units |
| `enrollment_date` | date | 2020-06-12 | Proof no legacy <2018 |
| `isp` | string | 4 | Stratification |
| `technology` | string | FIBER | Always FIBER |
| `advertised_down` | int | 300 | Tier |
| `hardware_version` | string | SK-WB8v2 | Modern HW proof |
| `seed` | int | 42 | Constant |
| `inclusion_flag` | bool | TRUE | TRUE included, FALSE goes to excluded_legacy_units.csv |
| `stratification_group` | string | ISP_4_300Mbps | isp+speed for balanced sampling |

**Validation:** `SELECT COUNT(*) FROM sampling_manifest WHERE enrollment_date < '2018-01-01'` must return 0.

### 3. curr_udplatency.csv - Primary Measurement (Raw, git-ignored)

**File:** `data/raw/validated-data-sept2022/curr_udplatency.csv` (122,828 KB)  
**Granularity:** 1 row = 1 UDP latency probe hourly per unit

| Column | Type | Example | Description |
| :--- | :--- | :--- | :--- |
| `unit_id` | int | 45218 | FK, must be in manifest |
| `dtime` | datetime | 2022-09-15 20:00:00 | UTC timestamp |
| `target` | string | 54.213.1.5 | FCC test server IP |
| `rtt` / `latency` | float | 18.5 | RTT ms - CORE metric for P95 |
| `success` | int | 1 | 1=success |

**Peak Filter (FCC):** 19:00-23:00 local time.

### 4. ftth_clean_for_sql.csv - Analysis-Ready (Input to SQL/Power BI)

**File:** `data/methodology_v2_CORRECTED/ftth_clean_for_sql.csv` (~8MB)  
**Granularity:** 1 row = 1 unit_id x peak window  
**Generation:** Filter `curr_udplatency.csv` by manifest + peak + P95

| Column | Type | Example | Description |
| :--- | :--- | :--- | :--- |
| `unit_id` | int | 45218 | PK |
| `month` | string | 2022-09 | Trend |
| `p95_rtt_peak_ms` | float | 28.4 | PRIMARY KPI - P95 RTT peak 19-23h |
| `avg_loss_peak_pct` | float | 0.2 | From curr_udpcloss.csv |
| `jitter_p95_ms` | float | 3.1 | From curr_udpjitter.csv |
| `total_measurements_peak` | int | 124 | Quality gate: must be >100 |
| `isp` | string | 4 | Slicer Power BI |
| `advertised_down` | int | 300 | Slicer |
| `risk_flag` | string | HIGH/MEDIUM/LOW | Derived in SQL: HIGH if p95>60ms or loss>1% |

**Quality Gate:** If `total_measurements_peak < 100`, set `p95 = NULL`.

### 5. excluded_legacy_units.csv - Audit Trail

**File:** `data/methodology_v2_CORRECTED/excluded_legacy_units.csv` | ~52 units <2018

| Column | Reason |
| :--- | :--- |
| `unit_id` | Legacy HW |
| `enrollment_date` | 2012-2017 |
| `exclusion_reason` | "Legacy whitebox <2018 - CPE CPU inflation, not last-mile" |

### 6. v1 vs v2 Summary

| Aspect | v1 (FAILED) | v2 (CORRECTED) |
| :--- | :--- | :--- |
| Population | head(1000) from curr_webget.csv | fiber_units.csv >=2018 |
| Metric | HTTP throughput | UDP latency P95 |
| Hardware | Mixed 2012-2022 | Only SK-WB8+ |
| Sampling | Convenience | Stratified random seed=42 |