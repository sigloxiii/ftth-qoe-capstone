# Risk Flag Redefinition - v2.1.3 (Python/pandas)
**Dataset:** Sept 2022 - FCC MBA Validated - 258 FTTH Gigabit-capable units
**Path:** `D:/Capstone FFTH/data/methodology_v2_1_CORRECTED/`
**Stack:** Python 3.14 + pandas (local)

### 1. Hallazgo v2.1.2

- `curr_udplatency.csv` 258 IDs: 172,800 filas → peak 19-23h local: 36,234 filas
- P95 real: mean 12.56 ms, p50 12.28 ms, p75 14.95 ms, max 70.45 ms
- Con umbral legacy `>80ms` → `risk_flag = 0.00%`
- Umbral 80ms es Instrument Bias de coax 2015, no aplica a FTTH moderno (skwb8 227 + ac1750v2 28)

### 2. Fuente industria 2022

**FCC Measuring Broadband America 13th Report (Sept 2022 data):**
- Mediana Fiber latency 12-15 ms → coincide con nuestro 12.56 ms
- P95 Fiber 18-22 ms. >20 ms = degradación QoE gaming
- Jitter Fiber medio <5 ms. >15 ms = congelamiento Zoom (Technical Appendix §4.2.3)
- Loss >1% peak = conexión degradada (Methodology §5.3)

**ITU-T G.114 / Y.1541 Class 0:**
- Interactive gaming preferido <20 ms, jitter <15 ms, loss <1%

### 3. Nueva definición en Python

```python
# En python/process_validated_v2_1_local.py
final['risk_flag'] = (
    (final['p95_latency_ms'] > 20.0) |
    (final['p95_jitter_ms'] > 15.0) |
    (final['avg_loss_pct'] > 1.0)
).astype(int)