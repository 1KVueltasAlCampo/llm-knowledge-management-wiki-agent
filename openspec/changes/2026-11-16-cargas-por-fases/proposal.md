# Proposal

## Why

El experimento base se hará con tres cargas progresivas del corpus de 100 papers y cuatro puntos de
consulta (0, 33, 66 y 100). El orden estrictamente cronológico deja casi todas las T2 sin fuentes parciales
y no reparte las re-mediciones (T3 y T4) entre las cargas. Ver decisión 0009.

## What Changes

- `data/corpus100/fases.json` fija la fase de cada paper (33, 33 y 34) con las 10 excepciones a la cronología.
- `wikillm.corpus fases` reordena el manifest: fase, luego fecha de la primera versión, y añade `fase`.
- `data/corpus100/manifest.jsonl` y `data/preguntas/banco_100.jsonl` (con `ingesta_minima` y los pasos de
  las T4 recalculados por `ampliar-banco`) se regeneran con ese orden.
- ADR 0009.

## Impact

- El orden de ingesta de `corpus100` deja de ser cronológico en 10 de 100 papers. `oficial-1` y el
  Gold de 50 no cambian.
- Contrato del manifest: se añade la columna `fase` (cambio aditivo).
