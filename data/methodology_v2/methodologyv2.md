# Data Dictionary - Methodology v2.1 Hardware-Corrected

> **Location:** `data/`  
> **Primary Files:** `fiber_units.csv` (final 258), `unit-profile-sept2022.xlsx` (fuente oficial FCC), `validated-data-sept2022.tar.gz` (6.8GB mediciones)  
> **Author:** Eng. Rafael Cansigno Peláez  
> **Status:** v2.1.2 FINAL - Solo metodología, sin implementación

This document defines the population and measurement sources for v2.1. It corrects convenience bias (v1) and instrument bias (v2.0). No implementation details are defined yet.

---

### 1. fiber_units.csv - Population Inventory (Source of Truth) - FINAL

**File:** `data/fiber_units.csv` (15KB, committed, UTF-8)  
**Granularity:** 1 row = 1 SamKnows Whitebox = 1 hogar FTTH con hardware Gigabit-capable  
**Source:** `unit-profile-sept2022.xlsx` FCC Thirteenth Report - https://data.fcc.[STRIPPED 67 bytes].xlsx  
**Rows:** 258 unidades (90.5% del total Fiber)

**Transformación documentada (Excel, evidencia `docs/evidence/filtrado_fiber_units.png`):**
- `Technology = Fiber` → 285 unidades
- `Whitebox Model IN (ac1750v2, skwb8, skwb8p)` → 258 unidades finales
- Validación `Unit ID` únicos: 258, duplicados 0

| Column | Type | Example | Description | Key for v2.1? |
| :--- | :--- | :--- | :--- | :--- |
| `Unit ID` | int | 925886 | PK. Whitebox ID secuencial, no aleatorio. Causa raíz del sesgo. | YES - PK |
| `ISP` | string | Verizon, Cincinnati Bell | Proveedor. Para estratificación. | YES |
| `Technology` | string | Fiber | Constante post-filtro. Irrelevante para análisis. | NO |
| `State` | string | OH, VA | Estado. Opcional geo. | NO |
| `Census` | string | Midwest | Región censal. Redundante. | NO |
| `timezone_offset` | int | -5 | Offset UTC sin DST. Esencial para peak 19-23h local. | YES |
| `timezone_offset_dst` | int | -4 | Offset UTC con DST. Esencial peak. | YES |
| `Download` | float | 250, 500 | Velocidad contratada bajada Mbps. Para estratificación por tier. | YES |
| `Upload` | float | 100, 500 | Velocidad subida Mbps. | YES |
| `Whitebox Model` | string | skwb8, ac1750v2, skwb8p | Hardware. Determina capacidad de medición. | YES |

**Distribución final:**
- `skwb8`: 227 (88%) - Gold Standard >900 Mbps
- `ac1750v2`: 28 (11%) - ~550 Mbps, válido hasta 500 Mbps
- `skwb8p`: 3 (1%) - >1000 Mbps

**Excluidas:** 27 legacy (`wnr3500l-high` 17, `wdr3600` 6, `wr1043nd/wr741nd` 4) - CPU 480MHz o puerto FE <100-180 Mbps, saturan y generan falsos P95 >80ms.

### 2. Measurement Source - validated-data-sept2022.tar.gz

**Archive:** `validated-data-sept2022.tar.gz` (6.8GB, 6,812,728,506 bytes descomprimido, 16 archivos) - git-ignored

**Contenido relevante:**
- `curr_udplatency.csv` (122MB) - PRIMARY - latencia UDP ms
- `curr_udpjitter.csv` (138MB) - jitter ms
- `curr_udpcloss.csv` (79MB) - pérdida %

**Contenido excluido:**
- `curr_dns.csv` (5GB) - fuera de alcance, no es last-mile
- `curr_webget.csv` (836MB) - causa Instrument Bias en v1
- `*t6.csv` (1KB) - IPv6 vacío

**Decisión v2.1:** Medición primaria es latencia UDP. Definición de ventana de análisis: hora local 19-23h usando `timezone_offset`.

---
*Evidencia: `docs/evidence/contenido_tar_6.8GB.png` + `docs/evidence/filtrado_fiber_units.png` + `data/fiber_units.csv` 258 únicos*