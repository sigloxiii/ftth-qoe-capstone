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

### 3. rtt_p95 - La latencia que REALMENTE sintió el cliente (no el promedio)

**Explicación para gente que no es de redes:**
`rtt_avg` es cuánto tarda un carrito en ir y volver de tu casa al servidor. Si tarda 20ms, va rápido. Si tarda 200ms, va lento y ves "cargando..." en Netflix.

El problema del promedio: Si en un día haces 10 pruebas:
9 pruebas de 20ms (perfecto) + 1 prueba de 500ms (se congeló todo)
Promedio = 68ms -> parece que todo bien, pero el cliente SÍ se enojó en esa de 500ms.

Por eso no usamos promedio, usamos **P95**.

**¿Qué es P95 con lenguaje compun?**
Ordenas las 10 pruebas; de más rápida a más lenta y te quedas con la que está en el lugar 95 de cada 100.

Traducción: "El 95% del tiempo estuviste MEJOR que este valor, y solo el 5% peor".

Si tu P95 es 85ms, significa que casi todo el día estuviste por debajo de 85ms, pero ese 5% de momentos malos ya fue de 85ms o más. Esos son los que provocan llamadas al call center.

**Ejemplo de la vida real:**
Tu tiempo al trabajo: Lunes 20 min, Martes 22, Miércoles 25, Jueves 21, Viernes 90 por tráfico.
Promedio = 35 min -> "no está tan mal"
P95 = 90 min -> "el viernes casi te corren por llegar tarde". Ese viernes es el que cuenta para decidir si cambias de ruta.

Así funciona con internet.

**¿De dónde sacarlo de los datos?**
Del `curr_udplatency.csv` documentado en `03_powershell_udplatency.png`:

Headerss: `unit_id,dtime,ddate,target,rtt_avg,rtt_min,rtt_max,rtt_std,successes,failures`

1. Agrupamos por cliente y día: `unit_id + ddate`
2. Tomamos todas sus `rtt_avg` de ese día (pueden ser 24, una por hora)
3. Calculamos el percentil 95

**Fórmula de negocio:**
rtt_p95 = El valor de latencia que solo el 5% de las pruebas del cliente en ese día superaron

Umbral de riesgo: >80ms
¿Por qué 80ms? Es el límite donde Zoom/Teams empieza a decir "conexión inestable". Para FTTH de fibra, un P95 sano debe estar <40ms. Arriba de 80ms en hora pico (19-23h) ya es motivo de truck roll preventivo de $135 USD.

Resumen para el dashboard:

rtt_avg = foto de un segundo
rtt_p95 = la película de todo tu día, quedándote con el peor momento que sí importa




### 4. risk_flag - ¿Este cliente de fibra es probable que se vaya? (churn)
**indicador indirecto que las empresas utilizan para predecir cuándo un cliente está a punto de abandonar el servicio (churn)

**Explicación para gente que no es de redes:**
Esta sería la variable principal, no hay lista real de quién canceló porque eso es confidencial y solo el ISP lo sabe, así que creamos un proxy: un cliente está en riesgo de irse si su internet falló justo cuando lo estaba usando.

risk_flag = 1 SI (Se le perdieron carritos >1.5% O su P95 >80ms) Y pasó entre 7pm y 11pm
risk_flag = 0 en cualquier otro caso


**Fórmula técnica final (Python):**
```python
risk_flag = 1 si (packet_loss_pct > 1.5 o rtt_p95 > 80) y is_peak_hour == 1
          = 0 si no


Este flag es tu KPI principal:

% Clientes FTTH en Riesgo en Hora Pico = AVG(risk_flag) * 100

Ahorro = Clientes_en_riesgo * 40% que se retienen con acción preventiva * $135 por truck roll evitado

