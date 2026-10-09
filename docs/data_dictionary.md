# Data Dictionary — FCC MBA Files Used in This Project

**Version:** 1.0.0 · **Last reviewed:** 2026-10-08
**Purpose:** Document what each column of each input file means, based on the official FCC documentation, and list what still has to be verified against the real files (Step 0 in `docs/metrics_spec.md`).

**How to read the status labels**

- **Documented:** stated in the FCC Technical Appendix data dictionary (see Sources).
- **Pending:** not stated or ambiguous in the documentation; must be verified in the actual file before being used.

> The dictionary below comes from the *Technical Appendix – Fixed Broadband 2023*, which accompanies the data release that includes the September 2022 files. Confirm that the headers of the local files match it (check 1 in section 5).

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
| `dtime` | Time test finished | UTC | Peak window (with offset) |
| `target` | Target hostname or IP address | text | **Pending:** on-net vs off-net handling (check 5) |
| `rtt_avg` | Average RTT | µs | `p95_latency_ms` = P95 of `rtt_avg / 1000` |
| `rtt_min` | Minimum RTT | µs | Not used |
| `rtt_max` | Maximum RTT | µs | Not used |
| `rtt_std` | Standard deviation in measured RTT | µs | Not used |
| `successes` | Number of successes | count | Loss denominator |
| `failures` | Number of failures (packets lost) | count | Loss numerator |
| `location_id` | Internal key mapping to unit profile data. The dictionary says to ignore it | n/a | Ignored |

**Packet loss (documented formula):** `failures / (successes + failures)`.
A packet is counted as lost if no response arrives within 3 seconds.

### 2.2 `curr_udpjitter.csv`

| Field | Official definition | Unit | Use in v3 |
| :--- | :--- | :--- | :--- |
| `unit_id` | Unique identifier for an individual unit | int | Join key |
| `dtime` | Time test finished | UTC | Peak window (with offset) |
| `target` | Target hostname or IP address | text | **Pending:** on-net vs off-net |
| `packet_size` | Size of each UDP datagram | bytes | Not used |
| `stream_rate` | Rate at which the UDP stream is generated | bits/s | Not used |
| `duration` | Total duration of test | **Pending** (general rule: µs) | Not used |
| `packets_up_sent` | Packets sent upstream (measured by client) | count | Not used |
| `packets_down_sent` | Packets sent downstream (measured by server) | count | Not used |
| `packets_up_recv` | Packets received upstream (measured by server) | count | Not used |
| `packets_down_recv` | Packets received downstream (measured by client) | count | Not used |
| `jitter_up` | Upstream jitter measured | **Pending** (not stated; general rule: µs) | `p95_jitter_ms` input |
| `jitter_down` | Downstream jitter measured | **Pending** (not stated; general rule: µs) | `p95_jitter_ms` input |
| `Latency` | 99th percentile of round trip times for all packets | **Pending** (general rule: µs) | Not used; **not equivalent to `rtt_avg`** |
| `successes` | Number of successes (always 1 or 0 for this test) | 0/1 | Not usable as a loss count |
| `failures` | Number of failures (always 1 or 0 for this test) | 0/1 | Not usable as a loss count |

### 2.3 `curr_udpcloss.csv`

| Field | Official definition | Unit | Use in v3 |
| :--- | :--- | :--- | :--- |
| `unit_id` | Unique identifier for an individual unit | int | Join key |
| `dtime` | Time test finished **in local time** | local (contradicts the general UTC note) | **Pending:** verify before any time filtering |
| `ddate` | Date test finished in local time | local date | Not used |
| `duration` | Duration of the outage/disconnection event | µs | Optional availability metric |
| `target` | Hostname the outage was experienced to | text | Not used |
| `address` | IP address of the host the outage was experienced to | IP | Not used |
| `packets` | The number of packets we lost | **count per event** | **Not a percentage.** Not used for loss |

No loss formula is defined for this file.

### 2.4 `unit-profile-sept2022.xlsx` (and `fiber_units.csv`)

The data dictionary in the Technical Appendix does **not** define the unit-profile fields; it only states that the file "identifies the various details of each test unit." The meanings below come from the column names and are **Pending** until confirmed in the file or in other FCC documentation.

| Field | Meaning (inferred from name) | Status |
| :--- | :--- | :--- |
| `Unit ID` | Whitebox identifier; joins to `unit_id` | Pending |
| `ISP` | Internet service provider | Pending |
| `Technology` | Access technology (we keep `Fiber`) | Pending |
| `State` | US state | Pending |
| `Census` | Census region | Pending |
| `timezone_offset` | UTC offset in hours (standard time) | Pending |
| `timezone_offset_dst` | UTC offset in hours during daylight saving time | **Pending, critical** (check 4) |
| `Download` / `Upload` | Provisioned tier, Mbps | Pending |
| `Whitebox Model` | Measurement device model | Pending |

---

## 3. Cross-File Notes (Documented)

- **Time zone:** "All dtime entries are in the UTC timezone." The `curr_udpcloss.csv` entry describes `dtime` as local time, which contradicts that note.
- **Units:** "All durations are in microseconds unless otherwise noted." Jitter units are not explicitly stated.
- **Loss source:** the appendix maps UDP packet loss to `curr_udplatency.csv`, not to `curr_udpcloss.csv`.
- **Targets:** each test runs against one on-net and one off-net node, so a unit can have rows for two different target types per hour.
- **Variable sample size:** the latency test sends fewer packets when the line is not idle, so `successes + failures` varies by hour.

## 4. Implications for the Pipeline

1. **Loss** comes only from `curr_udplatency` as `sum(failures) / sum(successes + failures) × 100`. Summing counts (instead of averaging hourly percentages) weights each hour by the packets actually sent, which matters because the number of packets varies.
2. **`curr_udpcloss` is an outage table**, not a loss-percentage table. The earlier `packets/10` conversion has no basis in the documentation.
3. **Jitter units** must be confirmed from the magnitude of the values before converting to milliseconds.
4. **`target`** may mix two types of measurement servers. Computing a single P95 across both without checking could blend different paths. Decision pending (check 5).
5. **`Latency` in the jitter file** is a P99 of a different test and must not be mixed with `rtt_avg`.
6. **`dtime` in `curr_udpcloss`** may be local time. If that file is used for an availability metric, its time handling is different from the other two files.

## 5. Verification Checklist (Step 0)

Record results in `docs/data_inspection.md`.

| # | Check | How | Result |
| :--- | :--- | :--- | :--- |
| 1 | Headers match this dictionary in all 3 files | Print header and 5 rows of each file | Pending |
| 2 | Jitter unit | Compare magnitude of `jitter_up/down` and `rtt_avg`; check that µs-to-ms gives plausible values | Pending |
| 3 | `dtime` format and time zone | Check offset suffix in the string; compare with `curr_udpcloss` | Pending |
| 4 | `timezone_offset_dst` correctness | Plot mean `rtt_avg` by local hour using `timezone_offset` vs `timezone_offset_dst`; compare evening pattern. Check units in states without daylight saving time | Pending |
| 5 | `target` values | List distinct targets and rows per unit and target; compare latency by target | Pending |
| 6 | Packets per hour | Distribution of `successes + failures` per row | Pending |
| 7 | Units without data | Count the 258 population units missing from each file | Pending |

## 6. Limitations of This Review

- The Technical Appendix text was read up to about 100,000 of 118,000 characters; the data dictionary was within the part read, but the unit-profile field list was not found.
- The dictionary describes the files in the 2023 release; local headers may differ.
- The `curr_udpcloss` time zone and the jitter units are ambiguous in the source and are treated as unknown until verified.

## 7. Sources

- FCC. *Technical Appendix – Fixed Broadband, 2023* (data dictionary, test schedule, loss definition): https://data.fcc.gov/download/measuring-broadband-america/2023/Technical-Appendix-fixed-2023.pdf
- FCC. *2023 Fixed Measuring Broadband America Report* (packet loss definition, 3-second rule, latency test volume): https://data.fcc.gov/download/measuring-broadband-america/2023/2023-Fixed-Measuring-Broadband-America-Report.pdf
- FCC. *Raw data releases – Measuring Broadband America* (data provided "as is"): https://www.fcc.gov/oet/mba/raw-data-releases