# FTTH QoE Risk Optimization - Resumen Ejecutivo del Proyecto
### Capstone: Google Data Analytics + FCC MBA Data | Sept 2022

>Contexto de negocio para lector no técnico.

---

### 1. ¿De qué se trata este proyecto? (Para todos)

Imagina que eres un ISP de fibra óptica (FTTH). Tienes miles de casas con un aparatito blanco (Whitebox) que mide la calidad del internet cada hora.

El problema: Durante la noche, de 19:00 a 23:00, cuando todos ven Netflix, juegan y hacen videollamadas, algunas casas sufren lag. Si no las detectas a tiempo, se van a la competencia.

**Este proyecto responde:** ¿Cuáles de mis casas de fibra están en riesgo de mala experiencia y cuánto dinero pierdo si no actúo?

**Resultado clave:** De 257 casas de fibra válidas, **N están en riesgo (N%)**. Si las arreglamos proactivamente, evitamos ~$XX de churn mensual.

### 2. ¿Qué mide cada registro? (Explicado sin tecnicismos)

Cada fila en los datos crudos NO es un cliente, es un **paquetito de prueba**.

*   **Nace en la casa:** El Whitebox genera un paquete UDP pequeño (como un ping).
*   **Viaja:** Whitebox -> Router -> ONT (caja de fibra) -> luz por fibra -> OLT en central -> Internet -> Servidor de prueba MBA.
*   **Regresa:** El servidor responde y el Whitebox mide cuánto tardó (latencia), cuánto varió (jitter) y si se perdió (loss).

**En condiciones normales (fibra sana):**
Latencia < 15ms, Jitter < 3ms, Pérdida 0%. Todo fluido.

**Cuando marcamos `risk_flag = 1`:**
No es por un paquete malo. Es porque durante TODO el mes, en horario pico, el 95% de sus paquetes son lentos. El percentil 95 (p95) > 20ms. Eso significa que esa casa, cada noche, ve videos que se congelan.

### 3. Datasets Usados

| Archivo | Rol | 1 fila = | Columnas Clave |
| :--- | :--- | :--- | :--- |
| `unit-profile-sept2022.csv` | DIM - Quién | 1 Whitebox / casa | `unit_id, Technology, Model, provisioned_down/up, timezone_offset` |
| `curr_udplatency.csv` | FACT - Latencia | 1 probe UDP | `unit_id, timestamp_utc, rtt_avg (us), success/failures` |
| `curr_udpjitter.csv` | FACT - Variación | 1 ráfaga UDP | `unit_id, timestamp_utc, jitter_up/down` |
| `curr_udploss.csv` | FACT - Pérdida | 1 test de pérdida | `unit_id, timestamp_utc, packets_sent/lost` |
| `fiber_units.csv` | DIM Limpia (258) | 1 casa válida | Filtro: `Model IN (skwb8 227, ac1750v2 28, skwb8p 3)` |
| `ftth_final_258_v2_1.csv` | FACT Agregada (257) | 1 casa resumida en pico | `unit_id, p95_latency_ms, p95_jitter_ms, avg_loss_pct, risk_flag` |

**Regla de Oro para recordar:** `raw microsegundos / 1000 = ms`. `p95` se calcula con `PERCENTILE.INC` en Python y PowerBI, NO con `AVERAGE`.

### 4. Proceso Completo (6 pasos para repaso rápido)

**Paso 1 - Limpieza de Sesgo de Instrumento (Tu diferenciador v2.1.3):**
Problema v1 daba 21% de riesgo porque incluía hardware legacy: `wnr3500l-high (CPU 480MHz capa a 95Mbps)` y `wdr3600 (sin HW NAT)` generaban latencia falsa.
Solución: `INCLUDE Model IN (skwb8, skwb8p, ac1750v2) AND capacity >= provisioned*1.1`. Quedan 258.

**Paso 2 - Normalización horaria:**
`local_time = timestamp_utc + timezone_offset`. Filtrar `local_hour BETWEEN 19 AND 22`. Esto es el horario pico.

**Paso 3 - Agregación:**
Por cada `unit_id` en pico: `p95_latency = P95(rtt_avg/1000)`, `p95_jitter = P95(avg(up/down)/1000)`, `avg_loss = MEAN(loss)`.

**Paso 4 - Flag de Riesgo:**
`risk_flag = IF(p95_latency_ms > 20, 1, 0)`. Resultado: 17/257.

**Paso 5 - PowerBI :**
Importar 2 tablas. NO filtrar hora de nuevo (ya está filtrado). Relación `fiber_units[Unit ID] -> ftth_final[unit_id]` One-to-Many Single. Medidas DAX: `PERCENTILEX.INC`, `COUNTROWS=257`, `SUM(risk_flag)=17`.

**Paso 6 - Actuar:**
Dashboard Ejecutivo: % Riesgo + $ ROI. Dashboard NOC: tabla por `unit_id` con timeline 19-23h para triage.

### 5. Glosario Rápido (Para stakeholder no técnico)

*   **FTTH:** Fiber To The Home. Internet por fibra hasta la casa.
*   **Whitebox:** Router de medición de la FCC, no el router del cliente.
*   **p95:** El 95% de las veces está mejor que este valor. Si p95 es alto, casi siempre es malo en pico.
*   **Bufferbloat:** Cola de paquetes en el router de casa cuando se satura el upload.
*   **OLT/ONT:** OLT es el equipo en la central del ISP, ONT es la cajita en casa. Entre ellos va la luz.
*   **Churn:** Cliente que se va. Cada cliente retenido vale ~$135.

### 6. Stakeholders y Preguntas de Negocio

**Stakeholders:** NOC Manager (quiere lista accionable), CXO (quiere $).

**3 Preguntas que responde:**
1. ¿Qué % de nuestra base de fibra tiene mala QoE en pico?
2. ¿Cuáles son las N unidades específicas a intervenir?
3. ¿Cuál es el impacto financiero de una intervención proactiva?

**3 Recomendaciones:**
1. Auto-alerta si p95>20ms por 3 días seguidos.
2. Triage remoto: revisar OLT y bufferbloat antes de enviar técnico.
3. SMS proactivo: "Detectamos lentitud nocturna, ¿quieres que revisemos?" Reduce churn X%.

---
