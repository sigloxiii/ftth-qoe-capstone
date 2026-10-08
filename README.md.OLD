# FTTH QoE Risk & Support Cost Optimization

> **From Network Telemetry to Churn Prevention and OPEX Reduction — Methodology v2.1.3 FINAL (Hardware-Corrected)**

[[License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) [[Data Source: FCC MBA](https://img.shields.io/badge/Data-FCC%20MBA%202023--2024-blue)](https://www.fcc.gov/general/measuring-broadband-america) [[Status](https://img.shields.io/badge/Status-v2.1.3%20FINAL-green)](https://github.com/sigloxiii/ftth-qoe-risk-optimization)

**September-October 2026 - Eng. Rafael Cansigno Peláez** | **Google Data Analytics Capstone - Track B (Self-directed)**

---

## Project Overview

This Capstone turns FCC Measuring Broadband America telemetry into actionable decisions for FTTH operators: which units are at real risk of poor QoE and which truck rolls can be avoided.

**Problem:** Raw measurements mix true fiber degradation with false latency/loss created by legacy Whiteboxes that cannot forward at line rate.

**Solution v2.1.3:** Hardware filtering in Excel + peak-hour analysis (19-23h local time) + FCC-aligned QoE thresholds for latency, jitter and loss.

**Final Output:** `data/methodology_v2/ftth_final_258_v2_1.csv` - 257 units, 17 at risk (6.6%), ready for PowerBI.

**Business Impact:** v1 overestimated risk by 3.2x. v2.1 avoids ~37 false truck rolls = ~$6,660 OPEX saved.

---

### Methodological Reconstruction Note

> **Rebuilt September 27 - October 1, 2026. v2.1.3 is definitive.**

**v1 FAILED - Convenience Bias:** Reading FCC monthly files with only the first 1000 rows captured legacy 2012-2016 enrollments.

**v2 REFINED - Instrument Bias:** `fiber_units.csv` is historically ordered. Legacy Whiteboxes with low CPU and FastEthernet ports saturate during tests.

**v2.1 Solution - Hardware Filter in Excel:** Filtering done in Excel from `unit-profile-sept2022.xlsx`, evidenced in `docs/evidence/filtrado_fiber_units.png`. Only gigabit-capable models retained.

| Mode | Effect |
| :--- | :--- |
| v1 Convenience Bias | Captured obsolete CPE |
| v2 Hardware Bottleneck | False latency/loss |
| **v2.1 Excel Filter** | **Real FTTH QoE** |

v2.1 reduces from 285 to 258 valid units. 27 legacy units excluded as audit trail. Final export 257 units (1 without peak measurements). v1 code preserved in `/data/methodology_v1_FAILED/`.

---

### Hardware Selection Logic

**Core Principle:** The Whitebox is the measurement instrument. If it cannot forward at line rate, it creates the degradation.

Audit of `fiber_units.csv` (285 units) - 30/09/2026:

| Model | Count | Real HW Cap | Status |
| :--- | :--- | :--- | :--- |
| **skwb8** | 227 | >900 Mbps | INCLUDE - Gold standard, quad-core, HW NAT |
| **skwb8p** | 3 | >1000 Mbps | INCLUDE - 2.5GbE |
| **ac1750v2** | 28 | ~550 Mbps | INCLUDE - HW NAT, 1.1x margin at 500 Mbps |
| wnr3500l-high | 17 | <95 Mbps | EXCLUDE - 480MHz CPU 2009 |
| wdr3600 | 6 | ~180 Mbps | EXCLUDE - No HW NAT |
| wr1043nd/wr741nd | 4 | 100 Mbps FE | EXCLUDE - FastEthernet |

**Total Valid: 258 (90.5%) | Excluded: 27 (9.5%)**

Filtering done in Excel. Full deep dive in `docs/hardware_audit.md`.

**Rule v2.1:** Include only `skwb8`, `skwb8p`, `ac1750v2` with capacity >= provisioned speed * 1.1.

---

### QoE Parameters

**Source:** FCC MBA validated Sept 2022. Analysis focused on peak congestion window 19-23h local time, with timezone correction from UTC to local (DST offsets).

**Metrics Calculated (per unit_id):**
- **p95_latency_ms:** P95 latency in peak hours. Raw `rtt_avg` in microseconds → ms.
- **p95_jitter_ms:** P95 jitter avg up/down in peak hours. Raw `jitter_up/down` in microseconds → ms.
- **avg_loss_pct:** Mean packet loss in peak hours. Derived from `failures / (successes+failures) * 100`.

**FCC + ITU-T Thresholds (ITU-T G.114 / Y.1541, FCC 13th Report 2023):**
- **Latency:** Fiber median 12-15ms, P95 18-22ms. Gaming preferred <20ms. **Risk if >20ms.**
- **Jitter:** Degraded Zoom/Teams if **>15ms**.
- **Loss:** Degraded if **>1%**.

**Risk Flag v2.1.3 FINAL:**
> For Capstone Project 1, risk_flag = 1 if p95_latency_ms > 20.0 else 0
> Jitter >15ms and Loss >1% thresholds are documented for v2.2 evolution. Full mathematical procedure in `docs/procedimiento_matematico_v2_1_3.md`.

**Final Dataset:** `data/methodology_v2/ftth_final_258_v2_1.csv`
- 257 rows, 5 columns: unit_id, p95_latency_ms, p95_jitter_ms, avg_loss_pct, risk_flag
- 17 at risk (6.6%), mean latency 12.47ms, mean jitter 1.10ms
- Sorted descending by latency, UTF-8

---

### Repository Structure

```
/
├── data/
│   ├── fiber_units.csv (258 valid filtered in Excel)
│   ├── methodology_v2/
│   │   └── ftth_final_258_v2_1.csv (final 257 rows, 17 risk)
│   ├── methodology_v1_FAILED/
│   └── raw/ (gitignored, 6.8GB FCC)
├── docs/
│   ├── evidence/filtrado_fiber_units.png
│   ├── hardware_audit.md
│   ├── procedimiento_matematico_v2_1_3.md (full math)
│   ├── data_dictionary.md
│   └── powerbi_model.md
├── README.md (this intro)
└── LICENSE
```

Detailed technical docs in `docs/` folder. This README is introduction only.

---

### PowerBI Next Steps

- Enrich final CSV with model/isp/speed from fiber_units.csv
- Dashboards: QoE Risk (6.6%), Hardware Audit, Cost Optimization
- See `docs/powerbi_model.md` for DAX measures

**Status:** ✅ v2.1.3 FINAL - Ready for PowerBI
