# Definición de Métricas - FTTH QoE Risk & Churn Proxy

## Objetivo de Negocio
Transformar telemetría técnica (latencia/pérdida) en indicador financiero `risk_flag` que predice necesidad de truck roll.

Fuente validada:
- curr_ping.csv: unit_id,dtime,ddate,target,rtt_avg,rtt_min,rtt_max,rtt_std,successes,failures
- curr_udplatency.csv: unit_id,dtime,ddate,target,rtt_avg,rtt_min,rtt_max,rtt_std,successes,failures
- fiber_units.csv: unit_id,technology=FIBER (285 units)

---


### 1. packet_loss_pct - % de pérdida de paquetes
**Definición:** Porcentaje de pings fallidos por hora. Es la métrica base de degradación.

**Explicación para gente que no es de redes:**
Imagina que internet es una carretera y cada mensaje (WhatsApp, Netflix, Microsoft Teams】) es una caravana de 100 carritos.

`successes` = carritos que sí llegaron a destino.
`failures` = carritos que se perdieron en el camino.

Si mandas 100 y llegan 98, perdiste 2%. Tu fórmula es:

**Fórmula de negocio:**

packet_loss_pct = failures / (successes + failures) * 100

### 2. is_peak_hour - Horas pico o de alta demanda ¿La falla pasó cuando al cliente le importa?

**Explicación para gente que no es de redes:**
No es lo mismo que se te vaya el agua a las 3 de la mañana que a las 8 de la noche cuando te estás bañando.

`dtime` en tu `curr_ping.csv` es la hora en que la cajita blanca de la FCC hizo la prueba. Nosotros marcamos:


is_peak_hour = 1 SI la prueba fue entre 19:00 y 23:00 (Hora de alta demanda residencial)
is_peak_hour = 0 SI fue a cualquier otra hora

Si falla a las 9pm cuando lo necesitas, al día siguiente llamas para cancelar y cambiarte a otra compañia

Por eso esta bandera es de negocio.

