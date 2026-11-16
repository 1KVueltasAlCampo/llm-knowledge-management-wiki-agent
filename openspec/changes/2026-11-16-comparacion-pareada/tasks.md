# Tasks

## 1. Estadística
- [x] 1.1 Pruebas primero en `tests/test_estadistica.py` (McNemar exacto, bootstrap reproducible, pares, columnas). Verificación: en rojo.
- [x] 1.2 `src/wikillm/eval/estadistica.py`. Verificación: en verde.

## 2. Informe
- [x] 2.1 `escribir_informe` escribe `comparacion_pareada.csv` y la sección del resumen. Verificación: `tests/test_informe.py` y las nuevas en verde; el informe sigue siendo idéntico al repetirlo.
- [ ] 2.2 Regenerar `results/oficial-1/informe/` y anotarlo en la bitácora. Verificación: `ruff check`, `ruff format --check` y `pytest`.
