# Data Source - FCC Measuring Broadband America

## Primary Source
**Program:** FCC Measuring Broadband America (MBA) - 13th Report
**Dataset:** Validated Data - September 2022 (last available)
**URL:** https://data.fcc.[STRIPPED 81 bytes].tar.gz
**Access Date:** May 13, 2026
**License:** Public Domain - U.S. Government Work
**Original Size:** 1.39 GB compressed / 6,812,728,506 bytes uncompressed (16 CSVs)

## What is Validated Data?
FCC validates tiers with ISPs and removes outliers. Cleansing documented by FCC:
- Time translated UTC -> local per unit_timezones.csv
- Tests with <50 samples/hour removed
- Packet loss >10% removed as anomalous
- RTT <0.5ms removed

## Files Used for FTTH QoE Risk Capstone
| File | Original Size | Lines | Role | Sample in repo |
|---|---|---|---|---|
| curr_ping.csv | 223 MB | 2,335,270 | packet_loss calculation | sample1000_curr_ping.csv 166KB |
| curr_udplatency.csv | 125 MB | 1,263,341 | rtt_avg and P95 | sample1000_udplatency.csv 191KB |
| curr_httpgetmt.csv | 40 MB | 280,042 | throughput SLA >300Mbps | sample1000_httpgetmt.csv 285KB |

Files discarded: curr_dns.csv (5.1 GB) - not relevant for churn.

## Secondary Processing - Fiber Filter
**File:** unit-profile-sept2022.xlsx (88KB) from FCC portal
**Process:** Excel filter Technology CONTAINS "Fiber" -> 285 units FTTH
**Evidence:** docs/excel_filter.png
**Output:** data/processed/fiber_units.csv (107 KB) - Key: unit_id for join

## Sampling Strategy for GitHub
Full dataset exceeds GitHub 100MB limit. Strategy:
1. Stream validation without extraction: `tar -tzf` and `tar -xOzf | Select-Object -First 1` in PowerShell (Windows 11) - evidence in docs/
2. Versionable sample 1000 rows ( <300KB ) per CSV for prototyping risk_flag
3. Local processing of 500k rows via SSMS Import Wizard in D:\Capstone FFTH\ for P95 calculation - scalable to full 6.8GB
4. Sample extraction method (header + 1000 records) without decompressing 6.8GB:

   ```powershell
   # For curr_ping.csv - 2,335,270 lines
   tar -xOzf .\validated-data-sept2022.tar.gz curr_ping.csv | Select-Object -First 1001 > sample1000_curr_ping.csv

   # For curr_udplatency.csv - 1,263,341 lines
   tar -xOzf .\validated-data-sept2022.tar.gz curr_udplatency.csv | Select-Object -First 1001 > sample1000_udplatency.csv

   # For curr_httpgetmt.csv - 280,042 lines
   tar -xOzf .\validated-data-sept2022.tar.gz curr_httpgetmt.csv | Select-Object -First 1001 > sample1000_curr_httpgetmt.csv

## Headers Verified by Streaming (PowerShell tar -xOzf)

Extracted without decompressing the 6.8GB. Method: `tar -xOzf file.tar.gz name.csv | Select-Object -First 1`

### 1. curr_ping.csv
`unit_id,dtime,ddate,target,rtt_avg,rtt_min,rtt_max,rtt_std,successes,failures`
- 2,335,270 lines
- Use: `packet_loss_pct = failures / (successes + failures) * 100`
- Sample: data/sample1000_curr_ping.csv (166 KB)

### 2. curr_udplatency.csv
`unit_id,dtime,ddate,target,rtt_avg,rtt_min,rtt_max,rtt_std,successes,failures`
- 1,263,341 lines  
- Use: Calculation of `rtt_p95` and `is_peak_hour` (dtime 19-23h)
- Note: Same schema as curr_ping.csv but measures UDP latency, more sensitive for QoE
- Sample: data/sample1000_udplatency.csv (191 KB)

### 3. curr_httpgetmt.csv
`unit_id,dtime,ddate,target,address,fetch_time,bytes_total,bytes_sec,bytes_sec_interval,warmup_time,warmup_bytes,sequence,threads,successes,failures`
- 280,042 lines
- Use: `throughput_mbps = bytes_sec * 8 / 1_000_000` to validate SLA plans >300 Mbps
- Sample: data/sample1000_httpgetmt.csv (285 KB)

### 4. fiber_units.csv (Processed)
`unit_id, technology, isp, tier` [from unit-profile-sept2022.xlsx filtered CONTAINS Fiber -> 285 units]
- 107 KB
- Use: Join key `unit_id` to filter only FTTH. Without this filter risk_flag mixes DSL/Cable/Fiber.
- Evidence: docs/excel_filter.png

## Validation of Schema
The 3 main files share `unit_id,dtime,ddate,successes,failures` which allows join and unified calculation of `risk_flag`. The difference is `target` vs `address/bytes_sec` for throughput.

## Full Dataset Processing Strategy - Final Project (Local)

**IMPORTANT: Final analysis will be executed on the FULL dataset locally.**

While this repo contains only 1000-row samples for GitHub compliance (<100MB limit), the capstone deliverables (metrics, Tableau dashboard, recommendations) are computed on the full 6.8GB dataset in local environment `D:\Capstone FFTH\`.

**Why samples in GitHub:**
- GitHub hard limit 100MB per file - full CSVs are 223MB, 125MB, 40MB
- Reviewer can clone and run notebook in <30 seconds without downloading 6.8GB
- Samples allow version control and reproducibility

**How full processing is demonstrated:**
- Stream validation without extraction (evidence in docs/evidence/):
  `tar -xOzf validated-data-sept2022.tar.gz curr_ping.csv | Measure-Object -Line` -> 2,335,270 lines
  `tar -xOzf validated-data-sept2022.tar.gz curr_udplatency.csv | Measure-Object -Line` -> 1,263,341 lines
- Scalable code in `python/01_process.ipynb`:
  GitHub mode: `pd.read_csv('data/sample1000_*.csv')` (fast)
  Local full mode: `pd.read_csv(..., chunksize=100000)` + filter by `fiber_units.csv` (285 units) to process 2.3M rows without OOM
- Final KPIs reported (`% FTTH clients at risk in peak hour`) come from full processing, not from samples.

This dual approach satisfies both Google Capstone reproducibility requirements and real-world Big Data handling.

# Author - Rafael Cansigno Peláez