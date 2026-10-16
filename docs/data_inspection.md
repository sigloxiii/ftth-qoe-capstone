# Data Inspection — Step 0 Results

**Status:** completed (checks 2 and 3 partly done, optional) · **Last updated:** 2026-10-15
**Scope:** the three raw FCC MBA files used in this project, restricted to the 258 FTTH units in `data/fiber_units.csv`.
**Related documents:** `docs/metrics_spec.md` (Step 0 checklist), `docs/data_dictionary.md` (official definitions), `docs/decisions.md` (decisions D-01 to D-10), `data/CSV_previews.md` (first rows of each file).

Results below come from the numbered scripts in `src/steps/` (`step_0.py` to `step_11.py`, pandas). Each script records its console output in its `OUTPUT` docstring. Items marked **Pending** are not yet verified.

---

## 1. Coverage of the 258 FTTH Units

| File | Rows | Rows after duplicates (`step_9.py`) | Units with data | First `dtime` | Last `dtime` |
| :--- | ---: | ---: | ---: | :--- | :--- |
| `curr_udplatency.csv` | 172,800 | 172,791 | 258 of 258 | 2022-09-12 00:00:05 | 2022-10-31 23:59:58 |
| `curr_udpjitter.csv` | 152,730 | 152,724 | 258 of 258 | 2022-09-12 00:00:16 | 2022-10-31 23:59:42 |
| `curr_udpcloss.csv` | 4,919 | not applicable | 242 of 258 | 2022-09-12 00:10:17 | 2022-10-31 23:49:37 |

**Findings**

- **Analysis period:** 2022-09-12 to 2022-10-31, **50 days (1,200 hours)**. The data is not limited to September, although the archive is named `validated-data-sept2022`.
- **Daylight saving time:** the US DST period ended on 2022-11-06, so the whole analysis period is under DST. `timezone_offset_dst` therefore applies to every row (the three offset pairs in the population are Eastern −5/−4, Central −6/−5 and Pacific −8/−7, and no unit is in a state without DST).
- **`curr_udpcloss` covers 242 units.** The other 16 units have no outage events in the period. Absence of rows means "no events recorded", which cannot be distinguished from "no data" without checking the other two files.
- **Row counts per unit:**
  - `curr_udplatency`: mean 670, median 722, minimum 7, maximum 769 over 1,200 possible hours, so more than half of the hours have a recorded test (the files contain validated data only).
  - `curr_udpjitter`: mean 592, median 642.5, minimum 35, maximum 720.
  - `curr_udpcloss`: mean 20.3, median 6, maximum 874 (event-based).
- **Rows per month are uneven.** `curr_udplatency`: 46,205 in September (19 days, about 2,430 per day) and 126,595 in October (31 days, about 4,080 per day), about 1.7 times more per day. `curr_udpjitter` shows the same pattern (40,862 and 111,868). The cause is not known. It does not affect the rules, but September alone would give few records per unit (D-01).
- **Duplicates and invalid records:** see check 1 in section 4.

## 2. `target` Values (258 FTTH units)

All targets in `curr_udplatency` are SamKnows-hosted servers (`spN-vm-<city>-us.samknows.com`). None is hosted by the ISP.

| ISP | Units | Rows | Main targets (units) |
| :--- | ---: | ---: | :--- |
| Cincinnati Bell | 120 | 81,110 | Chicago `sp2` (109), Chicago `sp1` (96), Atlanta (58), Ashburn (34) |
| Frontier | 62 | 42,397 | Miami (20), Dallas (20), Los Angeles (18) |
| Verizon | 76 | 49,293 | New York `sp2` (60), New York `sp1` (55), Ashburn (34) |

Minor targets (a few units each): Cincinnati Bell (Seattle, New York), Frontier (Chicago, Ashburn, New York, San Jose), Verizon (Chicago, Ashburn `sp2`).

**Findings**

- **Units use several targets.** A unit uses 1, 2, 3 or 4 servers (68, 131, 45 and 14 units). Units per target add up to more than the units per ISP (Cincinnati Bell: 300 target-unit pairs for 120 units; Verizon: 153 for 76; Frontier: 68 for 62). A unit's rows are split across targets.
- **The target depends on where the unit is.** Frontier units use Miami, Dallas and Los Angeles; Cincinnati Bell units use Chicago, Atlanta and Ashburn; Verizon units use New York and Ashburn. RTT depends on distance to the server, so a single absolute latency threshold would mix **distance** with **congestion**. The primary-server rule (D-04, D-06) removes the mixing between servers of the same unit; it does not remove the difference in distance between units.
- **`curr_udpjitter` uses the same family of servers.** Its ten most frequent targets (99.97% of its rows) are SamKnows-hosted `sp1` / `sp2` servers.
- **`curr_udpcloss` includes ISP-hosted targets** (`samk01.lsan.ca.frontiernet.net`, `samk01.asbn.va.frontiernet.net`, `newyorkfcc.west.verizon.net`, `restonfcc.west.verizon.net`): at least 1,898 of its 4,919 rows (39%) among its ten most frequent targets. This file is not used for risk in v3.0 (outage events, see `metrics_spec.md` section 5.1).
- **The on-net / off-net distinction is not visible in the latency and jitter target names.** The MBA documentation says one on-net and one off-net node are tested hourly. Here no latency target identifies an ISP-hosted server (the Cable unit preview used `...-on.east.cox.net`). Interpretation of `sp1` vs `sp2` is **Pending**.

## 3. Implications for the Specification

| Topic | Implication | Decision |
| :--- | :--- | :--- |
| Analysis period | 50 days, Sept–Oct 2022 | Done: D-01, period updated in the spec and config |
| `timezone_offset_dst` | Valid for the whole period | Superseded by D-03: `dtime` is read as local time; the offsets are kept only for the UTC sensitivity |
| Latency metric | Distance to target affects absolute RTT | Not part of v3.0: a baseline-adjusted latency (for example, peak P95 minus the unit-target off-peak median) was not adopted. D-04 and D-06 control for distance between servers of the same unit; the remaining distance effect between units stays as a limitation |
| `target` handling | Several targets per unit | Done: D-04 (primary server, one per unit) and D-06 (same server for latency, loss and jitter) |
| Availability from `curr_udpcloss` | Missing rows mean "no events" | Optional metric, outside v3.0; handle units without rows explicitly if added |

## 4. Check Results

| # | Check | Status | Result |
| :--- | :--- | :--- | :--- |
| 1 | Duplicates on (`unit_id`, `dtime`, `target`); nulls; `successes + failures` distribution | Done | Latency: 16 rows in 7 groups, all exact (9 extra rows removed). Jitter: 10 rows, 8 exact (4 extra removed) and 2 conflicting (unit 943232, both dropped). 0 invalid records in both files (nulls or negatives in `rtt_avg`, `jitter_up`, `jitter_down`; loss outside [0, 100]). `successes + failures` per row (172,791 rows): mean 1,736.6, minimum 50, P1 65, P5 231, median 2,065, P95 2,303, P99 2,356, maximum 2,401 |
| 2 | Targets per unit, and whether each unit keeps the same targets over time | Partly done | Targets per unit: 1 to 4 (68, 131, 45, 14 units). Stability of each unit's targets over time not checked: the primary server is chosen over the whole period |
| 3 | Median and P95 `rtt_avg` by target | Pending (optional) | Not required by D-04 or D-06. Median RTT per unit is 2.5 to 17.2 ms (`step_1.py`) |
| 4 | Mean RTT by hour using raw `dtime`, `dtime + timezone_offset` and `dtime + timezone_offset_dst` | Done | FTTH only (`step_0.py`): raw `dtime` gives a maximum at hour 21 (11.40 ms) and a minimum at hour 16 (10.99 ms); with the standard or DST offset the maximum moves to hours 16 to 17 (11.36 ms). The FTTH range is only about 0.4 ms, so it is not enough alone. The decision rests on the Eastern vs Pacific comparison for Cable and DSL (`step_7.py`, `step_8.py`): D-03 |
| 5 | Targets in `curr_udpjitter.csv` and `curr_udpcloss.csv` for the 258 units | Done | See section 2. Jitter uses the same SamKnows servers; `curr_udpcloss` also has ISP-hosted targets |
| 6 | Loss per unit (`sum(failures) / sum(successes + failures)`), all hours and peak hours | Done for peak hours | Base case, 237 analyzed units (`step_9.py`): median 0.007%, mean 0.029%, P90 0.04%, P99 0.43%, maximum 1.66%. Units above 0.05 / 0.1 / 0.5 / 1%: 18 / 10 / 2 / 1. The all-hours distribution was not computed |
| 7 | Jitter unit confirmed from the distribution of `jitter_up` / `jitter_down` | Supported, not proven | Per-unit median jitter 0.70 ms against median `rtt_std` 0.96 ms if both are µs (median ratio 0.83, Spearman 0.816, `step_10.py`). Raw maxima: `jitter_up` 580,881 and `jitter_down` 428,137; raw medians 1,220 and 86, so the average mostly reflects upstream. Observed `duration` (about 15 s) differs from the documented 10 s (open) |

Pending items that remain: interpretation of `sp1` vs `sp2`, stability of targets over time (check 2), median and P95 by target (check 3, optional) and the all-hours loss distribution (check 6, optional).