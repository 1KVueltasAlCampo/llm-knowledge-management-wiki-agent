# Proposal

## Why

Faltan días para la pre-sustentación oficial y hoy solo hay pilotos de 17 preguntas en 2 pasos.
`wikillm.eval metricas` ya escribe una fila por (sistema, paso), pero no hay cortes por tipo de
pregunta (T1–T5), ni tablas legibles, ni figuras, ni un comando que regenere todo desde
`results/<corrida>/`. Sin eso, la corrida completa (60 preguntas × 10 pasos) terminaría en CSV
sueltos y las cifras del informe se copiarían a mano, lo que rompe la regla de que las cifras
salen solo de corridas guardadas (constitución #9).

## What Changes

- Nuevo comando `uv run python -m wikillm.eval informe --corrida results/<corrida>` que lee
  `evaluados.jsonl` (ya escrito por `metricas`) y escribe, en `results/<corrida>/informe/`:
  - `por_sistema_paso.csv` y `por_tipo.csv` (cobertura, abstención correcta, obsolescencia,
    fundamentación, contexto, tokens por correcta, costo);
  - `resumen.md` con las tablas en Markdown, listas para pegar en documentos;
  - figuras SVG: cobertura contra paso de ingesta (RAG y wiki), tokens de contexto contra paso y
    costo acumulado por sistema.
- Las figuras se generan en SVG con Python puro: no se añaden dependencias (no hay matplotlib).
- Reutiliza `agregar` de `eval/metricas.py`; no cambia ninguna métrica existente ni el contrato de
  resultados.

## Impact

- Código nuevo: `src/wikillm/eval/informe.py` y su subcomando en `eval/__main__.py`.
- Specs: nueva capacidad `informe` (delta ADDED).
- No llama a ninguna API ni cambia corridas existentes (constitución #7).
