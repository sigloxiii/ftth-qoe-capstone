# Data Dictionary - Validated Sept 2022 - Verified Headers

| Columna | Tipo | Descripción negocio | Usado en |
|---|---|---|---|
| unit_id | int | Whitebox ID anonimizado - PK para join con fiber_units.csv | risk_flag |
| dtime | time | Hora local (ya convertida de UTC por FCC) | is_peak_hour |
| ddate | date | Fecha de prueba | rtt_p95 diario |
| rtt_avg/min/max/std | float ms | Latencia | QoE |
| successes/failures | int | Intentos de ping | packet_loss_pct |
| bytes_sec | int | Throughput medido | SLA compliance |
| technology | string | Tipo conexión - filtrado Fiber | Filtro FTTH |