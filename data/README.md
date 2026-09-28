# Data Lineage & Inventory - FTTH QoE Risk Optimization v2.0

> **Project:** FTTH QoE Risk & Support Cost Optimization (Methodology v2.0 Bias-Corrected)  
> **Author:** Eng. Rafael Cansigno Peláez | September 2026  
> **Capstone Track:** Google Data Analytics | Track B (Self-directed)  
> **Dataset:** validated-data-sept2022.tar.gz + fiber_units.csv

This document describes the full data lineage, from raw source to analysis-ready tables. Required for reproducibility under Google Data Analytics Framework - Prepare Phase.

---

### 1. Raw Source - What You Actually Have

**Archive:** `validated-data-sept2022.tar.gz`
- **Compressed:** 6.8GB archive
- **Decompressed:** 6,812,728,506 bytes / 16 files
- **Source:** FCC MBA / SamKnows validated data - September 2022
- **Location (local, git-ignored):** `data/raw/validated-data-sept2022/`

#### Evidence 1: TAR content (6.8GB total)
![TAR content - 6.8GB decompressed](../docs/evidence/contenido_tar_6.8GB.png)
*File `validated-data-sept2022.tar.gz` shows total decompressed size 6,812,728,506 bytes. Largest files: curr_dns.csv 5,169,818,037 bytes (5GB), curr_webget.csv 856,272,747 bytes, curr_ping.csv 223,174,915 bytes.*

#### Evidence 2: Extracted file list (Explorer)
![Explorer view - validated-data-sept2022](../docs/evidence/validated-data-sept2022_filelist.png)
*Extracted folder `Capstone FFTH > validated-data-sept2022` contains 16 CSVs. Note *_t6.csv files are 1KB (empty IPv6 tests in this dump).*

#### Full Inventory:
| File | Size (KB from screenshot) | Description | Use in v2? |
| :--- | :--- | :--- | :--- |
| `curr_dlpinq.csv` | 64,926 | Download latency (ping) | NO |
| `curr_dns.csv` | 5,048,651 | DNS resolution time | **NO - 5GB, out of scope, not last-mile** |
| `curr_httpget.csv` | 1 | HTTP GET (IPv4) | NO - empty |
| `curr_httpgetmt.csv` | 39,281 | HTTP GET multithread | NO |
| `curr_httppost.csv` | 1 | HTTP POST | NO - empty |
| `curr_httppostmt.csv` | 38,196 | HTTP POST multithread | NO |
| `curr_ping.csv` | 217,945 | ICMP ping to test nodes | YES - baseline comparison |
| `curr_udpcloss.csv` | 79,550 | UDP packet loss % | YES - risk_flag secondary |
| `curr_udpjitter.csv` | 138,493 | UDP jitter ms | YES - QoE degradation |
| `curr_udplatency.csv` | 122,828 | **UDP latency ms - PRIMARY** | **YES - CORE for P95** |
| `curr_ulping.csv` | 66,831 | Upload latency | NO |
| `curr_webget.csv` | 836,204 | HTTP throughput / webget | NO - used incorrectly in v1 |
| `*_t6.csv` / `*6.csv` | 1 | IPv6 variants | NO - empty |

**Decision v2:** Primary input is `curr_udplatency.csv` (122MB) + `curr_udpcloss.csv` + `curr_udpjitter.csv`. `curr_dns.csv` (5GB) and `curr_webget.csv` (836MB) are explicitly excluded to avoid hardware CPU bottleneck confusion and size issues.

### 2. Population File - fiber_units.csv

This is your `units.csv` equivalent. Must be in `data/`.

**Expected schema (from FCC MBA):**
- `unit_id`: int, SamKnows Whitebox unique ID. Sequential by enrollment date, NOT random.
- `technology`: string, FIBER / DSL / CABLE
- `isp`: int/string, anonymized ISP (e.g., 4, 7)
- `advertised_down`: int, Mbps (50, 100, 300, 1000)
- `enrollment_date`: date, when Whitebox installed. Critical - encodes hardware version.
- `hardware_version`: string, SK-WB8, SK-WB8v2, SK-WB7 (legacy)

**v1 MISTAKE:** We read `curr_webget.csv` directly with `head(1000)`. Never joined `fiber_units.csv`. Result: first 1000 rows sorted by `unit_id` are the oldest whiteboxes (2012-2015) with obsolete CPU.

**v2 CORRECTION:** Pipeline ALWAYS starts from `fiber_units.csv`:
```python
fiber = pd.read_csv("data/fiber_units.csv", parse_dates=["enrollment_date"])
fiber_ftth = fiber.query("technology == 'FIBER' and enrollment_date >= '2018-01-01'")
# Expected: ~285 modern FTTH units
fiber_ftth.to_csv("data/methodology_v2_CORRECTED/sampling_manifest.csv", index=False)