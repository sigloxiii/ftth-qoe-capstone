# Limpieza de datos - FTTH QoE

## Problema detectado
1. **Encoding**: Los CSV de FCC venían en UTF-16 LE (bytes FF FE). Causaba:
   - Excel abre todo en una columna
   - GitHub Actions falla con `UnicodeDecodeError: 0xFF`
   - `wc -l` contaba mal las filas
2. **Columnas inconsistentes**: `fiber_units.csv` traía `Unit ID` con espacio y mayúsculas, mientras que `sample1000_*.csv` usa `unit_id` snake_case. Causaba `KeyError: unit_id not in columns` en Actions.
3. **Filtro**: `fiber_units.csv` original traía 2025 filas (DSL, Cable, Fiber). Para churn FTTH solo necesitamos Fiber = 285 filas.

## Solución aplicada (simple y justificable)
1. Conversión UTF-16 LE -> UTF-8 con BOM (`utf-8-sig`) para compatibilidad Excel + Python + Linux
   - Tool: Excel > Guardar como UTF-8
2. Renombrado de columnas a snake_case minúsculas:
   - `Unit ID` -> `unit_id`, `Whitebox Model` -> `whitebox_model`, etc.
3. Filtro Technology == Fiber (285 filas)

## Archivos finales en data/
- fiber_units.csv: 285 filas, solo Fiber, columnas snake_case, UTF-8-sig
- sample1000_curr_ping.csv: 1001 filas, UTF-8-sig
- sample1000_httpgetmt.csv: 1001 filas, UTF-8-sig
- sample1000_udplatency.csv: 1001 filas, UTF-8-sig


