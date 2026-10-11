# Decision Log

**Version:** 1.0.0 · **Last updated:** 2026-10-11
**Purpose:** Record each methodological decision with its alternatives, evidence and impact, so any result can be traced to a justified choice. A decision is changed only by adding a new entry that supersedes it; the metrics specification (`docs/metrics_spec.md`) and `config.yaml` are updated in the same commit.

**Status values:** Accepted · Superseded

| ID | Decision | Date | Status | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| D-01 | Analysis period 2022-09-12 to 2022-10-31 | 2026-10-10 | Accepted | `step_2.py` |
| D-02 | `N_MIN` = 50 peak records per unit | 2026-10-10 | Accepted | `step_1.py`, `step_3.py` |
| D-03 | `dtime` treated as local time; UTC reading as sensitivity | 2026-10-11 | Accepted | `step_6.py`, `step_7.py`, `step_8.py` |
| D-04 | One server per unit (`primary_only`); all servers as sensitivity | 2026-10-11 | Accepted | `step_5.py`, `step_6.py` |
| D-05 | Duplicates: keep one if identical, drop all if conflicting | 2026-10-10 | Accepted | `step_4.py` |

---

## D-01 Analysis period

**Decision:** use the full observed period, 2022-09-12 to 2022-10-31 (both ends inclusive).

**Alternatives considered**
- September only (the original plan): about 32 peak records per unit, so the P95 rests on about 1.6 observations.
- Full period: about 120 peak records per unit, so the P95 rests on about 6 observations.

**Reason:** the P95 is a tail statistic and needs enough observations to be stable. The files contain 50 days, not one month, so the original "September" scope did not match the data.

**Impact:** the README and the specification must say "2022-09-12 to 2022-10-31", not "September".

## D-02 Minimum peak records per unit

**Decision:** `N_MIN` = 50 peak-window records. Units below it are reported in `units_insufficient_data.csv` and are not scored.

**Reason:** the top 5% of 50 records contains at least 2.5 observations, which is the smallest sample where a P95 is still defensible.

**Impact**
- 8 units are excluded before the server rule.
- 19 units are excluded after the `primary_only` rule, so 239 of 258 units are analyzed.

## D-03 Time convention of `dtime`

**Decision:** `dtime` is treated as the unit's **local time**. The peak window is `hour(dtime)` in [19, 23), with no offset added. The documented reading (UTC plus `timezone_offset_dst`) is reported as a sensitivity with every result.

**Alternatives considered**

| Reading | Rule | Flagged units (`primary_only`) |
| :--- | :--- | ---: |
| Local (base case) | `hour(dtime)` | 10 |
| UTC (FCC documentation) | `hour(dtime + timezone_offset_dst)` | 6 |
| All hours (no window) | none | 8 |

**Evidence**
- Eastern and Pacific mean hourly RTT profiles were compared, shifting the Pacific one by k hours. UTC implies k = +3; local implies k = 0.
- Cable: correlation 0.762 at k=0 and −0.107 at k=+3 (best k = −1, 0.892).
- DSL: correlation 0.594 at k=0 and −0.018 at k=+3 (best k = −2, 0.799).
- Fiber was not tested: only 18 Pacific units.

**Reason:** the data do not behave as UTC in either technology. The residual 1 to 2 h lead of the Pacific profile is not a time zone offset; it most likely reflects usage behavior or composition.

**Limitations:** the evidence is indirect and contradicts the FCC general note. The DSL best shift (−2 h) is outside the −1..+1 range set beforehand, but the decision is local versus UTC, and k=+3 is clearly rejected.

**Impact:** 6 units change flag between readings (943226, 1006958, 3798765, 4190285, 24840041, 25314149): 5 flagged only under local, 1 only under UTC. The unit-profile offsets stay verified but are not used in the base case.

**Files updated:** `config.yaml` (`time` block), `data_dictionary.md` v1.2.0 (section 4, checks 3 and 4), `metrics_spec.md` section 3 (pending).

## D-04 Server rule

**Decision:** compute metrics on one server per unit, the **primary server**: the target with the most peak-window records (ties broken alphabetically). Using all servers is reported as a sensitivity.

**Alternatives considered**
- All servers pooled: 17 units flagged.
- Primary server only: 6 units flagged (under the UTC reading; 10 under the local reading).

**Reason:** a unit uses 1 to 4 servers at different distances (68, 131, 45 and 14 units use 1, 2, 3 and 4). The access line is the same for all of them, so RTT differences between servers reflect distance and route, not the line. Pooling them flags units because of server distance. Servers are assigned by proximity, so the primary server is the nearest, most representative one.

**Impact:** 11 units flagged only with all servers pooled. Records kept: 77.7%. Units below `N_MIN` after the rule: 19 (see D-02).

## D-05 Duplicate records

**Decision:** duplicates are defined by the key (`unit_id`, `dtime`, `target`). If the duplicate rows are identical, keep one; if they conflict, drop all of them. Every case is counted in `data_quality_log.csv`.

**Evidence:** `curr_udplatency` has 16 rows in 7 groups, all exact (9 extra rows). `curr_udpjitter` has 10 rows: 8 exact and 2 conflicting (unit 943232).

**Reason:** an exact duplicate carries no extra information. A conflicting pair has no objective way to decide which row is right, so neither is used (no silent choice).

**Impact:** negligible (about 0.005% of rows).

---

## Open items

- Sensitivity grid for loss: global loss is about 0.022%, so the values {0.5, 1, 2, 5}% may leave most cells empty. Review against the per-unit loss distribution.
- Check 6 (distribution of `successes + failures`) is still pending.
- Jitter unit (µs) is plausible but not proven.
