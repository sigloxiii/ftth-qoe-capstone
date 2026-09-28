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
**Source:** FCC MBA units inventory + your filter `technology == FIBER`  
**Role:** Defines population BEFORE any measurement is read. v1 skipped this.

| Column | Type | Example | Description | Key for v2? |
| :--- | :--- | :--- | :--- | :--- |
| `unit_id` | int | 10231 | **PK.** SamKnows Whitebox ID. **Sequential, NOT random.** Low IDs = enrolled 2012-2014, High IDs = 2020+. This is the root cause of bias. | YES - Stratification key |
| `technology` | string | FIBER | Access technology: FIBER, CABLE, DSL. v2 filters `== FIBER` only. | YES - Filter |
| `isp` | int/string | 4 | Anonymized ISP ID. FCC masks real names. Used for stratified sampling to avoid ISP bias. | YES - Stratification |
| `advertised_down` | int | 300 | Advertised download tier in Mbps (50, 100, 300, 1000). Different tiers have different P95 baselines. | YES - Stratification |
| `enrollment_date` | date | 2019-03-15 | **Date Whitebox activated.** Encodes hardware generation. <2018-01-01 = Whitebox v1-v7 (Intel Puma, CPU bottleneck). >=2018 = WB8+ (valid for FTTH). **Critical confounding variable missed in v1.** | YES - Exclusion + Audit |
| `hardware_version` | string | SK-WB8 | SamKnows hardware: SK-WB8, SK-WB8v2, SK-WB7 (legacy). WB7 and lower have known UDP latency inflation >80ms due to CPE CPU, not last-mile. | YES - Exclusion |
| `state` / `region` | string | CA | Optional: US state. Can be used for geo stratification if needed. | NO - Optional |

**v1 Failure:** v1 read `curr_webget.csv` first, never checked `enrollment_date`. `head(1000)` took unit_id 1-1000, which are all 2012-2015 legacy hardware. P95 was inflated by CPE, not fiber.

**v2 Rule:** `enrollment_date >= '2018-01-01'` AND `hardware_version LIKE 'SK-WB8%'`

---

### 2. sampling_manifest.csv - Reproducibility Core (Audit Evidence)

**File:** `data/methodology_v2_CORRECTED/sampling_manifest.csv`  
**Granularity:** 1 row = 1 FTTH modern unit included in v2  
**Expected rows:** ~285  
**Generation:** `python/corrected_ingest.py`

| Column | Type | Example | Description |
| :--- | :--- | :--- | :--- |
| `unit_id` | int | 45218 | FK to fiber_units.csv. Only units that passed filter. |
| `enrollment_date` | date | 2020-06-12 | Copied from fiber_units. Proof no legacy <2018 included. |
| `isp` | string | 4 | For stratified sampling verification |
| `technology` | string | FIBER | Always FIBER |
| `advertised_down` | int | 300 | For tier analysis |
| `hardware_version` | string | SK-WB8v2 | Proof modern hardware |
| `seed` | int | 42 | Random state used for any sampling. Must be constant. |
| `inclusion_flag` | bool | TRUE | TRUE = included. File `excluded_legacy_units.csv` holds FALSE ones (52 units). |
| `stratification_group` | string | ISP_4_300Mbps | Concatenated `isp + speed` for balanced sampling. |

**Why this file exists:** Google Track B requires you to prove how you sampled. Without this, your 285 units look arbitrary. With seed=42, anyone can reproduce exactly.

**Validation SQL:**
```sql
-- Must return 0 rows
SELECT COUNT(*) FROM sampling_manifest WHERE enrollment_date < '2018-01-01';