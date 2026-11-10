# Proposal

## Why

El banco de 60 preguntas ya tiene las dos mitades verificadas por su autor y revisadas por el otro, pero ninguna llegó al estado `acordado`, que la regla 11 exige para que una pregunta cuente en el informe. Hoy `arnes correr` no encuentra preguntas con el filtro por defecto, y no hay un registro del acuerdo entre autores.

## What Changes

- Nueva orden `python -m wikillm.eval acordar --mitad A|B [--pendientes ID,ID] [--ejecutar]`: lee `banco_<mitad>.jsonl` y las dos revisiones de esa mitad (`revision_<mitad>_por_A.json` y `revision_<mitad>_por_B.json`), mide el acuerdo (porcentaje y kappa de Cohen sobre «aceptar o ajustar») y, con `--ejecutar`, pasa a `acordado` las preguntas que no estén pendientes.
- Las preguntas pendientes (que algún autor aún no ha leído) conservan su estado.
- Cada pregunta acordada guarda en `revision.acordado` la fecha y el acuerdo; el resumen de la mitad queda en `results/banco/acuerdo_<mitad>.json`.
- Sin `--ejecutar` solo informa; la orden nunca cambia el estado por su cuenta.

## Capabilities

### New Capabilities
- `banco-acordado`: medida del acuerdo entre autores y paso a «acordado» de una mitad del banco.

## Impact

- Código nuevo en `src/wikillm/eval/acordar.py` y la orden en `eval/__main__.py`; pruebas sin red ni saldo.
- Datos: `revision_A_por_B.json` y `revision_B_por_A.json` (formato de la página de revisión, sin citas de arXiv) y `results/banco/`.
- Sin dependencias nuevas ni llamadas al modelo.
