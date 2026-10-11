# src/ - Code for the FTTH QoE Capstone

Code that implements the methodology defined in [`docs/metrics_spec.md`](../docs/metrics_spec.md) (v1.1.0). Values live in [`config.yaml`](../config.yaml); code never hardcodes a value that appears there. If code and spec disagree, the spec wins.

## Layout

```
src/
├── README.md        # this file
├── steps/           # numbered exploration scripts, step_0.py ... step_N.py
└── pipeline.py      # single implementation of the metrics (planned)
```

| Folder / file | Role | Status |
| :--- | :--- | :--- |
| `steps/` | Step-by-step inspection and decision scripts. Each one produced the evidence behind a decision (D-01 to D-05) or a Step 0 check | Versioned |
| `pipeline.py` | One implementation of each transformation: raw FCC files -> unit-level metrics. Implements D-03 and D-04 | Planned |

## `steps/` - Script map

Each script is a numbered step with its objective written in the header comment. Every figure in `docs/` traces back to one of them.

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
| `step_9.py` | Local time + all servers (missing cell of the sensitivity matrix) | Pending |

The same map is in [`docs/procedure_summary_v3.md`](../docs/procedure_summary_v3.md). Decisions and their evidence: [`docs/decisions.md`](../docs/decisions.md).

### Conventions

- Scripts are numbered in the order the analysis was done (`step_0.py`, `step_1.py`, ...). A number is never reused.
- Every script starts with a comment that states its objective.
- Scripts are exploration and evidence, not the final pipeline. A rule found in a step is moved to the spec and `config.yaml` first, then implemented in `pipeline.py`.
- Figures quoted in the docs (for example 10 / 6 / 17 units flagged) are indicative until `pipeline.py` reproduces them over the same units (spec section 7).

## Inputs and configuration

- Raw FCC files (6.8 GB) are not in the repository. Set their folder in `config.local.yaml` (gitignored):

  ```yaml
  inputs:
    raw_dir: "D:/Capstone FTTH/data/raw/validated-data-sept2022"
  ```

  `config.yaml` keeps `raw_dir: null` on purpose, so no absolute path is committed.
- Population files are in `data/` (`fiber_units.csv`, `excluded_legacy_ftth_units.csv`, `excluded_legacy_units.csv`, `unit-profile-sept2022.xlsx`).
- Intermediate files go to `data/interim/` (gitignored). Final outputs go to `data/processed/`.

## Planned: `pipeline.py`

- Reads `config.yaml` (and the `config.local.yaml` override) and runs the order of operations in spec section 5.
- Writes `data/processed/ftth_qoe_unit_metrics.csv`, `units_insufficient_data.csv` and `data_quality_log.csv`.
- Power BI consumes only `data/processed/`; it does not recalculate metrics.

## Rules that apply to all code here

- No capping and no `fillna(0)`: invalid records are excluded and counted.
- `dtime` is read as local time; no offset is added (D-03). The UTC reading is a sensitivity.
- Loss comes from `curr_udplatency` as `sum(failures) / sum(successes + failures) * 100`; `curr_udpcloss` is never used as a loss percentage.