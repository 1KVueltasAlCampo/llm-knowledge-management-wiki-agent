# Proposal

## Why

La rúbrica (R.6.2 Cr6 y R.7.2 Cr5) pide medir el costo y el tiempo por paso y presentar la eficiencia como
calidad frente a costo. Hoy hay costos sueltos en cada corrida, pero ninguna vista que una la construcción
del wiki, la consulta y la calidad, ni que diga qué parte del costo del wiki se puede recortar.

## What Changes

- `scripts/costo_calidad.py` (sin gasto): costo y tiempo de ingesta por paper y por paso, calidad y costo
  por consulta de cada sistema y escenarios de uso (100, 1.000 y 10.000 consultas). Salida en
  `results/costo-calidad/`.
- Análisis, sin gasto, de dónde sale el costo de una consulta del wiki (por número de acciones).
- Un experimento barato con el arnés existente: el wiki del paso 100 con tope de 4 acciones
  (`ampliado-wiki-tope4`, unos 0,07 USD) para ver si el recorte de costo cuesta exactitud.
- `docs/eficiencia-calidad-costo.md` con los resultados y sus límites.

## Capabilities

### Added Capabilities
- `evaluation`: vista de calidad frente a costo y tiempo.

## Impact

- No cambia el arnés, los prompts ni las corridas anteriores. Dueño: Juan David (`scripts/`, `docs/`).
