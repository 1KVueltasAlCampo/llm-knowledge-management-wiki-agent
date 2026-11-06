# Bitácora de la parte de datos y evaluación (Juan Diego)

Rama de trabajo: `data/corpus`. Alcance: corpus de 50 papers, banco de preguntas y métricas de
calidad. RAG, agente de la wiki y arnés son de Juan David.

## 2026-11-06

**Estado del repo al empezar.** Juan David ya construyó el pipeline Bronze → Silver → Gold
(`src/wikillm/ingest/`) para 5 papers semilla, con 73 pruebas en verde. Este trabajo lo extiende,
no lo reemplaza.

**Decisiones tomadas con Juan Diego:**
1. Roles de modelos: responde `deepseek-flash`, redacta `deepseek-v4-pro`, juzga Gemini
   (`docs/decisiones/0003-…`, pendiente de revisión de Juan David).
2. El corpus se completa hasta 50 con papers de 2026; las semillas HippoRAG (2024) y
   HippoRAG 2 (2025) entran marcadas `pre_corte=true` y se reportan aparte.
3. En el repo la evidencia de cada pregunta va como `span_id` + offsets + huella; el fragmento
   literal solo se reconstruye en local (regla 8 de la constitución).

**Conflictos con el prompt inicial, resueltos a favor del repo:**
- Ritmo: `Crawl-delay: 15` de `robots.txt` en lugar de 3 s. La API de arXiv
  (`export.arxiv.org`) se rige por sus términos: 1 petición cada 3 s, una conexión.
- `User-Agent` genérico sin datos personales (spec Gold §5); no se pidió correo.
- Cliente de modelo: el SDK `openai` vía `ClienteModelo`, no `litellm`.
- Tope por corrida: `MAX_USD_PER_RUN` (2 USD) en lugar de 5.

**Hallazgo:** el corte de entrenamiento de DeepSeek-V4.1-Flash no está publicado (ver decisión
0003). Mitigación: corpus de 2026 + sonda de contaminación a libro cerrado (ver
`docs/corpus.md`).

**Propuesta escrita para Juan David:** `specs/propuesta-gold-v1.md` (versión en `sources`,
`spans.jsonl`, campos nuevos del manifest).

**Corpus cerrado (tarde del 6-nov).** 53 candidatos descargados a Bronze; 2604.11243 no
tiene HTML. Se eligieron 50 con la regla reproducible (`docs/corpus.md` §5). El validador
del Gold daba falsos positivos con marcadores como `<name>`; con la aprobación de Juan Diego se
restringió a etiquetas HTML reales (commit con prueba). Se generaron
`data/manifest_corpus.jsonl` (50 filas) y `data/gold/spans.jsonl` (8.387 fragmentos). Las
métricas corren de punta a punta con un banco sintético (`results/sintetico/`).

**Modelos confirmados por API (`GET /models`, 6-nov):** `deepseek-flash` y `deepseek-v4-pro`.

**Plan de borradores (sin gastar):** autor A, 54 llamadas y ~1,75 M tokens de entrada; autor
B, 42 llamadas y ~1,71 M. El costo depende de las tarifas de `deepseek-v4-pro`, que faltan en
`.env`.

**Preguntas en inglés**, el idioma del corpus, salvo que los autores decidan otra cosa.

## Pendiente

- Juan Diego: completar `.env` con `GEMINI_API_KEY` y las tarifas `DRAFT_PRICE_*`
  (`DEEPSEEK_API_KEY` ya está).
- Juan Diego: añadir a `.env.example` (los permisos del asistente no le dejan editarlo):
  `DRAFT_MODEL=deepseek-v4-pro`, `GEMINI_API_KEY=`, `JUDGE_MODEL=gemini-3.1-flash-lite`.
- Juan David: revisar decisión 0003 y `specs/propuesta-gold-v1.md`.
- Juan David: revisar el cambio del validador en `src/wikillm/ingest/gold.py` (`ETIQUETAS_HTML`).
- Juan David: revisar `AGENTS.md` (guía única para agentes), el `CLAUDE.md` reducido y las reglas
  11–13 propuestas en `CONSTITUTION.md`.
