# Tasks

## 1. Alineación (G0)

- [x] 1.1 Rama `data/corpus`, bitácora `docs/bitacora-datos.md`, decisión 0003 y `specs/propuesta-gold-v1.md`. Verificación: archivos en el commit 7983a8b.

## 2. Selección del corpus (G4)

- [x] 2.1 Cliente de la API de arXiv y reunión de candidatos (`uv run python -m wikillm.corpus candidatos`). Verificación: pruebas `tests/test_corpus_arxiv_api.py`; 61/61 ids del `.bib` encontrados en la API.
- [x] 2.2 Descargar Bronze de los candidatos y medir `html_available` y referencias cruzadas. Verificación: `capture.jsonl` por candidato; 52/53 con HTML.
- [x] 2.3 Elegir los 50 con los criterios de `docs/corpus.md` y escribir `data/corpus_ids.txt`. Verificación: 50 ids, las 5 semillas incluidas (commit 941aaae).

## 3. Gold, manifest y fragmentos (G1–G3)

- [x] 3.1 Fragmentos citables (`spans`). Verificación: `tests/test_corpus_spans.py`.
- [x] 3.2 Manifest con orden, mitad y señales. Verificación: `tests/test_corpus_manifest.py`.
- [x] 3.3 Ingesta de los 50, validación, `corpus.jsonl`, `manifest_corpus.jsonl` y `spans.jsonl`. Verificación: `uv run python -m wikillm.ingest` sin errores y `manifest` con 50 filas y todas con HTML.

## 4. Métricas (G6)

- [x] 4.1 Contrato `specs/contrato-resultados.md` y módulo `wikillm.eval` (capa 1, juez, fundamentación, cobertura, acuerdo). Verificación: `tests/test_eval.py`.
- [x] 4.2 Corrida de métricas sobre resultados sintéticos con el banco real. Verificación: `results/sintetico/metricas_por_paso.csv`.

## 5. Banco de preguntas (G5)

- [x] 5.1 Redactor anclado al Gold, plan con estimación y hojas de anotación. Verificación: `tests/test_eval_redaccion.py`.
- [ ] 5.2 Borradores de la mitad A (requiere `.env` con claves y tarifas `DRAFT_PRICE_*`). Verificación: `data/preguntas/borradores_A.jsonl` y `validar-banco` sin problemas.
- [ ] 5.3 Verificación humana y acuerdo (Juan Diego y Juan David). Verificación: `acuerdo` sobre las dos hojas.

## 6. Cierre

- [ ] 6.1 `uv run ruff check . && uv run ruff format --check . && uv run pytest`.
