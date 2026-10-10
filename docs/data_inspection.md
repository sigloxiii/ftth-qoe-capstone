# Data Inspection — Step 0 Results

**Status:** in progress · **Last updated:** 2026-10-09
**Scope:** the three raw FCC MBA files used in this project, restricted to the 258 FTTH units in `data/fiber_units.csv`.
**Related documents:** `docs/metrics_spec.md` (Step 0 checklist), `docs/data_dictionary.md` (official definitions), `data/CSV_previews.md` (first rows of each file).

Results below come from joining each raw file to `fiber_units.csv` with DuckDB. Items marked **Pending** are not yet verified.

---

## 1. Coverage of the 258 FTTH Units

| File | Rows | Units with data | First `dtime` | Last `dtime` |
| :--- | ---: | ---: | :--- | :--- |
| `curr_udplatency.csv` | 172,800 | 258 of 258 | 2022-09-12 00:00:05 | 2022-10-31 23:59:58 |
| `curr_udpjitter.csv` | 152,730 | 258 of 258 | 2022-09-12 00:00:16 | 2022-10-31 23:59:42 |
| `curr_udpcloss.csv` | 4,919 | 242 of 258 | 2022-09-12 00:10:17 | 2022-10-31 23:49:37 |

**Findings**

- **Analysis period:** 2022-09-12 to 2022-10-31, **50 days (1,200 hours)**. The data is not limited to September, although the archive is named `validated-data-sept2022`.
- **Daylight saving time:** the US DST period ended on 2022-11-06, so the whole analysis period is under DST. `timezone_offset_dst` therefore applies to every row (the three offset pairs in the population are Eastern −5/−4, Central −6/−5 and Pacific −8/−7, and no unit is in a state without DST).
- **`curr_udpcloss` covers 242 units.** The other 16 units have no outage events in the period. Absence of rows means "no events recorded", which cannot be distinguished from "no data" without checking the other two files.
- **Row counts per unit:** `curr_udplatency` has about 670 rows per unit on average over 1,200 possible hours, so roughly half of the hours have a recorded test (the files contain validated data only). The total, 172,800, is a round figure; check for duplicates and for gaps (Pending, section 4).

## 2. `target` Values in `curr_udplatency` (258 FTTH units)

All targets are SamKnows-hosted servers (`spN-vm-<city>-us.samknows.com`). None is hosted by the ISP.

| ISP | Units | Rows | Main targets (units) |
| :--- | ---: | ---: | :--- |
| Cincinnati Bell | 120 | 81,110 | Chicago `sp2` (109), Chicago `sp1` (96), Atlanta (58), Ashburn (34) |
| Frontier | 62 | 42,397 | Miami (20), Dallas (20), Los Angeles (18) |
| Verizon | 76 | 49,293 | New York `sp2` (60), New York `sp1` (55), Ashburn (34) |

Minor targets (a few units each): Cincinnati Bell (Seattle, New York), Frontier (Chicago, Ashburn, New York, San Jose), Verizon (Chicago, Ashburn `sp2`).

**Findings**

- **Units use several targets.** Units per target add up to more than the units per ISP (Cincinnati Bell: 300 target-unit pairs for 120 units; Verizon: 153 for 76; Frontier: 68 for 62). A unit's rows are split across targets.
- **The target depends on where the unit is.** Frontier units use Miami, Dallas and Los Angeles; Cincinnati Bell units use Chicago, Atlanta and Ashburn; Verizon units use New York and Ashburn. RTT depends on distance to the server, so a single absolute latency threshold would mix **distance** with **congestion**.
- **The on-net / off-net distinction is not visible in these target names.** The MBA documentation says one on-net and one off-net node are tested hourly. Here no `target` identifies an ISP-hosted server (the Cable unit preview used `...-on.east.cox.net`). Interpretation of `sp1` vs `sp2` is **Pending**.

## 3. Implications for the Specification

| Topic | Implication | Decision |
| :--- | :--- | :--- |
| Analysis period | 50 days, Sept–Oct 2022 | Update the period in all documents |
| `timezone_offset_dst` | Valid for the whole period | Use it for every row (confirm UTC vs local with the hourly pattern, section 4) |
| Latency metric | Distance to target affects absolute RTT | Pending: add a baseline-adjusted latency (e.g., peak P95 minus the unit-target off-peak median) next to the absolute P95 |
| `target` handling | Several targets per unit | Pending: compute metrics per unit-target and then aggregate, or use the unit's main target |
| Availability from `curr_udpcloss` | Missing rows mean "no events" | Optional metric; handle units without rows explicitly |

## 4. Pending Checks

| # | Check | Status |
| :--- | :--- | :--- |
| 1 | Duplicates on (`unit_id`, `dtime`, `target`); nulls; `successes + failures` distribution | Pending |
| 2 | Targets per unit, and whether each unit keeps the same targets over time | Pending |
| 3 | Median and P95 `rtt_avg` by target | Pending |
| 4 | Mean relative RTT by hour using raw `dtime`, `dtime + timezone_offset` and `dtime + timezone_offset_dst` (expected: evening peak and early-morning minimum with the correct conversion) | Pending |
| 5 | Targets in `curr_udpjitter.csv` and `curr_udpcloss.csv` for the 258 units | Pending |
| 6 | Loss per unit (`sum(failures) / sum(successes + failures)`), all hours and peak hours | Pending |
| 7 | Jitter unit confirmed from the distribution of `jitter_up` / `jitter_down` | Pending |
