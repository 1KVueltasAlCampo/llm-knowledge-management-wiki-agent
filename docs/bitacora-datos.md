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

**Banco de la mitad A cerrado (noche del 6-nov).** Juan Diego revisó 33 borradores en la
página local (`wikillm.eval revision`) y eligió 31. En una revisión asistida se acordaron 17
ajustes, registrados con su motivo en `data/preguntas/ajustes_A.json`:
- 4 descartes: una contradicción elegida/descartada y tres preguntas sin respuesta única o mal
  planteadas.
- Correcciones de respuestas imprecisas y de claves que ya estaban en la pregunta.
- 2 reclasificaciones: A016-T3-02 pasa a T1 y A018-T4-03 a T2.
- 3 reemplazos (A039-T4-03, A016-T4-03 y A013-T3-02), con las cifras verificadas en el Gold.
- Las T5 se aceptan: abstenerse es lo correcto por diseño.

Resultado: `data/preguntas/banco_A.jsonl` con 30 preguntas en `verificado_a` (10 T1, 7 T2,
6 T3, 2 T4 y 5 T5; 21 de T1–T4 con ingesta ≤ 30). Las decisiones originales del revisor
están en `data/preguntas/revision_A_por_A.json`.

**Hallazgo sobre las T4:** el redactor escribía "According to the later paper…", y así la
pregunta no tiene respuesta antes de esa ingesta. Las T4 se redactan en forma neutral ("…has
been reported…; give the most recent report") para que la respuesta cambie de un tramo al
otro.

## Pendiente

- Juan Diego: completar `.env` con `GEMINI_API_KEY` y las tarifas `DRAFT_PRICE_*`
  (`DEEPSEEK_API_KEY` ya está).
- Juan Diego: añadir a `.env.example` (los permisos del asistente no le dejan editarlo):
  `DRAFT_MODEL=deepseek-v4-pro`, `GEMINI_API_KEY=`, `JUDGE_MODEL=gemini-3.1-flash-lite`.
- Juan David: revisar decisión 0003 y `specs/propuesta-gold-v1.md`.
- Juan David: revisar el cambio del validador en `src/wikillm/ingest/gold.py` (`ETIQUETAS_HTML`).
- Juan David: revisar `AGENTS.md` (guía única para agentes), el `CLAUDE.md` reducido y las reglas
  11–13 propuestas en `CONSTITUTION.md`.
- Juan David: verificar las mismas 30 preguntas de la mitad A con la página (revisor B) para
  calcular el acuerdo, y redactar y revisar su mitad (B).

## 2026-11-06 (Juan David): T4 neutras y medida de respuesta obsoleta

Acordado con Juan Diego por mensaje. Los T4 deben poder contestarse en cualquier paso, así que
la pregunta no menciona el orden de los papers y trata de un solo dato; lo que cambia es la
respuesta correcta con el paso. Cambios (cambio OpenSpec `t4-neutras`):

- `src/wikillm/eval/redaccion.py`: nueva instrucción de T4 y descarte de borradores que mencionen
  el orden o no traigan `answer_before` con `answer_before_keys`. Las claves previas ya no se
  borran: pasan a ser `respuesta_clave` del tramo inicial.
- `src/wikillm/eval/banco.py`: `validar-banco` marca las T4 que mencionen el orden o no tengan
  claves previas. Sobre los 102 borradores de A marca 13 y 18.
- `src/wikillm/eval/metricas.py`: nueva medida `obsoleta` (tras el cambio, no es correcta y repite
  las claves previas) y, por sistema y paso, `obsoletas` y `tasa_obsoleta`.
- Los borradores de A no se regeneran: los T4 con problema se corrigen o descartan en la página
  de revisión. Los de B se generan ya con la instrucción nueva.
- `.env.example` ya incluye `DRAFT_*`, `GEMINI_API_KEY` y `JUDGE_MODEL` (decisión 0003).

## 2026-11-07 (Juan David): RAG v2 sobre el contrato de resultados

Cambio OpenSpec `contrato-brazo-v2`. El RAG ya cumple `specs/contrato-resultados.md`: ingiere un
paper a la vez en `orden_ingesta`, cita `span_id`, se abstiene con una frase común y reporta
`context_tokens`. Los fragmentos salen de los spans de `data/gold/spans.jsonl`, y al ingerir se
comprueba que el hash del Gold local coincide con `data/gold/corpus.jsonl`.

- **Ingesta real de los 50 papers** (GPU, bge-small): 5.430 fragmentos en 159 s, sin errores de hash.
  Una segunda ingesta tarda 0,4 s y no recalcula ningún embedding.
- **Recuperación sobre los 102 borradores de A** (k = 5, sin gastar saldo). Ahora se compara por
  `span_id` exacto de la evidencia:

| Tipo | Papers requeridos, todos en el top-5 | `span_id` de la evidencia, todos | alguno |
|---|---|---|---|
| T1 (46) | 78 % | 52 % | 52 % |
| T2 (19) | 32 % | 0 % | 42 % |
| T3 (19) | 16 % | 5 % | 26 % |
| T4 (18) | 11 % | 0 % | 44 % |

  Con el RAG v1 (6-nov, por pasaje aproximado) las T1 daban 78 % de papers y 48 % de pasaje; las de
  dos fuentes, 26–28 % de papers con ambos. Es comparable. Lo esperado de un RAG de una ronda:
  casi nunca trae a la vez las dos fuentes de una pregunta T2–T4.
- Para el wiki, `ingerir` queda definido en la interfaz y el registro `ingestas.jsonl` (costo por
  ingesta) es un añadido propuesto al contrato de resultados.
