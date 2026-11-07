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

## 2026-11-07 (Juan David): brazo WikiLLM v1, primera corrida real

Cambio OpenSpec `agente-wiki-v1`. Corrida de desarrollo con `deepseek-flash`, fuera de hora
pico, en `data/wiki/dev` (ignorada por Git). Todas las cifras salen de `results/dev/llamadas.jsonl`
y de la salida de `python -m wikillm.wiki`.

**Ingesta de los 5 primeros papers (2 llamadas por paper: plan y escritura)**

| Paso | Paper | s | Llamadas | USD | Páginas creadas / actualizadas |
|---|---|---|---|---|---|
| 1 | 2405.14831 | 33,6 | 2 | 0,0069 | 5 / 0 |
| 2 | 2502.14802 | 38,3 | 2 | 0,0086 | 2 / 4 |
| 3 | 2602.06052 | 68,6 | 2 | 0,0168 | 5 / 4 |
| 4 | 2603.02473 | 45,7 | 2 | 0,0080 | 2 / 4 |
| 5 | 2603.11768 | 135,2 | 3 | 0,0228 | 3 / 6 |
| Total | | 321,4 | 11 | 0,0630 | 17 páginas |

- El wiki quedó con 17 páginas (5 de paper y 12 de concepto), 13.701 palabras, 5 commits con
  etiquetas `paso-1` a `paso-5`. Citas eliminadas: 0. Enlaces rotos: 0.
- La caché de prefijo funciona: en cada escritura entre el 42 % y el 99 % de la entrada se leyó de
  la caché (19.712 de 20.419 tokens en el paso 1; 4.992 de 11.850 en el paso 4).
- **La escritura del paso 5 llegó al tope de 16.000 tokens de salida**, se cortó el JSON y se
  repitió una vez (de ahí la tercera llamada, 0,0096 USD más). La salida domina el costo
  (hasta 16.000 tokens a 0,60 USD por millón) y las páginas de concepto ya rondan las 800–1.100
  palabras, así que el tope se volverá a alcanzar a medida que crezca el wiki.
- El contador de líneas con cifra sin cita marcó 7 en el paso 4. En las líneas revisadas son
  descripciones con números que no son resultados («3-turn», «top-2k», «3×3»): el criterio es
  grueso y cuenta falsos positivos; no se revisaron las 7 una por una.
- Los resúmenes del índice son de 40 a 70 palabras, no «de una línea»: inflan el índice y los
  resultados de `wiki_search`.

**Tres preguntas reales (wiki de 5 papers)**

| Pregunta | Llamadas | Acciones | s | USD | Resultado |
|---|---|---|---|---|---|
| Algoritmo de recuperación de HippoRAG (un paper) | 3 | 1 búsqueda, 1 lectura | 4,1 | 0,00099 | cita 5 spans |
| Enlace consulta-grafo de HippoRAG 2 frente a HippoRAG (dos papers) | 3 | 1 búsqueda, 1 lectura | 4,6 | 0,00099 | cita 6 spans |
| Hardware cuántico para PPR (no está en el corpus) | 5 | 2 búsquedas, 1 lectura | 5,7 | 0,00101 | se abstiene, sin citas |

- Todas las citas resuelven a `span_id` de `spans.jsonl`. La cifra «12,5 %» de la segunda
  respuesta aparece en el Gold de 2502.14802 («query-to-triple improves Recall@5 by 12.5 %»).
- La línea de resultado de un brazo wiki pasa `leer_resultados`.
- La abstención usó 5 llamadas porque una acción mal formada se repitió y se recuperó.
- Contexto leído: 4.414, 4.418 y 4.852 tokens (entrada total de 6.611, 6.632 y 14.072).
- El RAG medido en pruebas anteriores gastó 0,00032–0,00041 USD por pregunta: el wiki cuesta unas
  2,5 veces más con 5 papers. No es el 21× que reporta la literatura, pero el wiki es pequeño aún.

**Proyección a 50 papers (no medida; extrapolación)**
- Ingesta: la media fue 0,0126 USD y 64 s por paper, y el costo sube con el tamaño del índice y de
  las páginas (pasos 3–5: 0,0159 USD de media). Rango esperado: 0,6–1,5 USD y 1–1,5 h para los 50.
- Consulta: mide de nuevo con el wiki de 50 papers; hoy no hay base para extrapolar.
- Una sola corrida de desarrollo con 3 preguntas no permite comparar la calidad con el RAG.

**Ajuste tras la primera corrida y segunda medición (mismos 5 papers, carpeta `data/wiki/dev2`)**

Cambios en las instrucciones de escritura: las páginas de concepto bajo unas 600 palabras (antes
1.200) y el resumen de una sola línea de 25 palabras como máximo. No cambió el tope de 16.000
tokens de salida.

| | Primera corrida (`dev`) | Segunda corrida (`dev2`) |
|---|---|---|
| Costo de ingesta, 5 papers | 0,0630 USD | 0,0282 USD |
| Tiempo de ingesta | 321 s | 198 s |
| Llamadas | 11 (una repetición por corte de JSON) | 10 |
| Páginas | 17 | 20 |
| Palabras en los cuerpos | 12.712 | 9.085 |
| Página de concepto, máximo / media (palabras) | 1.039 / 707 | 575 / 416 |
| Resumen, máximo / media (palabras) | 58 / 38 | 22 / 16 |
| Citas eliminadas / enlaces rotos | 0 / 0 | 0 / 0 |
| Líneas con cifra sin cita | 7 | 8 (4 en el paso 4 y 4 en el paso 5) |

- Las tres preguntas, repetidas sobre `dev2`, dieron respuestas equivalentes: 0,00079, 0,00077 y
  0,00078 USD (antes 0,00099, 0,00099 y 0,00101), con las mismas llamadas (3, 3 y 5) y la
  abstención correcta. Citan spans que existen y la cifra «12,5 %» sigue respaldada por el Gold.
- El wiki más pequeño sale más barato de construir y de consultar. Lo que no se ha medido es si
  condensar a 600 palabras pierde detalle en preguntas de cifras exactas: eso lo dirá el banco.
- La proyección a 50 papers baja con la media de `dev2` (0,0056 USD y 40 s por paper): 0,3–0,8 USD
  y unos 35–60 min. Sigue siendo extrapolación: el costo sube con el tamaño del wiki.
- El contador de líneas con cifra sin cita sigue siendo grueso (cuenta números descriptivos).
