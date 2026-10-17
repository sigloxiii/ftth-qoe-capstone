# Data Inspection — Step 0 Results

**Status:** Step 0 closed. Two checks are only partial (2 and 3) and the `sp1` / `sp2` interpretation is still open (section 5). · **Last updated:** 2026-10-17
**Scope:** the three raw FCC MBA files used in this project, restricted to the 258 FTTH units in `data/fiber_units.csv`.
**Related documents:** `docs/metrics_spec.md` (section 2, Step 0 summary), `docs/data_dictionary.md` (official definitions), `docs/decisions.md` (D-01 to D-10), `data/CSV_previews.md` (first rows of each file).

Results come from the scripts in `src/steps/` (pandas only), which print their findings to the console and keep the recorded output in an `OUTPUT` docstring. Each check below names its script.

---

## 1. Coverage of the 258 FTTH Units (`step_0.py`)

| File | Rows | Units with data | First `dtime` | Last `dtime` |
| :--- | ---: | ---: | :--- | :--- |
| `curr_udplatency.csv` | 172,800 | 258 of 258 | 2022-09-12 00:00:05 | 2022-10-31 23:59:58 |
| `curr_udpjitter.csv` | 152,730 | 258 of 258 | 2022-09-12 00:00:16 | 2022-10-31 23:59:42 |
| `curr_udpcloss.csv` | 4,919 | 242 of 258 | 2022-09-12 00:10:17 | 2022-10-31 23:49:37 |

| File | Rows 2022-09 (from the 12th) | Rows 2022-10 | Rows per unit: mean / median / min / max |
| :--- | ---: | ---: | :--- |
| `curr_udplatency.csv` | 46,205 | 126,595 | 670 / 722 / 7 / 769 |
| `curr_udpjitter.csv` | 40,862 | 111,868 | 592 / 643 / 35 / 720 |
| `curr_udpcloss.csv` | 1,265 | 3,654 | 20 / 6 / 1 / 874 |

**Findings**

- **Analysis period:** 2022-09-12 to 2022-10-31, **50 days (1,200 hours)**. The data is not limited to September, although the archive is named `validated-data-sept2022` (D-01).
- **Daylight saving time:** the US DST period ended on 2022-11-06, so the whole analysis period is under DST. `timezone_offset_dst` therefore applies to every row (the three offset pairs in the population are Eastern −5/−4, Central −6/−5 and Pacific −8/−7, and no unit is in a state without DST). The 258 units split as −4: 220, −5: 20, −7: 18.
- **`curr_udpcloss` covers 242 units.** The other 16 units have no outage events in the period. Absence of rows means "no events recorded", which cannot be distinguished from "no data" without checking the other two files; every one of the 258 units has rows in the latency and jitter files.
- **Row counts per unit:** `curr_udplatency` has about 670 rows per unit on average over 1,200 possible hours, so roughly half of the hours have a recorded test (the files contain validated data only). The total, 172,800, is a round figure. Duplicates were checked (check 1); gaps by hour were not analyzed.
- **Units with very few rows:** the minimum is 7 latency rows for a unit; the peak-window count per unit is what matters for scoring, handled by `N_MIN` (D-02).

## 2. `target` Values in `curr_udplatency` (258 FTTH units)

All latency targets are SamKnows-hosted servers (`spN-vm-<city>-us.samknows.com`). None is hosted by the ISP.

| ISP | Units | Rows | Main targets (units) |
| :--- | ---: | ---: | :--- |
| Cincinnati Bell | 120 | 81,110 | Chicago `sp2` (109), Chicago `sp1` (96), Atlanta (58), Ashburn (34) |
| Frontier | 62 | 42,397 | Miami (20), Dallas (20), Los Angeles (18) |
| Verizon | 76 | 49,293 | New York `sp2` (60), New York `sp1` (55), Ashburn (34) |

Minor targets (a few units each): Cincinnati Bell (Seattle, New York), Frontier (Chicago, Ashburn, New York, San Jose), Verizon (Chicago, Ashburn `sp2`).

**Findings**

- **Units use several targets.** Units per target add up to more than the units per ISP (Cincinnati Bell: 300 target-unit pairs for 120 units; Verizon: 153 for 76; Frontier: 68 for 62). A unit's rows are split across targets: 68, 131, 45 and 14 units use 1, 2, 3 and 4 targets.
- **The target depends on where the unit is.** Frontier units use Miami, Dallas and Los Angeles; Cincinnati Bell units use Chicago, Atlanta and Ashburn; Verizon units use New York and Ashburn. RTT depends on distance to the server, so a single absolute latency threshold would mix **distance** with **congestion**. The server rule (D-04, D-06) addresses this by using one server per unit.
- **Mixing servers changes results.** In the 5 units with the largest difference, the median RTT between servers of the same unit differs by up to 52 ms (unit 24559133: Seattle 65.5 ms against about 13.7 ms for the other three). Pooling all servers changes the P95 latency by more than 1 ms in 38 units and by more than 3 ms in 22 units (`step_5.py`, UTC reading). The primary server holds on average 78.1% of a unit's peak records (median 77.7%, minimum 37.8%; 257 units with peak records, UTC reading; `step_2.py`).
- **The on-net / off-net distinction is not visible in the latency and jitter targets.** The MBA documentation says one on-net and one off-net node are tested hourly. Among the 10 most frequent latency and jitter targets, none identifies an ISP-hosted server. ISP-hosted names do appear in `curr_udpcloss` (check 5). Interpretation of `sp1` vs `sp2` is still open (section 5).

## 3. Implications for the Specification

| Topic | Implication | Decision |
| :--- | :--- | :--- |
| Analysis period | 50 days, Sept–Oct 2022 | Adopted: 2022-09-12 to 2022-10-31 (D-01) |
| `timezone_offset_dst` | Valid for the whole period | Not used in the base case: `dtime` behaves as local time, offsets only in the UTC sensitivity (D-03) |
| Latency metric | Distance to target affects absolute RTT | One server per unit (D-04, D-06). A baseline-adjusted latency (peak P95 minus the unit-target off-peak median) is not part of the v3 specification |
| `target` handling | Several targets per unit | Adopted: the primary server of the latency file for all metrics (D-04, D-06); all servers as sensitivity |
| Availability from `curr_udpcloss` | Missing rows mean "no events" | Optional future metric, outside `risk_flag` (spec section 5.1) |
| Duplicates and invalid records | See check 1 | Duplicate policy (D-05); invalid records excluded and counted, none found |

## 4. Checks

| # | Check | Status | Result |
| :--- | :--- | :--- | :--- |
| 1 | Duplicates on (`unit_id`, `dtime`, `target`); nulls; `successes + failures` distribution | **Done** | Duplicates: latency 16 rows in 7 groups, all exact (9 extra rows); jitter 10 rows, 8 exact and 2 conflicting (unit 943232) (`step_4.py`). Nulls or negatives: 0 in `rtt_avg`, `jitter_up` and `jitter_down`; `successes + failures <= 0`: 0; loss outside [0, 100]: 0 (`step_2.py`, `step_9.py`). `successes + failures` per row: min 50, P1 65, P5 231, median 2,065, P95 2,303, max 2,401, mean 1,737 (`step_9.py`), which supports the ratio of sums |
| 2 | Targets per unit, and whether each unit keeps the same targets over time | **Partial** | Targets per unit: 68, 131, 45 and 14 units use 1, 2, 3 and 4. Stability over time was not tested; the primary server is defined over the whole period |
| 3 | Median and P95 `rtt_avg` by target | **Partial** | No table by target. Server mixing was quantified per unit instead (section 2; `step_2.py`, `step_5.py`) |
| 4 | Mean relative RTT by hour using raw `dtime`, `dtime + timezone_offset` and `dtime + timezone_offset_dst` | **Done, inconclusive alone** | September only, all units pooled, the mean `rtt_avg` varies by at most 0.4 ms across hours under any reading (UTC 10.99–11.40, standard 11.02–11.36, DST 11.02–11.36 ms), so no reading shows a clear evening peak. The question was settled by comparing Eastern and Pacific profiles (`step_7.py`, `step_8.py`; D-03): `dtime` behaves as local time. The evidence is indirect |
| 5 | Targets in `curr_udpjitter.csv` and `curr_udpcloss.csv` for the 258 units | **Done** (10 most frequent targets) | Jitter: SamKnows-hosted servers only. Outage events (`curr_udpcloss`): also ISP-hosted servers (`samk01.lsan.ca.frontiernet.net` 762, `newyorkfcc.west.verizon.net` 610, `restonfcc.west.verizon.net` 321, `samk01.asbn.va.frontiernet.net` 205 of 4,919 rows) |
| 6 | Loss per unit (`sum(failures) / sum(successes + failures)`), all hours and peak hours | **Done for the peak window** | Global loss 0.022% (all hours); 8.1% of latency rows have `failures > 0` (`step_2.py`). Per unit, peak window, base case (237 analyzed): median 0.007%, P99 0.43%, maximum 1.66%; units above 0.05 / 0.1 / 0.5 / 1%: 18 / 10 / 2 / 1 (`step_9.py`). Per unit for all hours was not computed |
| 7 | Jitter unit confirmed from the distribution of `jitter_up` / `jitter_down` | **Supported, not proven** | Per-unit median jitter 0.70 ms against median `rtt_std` 0.96 ms (median ratio 0.83, Spearman 0.816, 258 units; `step_10.py`), consistent with microseconds. Raw medians: `jitter_up` 1,220, `jitter_down` 86, so the average of both mostly reflects upstream. No documentation states the unit |

## 5. Open Items

- **Check 2:** whether each unit keeps the same servers over time.
- **Check 3:** median and P95 `rtt_avg` by target, as a table.
- **`sp1` vs `sp2`:** meaning of the two servers per city (for example Chicago `sp1` and `sp2`), and whether any latency or jitter target is on-net.
- **Jitter test length:** the observed `duration` (about 15 s) differs from the documented 10 s.
- **Gaps by hour:** coverage over the 1,200 hours was not analyzed.