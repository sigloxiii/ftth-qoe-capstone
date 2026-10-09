# Hallazgo de Error en Muestreo - FTTH QoE

**Fecha:** 27/09/2026  
**Archivo afectado:** `data/risk_flag_sample.csv` (0 filas)  
**Fase:** Process - Google Data Analytics Capstone

## 1. Síntoma detectado
El pipeline de GitHub Actions pasó en verde, pero el archivo de salida `risk_flag_sample.csv` resultó vacío:
```
(0, 15) - Empty DataFrame
unit_id,dtime,ddate,target,rtt_avg,...,risk_flag
```

## 2. Causa raíz
Metodología de muestreo por conveniencia: `head(1000)`.

- `sample1000_curr_ping.csv` se generó tomando las primeras 1000 filas del archivo original de 6.8GB.
- El archivo original está ordenado por `unit_id`. Las primeras 1000 filas pertenecen a 2 whiteboxes DSL/Cable (IDs: 26226437, 52849181).
- `fiber_units.csv` filtrado a Fiber solo contiene 285 IDs diferentes (IDs: 447, 1014, 5521...).
- **Overlap:** 0 coincidencias entre `sample1000_curr_ping.csv` y `fiber_units.csv`.
Por qué es sesgo de conveniencia:
FCC MBA ordena los unit_id por antigüedad de enrolamiento. Los primeros 1000 = Whiteboxes de 2012-2016. En 2023-2024 esos equipos:

Tienen hardware desfasado (SamKnows v1)
Están en hogares con planes antiguos <100 Mbps
Sobrevivencia sesgada: solo quedan los que no han hecho churn

Al hacer:
```python
df_ping_fiber = df_ping.merge(df_fiber[["unit_id"]], on="unit_id", how="inner")
```
El resultado es 0 filas → `df_final` 0 filas → exportación vacía.

Validación realizada:
- `sample1000_curr_ping.csv`: 0 / 1000 overlap con Fiber
- `sample1000_httpgetmt.csv`: 213 / 1000 overlap
- `sample1000_udplatency.csv`: 278 / 1000 overlap

## 3. Por qué es una metodología equivocada
1.  **Sesgo de selección:** Tomar los primeros N registros no es aleatorio, depende del orden del archivo.
2.  **No representa la población objetivo:** El objetivo del proyecto es FTTH (Fiber), pero la muestra no contiene Fiber.
3.  **No reproducible:** Si el proveedor reordena el CSV, "los primeros 1000" cambian.

## 4. Nuevo enfoque (correctivo)

**Principio:** Filtrar primero la población objetivo, luego muestrear.

> Población = Technology == Fiber (285 unit_id)
> Muestra = 1000 mediciones aleatorias de esa población

**Implementación simple y justificable:**

```python
import pandas as pd

# 1. Cargar IDs de población objetivo
fiber_ids = pd.read_csv("data/fiber_units.csv", encoding='utf-8-sig')["unit_id"]

# 2. Cargar archivo original (solo columnas necesarias para memoria)
df = pd.read_csv("data/original_curr_ping.csv", 
                 usecols=["unit_id","dtime","target","rtt_avg","rtt_min","rtt_max","successes","failures"],
                 encoding='utf-8-sig')

# 3. Filtrar por población Fiber
df_fiber = df[df["unit_id"].isin(fiber_ids)]

# 4. Muestreo aleatorio reproducible
df_sample = df_fiber.sample(n=1000, random_state=42)

# 5. Guardar normalizado
df_sample.to_csv("data/sample1000_curr_ping.csv", index=False, encoding='utf-8-sig')
```

Ventajas:
- 100% de las filas son Fiber → el `inner join` ya no da 0.
- `random_state=42` hace el experimento reproducible para el evaluador.
- Se puede explicar sin código avanzado: "filtré y luego tomé aleatorio".

## 5. Plan de acción
- [ ] Re-generar `sample1000_curr_ping.csv` con nuevo método
- [ ] Re-generar `sample1000_httpgetmt.csv` y `sample1000_udplatency.csv` con mismo método para consistencia
- [ ] Re-ejecutar `01_process.ipynb` y validar que `risk_flag_sample.csv` tenga >0 filas
- [ ] Actualizar `data_cleaning.md` con esta corrección
- [ ] Commit: `fix: sampling method from head to filtered random sample`

## 6. Lección aprendida
El muestreo por conveniencia (`head`) funciona para explorar rápido en local, pero rompe el pipeline cuando la población objetivo es un subconjunto. Para ETL productivo, siempre filtrar por la clave de negocio (`unit_id` en `fiber_units`) antes de muestrear.
