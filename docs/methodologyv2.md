# Data Dictionary - Methodology v2.1.3 FINAL Hardware-Corrected

> **Location:** `data/methodology_v2_1_CORRECTED/`
> **Primary Files:** `fiber_units.csv` (258), `ftth_final_258_v2_1_3.csv` (258, output), `validated-data-sept2022.tar.gz` (6.8GB raw, git-ignored)
> **Author:** Eng. Rafael Cansigno Peláez - Google Data Analytics Certificate - Proyecto 1
> **Status:** v2.1.3 FINAL - Implementado, validado, riesgo realista FCC 2022

This document defines population, measurement sources and final metrics for v2.1.3. Corrects convenience bias (v1) and instrument bias (v2.0). Implements P95 peak local and risk_flag >20ms.

---

### 1. fiber_units.csv - Population Inventory (Source of Truth) - FINAL

**File:** `data/fiber_units.csv` (15KB, committed, UTF-8)
**Granularity:** 1 row = 1 SamKnows Whitebox = 1 hogar FTTH Gigabit-capable
**Source:** `unit-profile-sept2022.xlsx` FCC 13th Report - https://data.fcc.gov/download/mba/2022/unit-profile-sept2022.xlsx
**Rows:** 258 unidades (90.5% Fiber total)

**Transformación documentada (Excel, evidencia `docs/evidence/filtrado_fiber_units.png`):**
- `Technology = Fiber` → 285 unidades
- `Whitebox Model IN (ac1750v2, skwb8, skwb8p)` → 258 finales
- Validación `Unit ID` únicos: 258, duplicados 0

| Column | Type | Example | Description | Key v2.1.3? |
| :--- | :--- | :--- | :--- | :--- |
| `Unit ID` | int | 925886 | PK. Causa raíz sesgo v1. | YES |
| `ISP` | string | 【entity-Verizon¦canonical_name=Verizon】 | Para estratificación Power BI. | YES |
| `timezone_offset_dst` | int | -4 | Offset con DST, esencial peak 19-23h local Sept 2022. | YES |
| `Download/Upload` | float | 500 | Tier contratado Mbps. | YES |
| `Whitebox Model` | string | skwb8 | Capacidad medición. | YES |

**Distribución final validada:**
- `skwb8`: 227 (88%) - Gold Standard >900 Mbps
- `ac1750v2`: 28 (11%) - ~550 Mbps, válido hasta 500 Mbps  
- `skwb8p`: 3 (1%) - >1000 Mbps

**Excluidas:** 27 legacy (`wnr3500l-high` 17, `wdr3600` 6, otros 4) - CPU 480MHz / puerto FE <180 Mbps, saturan y generan falsos P95 >80ms.

### 2. Measurement Source - validated-data-sept2022.tar.gz

**Archive:** 6.8GB (6,812,728,506 bytes), 16 archivos - git-ignored

**Relevantes v2.1.3:**
- `curr_udplatency.csv` (122MB) - PRIMARY - `rtt_avg` en µs
- `curr_udpjitter.csv` (138MB) - `jitter_up`, `jitter_down` en µs
- Loss derivado de `curr_udplatency`: `failures/(successes+failures)*100`

**Excluidos:**
- `curr_dns.csv` (5GB) - no last-mile
- `curr_webget.csv` (836MB) - Instrument Bias v1
- `*t6.csv` - IPv6 vacío

**Ventana análisis:** 19-23h local usando `timezone_offset_dst` (FCC MBA peak congestion).

### 3. Final Output - ftth_final_258_v2_1_3.csv

**File:** `data/methodology_v2_1_CORRECTED/ftth_final_258_v2_1_3.csv` (258 rows, UTF-8, 15KB committed)
**Encoding:** UTF-8 explícito `encoding='utf-8'` para GitHub/Power BI compatibilidad Windows.
**Granularity:** 1 row = 1 Unit ID con P95 peak.

| Column | Fuente | Unidad Original | Transformación | Descripción |
| :--- | :--- | :--- | :--- | :--- |
| `unit_id` | fiber_units | int | PK | Whitebox ID |
| `p95_latency_ms` | curr_udplatency.rtt_avg | µs | µs/1000, P95 peak 19-23h local | Latencia P95 real |
| `p95_jitter_ms` | curr_udpjitter.jitter_up/down | µs | (up+down)/2/1000, P95 peak | Jitter P95 real |
| `avg_loss_pct` | curr_udplatency.successes/failures | % | mean peak | Packet loss mean peak |
| `risk_flag` | p95_latency_ms >20 | 0/1 | FCC 13th Report | Flag churn risk |

**Resultado validado v2.1.3:**
- Mean latency: 12.56ms, P50 12.28ms, P75 14.95ms, Max 70.45ms (unit 24559133)
- Mean jitter: 1.14ms, Max 5.32ms (unit 24840041)
- Mean loss: 0.026%
- Risk: 19/258 = **7.36%** (0=239, 1=19)

### 4. Jitter (p95_jitter_ms) - Documentación Procesamiento

- **Fuente:** `curr_udpjitter.csv` columnas `jitter_up`, `jitter_down`
- **Unidad original:** microsegundos → ms: `(jitter_up + jitter_down)/2 /1000.0`
- **Fix timezone:** `pd.to_datetime(..., utc=True)` + `timezone_offset_dst` → `timestamp_local`
- **Ventana:** 19-23h local (`local_hour.between(19,23)`) - FCC MBA §4.3 peak
- **Métrica:** P95 por `unit_id` `groupby quantile(0.95)` - misma metodología que latencia FCC
- **Optimización:** `usecols` + `chunksize=500k` para 6.8GB sin OOM
- **Uso v2.1.3:** NO entra en `risk_flag` (risk = solo latencia >20ms)
- **Propósito:** Enriquecer dataset final para dashboard Power BI scatter `latency vs jitter` y análisis adicional Google
- **Resultado:** mean 1.14ms, max 5.32ms, 258 unidades, 0 valores constantes

### 5. Risk Flag v2.1.3 Justificación

- **Legacy >80ms (v2.0):** Era coax/DOCSIS 2015, flota FTTH moderna skwb8 nunca llega → 0% risk (bias)
- **Nuevo >20ms (v2.1.3):** P85-P90 real flota (max 70.45ms) + mediana FCC Fiber 13th Report 2022: 12-15ms, P95 18-22ms + ITU-T G.114 gaming <20ms preferido
- **Resultado:** 7.36% realista, defendible para churn FTTH, coincide con FCC degradado reportado.

---
*Evidencia: `docs/evidence/contenido_tar_6.8GB.png` + `filtrado_fiber_units.png` + `risk_736.png` (19/258) + `ftth_final_258_v2_1_3.csv` UTF-8*