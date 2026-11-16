# Tasks

## 1. Exportar
- [x] 1.1 Pruebas primero en `tests/test_auxiliar.py` (ítems ciegos, indeterminadas siempre, muestra reproducible, claves). Verificación: `uv run pytest tests/test_auxiliar.py` en rojo.
- [x] 1.2 `src/wikillm/eval/auxiliar.py` con `exportar`. Verificación: pruebas en verde.

## 2. Importar y acuerdo
- [x] 2.1 Pruebas primero (acuerdo total/por origen/por sistema, veredicto inválido, rótulo). Verificación: en rojo.
- [x] 2.2 `importar` reutilizando `kappa_cohen`. Verificación: en verde.

## 3. Comando y docs
- [x] 3.1 Subcomando `auxiliar` en `eval/__main__.py` y línea en `AGENTS.md`. Verificación: `--help` y ejecución sobre `results/piloto-2`.

## 4. Cierre
- [ ] 4.1 Veredictos de Claude sobre `preliminar-1` y acuerdo reportado como auxiliar; sincronizar spec y archivar. Verificación: `uv run ruff check . && uv run ruff format --check . && uv run pytest`.
