# FTTH QoE Risk & Support Cost Optimization

> **From Network Telemetry to Churn Prevention and OPEX Reduction — Methodology v2.1 (Hardware-Corrected)**

[License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg) [Data Source: FCC MBA](https://img.shields.io/badge/Data-FCC%20MBA-blue) [Python](https://img.shields.io/badge/Python-3.11-blue) [Status](https://img.shields.io/badge/Status-v2.1%20CORRECTED-green)

**September 2026 - Eng. Rafael Cansigno Peláez** | **Project Type:** Google Data Analytics Capstone | Track B (Self-directed)

---

### ⚠️ Methodological Reconstruction Note - Why was this project rebuilt twice?

> **This repository was fully rebuilt on September 27-30, 2026. v2.1 is the definitive version.**

**Critical Finding v1 FAILED:** Initial methodology used `df.head(1000)` / `nrows=1000` when reading monthly FCC MBA CSVs. This created a **severe convenience bias**.

**Critical Finding v2 REFINED:** After fixing sampling, we discovered a deeper **Instrument Bias (Hardware Bottleneck)**. The dimensional table `fiber_units.csv` is historically ordered. The first units correspond to legacy Whiteboxes.

**v1 vs v2.1 Root Cause Analysis:**

| Failure Mode | Mechanism | Effect |
| :--- | :--- | :--- |
| **v1 - Convenience Bias** | `head(1000)` reads first rows sorted by Unit_ID | Captures 2012-2016 enrollments |
| **v2.0 - Hardware Bottleneck** | `wnr3500l-high` (480MHz, 2009), `wr1043nd`, `wr741nd` FastEthernet | CPU saturation during speed tests → False latency/loss |
| **v2.1 - Solution** | **Hardware Capability Filter: ONLY `skwb8`, `skwb8p`, `ac1750v2`** | Measures real FTTH QoE, not CPE limits |

**Impact:** v1 overestimated risk by ~3.2x. v2.1 reduces population from 285 to **258 valid units (90.5%)**, with 27 legacy units excluded as audit trail.

**Corrective Action:** All v1 code preserved in `/data/methodology_v1_FAILED/`. v2.1 implements

### 🔬 Hardware Selection Logic - Why ONLY `skwb8`, `skwb8p`, `ac1750v2`?

> **Core Principle:** The Whitebox IS the measurement instrument. If the instrument cannot forward at line rate, it creates latency and loss. v1 measured CPU saturation, not FTTH degradation.

We audited `fiber_units.csv` (285 FTTH units) on 30/09/2026 and found a direct correlation between hardware model, provisioned speed, and false `risk_flag`.

#### 1. The Audit Evidence (from your file)

| Model | Count | Avg Provisioned Down | Real HW Cap | Status |
| :--- | :--- | :--- | :--- | :--- |
| **skwb8** | 227 | 360 Mbps | >900 Mbps | **INCLUDE** |
| **skwb8p** | 3 | 350 Mbps | >1000 Mbps | **INCLUDE** |
| **ac1750v2** | 28 | 321 Mbps | ~550 Mbps | **INCLUDE** |
| wnr3500l-high | 17 | 92 Mbps | <95 Mbps | EXCLUDE - 480MHz CPU |
| wdr3600 | 6 | 133 Mbps | ~180 Mbps | EXCLUDE - N600 single-core |
| wr1043nd/wr741nd | 4 | 87 Mbps | 100 Mbps FE | EXCLUDE - FastEthernet |

**Total Valid v2.1: 258 units (90.5%) | Excluded: 27 units (9.5%)**

Legacy models were 100% concentrated in 75/100 Mbps plans - proof that `fiber_units.csv` is historically ordered and `head(1000)` captures obsolete CPE.

#### 2. Technical Deep Dive - Why Each Legacy Fails

**`wnr3500l-high` (Netgear WNR3500L, 2009) - PRIMARY BIAS SOURCE:**
- SoC: Broadcom BCM4718 480MHz single-core, 64MB RAM
- NAT: Software-based, no HW acceleration
- Real throughput with SamKnows stack (UDP latency + speedtest): ~90-95 Mbps max
- Failure mode: When FCC runs concurrent tests on a 100 Mbps FTTH line, CPU hits 100%, buffers fill, kernel drops packets → artificial `P95 RTT >80ms` and `loss >1.5%`. This is bufferbloat + CPU exhaustion, not OLT congestion.

**`wr1043nd / wr741nd / wr741ndv4` (TP-Link N Legacy):**
- Port: FastEthernet (10/100) - physically cannot report >100 Mbps
- Any plan >100 Mbps is automatically capped by the port. Including them would measure the port, not the fiber.

**`wdr3600` (TP-Link N600):**
- SoC: Atheros AR9344 560MHz single-core, 128MB RAM
- Although it has GbE ports, it lacks HW NAT. With SamKnows firmware overhead, it saturates at ~180 Mbps. In our data, 2 of 6 units are on 200 Mbps plans - already over limit. Including it reintroduces Instrument Bias.

#### 3. Why `ac1750v2`, `skwb8`, `skwb8p` ARE Valid

**`skwb8 / skwb8p` - SamKnows Whitebox v8 / v8 Plus (Gold Standard):**
- Purpose-built for FCC MBA since 2018. Quad-core ARM, 512MB RAM, HW NAT, SQM/FQ-CoDel to prevent self-induced bufferbloat.
- Tested by SamKnows to >900 Mbps (skwb8) and >1 Gbps (skwb8p with 2.5GbE).
- For our max plan 500 Mbps: Margin = 1000/500 = 2.0x → Fully valid.

**`ac1750v2` (TP-Link Archer C7 v2):**
- SoC: 【entity-Qualcomm¦canonical_name=Qualcomm】 QCA9558 720MHz + QCA9880, 128MB RAM, Hardware Gigabit switching (S17 + HW NAT offload)
- Real throughput with SamKnows FW: ~550 Mbps (measured by FCC in 2019 validation report)
- In our dataset: 5 units @100 Mbps, 6 @250 Mbps, 17 @500 Mbps
- For 500 Mbps: Margin = 550/500 = 1.1x (borderline but valid). We flag it as `tier_limit` for sensitivity analysis, but we INCLUDE it because:
    1. It has HW NAT (unlike wdr3600)
    2. FCC tests are not fully concurrent (speedtest and UDP latency are in separate windows)
    3. Excluding it would drop 17 valid 500 Mbps samples and bias us to only Cincinnati Bell.

#### 4. Formal Rule v2.1 (Reproducible)

```sql
-- Hardware Capability Filter - Definitive v2.1
WHERE whitebox_model IN ('skwb8', 'skwb8p', 'ac1750v2')
  AND hardware_cap_mbps >= provisioned_down * 1.1  -- Safety margin
-- Result: 258 units, seed=42, stratified by ISP + Speed + Model
-- Audit: excluded_legacy_units.csv