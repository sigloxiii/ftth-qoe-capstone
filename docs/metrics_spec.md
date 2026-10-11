# Metrics Specification — FTTH QoE Risk

**Spec version:** 1.1.0 · **Last updated:** 2026-10-11
**Status:** Baseline. Any change is made first in this document, then in `config.yaml` and `src/`, and recorded in the Changelog (section 12).
**Central rule:** one implementation of each transformation (Python). Power BI does **not** recalculate metrics; it only visualizes them.

**Related documents:** `config.yaml` (values), `docs/decisions.md` (decisions D-01 to D-05 with alternatives and evidence), `docs/data_dictionary.md` (columns and time handling), `docs/data_inspection.md` (Step 0 results), `docs/procedure_summary_v3.md` (procedure overview).

---

## 1. Scope and Population

- **Population source:** `unit-profile-sept2022.xlsx` (FCC MBA, 13th Report, September 2022 data).
- **Filter 1:** `Technology = Fiber` → 285 units.
- **Filter 2 (hardware):** `Whitebox Model IN (skwb8, skwb8p, ac1750v2)` → **258 units**. The 27 excluded units (`wnr3500l-high` 17, `wdr3600` 6, `wr1043nd` 2, `wr741nd` 1, `wr741ndv4` 1) are kept in `data/excluded_legacy_FTTH_units.csv` for audit. `data/excluded_legacy_units.csv` lists every Whitebox outside the analysis (non-fiber, or fiber not used) and includes those 27.
- **Rationale:** the Whitebox is the measurement instrument. Models with insufficient CPU or port speed (FastEthernet, no hardware NAT) create artificial latency and loss (instrument bias).
- **ISPs in scope:** Cincinnati Bell 120, Verizon 76, Frontier 62.
- **Grain:** 1 row = 1 `Unit ID`.
- **Analysis period (D-01):** 2022-09-12 to 2022-10-31, both ends inclusive, applied to `dtime` as stored. The files contain 50 days, not only September. The full period gives about 120 peak records per unit (the P95 rests on about 6 observations); September alone gives about 32 (about 1.6 observations), which is too few for a tail statistic.

## 2. Data Verification (Step 0, completed)

Step 0 verified the three raw files (`curr_udplatency.csv`, `curr_udpjitter.csv`, `curr_udpcloss.csv`) against the FCC MBA Technical Appendix. Results are in `docs/data_inspection.md` and `docs/data_dictionary.md` (section 6). Items that shape this specification:

1. **Headers** differ from the FCC dictionary: `ddate` is present in all three files; `location_id` is absent from `curr_udplatency`; the jitter file uses lowercase `latency`.
2. **`curr_udpcloss`** records outage/disconnection events (`duration` in µs; `packets` = number of packets lost in the event, a count per event). `packets` is never used as a percentage and is never divided by a constant.
3. **Offsets:** `timezone_offset_dst` is in hours (values -4, -5, -7) and is consistent with each unit's state. All 258 units observe daylight saving time (DST).
4. **Coverage:** every one of the 258 units has rows in `curr_udplatency` and `curr_udpjitter`; 242 have rows in `curr_udpcloss` (event-based, so no rows means no events).
5. **Invalid records:** 0 found for each rule in section 5.
6. **Duplicates:** found and handled by the policy in section 5.
7. **Servers:** a unit uses 1 to 4 test servers (68, 131, 45 and 14 units use 1, 2, 3 and 4). See section 4.
8. **Pending:** distribution of `successes + failures` per row (dictionary check 6) and the jitter unit (µs is plausible but not proven).

## 3. Time and Peak Window (D-03)

- `dtime` is a naive timestamp (`YYYY-MM-DD HH:MM:SS`). The FCC documentation states that it is UTC, but the project data show that it behaves as each unit's **local time**: the hourly RTT profile of Pacific units does not trail the Eastern one by the 3 hours that UTC would imply (correlation at a +3 h shift is about 0 or negative in Cable and DSL; best alignment -1 to -2 h, much closer to 0 than to +3). See `docs/decisions.md`, D-03.
- **Base case:** `dtime` is read as local time. `local_hour = hour(dtime)`. No offset is added.
- **Peak window:** local hour **≥ 19 and < 23** (19:00:00–22:59:59), 4 hours.

```python
# dtime already is the unit's local time; no offset is applied
df["local_hour"] = df["dtime"].dt.hour
peak = df[(df["local_hour"] >= 19) & (df["local_hour"] < 23)]  # peak window [19, 23)
```

- **Sensitivity (reported with every result):** UTC reading, as documented by the FCC. `local_hour = hour(dtime + timezone_offset_dst)`. `timezone_offset_dst` applies to every record because US DST ended on 2022-11-06, after the last record. `timezone_offset` is never used.
- **Limitations:** the evidence for the local reading is indirect and contradicts the FCC general note. Fiber was not tested (only 18 Pacific units). `dtime` marks the end of each test, so records near 19:00 and 23:00 may partly belong to the adjacent hour.

## 4. Server Rule (D-04)

A unit tests against 1 to 4 servers at different distances. The access line is the same for all of them, so RTT differences between servers reflect distance and route, not the line. Pooling servers makes a unit look worse because of server distance (17 units flagged with all servers vs 6 with the primary server, under the UTC reading).

- **Base case, `primary_only`:** each unit is measured against its **primary server**, the `target` with the most peak-window records for that unit. Ties are broken by alphabetical order of `target`.
- **Sensitivity (reported with every result):** all servers pooled.

```python
# primary target per unit: most peak-window records, ties by alphabetical order
counts = peak.groupby(["unit_id", "target"]).size().reset_index(name="n")
counts = counts.sort_values(["unit_id", "n", "target"], ascending=[True, False, True])
primary = counts.drop_duplicates("unit_id")[["unit_id", "target"]]
peak_primary = peak.merge(primary, on=["unit_id", "target"])
```

## 5. Metrics per Unit

All metrics use **only records inside the peak window** and, in the base case, only the primary server. Order of operations:

1. Keep the 258 units and the analysis period (sections 1 and 3).
2. Remove invalid records (log them) and handle duplicates (below).
3. Keep records in the peak window.
4. Apply the server rule (section 4).
5. Count `n_peak_records`; units below `N_MIN` are reported separately and not scored.
6. Compute the three metrics.

| Metric | Source | Per-row value | Per-unit aggregation |
| :--- | :--- | :--- | :--- |
| `p95_latency_ms` | `curr_udplatency.rtt_avg` (µs) | `rtt_avg / 1000` | 95th percentile, linear interpolation |
| `p95_jitter_ms` | `curr_udpjitter` (`jitter_up`, `jitter_down`, µs) | `(jitter_up + jitter_down) / 2 / 1000` | 95th percentile, linear interpolation |
| `loss_pct` | See 5.1 | `failures / (successes + failures) * 100` | **Ratio of sums:** `sum(failures) / sum(successes + failures) * 100` |
| `n_peak_records` | `curr_udplatency` | Count of valid peak records (after the server rule) | Count |

- **Percentile:** linear interpolation (pandas `quantile(0.95)` default; equivalent to `PERCENTILE.INC` in Excel and Power BI, and to the default `List.Percentile` in Power Query).
- **Ratio of sums:** weights each test by its number of packets. Averaging per-row percentages biases the result when the packet count varies.
- **Jitter unit:** µs is plausible (0.2 to 55.7 ms after conversion) but not proven. Confirm before the final results.

### 5.1 Loss source

- **Single source (confirmed in the FCC MBA Technical Appendix 2023):** `failures` and `successes` from `curr_udplatency`. The appendix defines UDP packet loss as the fraction of UDP packets lost in the UDP latency test, maps it to `curr_udplatency.csv`, and gives `failures / (successes + failures)`. A packet is counted as lost if there is no response within 3 seconds.
- **`curr_udpcloss` is not a loss percentage source.** It records outage events (count per event). It is never divided or averaged as a percentage.
- **Optional future use:** `curr_udpcloss` could feed a separate **availability** metric (number and total duration of outages in the peak window). It stays outside the base `risk_flag` and would be added in a later version of this specification.
- One loss source per specification version. No mixing.

### 5.2 Data quality

- **Invalid records** (excluded and counted, never corrected with caps): `successes + failures <= 0`; `loss_pct` outside [0, 100]; `rtt_avg` null or negative; `jitter_up` or `jitter_down` null or negative; `dtime` not parseable. Step 0 found 0 records for each rule.
- **Forbidden:** capping values (`min(x, 100)`) and filling nulls with 0 (`fillna(0)`). An invented zero makes a unit without data look perfect.
- **Duplicates (D-05):** key (`unit_id`, `dtime`, `target`). If the duplicate rows are identical, keep one; if they conflict, drop all of them. Every case is counted in the log. Found: `curr_udplatency` 16 rows in 7 groups, all exact; `curr_udpjitter` 10 rows, 8 exact and 2 conflicting (unit 943232).
- **Minimum data (D-02):** a unit enters the risk analysis if `n_peak_records >= N_MIN`, with `N_MIN = 50` (set in `config.yaml`). The top 5% of 50 records contains at least 2.5 observations, the smallest sample where a P95 is still defensible. 8 units fall below it before the server rule and 19 after it, so **239 of 258 units** are analyzed.
- **Units without enough data:** listed in `data/processed/units_insufficient_data.csv` and left out of the risk denominator. Every report states `units_analyzed / 258`.
- **Quality log:** the pipeline writes `data/processed/data_quality_log.csv` with the number of records discarded per rule and the duplicate counts.

## 6. Risk Definition

- **Status of the thresholds:** they are **operating thresholds defined by the project**, not values from a standard. Earlier citations to ITU-T G.114/Y.1541 and to specific sections of the FCC report are **not verified** (G.114 covers one-way delay and Y.1541 defines network classes with other values) and are not cited until confirmed in the source.
- **Base thresholds** (parameters in `config.yaml`):

| Parameter | Base value |
| :--- | :--- |
| `latency_p95_ms` | 20 |
| `jitter_p95_ms` | 5 |
| `loss_pct` | 1.0 |

- **Rule:** `risk_flag = 1` if `p95_latency_ms > 20` **or** `p95_jitter_ms > 5` **or** `loss_pct > 1.0` (strictly greater). The individual flags (`flag_latency`, `flag_jitter`, `flag_loss`) are also stored to show which metric triggers the risk.
- **Severity tier:** `risk_severe = 1` if `loss_pct > 10` or `p95_latency_ms > 50` or `p95_jitter_ms > 15`.
- Thresholds are not chosen to reproduce a previous result. Changing one requires a change in this specification and a Changelog entry.

## 7. Sensitivity Analysis (mandatory with every result)

| Variant | What changes | Reference result (units flagged) |
| :--- | :--- | ---: |
| Base case | Local time + primary server | 10 |
| UTC reading | `dtime + timezone_offset_dst`, primary server | 6 |
| All servers | Local time, all servers pooled | pending (`step_9.py`) |
| UTC reading, all servers | UTC reading, all servers pooled | 17 |

- The 10 and 6 come from `step_6.py` and the 17 from `step_5.py`; the figures are indicative until the pipeline reproduces them over the same units.
- Six units change flag between the local and UTC readings: 943226, 1006958, 3798765, 4190285, 24840041 and 25314149 (5 flagged only under the local reading, 1 only under the UTC reading).
- **Threshold grid:** % of units at risk for latency {20, 30, 50} ms × loss {0.5, 1, 2, 5} %. Global loss is about 0.022%, so the loss grid is reviewed against the per-unit loss distribution before it is frozen.

## 8. Reconciliation Python ↔ Power BI

Power BI consumes `data/processed/ftth_qoe_unit_metrics.csv` generated by Python. If a metric is reimplemented in Power Query for audit:

1. Export both tables and join by `Unit ID`.
2. Tolerances: `p95_latency_ms` and `p95_jitter_ms` ±0.001 ms; `loss_pct` ±0.001 percentage points; `risk_flag` exact match; same number of units.
3. Units that differ are analyzed one by one (window, time convention, server rule, nulls); reconciliation is never done by totals only.
4. The result is saved in `docs/reconciliation.md`.

Power Query equivalent of the base peak window: `Time.Hour([dtime]) >= 19 and Time.Hour([dtime]) < 23`, with no offset.

## 9. Final Dataset Schema

`data/processed/ftth_qoe_unit_metrics.csv` (UTF-8, no version in the name; versions live in git tags):

`unit_id, isp, state, census, download_mbps, upload_mbps, whitebox_model, primary_target, n_peak_records, p95_latency_ms, p95_jitter_ms, loss_pct, flag_latency, flag_jitter, flag_loss, risk_flag, risk_severe`

Automated tests (`tests/`):

- `unit_id` is unique and a subset of `fiber_units.csv`.
- 0 nulls in the metrics of analyzed units.
- `0 <= loss_pct <= 100`; `p95_latency_ms > 0`.
- `risk_flag == (flag_latency | flag_jitter | flag_loss)`.
- `analyzed + insufficient == 258`.
- The 27 units in `excluded_legacy_FTTH_units.csv` are contained in `excluded_legacy_units.csv`, and none of them is in `fiber_units.csv`.

## 10. Business Impact

- Dollar savings and avoided truck rolls are omitted: there is no source for the unit cost, and the baseline (v1) was invalidated by bias.
- If an estimate is included, it goes as a **scenario** with explicit, parameterized assumptions (cost per truck roll, rate of unnecessary visits), labeled as illustrative.

## 11. Limitations

- Two months of data (2022-09-12 to 2022-10-31) from a non-random sample of volunteer units; results do not represent all FTTH subscribers.
- 220 of the 258 units (85%) are in the US Eastern time zone.
- Hardware is filtered by the nominal capability of each model, not by a per-unit throughput test.
- The local-time reading of `dtime` rests on indirect evidence and contradicts the FCC general note; the UTC reading is reported as a sensitivity.
- Thresholds are project-defined and their sensitivity is part of the reported results.
- The jitter unit is not proven.

## 12. Changelog

- **1.1.0** (2026-10-11): translated to English; text recovered from v1.0.1 (commit `5cecc72`) after `metrics_spec.md` was overwritten by the data dictionary in commit `c8fcc37`.
  - Analysis period set to 2022-09-12 to 2022-10-31 (D-01).
  - `N_MIN = 50` (D-02).
  - `dtime` treated as local time, no offset; UTC reading as sensitivity (D-03).
  - Server rule `primary_only`; all servers as sensitivity (D-04).
  - Duplicate policy (D-05).
  - Order of operations and the sensitivity matrix added; `primary_target` added to the dataset; exclusion files and tests updated.
  - Step 0 section rewritten as completed.
  - Dictionary and config values aligned.
- **1.0.1**: definition of `curr_udpcloss` confirmed with the FCC MBA Technical Appendix 2023 (outage events; `packets` = count of lost packets); single loss source = `curr_udplatency`.
- **1.0.0**: baseline: window [19, 23) with `timezone_offset_dst`; loss as ratio of sums from `curr_udplatency`; no capping or `fillna(0)`; parameterized thresholds with sensitivity analysis.

## 13. Open Items

- **Primary server in the jitter file:** `step_5.py` and `step_6.py` define the primary server from the records of the file being processed. Confirm that the jitter metric uses the primary server of its own file and not the latency primary target, and state it here.
- **`N_MIN` on jitter:** `N_MIN` is applied to `curr_udplatency` peak records. Decide whether a minimum is also required for jitter records.
- **Loss grid:** review the {0.5, 1, 2, 5} % values against the per-unit loss distribution.
- **Check 6:** distribution of `successes + failures`.
- **Sensitivity matrix:** compute the "local time + all servers" cell (`step_9.py`).