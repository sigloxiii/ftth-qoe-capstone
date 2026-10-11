![ftth-qoe-capstone banner](./assets/main_banner.jpg)

# ftth-qoe-capstone
### FCC QoE Risk Analysis / Análisis de Riesgo QoE

**Author:** Eng. Rafael Cansigno P. | Data Analyst | Telecom + BI · Google Data Analytics Capstone (Track B, self-directed) · September–October 2026
**Stack:** Python | Power BI | VS Code | SQL
**KPIs:** P95 Latency | Jitter | Packet Loss

> Identifying fiber (FTTH) subscribers at risk of poor Quality of Experience (QoE) from FCC Measuring Broadband America telemetry, using a reproducible and auditable pipeline.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
![Data: FCC MBA Sept-Oct 2022](https://img.shields.io/badge/Data-FCC%20MBA%20Sept--Oct%202022-blue)
![Status: Methodology v3 in progress](https://img.shields.io/badge/Status-Methodology%20v3%20in%20progress-orange)

---

## 1. Project Summary

This project uses FCC Measuring Broadband America (MBA) telemetry from 2022 to answer one question:

> Which FTTH units show degraded QoE during peak hours, and how much of that degradation is real versus an artifact of the measurement instrument or the analysis?

The analysis focuses on three metrics measured in the local evening peak window: latency (P95), jitter (P95) and packet loss.

**Why P95 instead of the average?** The average hides the tail: a unit can have a 15 ms average latency and still show much higher values in a share of its hours. The 95th percentile (P95) is the value that 95% of the measurements do not exceed, so it describes the poorer end of the distribution, where bad QoE lives. Each `rtt_avg` value is itself the average of one hourly test, so the P95 here summarizes the *hourly averages*; spikes inside a single test are only visible in `rtt_max`.

**Current status:** Methodology v3 is specified (`docs/metrics_spec.md`). The pipeline is being rebuilt from the raw data. **No results are published yet**; they will be added only after the data inspection step and the Python ↔ Power BI reconciliation are complete.

## 2. Why Version 3 Was Necessary

The project went through two methodology iterations. Each one found a real problem, and the audit of the second one showed that patching it was less reliable than rebuilding it on a single, verified specification.

| Version | What it did | What it revealed |
| :--- | :--- | :--- |
| **v1** | Read the first 1,000 rows of each monthly FCC file | **Convenience bias:** the sample was dominated by legacy enrollments, not representative of the fleet |
| **v2 / v2.1.3** | Filtered FTTH units by hardware (285 → 258) and flagged risk by latency only | **Instrument bias solved:** legacy Whiteboxes (low CPU, FastEthernet) created false latency and loss. **New problem:** packet loss was computed from a raw count (`packets`) treated as a percentage |
| **v2.2** | Patched loss with `packets/10`, capped at 100%, and filled nulls with 0 | **Patch masked data issues** and left the two implementations inconsistent (details below) |
| **v3** | Single specification, single implementation, verified inputs | Current version |

### Findings that drove the rebuild

1. **The loss field was misinterpreted.** In v2.1.3, values such as `10055` were read as 1,005% loss, and the v2.2 fix assumed 1,000 datagrams per test (`packets/10`). According to the FCC MBA Technical Appendix data dictionary, `curr_udpcloss.csv` records **outage/disconnection events** (`duration` and `packets`, the number of packets lost in the event), not a per-test loss percentage. Packet loss is defined from `curr_udplatency.csv` as `failures / (successes + failures)`. The `packets/10` conversion therefore had no valid basis, and the 34.5% risk it produced was an artifact.
2. **Corrections hid problems instead of exposing them.** Capping values at 100% turned corrupt counters into "total loss", and `fillna(0)` made a unit with no data look perfect (0 ms latency, 0 ms jitter).
3. **Python and Power BI implemented the metrics differently.** The documented versions differed in the UTC offset used (`timezone_offset` vs `timezone_offset_dst`; the data period is under daylight saving time), the peak window (19:00–22:59 vs 19:00–23:59) and the loss source (`curr_udplatency` failures/successes vs `curr_udpcloss` packets, which measure different things). Matching totals could not prove they matched unit by unit.
4. **Risk thresholds changed without justification.** The flag moved from latency > 20 ms / jitter > 15 ms / loss > 1% to latency > 50 ms / jitter > 5 ms / loss > 1%. With the observed distribution, the jitter condition never triggered and the latency condition triggered for a single unit, so the result depended almost entirely on the misinterpreted loss metric.
5. **Results were not reproducible from the repository.** The scripts that generated the datasets were not versioned, several documents cited files that did not exist, and key figures (units at risk, mean loss) differed across documents.

### What v3 changes

- **One specification** (`docs/metrics_spec.md`) that defines every metric, window and threshold. Code follows the spec, never the other way around.
- **One implementation** of each transformation, in Python. Power BI only visualizes the processed output.
- **Data inspection first:** column definitions and units are verified against the FCC documentation and the real files before any metric is computed (`docs/data_dictionary.md`, `data/CSV_previews.md`).
- **No capping and no zero-filling.** Invalid records are excluded and counted in a data-quality log; units without enough data are reported separately, not scored.
- **Unit-level reconciliation** between Python and Power BI (per `Unit ID`, with explicit tolerances), instead of comparing totals.
- **Parameterized thresholds** with a sensitivity analysis. They are project-defined operating thresholds, not values attributed to a standard until verified in the source.

## 3. Methodology v3 (Summary) - Aligned to config.yaml v3.0

Full definitions are in [`docs/metrics_spec.md`](docs/metrics_spec.md) v1.1.0 and [`config.yaml`](config.yaml) is the single source of truth. Decisions in [`docs/decisions.md`](docs/decisions.md).

**Analysis period**
- Full observed period inclusive: `2022-09-12` to `2022-10-31` (50 days). Rationale: September alone gives ~32 peak records per unit (P95 rests on ~1.6 obs); full period gives ~120 (~6 obs for P95). See `config.yaml` `analysis_period`.

**Population**
- FTTH units in the FCC unit profile (285), filtered to gigabit-capable Whitebox models (`skwb8`, `skwb8p`, `ac1750v2`) → **258 units**. The 27 excluded legacy units (`wnr3500l-high` 17, `wdr3600` 6, `wr1043nd` 2, `wr741nd` 1, `wr741ndv4` 1) are in `data/excluded_legacy_FTTH_units.csv` and reproduced from `data/unit-profile-sept2022.xlsx`. `data/excluded_legacy_units.csv` contains all out-of-scope units (audit).
- The 258 units belong to three ISPs (Cincinnati Bell 120, Verizon 76, Frontier 62) in 16 US states.
- Allowed TZ offsets: `[-4, -5, -7]` hours (`timezone_offset_dst`). Any other value stops pipeline. See `config.yaml` `population`.
- Rationale: the Whitebox is the measurement instrument. A device that cannot forward traffic at line rate creates the degradation it reports. Filter uses nominal capability, not per-unit throughput test (see Limitations).

**Peak window - DECISION D-03**
- **D-03 (2026-10-10): `dtime` is treated as LOCAL time, not UTC.** Implementation in `src/pipeline_v3.py`: `local_hour = hour(dtime)`. No offset added. `dtime_format: "%Y-%m-%d %H:%M:%S"` string with no TZ marker (verified Step 0, not unix epoch).
- Evidence (Step 7/8): FCC dictionary says UTC, but hourly RTT profile of Pacific units (UTC-7) does not trail Eastern (UTC-4) by 3h as UTC would imply. Correlation at +3h shift ~0 or negative; best alignment -1 to -2h, much closer to 0 (local) than to +3 (UTC).
  - Cable: k=0 corr 0.762 vs k=+3 -0.107, best k=-1 0.892, peak Eastern 21h / Pacific 20h (dtime hour)
  - DSL: k=0 0.594 vs k=+3 -0.018, best k=-2 0.799, peak 21h/19h
  - Conclusion: indirect proof, does not prove FCC docs wrong, only that latency data does not behave as FCC says. See `docs/decisions.md`.
- `timezone_offset_dst` in HOURS (-4,-5,-7), all 258 observe DST, verified but NOT used to compute window. Kept as sensitivity analysis per `config.yaml` `time.sensitivity_utc_reading`: `local_hour = hour(dtime + timezone_offset_dst)` expected 6 flagged with primary_only vs 10 base.
- Peak window: local hour >=19 and <23 (19:00:00 to 22:59:59 local) per `time.peak_start_hour: 19`, `peak_end_hour_exclusive: 23`

**Server rule - DECISION D-04**
- **D-04 (2026-10-10): `primary_only` as base case** (vs `all_servers` variant). Rationale: a unit uses 1 to 4 servers at different distances. Access line is same, RTT differences reflect distance/route, not line. Mixing servers inflated risk: 17 flagged with all servers vs 6 with primary_only (step_5.py). Base now ~10 with D-03 local.
- Primary definition: target with most peak-window records for the unit, tie alphabetical order of target. See `config.yaml` `server_rule` and `src/pipeline_v3.py` `select_primary_server()`.
- Sensitivity Variant A `all_servers` reported with every result.

**Metrics (per unit, peak window only, after server rule, after D-03/D-04)**
- `p95_latency_ms`: 95th percentile of `rtt_avg` (µs → ms via /1000). `percentile: 0.95`, `percentile_method: linear` (pandas quantile default, same as PERCENTILE.INC). Description: P95 describes tail where bad QoE lives.
- `p95_jitter_ms`: 95th percentile of average of up/down jitter `(jitter_up + jitter_down)/2` (µs → ms; unit to be confirmed, duration ~15s, values 0.2-55ms). Same percentile/method.
- `loss_pct`: `sum(failures) / sum(successes + failures) * 100` ratio_of_sums weighted by packets (successes+failures varies 131-2365), from `curr_udplatency` (NOT `curr_udpcloss`). See `config.yaml` `metrics.loss`.

**Data quality v3.0**
- No capping, no fillna(0): `data_quality.no_capping: true`, `no_fillna_zero: true`. v2.2 hid problems.
- Invalid records excluded and counted: `successes+failures<=0`, loss outside [0,100], rtt_avg null/negative, jitter null/negative, dtime not parseable. Step 0 found 0 for each.
- Duplicates key `[unit_id, dtime, target]` policy `keep_one_if_identical_else_drop_all`: latency 16 rows in 7 groups all exact, jitter 10 rows 8 exact 2 conflicting (unit 943232).
- `n_min_peak_records: 50` - Top 5% of 50 = 2.5 obs, excludes 8 units in step_1 (before server rule). Units below reported in `units_insufficient_data.csv` and NOT scored.
- Outputs: `data/processed/ftth_qoe_unit_metrics.csv`, `units_insufficient_data.csv`, `data_quality_log.csv` (CSV only, no Parquet, version in git tags)

**Risk definition**
- `risk_flag = 1 if p95_latency_ms > latency_p95_ms OR p95_jitter_ms > jitter_p95_ms OR loss_pct > loss_pct` (strictly greater). Thresholds live in `config.yaml` `thresholds.base: 20/5/1.0`, `severe: 50/15/10` and are project-defined operating thresholds (NOT values attributed to standard).
- `risk_severe` second tier separates extreme cases.
- Sensitivity grid reported with every result per `thresholds.sensitivity`: `latency_p95_ms [20,30,50]` x `loss_pct [0.5,1,2,5]` -> % units at risk. Global loss ~0.022% so review loss grid after distribution.
- Expected base case D-03 local + D-04 primary_only: ~10 units at risk (was 6 with UTC reading, 17 with all_servers).

## 4. Repository Structure

```
ftth-qoe-capstone/
├── assets/                  # banner main_banner.jpg
├── data/
│   ├── fiber_units.csv      # 258 FTTH units (gigabit-capable Whitebox models)
│   ├── excluded_legacy_FTTH_units.csv  # 27 legacy FTTH excluded (hardware not credible) - used by pipeline
│   ├── excluded_legacy_units.csv       # All out-of-scope (audit, includes 27)
│   ├── unit-profile-sept2022.xlsx   # FCC unit profile (source)
│   ├── CSV_previews.md      # first 10 rows of raw files (verified structure)
│   ├── interim/             # Parquet intermediates, gitignored (planned)
│   └── processed/           # final unit-level dataset: ftth_qoe_unit_metrics.csv, units_insufficient_data.csv, data_quality_log.csv
├── docs/
│   ├── metrics_spec.md      # source of truth v1.1.0 for all metrics
│   ├── data_dictionary.md   # meaning of every input column, with Step 0 verification (real vs FCC dictionary)
│   ├── decisions.md         # D-03 local vs UTC, D-04 primary_only with evidence
│   ├── glossary_of_terms.md
│   ├── reconciliation.md    # Python ↔ Power BI unit-level reconciliation
│   └── lessons_learned.md
├── src/
│   ├── pipeline_v3.py       # single implementation, implements D-03/D-04, config.yaml as source of truth
│   └── utils.py             # load_config() with config.local.yaml override
├── tests/
│   ├── test_qoe.py          # population 258+27, no overlap, timezone allowed, loss range, n_min, reconciliation
│   └── test_population.py   # expected counts
├── powerbi/                 # dashboard, consumes processed data only, expected_schema.csv for reconciliation
├── config.yaml              # v3.0 single source of truth (222 lines, methodology 3.0, spec 1.1.0, raw_dir: null)
├── config.local.yaml.example # template: inputs.raw_dir local path, gitignored
├── requirements.txt         # pandas, pyyaml, openpyxl
└── LICENSE
```

Raw FCC data (6.8 GB) is NOT stored in the repository. Its local path is set in `config.local.yaml` (gitignored). Example `config.local.yaml`:

```yaml
inputs:
  raw_dir: "D:/Capstone FTTH/data/raw/validated-data-sept2022"
```

`config.yaml` has `raw_dir: null` by design - local override pattern prevents absolute paths in repo.

## 5. Reproducibility

Raw data: FCC MBA validated data, 2022 release (13th Measuring Broadband America report), including `curr_udplatency.csv`, `curr_udpjitter.csv` and `curr_udpcloss.csv`. `curr_udpcloss` is reference only: outage events (`duration ~4.5s, packets 2-3`) NOT a loss metric.

1. Download and extract the files listed above to a local folder.
2. Copy `config.local.yaml.example` to `config.local.yaml` and set `raw_dir`.
3. Install dependencies: `pip install -r requirements.txt` (pandas, pyyaml, openpyxl)
4. Run pipeline: `python src/pipeline_v3.py` (inspection mode if raw_dir missing, prints config v3.0 D-03/D-04)
5. Validate with tests: `pytest tests/` - checks population 258/27, timezone allowed [-4,-5,-7], loss range, no fillna(0), duplicates policy
6. Reconcile Power BI: Power BI consumes ONLY `data/processed/` and compares per unit_id with tolerances 0.05ms latency, 0.01% loss per `docs/reconciliation.md`

## 6. Roadmap

- [x] Hardware filter and population definition (258 units) - `data/fiber_units.csv`
- [x] Metrics specification v1.1.0 - `docs/metrics_spec.md`
- [x] Data dictionary with real vs FCC dictionary - `docs/data_dictionary.md`
- [x] Preview of the first rows of the raw files - `data/CSV_previews.md`
- [x] Repository restructure and archive of previous versions - `archive/`
- [x] Decisions D-03 local vs UTC and D-04 primary_only - `docs/decisions.md`, `config.yaml` v3.0
- [ ] Data inspection of raw files (headers, units, time zone, `target` values, date range) - Step 0 verified facts in config.yaml
- [ ] Pipeline: raw → unit-level metrics (CSV) with DQ log - `src/pipeline_v3.py` in inspection mode, full run needs raw_dir
- [ ] Data-quality log and automated tests - `tests/test_qoe.py`
- [ ] Threshold selection from observed distributions, with sensitivity analysis - `thresholds.sensitivity` grid
- [ ] Power BI dashboard and unit-level Python ↔ Power BI reconciliation - `powerbi/`
- [ ] Results and findings section

## 7. Limitations

- Data from a single release period (2022) and a non-random sample of volunteer units; results do not generalize to all FTTH subscribers.
- The population covers three ISPs, and 220 of the 258 units (85%) are in the US Eastern time zone.
- Hardware suitability is based on the nominal capability of each Whitebox model, not on a per-unit throughput test.
- Risk thresholds are project-defined and their sensitivity is part of the reported results.

## 8. Documentation Index

- [`docs/metrics_spec.md`](docs/metrics_spec.md): metric definitions, data quality rules, reconciliation protocol.
- [`docs/data_dictionary.md`](docs/data_dictionary.md): meaning of every input column, with sources and pending verifications.
- [`data/CSV_previews.md`](data/CSV_previews.md): first rows of each raw file and what they show.
- [`docs/glossary_of_terms.md`](docs/glossary_of_terms.md): glossary of terms.
- [`archive/`](archive/): v1 and v2 material, kept as a record of the iteration.

## 9. License

MIT. See [LICENSE](LICENSE).
