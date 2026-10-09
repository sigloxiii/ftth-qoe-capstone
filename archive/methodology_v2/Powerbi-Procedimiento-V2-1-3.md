# PowerBI - FTTH QoE Risk v2.1.3 - Data Methodology & Model

**Dataset:** FCC Measuring Broadband America - Sept 2022 Validated
**Scope:** 285 FTTH units = 258 valid + 27 excluded = fiber_units.csv + excluded_legacy_ffth_units.csv
**Final Fact:** 257 units with peak measurements, 17 at risk (6.61%)
**Version:** v2.1.3 FINAL - Hardware-Corrected
**File Names:** Exact names as in repo screenshot (corrected)

---

## 1. Data Lineage - Exact File Names

### 1.1 Source Files (from screenshot)
- `unit-profile-sept2022.xlsx` / `unit-profile-sept2022.csv`: 2025 rows total (DSL 1139, Cable 601, Fiber 285). Columns: Unit ID, ISP, Technology, State, Census, timezone_offset, Download, Upload, Whitebox Model. This is the census of all Whiteboxes FCC Sept 2022.
- Raw hourly (gitignored 6.8GB local): `curr_udplatency.csv` (rtt_avg µs), `curr_udpjitter.csv` (jitter up/down µs), `curr_udploss.csv` (successes/failures).
- For FTTH 258 valid: 172,800 rows total → 36,234 rows in peak window 19-23h local.

### 1.2 Hardware-Corrected Filtering (Excel, evidenced)
Evidence: `docs/evidence/filtrado_fiber_units.png`
Rule: INCLUDE only Model IN (skwb8, skwb8p, ac1750v2) with capacity >= provisioned *1.1. EXCLUDE legacy: wnr3500l-high (480MHz CPU cap <95Mbps), wdr3600 (no HW NAT ~180Mbps), wr1043nd/wr741nd/wr741ndv4 (FastEthernet 100Mbps).

Result using exact screenshot names:
- `fiber_units.csv`: 258 rows (90.5%) - skwb8 227, ac1750v2 28, skwb8p 3 - VALID gigabit-capable
- `excluded_legacy_ffth_units.csv`: 27 rows (9.5%) - wnr3500l-high 17, wdr3600 6, wr1043nd 2, wr741nd 1, wr741ndv4 1 - EXCLUDED FTTH hardware bias
- `excluded_legacy_units.csv`: 177 rows - wdr3600 63, wnr3500l-high 50, wr741ndv4 38, wr1043nd 17, wr741nd 9 - LEGACY all-tech (DSL 91 + Cable 86, appendix)
- Validation: 285 FTTH = fiber_units.csv (258) + excluded_legacy_ffth_units.csv (27)

### 1.3 QoE Metrics (peak 19-23h local)
Window: FCC 7-11pm local with DST correction using timezone_offset.
- `p95_latency_ms`: P95 rtt_avg in peak, µs→ms /1000
- `p95_jitter_ms`: P95 avg(up/down jitter) in peak, µs→ms
- `avg_loss_pct`: Mean loss peak = failures/(successes+failures)*100

Final fact: `ftth_final_258_v2_1.csv` - 257 rows (1 of 258 without peak data), cols: unit_id, p95_latency_ms, p95_jitter_ms, avg_loss_pct, risk_flag. Stats: mean latency 12.47ms, P75 14.88ms, max 65.51ms; mean jitter 1.10ms; mean loss 2.03%.

---

## 2. Risk Flag Definition v2.1.3

**Sources:** FCC MBA 13th Report Sept 2022: fiber median 12-15ms (observed 12.56ms), P95 18-22ms >20ms=degraded gaming. Jitter mean <5ms >15ms=Zoom freeze (Technical Appendix §4.2.3). Loss >1% degraded (Methodology §5.3). ITU-T G.114/Y.1541 Class 0: preferred <20ms latency, <15ms jitter, <1% loss.

**Parameters:**
- p95_latency_ms >20.0 ms = risk
- p95_jitter_ms >15.0 ms = degraded
- avg_loss_pct >1.0% = degraded

**Business Rule v2.1.3:** risk_flag = 1 if p95_latency_ms >20.0 else 0 (simplified for Capstone). Complete v2.2: risk =1 if latency>20 OR jitter>15 OR loss>1. Result 17/257=6.61% vs legacy >80ms=0.00% (Instrument Bias coax 2015 not applicable to modern FTTH).

---

## 3. PowerBI Model - Two-Table Relationship (No Enriched File)

**Location:** Root folder with exact names from screenshot

| File (exact name) | Rows | Content | Role |
|---|---|---|---|
| `fiber_units.csv` | 258 | Unit ID, ISP, Technology=Fiber, State, Census, Download, Upload, Whitebox Model | Dimension |
| `excluded_legacy_ffth_units.csv` | 27 | Unit ID, ISP, Technology, State, Download, Whitebox Model 17/6/2/1/1 | Audit - no relationship |
| `excluded_legacy_units.csv` | 177 | Unit ID, ISP, Technology DSL/Cable, Model 63/50/38/17/9 | Appendix - legacy all-tech |
| `ftth_final_258_v2_1.csv` | 257 | unit_id, p95_latency_ms, p95_jitter_ms, avg_loss_pct, risk_flag (17 risk) | Fact |
| `unit-profile-sept2022.xlsx` / `.csv` | 2025 | Full census | Source |

**Relationship in PowerBI Model View:**
- `fiber_units.csv[Unit ID]` (One, PK, 258) → `ftth_final_258_v2_1.csv[unit_id]` (Many, FK, 257)
- Cardinality: One-to-many, Single direction, Dim filters Fact
- 1 unit of 258 without peak measurements shows blank in fact (expected, 257 final)

**DAX Measures:**
```
Total Units = COUNTROWS(fiber_units)
Units With Peak = COUNTROWS(ftth_final_258_v2_1)
Risk Count = CALCULATE(COUNTROWS(ftth_final_258_v2_1), ftth_final_258_v2_1[risk_flag]=1)
% Risk v2.1.3 = DIVIDE([Risk Count], [Units With Peak])
% Risk v1 = 0.21
Risk Reduction pp = [% Risk v1] - [% Risk v2.1.3]
Truck Rolls Avoided = [Risk Reduction pp] * [Units With Peak]
OPEX Saved = [Truck Rolls Avoided] * 180
Avg Latency P95 = AVERAGE(ftth_final_258_v2_1[p95_latency_ms])
Avg Jitter P95 = AVERAGE(ftth_final_258_v2_1[p95_jitter_ms])
Avg Loss = AVERAGE(ftth_final_258_v2_1[avg_loss_pct])
```

---

## 4. PowerBI Import Procedure

1. Get Data → Text/CSV → `fiber_units.csv` → Load (Dim)
2. Get Data → Text/CSV → `ftth_final_258_v2_1.csv` → Load (Fact)
3. Get Data → Text/CSV → `excluded_legacy_ffth_units.csv` → Load (Audit, no relationship)
4. Get Data → Text/CSV → `excluded_legacy_units.csv` → Load (Appendix, no relationship)
5. Model View → Drag `fiber_units[Unit ID]` → `ftth_final_258_v2_1[unit_id]` → One-to-Many
6. Create DAX measures Section 3
7. Build 3 dashboards

No pre-joined enriched file - relationship built in PowerBI for Google Certificate competency.

---

## 5. Dashboards

**Dashboard 1 - QoE Risk Overview:**
- KPIs: Total 257, % Risk 6.61%, Avg Latency 12.47ms, Avg Loss 2.03%
- Table: Top 17 risk_flag=1 sorted p95_latency_ms DESC (Top 24559133 - 65.51ms). Columns: Unit ID (dim), ISP (dim), State (dim), Download (dim), p95_latency_ms (fact), avg_loss_pct (fact)
- Bar: Risk % by Download tier 75/100/250/500 Mbps
- Slicers: Whitebox Model, ISP, State

**Dashboard 2 - Hardware Audit:**
- Donut: Whitebox Model from fiber_units.csv (skwb8 227, ac1750v2 28, skwb8p 3)
- Card: 27 excluded (COUNTROWS excluded_legacy_ffth_units.csv)
- Table: Breakdown 17/6/2/1/1 from excluded_legacy_ffth_units.csv
- Evidence: docs/evidence/filtrado_fiber_units.png

**Dashboard 3 - Cost Optimization:**
- Cards: OPEX Saved $6,660 (37*180), Truck Rolls Avoided 37
- Bar: v1 21% vs v2.1.3 6.61% (14.4pp reduction, 3.2x overestimation)
- Narrative: v1 Instrument Bias legacy whiteboxes caused false latency/loss.

---

## 6. References

- FCC MBA 13th Report 2023 Sept 2022 data §3 Fig12, Technical Appendix §4.2.3, Methodology §5.3
- ITU-T G.114/Y.1541 Class 0
- docs/procedimiento_matematico_v2_1_3.md
- data/methodology/risk_flag_justification_v2.1.md
- docs/evidence/filtrado_fiber_units.png

**Status:** v2.1.3 FINAL - Validated 258+27=285, fact 257, risk 6.61%, 2-table model, exact file names from repo screenshot.
**File Location:** docs/powerbi_procedimiento_v2_1_3.md
**Corrected Names Folder:** corrected_names/ with 5 files matching screenshot
