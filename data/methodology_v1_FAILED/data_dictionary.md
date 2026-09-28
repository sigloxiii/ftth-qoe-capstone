# Data Dictionary - FCC Measuring Broadband America 2023-2024

**Source:** https://www.fcc.gov/general/measuring-broadband-america
**Validated Data:** https://data.fcc.gov/download/measuring-broadband-america/
**Size:** ~2.5GB+ per month raw, ~500MB validated tar.gz

### Filter Applied for this Capstone
`technology = FIBER` (FTTH)

### Key Columns Used

| Column | Type | Description |
| :--- | :--- | :--- |
| `unit_id` | int | Unique whitebox ID (household) |
| `dtime` | datetime | Test timestamp UTC, converted to local for peak flag |
| `target` | string | Test server hostname |
| `technology` | string | DSL, CABLE, FIBER - we filter FIBER |
| `download_kbps` | float | Download speed |
| `upload_kbps` | float | Upload speed |
| `rtt_avg_ms` | float | Average RTT latency - base for P95 |
| `rtt_95th_ms` | float | 95th percentile RTT (if precomputed) |
| `packet_loss_pct` | float | UDP packet loss % |
| `latency_under_load` | float | Latency during upload/download |

### Engineered Fields (FASE 3)
- `hour_local` = hour from dtime in local timezone
- `is_peak` = 1 if hour in [19,20,21,22,23]
- `risk_flag` = 1 if (P95_latency >80ms OR packet_loss >1.5%) AND is_peak=1

### Raw Files Not in Git
- `validated_data_2023.tar.gz` - contains `curr_httpgetmt.csv`, `curr_udp_latency.csv`, `curr_udp_packetloss.csv`
- Raw files excluded via .gitignore due to size.

License: Data Public Domain, Code MIT.
