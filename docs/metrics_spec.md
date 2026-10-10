# Data Dictionary — FCC MBA Files Used in This Project

**Version:** 1.1.0 · **Last reviewed:** 2026-10-10
**Purpose:** Document what each column of each input file means, based on the official FCC documentation, and record what has been verified against the real files (Step 0 in `docs/metrics_spec.md`).

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
| `dtime` | Time test finished | UTC (documented) | Peak window (with offset). **Not independently verified**, see section 4 |
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
| `dtime` | Time test finished | UTC (documented) | Peak window (with offset). **Not independently verified**, see section 4 |
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
| `timezone_offset` | UTC offset in hours (standard time) | **Verified:** consistent with `State`. Not used for this period (section 4) |
| `timezone_offset_dst` | UTC offset in hours during daylight saving time | **Verified:** consistent with `State`. Used for every record (section 4) |
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

`dtime` is stored as a plain timestamp (`YYYY-MM-DD HH:MM:SS`) with no time zone marker. The FCC documentation states that it is in UTC. Local time is derived by adding the unit's UTC offset, which is stored in the unit profile.

### 4.1 Time-related columns

| Column | Source | Meaning | Notes |
| :--- | :--- | :--- | :--- |
| `dtime` | `curr_udplatency`, `curr_udpjitter` | Time the test finished | UTC per the FCC general note; not independently verified |
| `dtime` | `curr_udpcloss` | Time the test finished | Described as local time in the FCC dictionary (contradicts the general note); not used in the base risk flag |
| `ddate` | the three files above | Date of the test | In the previewed rows it equals the date part of `dtime`; not used |
| `timezone_offset` | `fiber_units.csv` | Hours from UTC in standard time | Not used for this period |
| `timezone_offset_dst` | `fiber_units.csv` | Hours from UTC during daylight saving time | Used for every record |

### 4.2 How to read the offsets

Offsets are constants per unit, expressed in hours relative to UTC. A negative sign means local time is behind UTC.

Example: a unit with `timezone_offset = -5` and `timezone_offset_dst = -4` is in the Eastern time zone.

- `-5`: standard time (EST, UTC−5), in winter.
- `-4`: daylight saving time (EDT, UTC−4), in summer.

Time zones in the FTTH population (258 units):

| Time zone | `timezone_offset` | `timezone_offset_dst` | Units |
| :--- | ---: | ---: | ---: |
| Eastern | -5 | -4 | 220 |
| Central | -6 | -5 | 20 |
| Pacific | -8 | -7 | 18 |

All 258 units are in states that observe daylight saving time.

### 4.3 Which offset is used

The data covers 2022-09-12 to 2022-10-31. Daylight saving time in the United States ended on 2022-11-06, after the last record. Therefore `timezone_offset_dst` applies to every record, and `timezone_offset` is not used. Using the standard offset would shift every timestamp by one hour.

### 4.4 Conversion rule

```python
# dtime is a naive timestamp interpreted as UTC
df["local_time"] = df["dtime"] + pd.to_timedelta(df["timezone_offset_dst"], unit="h")
df["local_hour"] = df["local_time"].dt.hour
peak = df[(df["local_hour"] >= 19) & (df["local_hour"] < 23)]  # peak window [19, 23)
```

Because the offset is negative, the conversion subtracts hours, and the calendar date can change.

| `dtime` (UTC) | `timezone_offset_dst` | Local time | In peak window? |
| :--- | ---: | :--- | :--- |
| 2022-10-06 22:35:03 | -4 | 2022-10-06 18:35:03 | No |
| 2022-10-07 01:10:00 | -4 | 2022-10-06 21:10:00 | Yes (previous calendar day) |

### 4.5 Verification status and limitations

- **Verified:** the offsets are consistent with each unit's state, and no unit is in a state without daylight saving time.
- **Not verified:** that `dtime` is UTC in `curr_udplatency` and `curr_udpjitter`. Mean RTT by hour (10.99 to 11.40 ms) and test counts by hour (6,979 to 7,501 per hour) are nearly flat for FTTH units, so they cannot distinguish UTC from local time. The convention follows the FCC documentation.
- **Mitigation:** a sensitivity check recomputes `risk_flag` treating `dtime` as local time and reports how many units change flag.
- **`curr_udpcloss`:** its time zone is ambiguous in the source. The file is excluded from the base risk flag.
- **Window edges:** `dtime` marks the end of each test. The test duration is not documented in the sources reviewed, so records near 19:00 and 23:00 may partly belong to the adjacent hour.

---

## 5. Implications for the Pipeline

1. **Loss** comes only from `curr_udplatency` as `sum(failures) / sum(successes + failures) × 100`. Summing counts (instead of averaging hourly percentages) weights each hour by the packets actually sent, which matters because the number of packets varies.
2. **`curr_udpcloss` is an outage table**, not a loss-percentage table. The earlier `packets/10` conversion has no basis in the documentation.
3. **Jitter units:** the values in the first rows are consistent with microseconds (0.2 to 55.7 ms after conversion), but this is not proven. Confirm before the final conversion to milliseconds.
4. **`target`:** FTTH units use between 1 and 4 distinct servers. Computing a single P95 per unit across servers at different distances could blend different paths. Quantification pending (check 5).
5. **`latency` in the jitter file** is a P99 of a different test and must not be mixed with `rtt_avg`.
6. **`dtime` in `curr_udpcloss`** may be local time. If that file is used for an availability metric, its time handling is different from the other two files.
7. **Date range:** the files cover 2022-09-12 to 2022-10-31. The analysis period must be stated explicitly in the metrics specification.

## 6. Verification Checklist (Step 0)

Detailed results are recorded in `docs/data_inspection.md`.

| # | Check | How | Result |
| :--- | :--- | :--- | :--- |
| 1 | Headers match this dictionary in all 3 files | Print header and rows of each file (`data/CSV_previews.md`) | **Done.** Differences: `ddate` present in all three files (not listed for latency and jitter); `location_id` absent in `curr_udplatency`; jitter header uses lowercase `latency` |
| 2 | Jitter unit | Compare magnitude of `jitter_up/down` and `rtt_avg` | **Partial.** Values 218 to 55,714 give 0.2 to 55.7 ms if µs (plausible, not proven). `duration` ≈ 15 s versus the documented 10 s is an open discrepancy |
| 3 | `dtime` format and time zone | Check offset suffix in the string; compare with `curr_udpcloss` | **Format verified:** `YYYY-MM-DD HH:MM:SS`, no offset suffix. The time zone cannot be read from the string (section 4) |
| 4 | `timezone_offset_dst` correctness | Compare offsets with `State`; mean `rtt_avg` and test counts by hour | **Offsets verified** (consistent with state, no non-DST units). UTC versus local `dtime` is not distinguishable with this data; sensitivity check planned |
| 5 | `target` values | List distinct targets and rows per unit and target; compare latency by target | **Partial.** About 10 servers; 1 to 4 per unit; median RTT per unit 2.5 to 17.2 ms. Servers appear assigned by proximity (CA and TX near 4 ms, OH 13.6 ms). Mixing within a unit pending |
| 6 | Packets per hour | Distribution of `successes + failures` per row | **Pending.** In the first rows of `curr_udplatency` it ranges from 131 to 2,365 |
| 7 | Units without data | Count the 258 population units missing from each file | **Done.** Latency 258/258, jitter 258/258, `curr_udpcloss` 242/258 (event-based, expected) |
| 8 | Date range of `dtime` | Minimum and maximum per file | **Done.** 2022-09-12 to 2022-10-31 (section 3) |

## 7. Limitations of This Review

- The Technical Appendix text was read up to about 100,000 of 118,000 characters; the data dictionary was within the part read, but the unit-profile field list was not found.
- The dictionary describes the files in the 2023 release; local headers may differ (see check 1).
- The first-rows previews (`data/CSV_previews.md`) contain no FTTH units. They show structure only; FTTH-specific checks use the filtered data.
- The time zone of `dtime` and the jitter units cannot be proven with the available data and follow the FCC documentation or the most plausible reading.

## 8. Sources

- FCC. *Technical Appendix – Fixed Broadband, 2023* (data dictionary, test schedule, loss definition): https://data.fcc.gov/download/measuring-broadband-america/2023/Technical-Appendix-fixed-2023.pdf
- FCC. *2023 Fixed Measuring Broadband America Report* (packet loss definition, 3-second rule, latency test volume): https://data.fcc.gov/download/measuring-broadband-america/2023/2023-Fixed-Measuring-Broadband-America-Report.pdf
- FCC. *Raw data releases – Measuring Broadband America* (data provided "as is"): https://www.fcc.gov/oet/mba/raw-data-releases