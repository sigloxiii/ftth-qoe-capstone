# Metrics Specification — FTTH QoE Risk

**Spec version:** 1.0.1
**Estado:** Baseline. Cualquier cambio se hace primero en este documento, luego en `config.yaml` y `src/`, y se registra en el Changelog (sección 11).
**Regla central:** una sola implementación de cada transformación (Python). Power BI **no** recalcula métricas; solo las visualiza.

---

## 1. Alcance y población

- **Fuente de población:** `unit-profile-sept2022.xlsx` (FCC MBA, 13th Report, datos Sept 2022).
- **Filtro 1:** `Technology = Fiber` → 285 unidades.
- **Filtro 2 (hardware):** `Whitebox Model IN (skwb8, skwb8p, ac1750v2)` → 258 unidades. Las 27 excluidas se conservan en `data/processed/excluded_legacy_ftth_units.csv` para auditoría.
- **Justificación del filtro:** el Whitebox es el instrumento de medición; modelos con CPU o puerto insuficiente (FastEthernet, sin HW NAT) generan latencia y pérdida artificiales (instrument bias).
- **Unidad de análisis (grain):** 1 fila = 1 `Unit ID`.

## 2. Verificación previa de datos (Step 0, obligatoria)

Antes de ejecutar el pipeline, documentar en `docs/data_inspection.md`:

1. Columnas, tipos y 5 filas de ejemplo de `curr_udplatency.csv`, `curr_udpjitter.csv` y `curr_udpcloss.csv`.
2. Definición oficial de cada columna usada (FCC MBA Technical Appendix / data dictionary), con enlace.
3. Confirmar en el encabezado real de `curr_udpcloss.csv` los campos que el Technical Appendix FCC (2023, data dictionary) describe: `unit_id, dtime, ddate, target, address, duration, packets`. Según ese diccionario, `curr_udpcloss` registra **eventos de corte/desconexión**: `duration` es la duración del evento en microsegundos y `packets` es "the number of packets we lost" (un conteo por evento, no un porcentaje). **`packets` no se usa como porcentaje ni se divide entre una constante.**
4. Valor de `timezone_offset_dst` de las unidades en estados sin DST (por ejemplo Arizona), si las hay.
5. Rango de `dtime` (UTC) y frecuencia de mediciones por unidad y por hora.

## 3. Tiempo y ventana pico

- `dtime` está en **UTC**.
- `local_time = dtime + timezone_offset_dst` (septiembre 2022 está en horario de verano). **No** usar `timezone_offset`.
- **Ventana pico:** hora local **≥ 19 y < 23** (19:00:00–22:59:59), 4 horas.
- Implementación única:

```python
# Hora local con offset DST; ventana pico [19, 23)
df["local_hour"] = (df["dtime"] + pd.to_timedelta(df["timezone_offset_dst"], unit="h")).dt.hour
peak = df[(df["local_hour"] >= 19) & (df["local_hour"] < 23)]
```

- Equivalente en Power Query (solo si se reimplementa para conciliación): `Time.Hour([dtime] + #duration(0,[timezone_offset_dst],0,0)) >= 19 and < 23`.

## 4. Métricas por unidad

Todas se calculan **solo con registros dentro de la ventana pico**.

| Métrica | Fuente | Registro (por fila) | Agregación por unidad |
| :--- | :--- | :--- | :--- |
| `p95_latency_ms` | `curr_udplatency.rtt_avg` (µs) | `rtt_avg / 1000` | Percentil 95, interpolación lineal |
| `p95_jitter_ms` | `curr_udpjitter` (`jitter_up`, `jitter_down`, µs) | `(jitter_up + jitter_down) / 2 / 1000` | Percentil 95, interpolación lineal |
| `loss_pct` | Ver 4.1 | `failures / (successes + failures) * 100` | **Razón de sumas:** `sum(failures) / sum(successes + failures) * 100` |
| `n_peak_records` | `curr_udplatency` | Conteo de registros pico válidos | Conteo |

- **Percentil:** interpolación lineal (pandas `quantile(0.95)` por defecto; equivale a `PERCENTILE.INC` y a `List.Percentile` por defecto en Power Query).
- **Pérdida con razón de sumas:** pondera cada prueba por su número de paquetes; el promedio simple de porcentajes sesga el resultado cuando el número de paquetes varía.

### 4.1 Fuente de pérdida

- **Fuente única (confirmada en el FCC MBA Technical Appendix 2023):** `failures` y `successes` de `curr_udplatency`. El apéndice define la pérdida UDP como la "fracción de paquetes UDP perdidos de la prueba de latencia UDP", la mapea a `curr_udplatency.csv` e indica calcularla como `failures / (successes + failures)`. Un paquete se cuenta como perdido si no hay respuesta en 3 s.
- **`curr_udpcloss` no es una fuente de porcentaje de pérdida.** Según el mismo diccionario de datos, registra eventos de corte/desconexión (`duration` en µs y `packets` = número de paquetes perdidos en el evento, un conteo). No se divide ni se promedia como porcentaje.
- **Uso opcional futuro:** `curr_udpcloss` puede alimentar una métrica de **disponibilidad** distinta (número de cortes y duración total en ventana pico). Queda fuera del `risk_flag` base y se evalúa en una versión posterior de la spec.
- Una sola fuente de pérdida por versión de la spec. No mezclar.

## 5. Calidad de datos

- **Registros inválidos** (excluir, nunca corregir con topes): `successes + failures <= 0`, `loss_pct` fuera de [0, 100], `rtt_avg` nulo o negativo, jitter nulo o negativo.
- **Prohibido:** capear valores (`min(x, 100)`) y rellenar nulos con 0 (`fillna(0)`). Un cero inventado hace parecer perfecta a una unidad sin datos.
- **Mínimo de datos:** una unidad entra al análisis de riesgo si `n_peak_records >= N_MIN`. `N_MIN` se fija en `config.yaml` tras inspeccionar la distribución de `n_peak_records` (Step 0) y se justifica en `docs/data_inspection.md`.
- **Unidades sin datos suficientes:** se listan en `data/processed/units_insufficient_data.csv` y quedan fuera del denominador de riesgo. El reporte indica siempre `unidades_analizadas / 258`.
- **Registro de calidad:** el pipeline escribe `data/processed/data_quality_log.csv` con conteo de registros descartados por regla.

## 6. Definición de riesgo

- **Estatus de los umbrales:** son **umbrales operativos definidos por el proyecto**, no valores de un estándar. Las citas previas a ITU-T G.114/Y.1541 y a secciones específicas del reporte FCC **no están verificadas** (G.114 trata retardo unidireccional y Y.1541 define clases de red con otros valores); no se citan en el README hasta confirmarlas en la fuente.
- **Umbrales base** (parámetros en `config.yaml`):

| Parámetro | Valor base |
| :--- | :--- |
| `latency_p95_ms` | 20 |
| `jitter_p95_ms` | 5 |
| `loss_pct` | 1.0 |

- **Regla:** `risk_flag = 1` si `p95_latency_ms > 20` **o** `p95_jitter_ms > 5` **o** `loss_pct > 1.0`. Además se guardan las banderas individuales (`flag_latency`, `flag_jitter`, `flag_loss`) para ver qué métrica activa el riesgo.
- **Tier de severidad:** `risk_severe = 1` si `loss_pct > 10` o `p95_latency_ms > 50` o `p95_jitter_ms > 15`.
- **Análisis de sensibilidad (obligatorio):** tabla de % de unidades en riesgo para latencia {20, 30, 50} ms × pérdida {0.5, 1, 2, 5} %. Los umbrales base no se eligen para reproducir un resultado previo.

## 7. Conciliación Python ↔ Power BI

Power BI consume `data/processed/ftth_qoe_unit_metrics.csv` generado por Python. Si se reimplementa una métrica en Power Query para auditoría:

1. Exportar ambas tablas y unir por `Unit ID`.
2. Tolerancias: `p95_latency_ms` y `p95_jitter_ms` ±0.001 ms; `loss_pct` ±0.001 pp; `risk_flag` coincidencia exacta; mismo número de unidades.
3. Las unidades que difieren se analizan una por una (ventana, offset, nulos); no se concilia solo por totales.
4. El resultado se guarda en `docs/reconciliation.md`.

## 8. Esquema del dataset final

`data/processed/ftth_qoe_unit_metrics.csv` (UTF-8, sin versión en el nombre; el versionado va en git tags):

`unit_id, isp, state, census, download_mbps, upload_mbps, whitebox_model, n_peak_records, p95_latency_ms, p95_jitter_ms, loss_pct, flag_latency, flag_jitter, flag_loss, risk_flag, risk_severe`

Pruebas automáticas (`tests/`):

- `unit_id` único y ⊆ `fiber_units.csv`.
- 0 nulos en métricas de unidades analizadas.
- `0 <= loss_pct <= 100`; `p95_latency_ms > 0`.
- `risk_flag == (flag_latency | flag_jitter | flag_loss)`.
- `analizadas + insuficientes == 258`.

## 9. Impacto de negocio

- Se omite el ahorro en dólares y el conteo de truck rolls evitados: no hay fuente para el costo unitario y la línea base (v1) fue invalidada por sesgo.
- Si se incluye una estimación, va como **escenario** con supuestos explícitos y parametrizables (costo por truck roll, tasa de visitas innecesarias), etiquetado como ilustrativo.

## 10. Limitaciones

- Un solo mes (septiembre 2022) y una muestra de unidades voluntarias; no representa a toda la población FTTH.
- Hardware filtrado por capacidad nominal del modelo, no por prueba de throughput por unidad.
- Los umbrales son del proyecto y su sensibilidad se reporta.

## 11. Changelog

- **1.0.1** — Definición de `curr_udpcloss` confirmada con el FCC MBA Technical Appendix 2023 (eventos de corte; `packets` = conteo de paquetes perdidos); fuente única de pérdida = `curr_udplatency`. Pendiente: confirmar los campos en el encabezado real del archivo (Step 0).
- **1.0.0** — Baseline: ventana [19, 23) con `timezone_offset_dst`; pérdida por razón de sumas desde `curr_udplatency`; sin capping ni `fillna(0)`; umbrales parametrizados con análisis de sensibilidad.
