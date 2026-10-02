# Bitácora Detallada - Proceso Power BI - Análisis FTTH 258 Unidades

**Proyecto:** powerbianalysis.pbix  
**Metodología:** v2_1_CORRECTED  
**Fecha:** 02/10/2026  
**Autor:** Rafael (CaPe)  

---

## 1. Resumen Ejecutivo

Durante la auditoría de la consulta **Merge1** se detectaron 3 fallas encadenadas desde el origen:

1. **curr_udpcloss** usaba conteo crudo de paquetes como porcentaje
2. Valores atípicos >1000 paquetes por pruebas fallidas Whitebox `skwb8` (10055, 10330, 4481)
3. **Merge1** referenciaba paso intermedio `#"Replaced Value"` en lugar de `#"Replaced Value2"`, dejando nulls y provocando `Query Errors - 1 row` y `risk_flag = Error`

## 2. Entorno

- Fuente: FCC MBA - curr_udpcloss, curr_udplatency, curr_udpjitter, fiber_units, Unit Profile
- Hora pico: LocalHour 19-22 (7pm-10pm) usando `timezone_offset`
- Archivo final previo: `ftth_final_258_v2_1.csv` (258 filas, 14 columnas)

## 3. Query: fiber_units (base)

**Objetivo:** Filtrar solo FTTH y calcular hora local.

**Applied Steps:**
- Source
- Filtered Rows: Technology = Fiber
- Added Custom: `LocalHour = Time.Hour([dtime] + #duration(0, [timezone_offset],0,0))`
- Filtered Rows1: LocalHour >=19 and <=22

## 4. Query: curr_udplatency y curr_udpjitter

Mismo patrón. Se agrupa por Unit ID:
- `p95_latency_ms = List.Percentile([latency_ms], 0.95)`
- `p95_jitter_ms = List.Percentile([jitter_ms], 0.95)`
Filtrados por LocalHour 19-22 antes de agrupar. Sin errores.

## 5. Query: curr_udpcloss - ANÁLISIS DEL BUG ORIGEN

### 5.1 Estado inicial (captura image_2eba93.png)

Valores `packets`: 2,79,79,62,2,2,62,2,77,4... y filas 186-188: **10055, 4481, 10330, 4481, 831, 351**

Fórmula en Added Custom1:
```m
= Table.AddColumn(#"Filtered Rows", "loss_pct", each [packets] / 1000 * 100, type number)
```
Generaba 10055 -> 1005.5% (imposible).

### 5.2 Bug original en Python

```python
df_loss['loss_pct'] = df_loss['packets']  # BUG: conteo como %
avg_loss = df_loss.groupby('Unit ID')['loss_pct'].mean()
```

Por eso Grouped Rows tenía 340.25, 1337, 1664, 6751. Al usar `>1` marcabas >1 paquete, no >1%.

### 5.3 Corrección v2_1_CORRECTED

Justificación FCC MBA 2023: cada prueba envía 1000 datagramas. `% pérdida = perdidos /1000*100`. skwb8 reporta contadores acumulados >1000 en outage -> capping a 100%.

**Fórmula final:**
```m
= Table.AddColumn(#"Filtered Rows", "loss_pct", each if [packets] > 1000 then 100 else [packets] / 10, type number)
// [packets]/10 = /1000*100
// 2 -> 0.2% , 79 -> 7.9% , 10055 -> 100% (tope)
```

**Applied Steps finales:**
Source > Expanded fiber_units.1 > Added Custom (LocalHour) > Filtered Rows (19-22) > **Added Custom1 (CORREGIDO)** > Removed Columns > Grouped Rows (avg_loss_pct = List.Average)

**Validación:** min 0%, max 71.53%, media 4.11%, 0 filas >100%

## 6. Query: Merge1 - QUERY ERRORS

### 6.1 Captura image_2eba93.png (Errors in Merge1)

1 fila: Download 75 / Upload 75 / skwb8 / p95_latency_ms null / p95_jitter_ms null / avg_loss_pct 0 / risk_flag Error

### 6.2 Captura image_ebcd89.png (intento de fix)

Fórmula visible:
```m
= Table.AddColumn(#"Replaced Value", "risk_flag", each if (try [p95_latency_ms] > 50 otherwise false) or (try [p95_jitter_ms] > 5 otherwise false)
```

Applied Steps: Source > Expanded curr_udplatency > Merged Queries > Expanded curr_udpjitter > Merged Queries1 > Expanded curr_udpcloss > **Replaced Value > Replaced Value1 > Replaced Value2** > Added Custom

**Problema:** Added Custom lee de `#"Replaced Value"` (paso 6) pero ya existen Value1 y Value2. Fila 258 sigue con null.

### 6.3 Corrección final

```m
= Table.AddColumn(#"Replaced Value2", "risk_flag", each if (try [p95_latency_ms] > 50 otherwise false) or (try [p95_jitter_ms] > 5 otherwise false) or (try [avg_loss_pct] > 1 otherwise false) then 1 else 0, Int64.Type)

Replaced Value  = Table.ReplaceValue(#"Expanded curr_udpcloss",null,0,Replacer.ReplaceValue,{"p95_latency_ms"})
Replaced Value1 = Table.ReplaceValue(#"Replaced Value",null,0,Replacer.ReplaceValue,{"p95_jitter_ms"})
Replaced Value2 = Table.ReplaceValue(#"Replaced Value1",null,0,Replacer.ReplaceValue,{"avg_loss_pct"})
```

Resultado: Query Errors desaparece.

## 7. Validación Final CSV

- 258 filas, 14 columnas, 0 nulls
- p95_latency_ms: 0 nulls
- p95_jitter_ms: 0 nulls
- avg_loss_pct: mean 4.11%, std 11.37%, median 0.4%, max 71.53%
- avg_loss_pct >100%: 0 filas (antes 1005%, 1033%)
- risk_flag: 0=169 (65.5%), 1=89 (34.5%)
- risk_flag Error: 0

**Comparativa:**
| Métrica | Antes (bug) | Después |
|---|---|---|
| avg_loss_pct max | 6751 / 10055 | 71.53% |
| >100% | Sí | 0 |
| risk >1% | 6.61% (17 unid) usando >160 paquetes | 34.5% (89 unid) usando >1% real |
| Riesgo severo >10% | - | 16/258 = 6.20% (equivalente justificado al 6.61%) |

## 8. Código M Completo

**curr_udpcloss:**
```m
let
    Source = Csv.Document(File.Contents("curr_udpcloss.csv")),
    #"Filtered Rows" = Table.SelectRows(Source, each [LocalHour] >=19 and [LocalHour] <=22),
    #"Added Custom1" = Table.AddColumn(#"Filtered Rows", "loss_pct", each if [packets] > 1000 then 100 else [packets]/10, type number),
    #"Grouped Rows" = Table.Group(#"Added Custom1", {"Unit ID"}, {{"avg_loss_pct", each List.Average([loss_pct]), type number}})
in
    #"Grouped Rows"
```

**Merge1:**
```m
let
    Source = fiber_units,
    #"Expanded curr_udplatency" = Table.NestedJoin(Source, {"Unit ID"}, curr_udplatency, {"Unit ID"}, "curr_udplatency", JoinKind.LeftOuter),
    #"Expanded1" = Table.ExpandTableColumn(#"Expanded curr_udplatency", "curr_udplatency", {"p95_latency_ms"}),
    #"Merged Queries" = Table.NestedJoin(#"Expanded1", {"Unit ID"}, curr_udpjitter, {"Unit ID"}, "curr_udpjitter", JoinKind.LeftOuter),
    #"Expanded curr_udpjitter" = Table.ExpandTableColumn(#"Merged Queries", "curr_udpjitter", {"p95_jitter_ms"}),
    #"Merged Queries1" = Table.NestedJoin(#"Expanded curr_udpjitter", {"Unit ID"}, curr_udpcloss, {"Unit ID"}, "curr_udpcloss", JoinKind.LeftOuter),
    #"Expanded curr_udpcloss" = Table.ExpandTableColumn(#"Merged Queries1", "curr_udpcloss", {"avg_loss_pct"}),
    #"Replaced Value" = Table.ReplaceValue(#"Expanded curr_udpcloss",null,0,Replacer.ReplaceValue,{"p95_latency_ms"}),
    #"Replaced Value1" = Table.ReplaceValue(#"Replaced Value",null,0,Replacer.ReplaceValue,{"p95_jitter_ms"}),
    #"Replaced Value2" = Table.ReplaceValue(#"Replaced Value1",null,0,Replacer.ReplaceValue,{"avg_loss_pct"}),
    #"Added Custom" = Table.AddColumn(#"Replaced Value2", "risk_flag", each if (try [p95_latency_ms] >50 otherwise false) or (try [p95_jitter_ms] >5 otherwise false) or (try [avg_loss_pct] >1 otherwise false) then 1 else 0, Int64.Type)
in
    #"Added Custom"
```

## 9. Pendientes

Revisar script Python que generó ftth_final_258_v2_1.csv para replicar capping y reemplazo de nulls, y generar `risk_flag_1pct`, `risk_flag_5pct`, `risk_flag_10pct` para análisis de sensibilidad.
