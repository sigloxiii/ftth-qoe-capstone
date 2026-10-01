# Postmortem: Convenience Bias + Instrument Bias - FCC MBA FTTH
## Metodología v1 (FAILED) vs v2.0 vs v2.1 (Hardware-Corrected Final)

**Date:** 2026-09-30  
**Author:** Eng. Rafael Cansigno Peláez  
**Status:** `v1 FAILED` -> `v2.0 PARTIAL` -> `v2.1 CORRECTED & AUDITED`  
**Severity:** High - Invalidated ROI and risk_flag distribution  
**Related:** `data/methodology_v1_FAILED/`, `data/fiber_units_clean_essential.csv`, `docs/evidence/filtrado_fiber_units.png`  
**Dataset:** FCC MBA Thirteenth Report - Sept 2022 - `unit-profile-sept2022.xlsx` + `validated-data-sept2022.tar.gz` (6.8GB)

---

## 1. Executive Summary - Dos sesgos encadenados

**Sesgo 1 - Convenience Bias (v1):**
Durante peer review de metodología v1, identificamos uso de `df.head(1000)` / `nrows=1000` sobre CSVs de mediciones FCC. Las primeras 1000 filas no son aleatorias, corresponden a los `unit_id` más antiguos (2012-2016, Whitebox v1). Esto sobrestimó `risk_flag` ~3.2x.

**Sesgo 2 - Instrument Bias / Hardware Bias (v2.0 -> v2.1):**
Al corregir v1 y usar `fiber_units.csv` completo (285 FTTH), descubrimos que `fiber_units.csv` está ordenado históricamente por `Unit ID`. Los primeros IDs son modelos legacy con cuello de botella de CPU que saturan <100 Mbps. Medir latencia sobre esos Whiteboxes mide la saturación del instrumento, no la degradación del FTTH.

**Decisión v2.1:** Preservar v1 como evidencia en `methodology_v1_FAILED/` y reconstruir con **Hardware Capability Filter** + muestreo estratificado probabilístico con `seed=42`.

Este documento sigue Google Data Analytics Fase 6 (Act) - documentar limitaciones y acciones correctivas.

## 2. Contexto Operativo - Whitebox como instrumento

En FCC MBA, las mediciones no se hacen desde el modem del cliente, sino desde **Whiteboxes** (routers SamKnows) instalados en cascada con la ONT.

**Punto crítico:** El Whitebox ES el instrumento. Si el instrumento no puede procesar el tráfico, la medición es inválida (falso positivo de latencia/pérdida).

## 3. Diagnóstico v1 y v2.0

**v1 - Convenience Sampling:**
`curr_udplatency.csv` leído con `head(1000)`. Población ~40 unidades legacy-biased, mean down ~99 Mbps, P95 RTT ~110ms (saturación CPU).

**v2.0 - Corrección parcial:**
Se usó `fiber_units.csv` completo (285 unidades) desde `unit-profile-sept2022.xlsx` filtrado `Technology=Fiber`. Se corrigió muestreo pero se mantuvo hardware legacy:

**Evidencia auditoría 30/09/2026 - `fiber_units.csv` 285 FTTH:**
- `wnr3500l-high`: 17 unidades, planes 75/100 Mbps - Netgear 2009 BCM4718 480MHz 64MB RAM NAT SW
- `wdr3600`: 6 unidades, 100/200 Mbps - AR9344 560MHz single-core
- `wr1043nd / wr741nd`: 4 unidades, 75/100 Mbps - FastEthernet
- **Total Legacy con cuello de botella: 27 unidades (9.5%)**

Anomalía: picos latencia >80ms, jitter, pérdida >1.5% atribuidos a FTTH eran **Instrument Bias**.

## 4. Corrección v2.1 - Hardware Capability Filter + Excel Auditado

Para aislar instrumento y medir solo QoE real de red, v2.1 implementa filtro estricto.

**Decisión Final Validada 30/09/2026: Usar ÚNICAMENTE `skwb8`, `skwb8p`, `ac1750v2`**

### Proceso realizado en Excel (reemplaza script Python - evidencia trazable)

Proceso auditado en `unit-profile-sept2022.xlsx` (fuente oficial https://data.fcc.gov/download/measuring-broadband-america/2023/unit-profile-sept2022.xlsx):

1. Filtro `Technology = Fiber` → 285 unidades
2. Filtro `Whitebox Model IN (ac1750v2, skwb8, skwb8p)` → 258 unidades
3. `Datos > Quitar duplicados > Unit ID` → 258 únicos, 0 duplicados
4. Guardado CSV UTF-8 → `fiber_units.csv` (data/fiber_units.csv)

#### Evidencia: Filtrado por modelo en Excel

![Filtrado Fiber Units - Excel - Modelos válidos](./evidence/filtrado_fiber_units.png)
*Captura Excel mostrando filtro activo en columna `Whitebox Model` con valores `ac1750v2`, `skwb8`, `skwb8p`. Archivo `unit-profile-sept2022.xlsx` en `D:\Capstone FFTH\data`. 258 filas resultantes validadas: skwb8 227 (88%), ac1750v2 28 (11%), skwb8p 3 (1%).*

### Tabla de capacidad v2.1

| Modelo | Arquitectura | Capacidad Real | Throughput SamKnows | Criterio v2.1 |
| :--- | :--- | :--- | :--- | :--- |
| **skwb8** | SamKnows v8 Quad-core Gigabit HW NAT | Multi-Gig | >900 Mbps | **INCLUIR - Gold Standard (227, 79.6%)** |
| **skwb8p** | SamKnows v8 Plus 2.5GbE | Multi-Gig | >1000 Mbps | **INCLUIR (3)** |
| **ac1750v2** | TP-Link Archer C7 v2 QCA9558 HW NAT | Mid-Gigabit | ~550 Mbps | **INCLUIR con nota (28) - Válido hasta 500 Mbps, margen 1.1x** |
| wdr3600 | TP-Link N600 AR9344 560MHz | Mid | ~180 Mbps | **EXCLUIR (6) - Satura >100 Mbps** |
| wnr3500l-high | Netgear 2009 BCM4718 480MHz 64MB | Legacy FE | <95 Mbps | **EXCLUIR (17) - Origen primario sesgo v1** |
| wr1043nd/wr741nd | TP-Link N FE | Legacy FE | <100 Mbps | **EXCLUIR (4)** |

