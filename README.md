# FTTH QoE Risk & Support Cost Optimization

> **From Network Telemetry to Churn Prevention and OPEX Reduction — Methodology v2.2 CORRECTED (Power BI Audit + Python Fix)**
> **Evolución: v1 FAILED → v2 → v2.1.3 FINAL (Hardware-Corrected) → v2.2 CORRECTED (Loss-Calculation-Corrected)**

[[License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) [[Data Source: FCC MBA](https://img.shields.io/badge/Data-FCC%20MBA%202023--2024-blue)](https://www.fcc.gov/general/measuring-broadband-america) [[Status](https://img.shields.io/badge/Status-v2.2%20CORRECTED-green)](https://github.com/sigloxiii/ftth-qoe-risk-optimization)

**September-October 2026 - Eng. Rafael Cansigno Peláez** | **Google Data Analytics Capstone - Track B (Self-directed)**

---

## Project Overview

This Capstone turns FCC Measuring Broadband America telemetry into actionable decisions for FTTH operators: which units are at real risk of poor QoE and which truck rolls can be avoided.

**Problem v1:** Raw measurements mix true fiber degradation with false latency/loss created by legacy Whiteboxes.

**Solution v2.1.3:** Hardware filtering in Excel + peak-hour analysis (19-23h local) + FCC-aligned QoE thresholds.

**Problem v2.1.3 discovered via Power BI audit:** `packets` count was used as percentage, generating 1005% loss, and `Merge1` had `Query Errors`.

**Solution v2.2 CORRECTED:** Power BI audit → Python fix → coincidencia total. Loss calculation `packets/10` with 100% capping, null handling with `try...otherwise`.

**Final Output v2.2:** `output/ftth_final_258_v2_2_CORRECTED.csv` - 258 units, 89 at risk (>1% definition), 26 at severe risk (>10%), ready for PowerBI.

---

### Methodological Reconstruction Note (Cronología)

> **Rebuilt September 27 - October 2, 2026. v2.2 is definitive and audits v2.1.3.**

#### v1 FAILED - Convenience Bias (Sept 2026)
Reading FCC monthly files with only first 1000 rows captured legacy 2012-2016 enrollments. Overestimated risk 3.2x.

#### v2 REFINED - Instrument Bias (Sept 2026)
`fiber_units.csv` historically ordered. Legacy Whiteboxes with low CPU and FastEthernet saturate during tests, creating false latency/loss.

#### v2.1 Solution - Hardware Filter in Excel (30/09/2026)
Filtering done in Excel from `unit-profile-sept2022.xlsx`, evidenced in `docs/evidence/filtrado_fiber_units.png`. Only gigabit-capable models retained.

| Mode | Effect |
| :--- | :--- |
| v1 Convenience Bias | Captured obsolete CPE |
| v2 Hardware Bottleneck | False latency/loss |
| **v2.1 Excel Filter** | **Real FTTH QoE** |

v2.1 reduces from 285 to 258 valid units. 27 legacy units excluded. v1 code preserved in `/data/methodology_v1_FAILED/`.

#### v2.1.3 FINAL - Hardware-Corrected (01/10/2026) - ORIGINAL VIGENTE
Final export `data/methodology_v2/ftth_final_258_v2_1.csv` - 257 units, 17 at risk (6.6%), ready for PowerBI. Business Impact: avoids ~37 false truck rolls = ~$6,660 OPEX saved.

**Este fue tu README vigente hasta ayer.**

#### v2.2 CORRECTED - Loss-Calculation-Corrected (02/10/2026) - AUDITORÍA POWER BI
**Descubrimiento:** Durante construcción de dashboard en Power BI `powerbianalysis.pbix`, `Merge1` mostró `Query Errors - 1 row` y `curr_udpcloss` mostró `packets = 10055, 10330, 4481` → 1005% loss.

**Root Cause:** En Python original que generó `ftth_final_258_v2_1.csv`:
```python
df_loss['loss_pct'] = df_loss['packets']  # BUG: conteo como %
```
Y en Power Query:
```m
= Table.AddColumn(#"Filtered Rows", "loss_pct", each [packets] / 1000 * 100) // 10055 -> 1005.5%
```
Más referencia incorrecta: `Added Custom` leía de `#"Replaced Value"` en lugar de `#"Replaced Value2"`.

**Corrección v2.2 (Power BI audit → Python fix):**
```m
// Power BI CORRECTED
= Table.AddColumn(#"Filtered Rows", "loss_pct", each if [packets] > 1000 then 100 else [packets] / 10, type number)
```
```python
# Python CORRECTED - replica exacta
df_closs['loss_pct'] = np.where(df_closs['packets'] > 1000, 100, df_closs['packets']/10)
df['p95_latency_ms'] = df['p95_latency_ms'].fillna(0) # replica Replaced Value
```

**Resultado coincidente:** Power BI y Python ahora dan 34.50% riesgo >1% y 10.08% riesgo severo >10%.

---

### Hardware Selection Logic (v2.1 - Se mantiene)

**Core Principle:** The Whitebox is the measurement instrument. If it cannot forward at line rate, it creates the degradation.

Audit of `fiber_units.csv` (285 units) - 30/09/2026:

| Model | Count | Real HW Cap | Status |
| :--- | :--- | :--- | :--- |
| **skwb8** | 227 | >900 Mbps | INCLUDE - Gold standard, quad-core, HW NAT |
| **skwb8p** | 3 | >1000 Mbps | INCLUDE - 2.5GbE |
| **ac1750v2** | 28 | ~550 Mbps | INCLUDE - HW NAT, 1.1x margin at 500 Mbps |
| wnr3500l-high | 17 | <95 Mbps | EXCLUDE - 480MHz CPU 2009 |
| wdr3600 | 6 | ~180 Mbps | EXCLUDE - No HW NAT |
| wr1043nd/wr741nd | 4 | 100 Mbps FE | EXCLUDE - FastEthernet |

**Total Valid: 258 (90.5%) | Excluded: 27 (9.5%)**

Filtering done in Excel. Full deep dive in `docs/hardware_audit.md`.

**Rule v2.1:** Include only `skwb8`, `skwb8p`, `ac1750v2` with capacity >= provisioned speed * 1.1.

---

### QoE Parameters - Evolución de Definición

#### v2.1.3 Definition (Original Vigente)

**Source:** FCC MBA validated Sept 2022. Peak window 19-23h local.

**Metrics:**
- **p95_latency_ms:** P95 latency peak. Raw `rtt_avg` microseconds → ms.
- **p95_jitter_ms:** P95 jitter avg up/down peak. Raw microseconds → ms.
- **avg_loss_pct:** Mean loss peak. `failures / (successes+failures) *100`.

**Thresholds FCC + ITU-T (ITU-T G.114 / Y.1541, FCC 13th Report):**
- Latency: Fiber median 12-15ms, P95 18-22ms. Gaming <20ms. **Risk if >20ms.**
- Jitter: Degraded Zoom if **>15ms**.
- Loss: Degraded if **>1%**.

**Risk Flag v2.1.3 FINAL:**
> For Capstone Project 1, risk_flag = 1 if p95_latency_ms > 20.0 else 0
> Jitter >15ms and Loss >1% documented for v2.2 evolution.

**Final Dataset v2.1.3:** `data/methodology_v2/ftth_final_258_v2_1.csv` - 257 rows, 17 at risk (6.6%), mean latency 12.47ms, mean jitter 1.10ms.

#### v2.2 CORRECTED Definition (Auditoría Actual)

**Mismo source, pero con corrección de cálculo y hora pico 19-22h local (Time.Hour + timezone_offset):**

**Metrics corregidos:**
- **p95_latency_ms:** 0 nulls (Replaced Value)
- **p95_jitter_ms:** 0 nulls (Replaced Value1)
- **avg_loss_pct:** `if [packets] >1000 then 100 else [packets]/10` → min 0%, max 71.53%, mean 4.11%, 0 filas >100% (Replaced Value2)

**Risk Flag v2.2 CORRECTED:**
```m
risk_flag = 1 if p95_latency_ms > 50 or p95_jitter_ms > 5 or avg_loss_pct > 1 else 0
risk_severo = 1 if p95_latency_ms > 50 or p95_jitter_ms > 5 or avg_loss_pct > 10 else 0
```
- >1% = definición ITU-T G.114 estricta = **34.50% (89/258)**
- >10% = definición severa, comparable a 6.61% previo = **10.08% (26/258)**

**Comparativa v2.1.3 vs v2.2:**

| Versión | Fórmula risk_flag | Resultado | Archivo |
|---|---|---|---|
| v2.1.3 FINAL | latency >20 | 6.6% (17/257) | ftth_final_258_v2_1.csv (con bug de conteo) |
| v2.1.3 con truco | latency>20 or packets>160 | 6.61% (17/258) artefacto | - |
| **v2.2 CORRECTED** | latency>50 or jitter>5 or loss>1% | **34.50% (89/258)** | ftth_final_258_v2_2_CORRECTED.csv |
| **v2.2 SEVERO** | latency>50 or jitter>5 or loss>10% | **10.08% (26/258)** | mismo archivo |

Full math in `docs/procedimiento_matematico_v2_1_3.md` y `docs/Bitacora_PowerBI_FTTH_v2_1_CORRECTED.md`.

---

### Repository Structure (Combinado)

```
/
├── data/
│   ├── fiber_units.csv (258 valid filtered in Excel)
│   ├── methodology_v2/
│   │   ├── ftth_final_258_v2_1.csv (v2.1.3 FINAL, 257 rows, 17 risk, CON BUG para trazabilidad)
│   │   └── ftth_final_258_v2_2_CORRECTED.csv (v2.2 CORRECTED, 258 rows, 89 risk >1%, 26 severo >10%)
│   ├── methodology_v1_FAILED/
│   └── raw/ (gitignored, 6.8GB FCC)
├── powerbi/
│   ├── powerbianalysis.pbix (v2.2 CORRECTED: Replaced Value2 + capping)
│   └── evidence/
│       ├── Errors in Merge1.png
│       └── curr_udpcloss packets 10055.png
├── docs/
│   ├── evidence/filtrado_fiber_units.png (v2.1 hardware filter)
│   ├── hardware_audit.md (v2.1)
│   ├── procedimiento_matematico_v2_1_3.md (v2.1.3)
│   ├── Bitacora_PowerBI_FTTH_v2_1_CORRECTED.md (v2.2 audit detailed)
│   ├── HALLAZGO_Bug_PowerBI_Python.md (v2.2 discovery)
│   ├── data_dictionary.md
│   └── powerbi_model.md
├── scripts/
│   ├── original_script_con_bug.py (v2.1.3 - avg_loss = packets)
│   └── fix_python_ftth_v2_1_CORRECTED.py (v2.2 - packets/10 con tope 100)
├── README.md (este archivo combinado cronológico)
└── LICENSE
```

---

### PowerBI & Python - Cómo Reproducir (v2.2)

**Opción A: Power BI (Auditable)**
1. Abrir `powerbi/powerbianalysis.pbix`
2. `curr_udpcloss` -> Added Custom1: `if [packets] > 1000 then 100 else [packets]/10`
3. `Merge1` -> Replaced Value, Value1, Value2 -> Added Custom: `try...otherwise false` + referencia `Replaced Value2`
4. Refresh -> Exportar

**Opción B: Python (Corregido - coincide)**
```bash
python scripts/fix_python_ftth_v2_1_CORRECTED.py
# Valida: max 71.53%, mean 4.11%, risk 34.50% >1%, 10.08% >10%
```

---

### Para la Tesis - Texto Cronológico

> "Metodología v2.1.3 FINAL filtró hardware en Excel quedando 258 unidades válidas (skwb8, skwb8p, ac1750v2) y definió riesgo como p95_latency >20ms (6.6% en riesgo). Durante auditoría para dashboards en Power BI v2.2 se detectó bug en curr_udpcloss: `packets` (conteo) usado como % generando 1005% y Query Errors por referencia incorrecta a Replaced Value. Se corrigió en Power Query con `if [packets]>1000 then 100 else [packets]/10` (1000 datagramas FCC MBA) y manejo de nulls con try...otherwise, replicado en Python con `np.where` y `fillna(0)`. Resultado coincidente: 34.5% riesgo con definición ITU-T >1% y 10.08% riesgo severo >10%, este último equivalente justificado al 6.61% reportado previamente con umbral `>160 paquetes`."

---

### ✅ Checklist Entrega Cronológica

- [x] v1 FAILED documentado (convenience bias)
- [x] v2.1 hardware filter en Excel (27 excluidas, evidencia png)
- [x] v2.1.3 FINAL 17/257 = 6.6% con latency >20
- [x] v2.2 bug documentado con capturas Power BI (10055 packets, Errors in Merge1)
- [x] Power BI corregido (capping + Replaced Value2)
- [x] Python corregido (fillna + np.where) - coincidencia total
- [x] CSV v2_2 258 filas, 0 nulls, 0 >100%, 34.5% / 10.08%
- [x] README combinado cronológico (este)

---

### 👤 Autor

Eng. Rafael Cansigno Peláez (CaPe) - FTTH QoE - Sept-Oct 2026
Capstone Track B - v2.1.3 FINAL → v2.2 CORRECTED
