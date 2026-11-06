# Proposal

## Why

El experimento necesita el corpus completo (50 papers posteriores al corte del modelo, en orden
de ingesta), un banco de 60 preguntas con respuesta fijada por humanos y métricas de calidad
que se calculen sobre lo que produzca el arnés. El mini-corpus de 5 papers desbloqueó los
prototipos; esto completa la parte de Juan Diego sin tocar RAG, wiki ni arnés.

## What Changes

- `wikillm.corpus`: metadatos verificados contra la API de arXiv, búsqueda de candidatos de
  2026, manifest con orden de ingesta, mitad por autor y señales de selección, y fragmentos
  citables (`spans.jsonl`) con posición y huella, sin texto.
- `wikillm.eval`: banco de preguntas (esquema y validación), correctitud en dos capas
  (determinista y juez Gemini), fundamentación, cobertura por paso, abstención, contexto y
  costo; acuerdo entre autores (porcentaje y kappa de Cohen); borradores con LLM anclados a
  fragmentos del Gold y hojas de anotación locales.
- Contratos para revisión de Juan David: `specs/contrato-resultados.md` y
  `specs/propuesta-gold-v1.md`. Decisión `docs/decisiones/0003` (roles de los modelos).
- `data/corpus_ids.txt` pasa de 5 a 50 identificadores.

## Capabilities

### New Capabilities
- `corpus-seleccion`: selección reproducible de los 50 papers y su manifest.
- `evaluacion`: banco de preguntas y métricas de calidad sobre el contrato de resultados.

### Modified Capabilities

## Impact

- Código nuevo en `src/wikillm/corpus/` y `src/wikillm/eval/`; no cambia `ingest/` ni `common/`.
- Peticiones: 1 cada 3 s a la API de arXiv; 1 cada 15 s a `arxiv.org` (Crawl-delay).
- Gasto: borradores con `deepseek-v4-pro` y juez `gemini-3.8-flash`, siempre con estimación
  previa y tope (`MAX_USD_PER_RUN` y confirmación por encima de 5 USD).
- Se versionan solo identificadores, metadatos, posiciones y huellas (regla 8).
