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

## 3. Methodology v3 (Summary)

Full definitions are in [`docs/metrics_spec.md`](docs/metrics_spec.md).

**Population**
- FTTH units in the FCC unit profile (285), filtered to gigabit-capable Whitebox models (`skwb8`, `skwb8p`, `ac1750v2`) → **258 units**. The 27 excluded legacy units (`wnr3500l-high` 17, `wdr3600` 6, `wr1043nd` 2, `wr741nd` 1, `wr741ndv4` 1) can be reproduced from `data/unit-profile-sept2022.xlsx`.
- The 258 units belong to three ISPs (Cincinnati Bell 120, Verizon 76, Frontier 62) in 16 US states.
- Rationale: the Whitebox is the measurement instrument. A device that cannot forward traffic at line rate creates the degradation it reports.

**Peak window**
- `dtime` is UTC. Local time = `dtime + timezone_offset_dst`. Peak window: local hour ≥ 19 and < 23.

**Metrics (per unit, peak window only)**
- `p95_latency_ms`: 95th percentile of `rtt_avg` (µs → ms).
- `p95_jitter_ms`: 95th percentile of the average of up/down jitter (µs → ms; unit to be confirmed).
- `loss_pct`: `sum(failures) / sum(successes + failures) × 100` (ratio of sums, weighted by packets), from `curr_udplatency`.

**Risk definition (provisional)**
- `risk_flag = 1` if any metric exceeds its threshold. Thresholds live in `config.yaml` and are finalized after reviewing the observed distributions; a sensitivity table (latency × loss) is reported with every result.
- A second tier (`risk_severe`) separates extreme cases.

## 4. Repository Structure

```
ftth-qoe-capstone/
├── assets/                  # banner
├── data/
│   ├── fiber_units.csv      # 258 FTTH units (gigabit-capable Whitebox models)
│   ├── unit-profile-sept2022.xlsx   # FCC unit profile (source)
│   ├── CSV_previews.md      # first rows of the raw files used
│   ├── interim/             # (planned) Parquet intermediates, gitignored
│   └── processed/           # (planned) final unit-level dataset
├── docs/
│   ├── metrics_spec.md      # source of truth for all metrics
│   ├── data_dictionary.md   # meaning of every input column, with sources
│   ├── glossary_of_terms.md
│   └── lessons_learned.md   # (planned)
├── src/                     # (planned) pipeline, single implementation
├── tests/                   # (planned) data-quality and consistency tests
├── powerbi/                 # (planned) dashboard, consumes processed data only
├── config.yaml              # (planned) thresholds and parameters
├── archive/                 # superseded material (v1, v2), not used by the pipeline
└── LICENSE
```

Raw FCC data (6.8 GB) is not stored in the repository. Its local path is set in `config.local.yaml` (gitignored).

## 5. Reproducibility

Raw data: FCC MBA validated data, 2022 release (13th Measuring Broadband America report), including `curr_udplatency.csv`, `curr_udpjitter.csv` and `curr_udpcloss.csv`.

1. Download and extract the files listed above.
2. Set `raw_dir` in `config.local.yaml`.
3. Run the pipeline (command will be documented here once the pipeline is complete).
4. Validate with the tests in `tests/`.

## 6. Roadmap

- [x] Hardware filter and population definition (258 units)
- [x] Metrics specification
- [x] Data dictionary from the FCC Technical Appendix
- [x] Preview of the first rows of the raw files
- [x] Repository restructure and archive of previous versions
- [ ] Data inspection of raw files (headers, units, time zone, `target` values, date range)
- [ ] Pipeline: raw → Parquet → unit-level metrics
- [ ] Data-quality log and automated tests
- [ ] Threshold selection from observed distributions, with sensitivity analysis
- [ ] Power BI dashboard and unit-level Python ↔ Power BI reconciliation
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
