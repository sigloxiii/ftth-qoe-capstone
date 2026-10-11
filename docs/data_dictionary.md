# Data Dictionary — FCC MBA Files Used in This Project

**Version:** 1.2.0 · **Last reviewed:** 2026-10-10
**Purpose:** Document what each column of each input file means, based on the official FCC documentation, and record what has been verified against the real files (Step 0 in `docs/metrics_spec.md`).

**Changes in 1.2.0:** `dtime` is now treated as local time (decision D-03, see `docs/decisions.md`); section 4 rewritten, checks 3 and 4 closed, UTC reading kept as a sensitivity.

**Changes in 1.1.0:** Step 0 results incorporated. Real headers compared with the FCC dictionary, time handling documented (new section 4), observed coverage for the 258 FTTH units added, verification checklist updated.

**How to read the status labels**

- **Documented:** stated in the FCC Technical Appendix data dictionary (see Sources).
- **Verified:** confirmed in the real files or in the project data (see section 6).
- **Pending:** not stated or ambiguous in the documentation; must be verified in the actual file before being used.

> The dictionary below comes from the *Technical Appendix – Fixed Broadband 2023*, which accompanies the data release that includes the September 2022 files. The headers of the local files were compared with it (check 1 in section 6).

---

## 1. Files Overview

| File | Content | Test schedule (documented) | Use in v3 |
| :--- | :--- | :--- | :--- |
| `curr_udplatency.csv` | UDP round-trip time and packet loss | Hourly, 24×7, one on-net and one off-net node; ~2,000 packets per hour (fewer if the line is not idle) | **Latency and loss** |
| `curr_udpjitter.csv` | UDP jitter (VoIP-style stream) | Hourly, 24×7, one on-net and one off-net node; 10 s at 64 kbps | **Jitter** |
| `curr_udpcloss.csv` | Outage / disconnection events | Event-based (a row exists only when an event occurred) | Not used for loss. Optional future availability metric |
| `unit-profile-sept2022.xlsx` | Unit metadata (ISP, state, tier, Whitebox model) | n/a | **Population definition** |

The other 13 files in the archive (DNS, web get, HTTP, ping, download/upload ping, IPv6 variants) are out of scope.

---

## 2. Field Definitions

### 2.1 `curr_udplatency.csv`

| Field | Official definition | Unit | Use in v3 |
| :--- | :--- | :--- | :--- |
| `unit_id` | Unique identifier for an individual unit | int | Join key |
| `dtime` | Time test finished | UTC (documented); **behaves as local time** in the data | Peak window = `hour(dtime)`, no offset (decision D-03, section 4) |
| `ddate` | Not listed in the dictionary; present in the real header | date | Not used. In the previewed rows it equals the date part of `dtime` |
| `target` | Target hostname or IP address | text | **Pending:** server mixing within a unit (check 5) |
| `rtt_avg` | Average RTT | µs | `p95_latency_ms` = P95 of `rtt_avg / 1000` |
| `rtt_min` | Minimum RTT | µs | Not used |
| `rtt_max` | Maximum RTT | µs | Not used |
| `rtt_std` | Standard deviation in measured RTT | µs | Not used |
| `successes` | Number of successes | count | Loss denominator |
| `failures` | Number of failures (packets lost) | count | Loss numerator |
| `location_id` | Internal key mapping to unit profile data. The dictionary says to ignore it | n/a | **Verified:** not present in the real header; ignored |

**Packet loss (documented formula):** `failures / (successes + failures)`.
A packet is counted as lost if no response arrives within 3 seconds.

### 2.2 `curr_udpjitter.csv`

| Field | Official definition | Unit | Use in v3 |
| :--- | :--- | :--- | :--- |
| `unit_id` | Unique identifier for an individual unit | int | Join key |
| `dtime` | Time test finished | UTC (documented); **behaves as local time** in the data | Peak window = `hour(dtime)`, no offset (decision D-03, section 4) |
| `ddate` | Not listed in the dictionary; present in the real header | date | Not used. In the previewed rows it equals the date part of `dtime` |
| `target` | Target hostname or IP address | text | **Pending:** server mixing within a unit (check 5) |
| `packet_size` | Size of each UDP datagram | bytes | Not used |
| `stream_rate` | Rate at which the UDP stream is generated | bits/s | Not used |
| `duration` | Total duration of test | µs (general rule); preview shows ≈ 15 s | Not used. **Pending:** the documented test length is 10 s |
| `packets_up_sent` | Packets sent upstream (measured by client) | count | Not used |
| `packets_down_sent` | Packets sent downstream (measured by server) | count | Not used |
| `packets_up_recv` | Packets received upstream (measured by server) | count | Not used |
| `packets_down_recv` | Packets received downstream (measured by client) | count | Not used |
| `jitter_up` | Upstream jitter measured | Not stated; values consistent with µs | `p95_jitter_ms` input. **Pending:** unit not proven |
| `jitter_down` | Downstream jitter measured | Not stated; values consistent with µs | `p95_jitter_ms` input. **Pending:** unit not proven |
| `latency` | 99th percentile of round trip times for all packets (the dictionary writes `Latency`; the real header is lowercase) | µs (general rule) | Not used; **not equivalent to `rtt_avg`** |
| `successes` | Number of successes (always 1 or 0 for this test) | 0/1 | Not usable as a loss count. Preview shows 1 in all rows |
| `failures` | Number of failures (always 1 or 0 for this test) | 0/1 | Not usable as a loss count. Preview shows 0 in all rows |

### 2.3 `curr_udpcloss.csv`

| Field | Official definition | Unit | Use in v3 |
| :--- | :--- | :--- | :--- |
| `unit_id` | Unique identifier for an individual unit | int | Join key |
| `dtime` | Time test finished **in local time** | local (contradicts the general UTC note) | **Pending:** verify before any time filtering. See section 4 |
| `ddate` | Date test finished in local time | local date | Not used |
| `duration` | Duration of the outage/disconnection event | µs | Optional availability metric. Preview shows ≈ 4.5 s per event |
| `target` | Hostname the outage was experienced to | text | Not used |
| `address` | IP address of the host the outage was experienced to | IP | Not used |
| `packets` | The number of packets we lost | **count per event** | **Not a percentage.** Not used for loss |

No loss formula is defined for this file.

### 2.4 `unit-profile-sept2022.xlsx` (and `fiber_units.csv`)

The data dictionary in the Technical Appendix does **not** define the unit-profile fields; it only states that the file "identifies the various details of each test unit." The meanings below come from the column names. The status shows what has been confirmed in the project data.

| Field | Meaning (inferred from name) | Status |
| :--- | :--- | :--- |
| `Unit ID` | Whitebox identifier; joins to `unit_id` | **Verified:** all 258 FTTH units have rows in `curr_udplatency` and `curr_udpjitter` |
| `ISP` | Internet service provider | Pending |
| `Technology` | Access technology (we keep `Fiber`) | Pending |
| `State` | US state | **Verified:** consistent with the time zone offsets of every unit |
| `Census` | Census region | Pending |
| `timezone_offset` | UTC offset in hours (standard time) | **Verified:** consistent with `State`. Not used (section 4) |
| `timezone_offset_dst` | UTC offset in hours during daylight saving time | **Verified:** consistent with `State`. Used only in the UTC-reading sensitivity (section 4) |
| `Download` / `Upload` | Provisioned tier, Mbps | Pending |
| `Whitebox Model` | Measurement device model | Pending |

---

## 3. Cross-File Notes

**Documented**

- **Time zone:** "All dtime entries are in the UTC timezone." The `curr_udpcloss.csv` entry describes `dtime` as local time, which contradicts that note.
- **Units:** "All durations are in microseconds unless otherwise noted." Jitter units are not explicitly stated.
- **Loss source:** the appendix maps UDP packet loss to `curr_udplatency.csv`, not to `curr_udpcloss.csv`.
- **Targets:** each test runs against one on-net and one off-net node, so a unit can have rows for two different target types per hour.
- **Variable sample size:** the latency test sends fewer packets when the line is not idle, so `successes + failures` varies by hour.

**Observed coverage for the 258 FTTH units (Step 0)**

| File | FTTH rows | Units with data | `dtime` range |
| :--- | ---: | ---: | :--- |
| `curr_udplatency.csv` | 172,800 | 258 / 258 | 2022-09-12 00:00:05 – 2022-10-31 23:59:58 |
| `curr_udpjitter.csv` | 152,730 | 258 / 258 | 2022-09-12 00:00:16 – 2022-10-31 23:59:42 |
| `curr_udpcloss.csv` | 4,919 | 242 / 258 | 2022-09-12 00:10:17 – 2022-10-31 23:49:37 |

- The files cover 50 days, **not only September**. In `curr_udplatency`, September has 46,205 rows (27%) and October 126,595 (73%).
- Rows per unit (median / min / max): `curr_udplatency` 722 / 7 / 769; `curr_udpjitter` 642.5 / 35 / 720; `curr_udpcloss` 6 / 1 / 874 (units with at least one event).
- `curr_udpcloss` is event-based: a unit with no outage events has no rows. The 16 units without rows are expected, not missing data.
- `curr_udplatency` has about 10 distinct target servers for FTTH units, and each unit uses between 1 and 4 of them (68, 131, 45 and 14 units use 1, 2, 3 and 4 servers).

---

## 4. Time Handling

`dtime` is stored as a plain timestamp (`YYYY-MM-DD HH:MM:SS`) with no time zone marker. The FCC documentation states that it is UTC, but the project data shows it behaves as each unit's **local time**. **Decision D-03:** the peak window is computed directly on `hour(dtime)`, with no offset added. The UTC reading is kept as a sensitivity analysis.

### 4.1 Time-related columns

| Column | Source | Meaning | Notes |
| :--- | :--- | :--- | :--- |
| `dtime` | `curr_udplatency`, `curr_udpjitter` | Time the test finished | FCC says UTC; data behaves as local time (section 4.5). **Treated as local** |
| `dtime` | `curr_udpcloss` | Time the test finished | Described as local in the FCC dictionary; not used in the base risk flag |
| `ddate` | the three files above | Date of the test | In the previewed rows it equals the date part of `dtime`; not used |
| `timezone_offset` | `fiber_units.csv` | Hours from UTC in standard time | Not used |
| `timezone_offset_dst` | `fiber_units.csv` | Hours from UTC during daylight saving time | Used only in the UTC-reading sensitivity |

### 4.2 How to read the offsets

Offsets are constants per unit, in hours relative to UTC. A negative sign means local time is behind UTC. Example: `timezone_offset = -5` and `timezone_offset_dst = -4` is Eastern time (EST UTC−5 in winter, EDT UTC−4 in summer).

| Time zone | `timezone_offset` | `timezone_offset_dst` | Units |
| :--- | ---: | ---: | ---: |
| Eastern | -5 | -4 | 220 |
| Central | -6 | -5 | 20 |
| Pacific | -8 | -7 | 18 |

All 258 units are in states that observe daylight saving time. US daylight saving time ended on 2022-11-06, after the last record (2022-10-31), so `timezone_offset_dst` is the only offset that would apply to this period.

### 4.3 Base case rule (local reading)

```python
# dtime is a naive timestamp that already is the unit's local time
df["local_hour"] = df["dtime"].dt.hour
peak = df[(df["local_hour"] >= 19) & (df["local_hour"] < 23)]  # peak window [19, 23)
```

No offset is applied, so the calendar date does not change.

### 4.4 Sensitivity rule (UTC reading, FCC documentation)

```python
# dtime read as UTC; convert with the DST offset (applies to every record)
local_time = df["dtime"] + pd.to_timedelta(df["timezone_offset_dst"], unit="h")
df["local_hour"] = local_time.dt.hour
```

With the server rule `primary_only`, the base case flags 10 units and the UTC reading flags 6. Six units change flag (943226, 1006958, 3798765, 4190285, 24840041, 25314149): 5 are flagged only under the local reading and 1 only under the UTC reading.

### 4.5 Evidence for the local reading

The test compares the mean hourly RTT profile (by `dtime` hour) of Eastern units against Pacific units, shifting the Pacific profile by k hours (`step_8.py`, by technology). If `dtime` were UTC, the Pacific profile (UTC−7) would trail the Eastern one (UTC−4) by k = +3. If it were local, k = 0.

| Technology | Correlation k=0 (local) | Correlation k=+3 (UTC) | Best k | Peak hour, Eastern / Pacific |
| :--- | ---: | ---: | ---: | :--- |
| Cable | 0.762 | −0.107 | −1 (0.892) | 21 / 20 |
| DSL | 0.594 | −0.018 | −2 (0.799) | 21 / 19 |

- UTC is rejected: the correlation at k=+3 is about 0 or negative in both technologies.
- The best shift (−1 to −2 h) is far closer to 0 than to +3. The residual lead of the Pacific profile is not a time zone offset; it most likely reflects usage behavior or population composition (few Pacific observations).
- Fiber was not tested: only 18 Pacific units, too few for a profile.
- Earlier (step_2, all technologies pooled and FTTH only) the mean RTT by hour was nearly flat, so it could not discriminate. The conclusion rests on Cable and DSL.

### 4.6 Verification status and limitations

- **Verified:** the offsets are consistent with each unit's state, and no unit is in a state without daylight saving time.
- **Indirect evidence only:** the local reading is inferred from behavior, not proven. It contradicts the FCC general note, so the UTC reading is reported as a sensitivity with every result.
- **`curr_udpcloss`:** its time zone is ambiguous in the source. The file is excluded from the base risk flag.
- **Window edges:** `dtime` marks the end of each test. The test duration is not documented in the sources reviewed, so records near 19:00 and 23:00 may partly belong to the adjacent hour.

---

## 5. Implications for the Pipeline

1. **Loss** comes only from `curr_udplatency` as `sum(failures) / sum(successes + failures) × 100`. Summing counts (instead of averaging hourly percentages) weights each hour by the packets actually sent, which matters because the number of packets varies.
2. **`curr_udpcloss` is an outage table**, not a loss-percentage table. The earlier `packets/10` conversion has no basis in the documentation.
3. **Jitter units:** the values in the first rows are consistent with microseconds (0.2 to 55.7 ms after conversion), but this is not proven. Confirm before the final conversion to milliseconds.
4. **`target`:** FTTH units use between 1 and 4 distinct servers. Computing a single P95 per unit across servers at different distances could blend different paths. Quantified in check 5: all servers flag 17 units, primary server only flags 6 (decision D-04: `primary_only`).
5. **`latency` in the jitter file** is a P99 of a different test and must not be mixed with `rtt_avg`.
6. **`dtime` in `curr_udpcloss`** is described as local time by the FCC. Since the other two files are now also treated as local, no special handling is expected if that file is used for an availability metric.
7. **Date range:** the files cover 2022-09-12 to 2022-10-31. The analysis period must be stated explicitly in the metrics specification.

## 6. Verification Checklist (Step 0)

Detailed results are recorded in `docs/data_inspection.md`.

| # | Check | How | Result |
| :--- | :--- | :--- | :--- |
| 1 | Headers match this dictionary in all 3 files | Print header and rows of each file (`data/CSV_previews.md`) | **Done.** Differences: `ddate` present in all three files (not listed for latency and jitter); `location_id` absent in `curr_udplatency`; jitter header uses lowercase `latency` |
| 2 | Jitter unit | Compare magnitude of `jitter_up/down` and `rtt_avg` | **Partial.** Values 218 to 55,714 give 0.2 to 55.7 ms if µs (plausible, not proven). `duration` ≈ 15 s versus the documented 10 s is an open discrepancy |
| 3 | `dtime` format and time zone | Check offset suffix in the string; compare Eastern and Pacific hourly profiles | **Closed.** Format `YYYY-MM-DD HH:MM:SS`, no suffix. Behavior indicates local time, not UTC (section 4.5). Decision D-03 |
| 4 | `timezone_offset_dst` correctness | Compare offsets with `State` | **Done.** Offsets consistent with state, no non-DST units. Kept for the UTC-reading sensitivity |
| 5 | `target` values | List distinct targets and rows per unit and target; compare latency by target | **Done.** About 10 servers; 1 to 4 per unit; median RTT per unit 2.5 to 17.2 ms. Servers assigned by proximity. Mixing impact: 17 units flagged with all servers vs 6 with primary only. Decision D-04 |
| 6 | Packets per hour | Distribution of `successes + failures` per row | **Pending.** In the first rows of `curr_udplatency` it ranges from 131 to 2,365 |
| 7 | Units without data | Count the 258 population units missing from each file | **Done.** Latency 258/258, jitter 258/258, `curr_udpcloss` 242/258 (event-based, expected) |
| 8 | Date range of `dtime` | Minimum and maximum per file | **Done.** 2022-09-12 to 2022-10-31 (section 3) |

## 7. Limitations of This Review

- The Technical Appendix text was read up to about 100,000 of 118,000 characters; the data dictionary was within the part read, but the unit-profile field list was not found.
- The dictionary describes the files in the 2023 release; local headers may differ (see check 1).
- The first-rows previews (`data/CSV_previews.md`) contain no FTTH units. They show structure only; FTTH-specific checks use the filtered data.
- The time zone of `dtime` (local) is inferred from behavior and contradicts the FCC note; the jitter units cannot be proven and follow the most plausible reading.

## 8. Sources

- FCC. *Technical Appendix – Fixed Broadband, 2023* (data dictionary, test schedule, loss definition): https://data.fcc.gov/download/measuring-broadband-america/2023/Technical-Appendix-fixed-2023.pdf
- FCC. *2023 Fixed Measuring Broadband America Report* (packet loss definition, 3-second rule, latency test volume): https://data.fcc.gov/download/measuring-broadband-america/2023/2023-Fixed-Measuring-Broadband-America-Report.pdf
- FCC. *Raw data releases – Measuring Broadband America* (data provided "as is"): https://www.fcc.gov/oet/mba/raw-data-releases
