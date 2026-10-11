# FTTH QoE Capstone - Procedure Summary v3.1

**Methodology:** v3.0 | **Spec:** v1.1.0 (pending publication) | **Document:** v3.1 | **Last updated:** 2026-10-11 | **Author:** Eng. Rafael Cansigno P.

Companion documents: `docs/decisions.md` (decision log), `docs/data_dictionary.md` (columns and time handling), `docs/metrics_spec.md` (rules), `config.yaml` (values).

## 1. Original problem and v1/v2 audit findings

### Project goal
Identify FTTH units at risk of poor QoE during local evening peak hours (19:00-22:59) using FCC MBA telemetry Sep-Oct 2022, and separate real degradation from measurement artifacts.

### v1/v2 failures

**v1 - Convenience bias:**
- Only the first 1000 rows per monthly file were read.

**v2 - Instrument bias:**
- Legacy Whiteboxes `wnr3500l-high, wdr3600, wr1043nd, wr741nd, wr741ndv4` cannot forward at gigabit line rate. They create the degradation they report.
- FTTH population: 285 raw -> 258 after filter. The 27 excluded units are in `excluded_legacy_ftth_units.csv`.

**v2.1.3 -> v2.2 - Loss misinterpreted (Finding #1):**
- `curr_udpcloss.packets` was treated as loss %, then patched as `packets/10`.
- FCC dictionary: that file records **outage/disconnection events**, NOT continuous loss %.
- Real loss comes from `curr_udplatency`: `failures / (successes + failures)`.

**v2 - Inconsistent implementations:**
- Python used `timezone_offset` while Power BI used `timezone_offset_dst` -> peak window shifted 1 h.
- Peak window 19-22:59 vs 19-23:59, different loss sources. Totals matched but unit-level reconciliation failed.
- Thresholds changed without justification: 20 ms -> 50 ms latency.

**v2.2 - Data quality:**
- `fillna(0)` made a unit with no data look perfect (0 ms).
- `clip 100%` turned corrupt counters into "total loss".
- v3: invalid records are excluded and counted in a log; units with insufficient data are reported separately.

## 2. Procedure: Step 0 to Step 8

### Script map

Each script is a numbered step (`step_N.py`) with its objective in the header. Every figure in this document traces back to one of them.

| Script | Objective | Feeds |
| :--- | :--- | :--- |
| `step_0.py` | Real structure, coverage, targets, hourly RTT, offsets | Dictionary checks 1, 4, 7, 8 |
| `step_1.py` | Extract the 258 FTTH units to interim CSVs; effect of `N_MIN` | D-02 |
| `step_2.py` | Period coverage, rows per unit, hourly RTT profile | D-01 |
| `step_3.py` | Impact of the time convention on the risk flag (all servers) | D-03 |
| `step_4.py` | Duplicates by key | D-05 |
| `step_5.py` | Server mixing: all servers vs primary server | D-04 |
| `step_6.py` | Time convention repeated under `primary_only` | D-03 |
| `step_7.py` | Eastern vs Pacific RTT profile, all technologies pooled, shifts 0..+6 h | D-03 |
| `step_8.py` | Same test by technology, shifts -6..+6 h | D-03 |

### Step 0 - Real structure verification
`data/CSV_previews.md` - first 10 rows of the real files.

**Real columns vs FCC dictionary:**
- `udplatency`: the dictionary lists `location_id` but the real file does NOT have it. The real file has `ddate`, which the dictionary does not list for latency/jitter.
- `udpjitter`: uses lowercase `latency` vs `Latency` in the dictionary.
- Verified in `config.yaml`:
```yaml
udplatency: [unit_id, dtime, ddate, target, rtt_avg, rtt_min, rtt_max, rtt_std, successes, failures]
udpjitter: [unit_id, dtime, ddate, target, packet_size, stream_rate, duration, packets_up_sent, packets_down_sent, packets_up_recv, packets_down_recv, jitter_up, jitter_down, latency, successes, failures]
udpcloss: [unit_id, dtime, ddate, duration, target, address, packets]
```

**Verified facts:**
- `dtime` is a string "%Y-%m-%d %H:%M:%S" with no TZ marker, NOT unix epoch.
- `timezone_offset_dst` is in HOURS (-4, -5, -7); all 258 units observe DST.
- FTTH period is 2022-09-12 to 2022-10-31 (50 days), not September only.
- Median RTT per unit is 2.5-17.2 ms; global loss is about 0.022%.
- `rtt_avg` is in microseconds.
- `successes + failures` ranges 131-2365 **in the first rows of `curr_udplatency`**; the full distribution is pending (dictionary check 6). It still supports ratio-of-sums, because the packet count varies by row.

### Step 1 - Analysis period (D-01)
September alone gives ~32 peak records per unit (P95 rests on ~1.6 observations). The full period gives ~120 (about 6 observations).
```yaml
analysis_period: 2022-09-12 to 2022-10-31   # both inclusive
```

### Step 2 - Minimum records per unit (D-02)
`n_min_peak_records: 50`. The top 5% of 50 records holds at least 2.5 observations.
- 8 units are excluded before the server rule.
- 19 units are below 50 after `primary_only`, so **239 of 258** units are analyzed.

### Step 4 - Duplicates (D-05)
Key: `[unit_id, dtime, target]`
- Latency: 16 rows in 7 groups, all exact duplicates.
- Jitter: 10 rows; 8 exact and 2 conflicting (unit 943232).

**Policy v3.0:** `keep_one_if_identical_else_drop_all`. Every case is counted in `data_quality_log.csv`.

### Step 5 - Server rule (D-04)
A unit uses 1 to 4 servers at different distances (68, 131, 45 and 14 units use 1, 2, 3 and 4). The access line is the same, so RTT differences reflect distance and route, not the line.
- Measured under the UTC reading: all servers flag 17 units; primary server only flags 6.
- 11 units are flagged only with all servers pooled.

### Step 7/8 - Local vs UTC time (D-03)

**Question:** is `dtime` UTC as the FCC says, or already local time?

**Procedure:** correlation of the mean hourly RTT profile of Eastern units (UTC-4) vs Pacific units (UTC-7), shifting the Pacific profile by k hours.
- If `dtime` were UTC, Pacific should trail Eastern by 3 h -> expected k=+3.
- If `dtime` is local, expected k=0.

**Observed (by technology):**

| Technology | Pacific units | k=0 (local) | k=+3 (UTC) | Best k | Peak Eastern / Pacific (dtime hour) |
| :--- | ---: | ---: | ---: | ---: | :--- |
| Cable | 138 | 0.762 | -0.107 | -1 (0.892) | 21 / 20 |
| DSL | 175 | 0.594 | -0.018 | -2 (0.799) | 21 / 19 |

- Correlation at +3 h is about 0 or negative in both technologies -> UTC rejected.
- Best alignment is -1 to -2 h, much closer to 0 than to +3.
- The residual 1-2 h lead of Pacific is not a time zone offset; most likely usage behavior or composition. Not proven, so it is not over-interpreted.
- The DSL best k (-2/-3) is outside the -1..+1 criterion set beforehand, but the local-vs-UTC distinction is clear.
- Fiber was not tested: only 18 Pacific units.

**Conclusion:** indirect evidence. It does not prove the FCC documentation wrong, only that the latency data do not behave as it says.

## 3. Decisions

All decisions are recorded with alternatives and impact in `docs/decisions.md`.

| ID | Decision | Date |
| :--- | :--- | :--- |
| D-01 | Analysis period 2022-09-12 to 2022-10-31 | 2026-10-10 |
| D-02 | `N_MIN` = 50 peak records | 2026-10-10 |
| D-03 | `dtime` treated as local time; UTC reading as sensitivity | 2026-10-11 |
| D-04 | `primary_only` server rule; all servers as sensitivity | 2026-10-11 |
| D-05 | Duplicates: keep one if identical, drop all if conflicting | 2026-10-10 |

### D-03: dtime as local time (confirmed 2026-10-11)

```yaml
time:
  dtime_is_utc: false
  dtime_interpretation: local
  peak_start_hour: 19
  peak_end_hour_exclusive: 23   # 19:00:00 to 22:59:59 local
```

**Implementation (planned, `src/pipeline.py`):**
```python
# v2 assumed dtime was UTC and added an offset, without testing the assumption
# v3.0, D-03: dtime already is local time, no offset
local_hour = df["dtime"].dt.hour
```

The unit-profile offsets stay verified but are NOT used in the base case. The UTC reading is reported as a sensitivity:
```yaml
sensitivity_utc_reading:
  rule: "local_hour = hour(dtime + timezone_offset_dst)"
```

**Base result (`primary_only`):** 10 units flagged (6 under the UTC reading). 6 units change flag: 5 enter, 1 leaves (943226, 1006958, 3798765, 4190285, 24840041, 25314149).

### D-04: primary_only as base case (confirmed 2026-10-11)

```yaml
server_rule:
  mode: primary_only
  primary_definition: "target with the most peak-window records for the unit"
  tie_break: "alphabetical order of target"
  report_sensitivity_all_servers: true
```

### Thresholds - restored to spec

The `config.yaml` values were realigned with the specification:

```yaml
thresholds:
  base:
    latency_p95_ms: 20
    jitter_p95_ms: 5
    loss_pct: 1.0
  severe:
    latency_p95_ms: 50
    jitter_p95_ms: 15
    loss_pct: 10
  risk_rule: "risk_flag = 1 if p95_latency_ms > ... OR ... (strictly greater)"
  sensitivity:
    latency_p95_ms: [20, 30, 50]
    loss_pct: [0.5, 1, 2, 5]
```

Any other value must be justified first in the spec and changed in `config.yaml` in the same commit. The loss grid will be reviewed against the per-unit loss distribution (global loss is about 0.022%).

### Outputs and parameters

- Outputs Parquet `unit_qoe_v3.*` did not match the decision to use CSV -> now `ftth_qoe_unit_metrics.csv`, `units_insufficient_data.csv`, `data_quality_log.csv`.
- `transform: "p95_us_to_ms"` was text that code had to interpret -> explicit parameters `percentile: 0.95, to_ms_divisor: 1000, method: linear`.

### Population files

- `fiber_units.csv`: 258 FTTH units in scope (Technology = Fiber and Whitebox model `skwb8`, `skwb8p` or `ac1750v2`).
- `excluded_legacy_ftth_units.csv`: 27 FTTH units excluded because the hardware is not credible -> `excluded_units_file` in config, used by the pipeline.
- `excluded_legacy_units.csv`: all out-of-scope units (non-fiber and unused fiber). Includes the 27. Audit only -> `all_excluded_units_file`.

Tests verify:
- the 27 are contained in `all_excluded`;
- no overlap between `fiber_units` and the excluded files.

## 4. What "it is an outage event, not a loss %" means

`curr_udpcloss.csv` does **not** measure continuous loss %. A row exists only when an outage/disconnection event occurred (FCC definition).

**Real columns:**
```
udpcloss: [unit_id, dtime, ddate, duration, target, address, packets]
```

**Observed in previews:**
- `duration` is about 4,500,000 µs = 4.5 s
- `packets` = 2-3

Illustrative reading: "at 19:00:00, unit 123 had a 4.5 s outage with 2 packets lost against target X". The row has no denominator, so it cannot give a percentage.

**Real loss (v3.0) comes from `curr_udplatency.csv`:**
```
udplatency: [..., successes, failures]
successes=2300, failures=5 in one hour
```

Formula (`config.yaml`):
```yaml
formula: "sum(failures) / sum(successes + failures) * 100"
method: "ratio_of_sums"   # weights by packets, not mean of %
```

**v3.0 code (applied per unit, only on peak-window records of the primary server):**
```python
loss = df.groupby("unit_id").apply(
  lambda g: g["failures"].sum() / (g["successes"].sum() + g["failures"].sum()) * 100
)
```

**v2 error:**
- v2.1.3: `loss = packets` -> if packets=2, it reported 2% (false).
- v2.2: `loss = packets/10` -> if packets=2, it reported 0.2% (still false).

v3 keeps `udpcloss` only as an audit reference, outside `risk_flag`. Real global loss is about 0.022% (from `udplatency`).

## 5. Expected results with config v3.0

**Base case (D-03 local + D-04 primary_only):**
- 10 units at risk (thresholds 20 / 5 / 1.0), out of 239 analyzed (4.2%). The denominator is confirmed on the first pipeline run.
- About 120 peak records per unit (median 722 rows x 4/24).
- 8 units excluded by `n_min=50` before the server rule; 19 after it.

**Sensitivity matrix (units flagged):**

| | Primary server | All servers |
| :--- | ---: | ---: |
| Local time (base) | 10 | pending (`step_9.py`) |
| UTC reading | 6 | 17 |

The all-servers figure (17) was measured under the UTC reading, so it must not be compared with the base 10. The local-time cell is computed before this document is frozen.

**Also reported with every run:**
- Latency x loss grid for [20, 30, 50] x [0.5, 1, 2, 5]: % of units flagged in each combination.

**Outputs:**
- `data/processed/ftth_qoe_unit_metrics.csv` - per-unit metrics
- `data/processed/units_insufficient_data.csv` - fewer than 50 records
- `data/processed/data_quality_log.csv` - data quality counters and duplicates

**Reproducibility (planned):**
```bash
# config.yaml has raw_dir: null (commitable)
# config.local.yaml is gitignored:
inputs:
  raw_dir: "D:/Capstone FTTH/data/raw/validated-data-sept2022"

python src/pipeline.py
```
Dependencies: pandas and PyYAML.

## 6. Status and next steps

| Item | Status |
| :--- | :--- |
| `docs/data_dictionary.md` v1.2.0 | Done |
| `docs/decisions.md` v1.0.0 | Done |
| `config.yaml` | Done |
| `step_9.py` (local time + all servers) | Pending |
| `docs/metrics_spec.md` v1.1.0 (English) | Pending |
| `docs/data_inspection.md` | Pending |
| README update | Pending |
| Loss sensitivity grid review | Pending |
| Check 6 (`successes + failures` distribution) | Pending |
| `src/pipeline.py` and tests | Pending |