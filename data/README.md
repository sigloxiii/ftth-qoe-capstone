# Data Source - FCC Measuring Broadband America

## Primary Source
**Program:** FCC Measuring Broadband America (MBA) - 13th Report
**Dataset:** Validated Data - September 2022 (last available)
**URL:** https://data.fcc.[STRIPPED 69 bytes].tar.gz
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

## Headers Verificados por Streaming (PowerShell tar -xOzf)

Extraídos sin descomprimir los 6.8GB. Método: `tar -xOzf archivo.tar.gz nombre.csv | Select-Object -First 1`

### 1. curr_ping.csv
`unit_id,dtime,ddate,target,rtt_avg,rtt_min,rtt_max,rtt_std,successes,failures`
- 2,335,270 líneas
- Uso: `packet_loss_pct = failures / (successes + failures) * 100`
- Sample: data/sample1000_curr_ping.csv (166 KB)

### 2. curr_udplatency.csv
`unit_id,dtime,ddate,target,rtt_avg,rtt_min,rtt_max,rtt_std,successes,failures`
- 1,263,341 líneas  
- Uso: Cálculo de `rtt_p95` y `is_peak_hour` (dtime 19-23h)
- Nota: Mismo schema que curr_ping.csv pero mide UDP latency, más sensible para QoE
- Sample: data/sample1000_udplatency.csv (191 KB)

### 3. curr_httpgetmt.csv
`unit_id,dtime,ddate,target,address,fetch_time,bytes_total,bytes_sec,bytes_sec_interval,warmup_time,warmup_bytes,sequence,threads,successes,failures`
- 280,042 líneas
- Uso: `throughput_mbps = bytes_sec * 8 / 1_000_000` para validar SLA planes >300 Mbps
- Sample: data/sample1000_httpgetmt.csv (285 KB)

### 4. fiber_units.csv (Procesado)
`unit_id, technology, isp, tier` [proviene de unit-profile-sept2022.xlsx filtrado CONTAINS Fiber -> 285 units]
- 107 KB
- Uso: Join key `unit_id` para filtrar solo FTTH. Sin este filtro el risk_flag mezcla DSL/Cable/Fiber.
- Evidencia: docs/excel_filter.png

## Validación de Schema
Los 3 archivos principales comparten `unit_id,dtime,ddate,successes,failures` lo que permite join y cálculo unificado de `risk_flag`. La diferencia es `target` vs `address/bytes_sec` para throughput.

# Author - Rafael Cansigno Peláez