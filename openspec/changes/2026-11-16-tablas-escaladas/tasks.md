# Tasks

## 1. Conversor
- [x] 1.1 Reconocer `span.ltx_tabular`, `ltx_tr`, `ltx_td`, `ltx_th` y `ltx_colspan_N` en `markdown.py`. Verificación: `uv run pytest tests/test_ingest_markdown.py`.
- [x] 1.2 Reconvertir el Bronze de los 50 y de la ampliación: solo cambian 4 papers. Verificación: comparar con el Gold actual.

## 2. Gold de 100 papers
- [x] 2.1 Construir `data/corpus100` con el conversor corregido y regenerar `spans.jsonl` de los cuatro papers. Verificación: `uv run python -m wikillm.ingest --ids data/corpus100/ids.txt --datos data/corpus100` termina sin problemas.
- [x] 2.2 Reanclar las preguntas con evidencia en esos papers. Verificación: `uv run python -m wikillm.eval validar-banco` sin problemas.
