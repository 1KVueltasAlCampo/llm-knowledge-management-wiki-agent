# Tasks

## 1. Lógica
- [x] 1.1 `src/wikillm/eval/inyeccion.py` (ataques, siembra, éxito, elección con semilla, resumen). Verificación: `tests/test_eval_inyeccion.py`.

## 2. Ejecución
- [x] 2.1 `scripts/prueba_inyeccion.py` con modelo guionado probado sin red y tope de gasto de 0,25 USD.
- [x] 2.2 Corrida real con aviso previo (aprobada el 17-nov-2026: 0,10 USD estimados) y resultados en `results/inyeccion/`.

## 3. Documentación
- [x] 3.1 `docs/prueba-de-inyeccion.md` con resultados y límites; actualizar `cumplimiento_rubrica.md`.
- [x] 3.2 `uv run ruff check . && uv run ruff format --check . && uv run pytest`.
