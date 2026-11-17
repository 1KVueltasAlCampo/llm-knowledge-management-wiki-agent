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

## 2026-11-07 (Juan David): arnés de comparación, piloto real

Cambio OpenSpec `arnes-comparacion`: `python -m wikillm.arnes correr`. Piloto `piloto-1` con
`deepseek-flash`, fuera de hora pico, sábado. **No vale para el informe**: usa borradores
(`--estado-minimo borrador`) y `corrida.json` lo marca con `valida_para_informe: false`.

- Configuración: 17 preguntas del banco (T1, T4 y T5), pasos 0 y 5, RAG con k = 5 y wiki con tope de
  8 acciones: 68 respuestas, 5 papers ingeridos en cada brazo.
- Los brazos reales (índice de Chroma en GPU y wiki en disco) arrancan y responden desde el paso 0.
  Los archivos pasan `leer_resultados` y `python -m wikillm.eval metricas` corre sobre ellos.

| | RAG | Wiki |
|---|---|---|
| Respuestas / abstenciones | 34 / 32 | 34 / 27 (28 tras la reanudación) |
| Costo de ingesta | 0 USD, 10 s | 0,0363 USD, 222 s |
| Costo de las 34 preguntas | 0,0040 USD, 36 s | 0,0136 USD, 134 s |
| Contexto mediano | 384 tokens | 1.021 tokens |

- Gasto registrado en `respuestas` e `ingestas`: 0,052 USD; contando la tanda repetida, unos 0,056 USD.
  La estimación del arnés (cota alta) era 0,31 USD: queda unas 6 veces por encima del gasto real.
- Costo por respuesta: 0,00012 USD el RAG y 0,0004 USD el wiki con 5 papers (unas 3 veces más). Con
  las cifras de la cota, la corrida completa saldría por debajo de 5 USD y no pediría confirmación.
- **Solo 6 de las 17 preguntas eran respondibles en el paso 5** (el resto necesita papers que aún no
  entran, o es T5). En esas, `eval metricas` da cobertura 0,33 en el RAG (2 de 6) y 0,83 en el wiki
  (5 de 6), con una respuesta indeterminada que necesitaría el juez. Con n = 6 no es evidencia de
  nada: solo muestra que la cadena arnés → métricas funciona.
- **Reanudación probada con los brazos reales**: se recortaron a mano los últimos 10 resultados y las
  5 trazas del wiki, y se repitió la misma orden. Salió «Paso 0: ya estaba completo» y «Paso 5: 10
  respuestas por hacer de 34». No hubo ingestas repetidas ni costo de ingesta nuevo, y el archivo
  quedó con 68 claves únicas en 68 líneas, 10 ingestas y 34 trazas.
- **Con temperatura 0, el wiki no repitió una respuesta**: AT5-T5-12 (T5) se contestó con una cita
  en la primera tanda y con la abstención en la segunda («No page mentions a method called
  "HyperAddress"…»). El texto de la primera respuesta no se conservó, así que no se pudo comprobar
  si era una alucinación. El modelo del proveedor no es determinista: una sola corrida por pregunta
  tiene ruido, y el informe debe decirlo o repetir las corridas.
- Las preguntas repetidas parecen abaratarse por la caché de prefijo del proveedor (no se verificó; el RAG pasó de 0,0040 a
  0,0032 USD en las 34 respuestas al repetir 5): los costos de una repetición no se pueden comparar
  con los de una primera corrida.
- Tiempos medidos: el wiki tarda 3,9 s por respuesta y el RAG 1,1 s; ingerir cuesta 44 s por paper en
  el wiki. Para la corrida completa (60 preguntas, 11 pasos, 50 papers) la extrapolación es de 2 a 3
  horas, y 1 a 2,5 USD. Es una extrapolación: el wiki crece y cada consulta se encarece.

## 2026-11-07 (Juan David): banco de la mitad B

- **Candidatas.** Los 67 borradores T1–T4 de B no tenían ninguna T4 real (una comparaba dos
  datasets, dos no cambiaban de valor y la cuarta daba el valor de otro sistema) y solo una T3
  válida: las demás comparaban sistemas que nunca se midieron en lo mismo o dependían de
  afirmaciones negativas. Se añadieron 9 candidatas (6 T3 y 3 T4) a `borradores_B.jsonl`,
  redactadas por Claude (`redactado_por`) a partir de cifras que el corpus repite o contradice y
  verificadas contra el Gold: huella de cada fragmento, cada clave literal en la evidencia y
  `validar_banco` sin problemas.
- **La T4 de B es estructuralmente escasa.** Exige que un paper posterior repita la cifra y que
  ese paper sea de B (orden par): solo ocurre con HippoRAG → HippoRAG 2 y con LongMemEval-S
  (ReFind → APDMem). Las demás repeticiones las hacen papers de la mitad A.
- **Selección.** Cuatro revisores independientes evaluaron las 76 candidatas T1–T4 y las 9 T5 sobre
  un paquete con códigos neutros y orden aleatorio. Uno aceptó 78 de 85, incluidas todas las T3 con
  afirmaciones negativas que los otros tres descartaban, y con dos «correcciones» sobre contenido
  que no está en el paquete; no se tuvo en cuenta. Con los otros tres se contrastó cada
  desacuerdo contra el Gold. Cambios respecto a la primera elección: se quitó la comparación
  ReFind–APDMem (50 frente a 500 preguntas y backbones distintos) y una T5 demasiado fácil, y se
  recuperó una T2 que se había descartado por error porque su respaldo estaba en pasajes que el
  paquete no ofrecía.
- **Resultado.** `banco_B.jsonl` tiene 30 preguntas: 13 T1, 5 T2, 5 T3, 2 T4 y 5 T5, con 20 de las 25
  de T1–T4 en ingesta ≤ 30. Seis llevan corrección (ajustes en `ajustes_B.json`, con motivo).
  `banco.jsonl` queda con las 60 (30 de A y 30 de B) y `validar-banco` no reporta problemas.
- **Estado.** Las de B quedan en `borrador`: la selección y las correcciones están aprobadas, pero
  falta la verificación humana de cada respuesta contra su paper. El material de la selección
  (paquete, respuestas de los revisores, votos) lleva texto de arXiv y vive fuera del repo.

## 2026-11-09 (Juan David): comparación puntual de una pregunta y ajuste de dos T4 de B

Cambio OpenSpec `demo-comparacion`: `python -m wikillm.arnes comparar "<pregunta>" --wiki <carpeta>`
hace la misma pregunta al RAG y al wiki, con el mismo modelo, y muestra respuesta, citas con el
fragmento del Gold que las respalda, los pasos del agente del wiki (qué buscó, qué leyó), tokens,
segundos y dólares. El paso de ingesta lo fija el wiki indicado. La evidencia queda en
`results/demo/comparaciones.jsonl`, sin texto de arXiv. La traza del agente guarda ahora el detalle
ordenado de sus acciones. El recorrido está en [docs/demo.md](demo.md).

**Ensayo del recorrido sobre el wiki de desarrollo (5 papers, deepseek-flash):**

| Paso | Sistema | Resultado | Llamadas | USD | s |
|---|---|---|---|---|---|
| 5 (BeliefShift aún no ingerido) | RAG | se abstiene | 1 | 0,000200 | 1,3 |
| 5 | Wiki | 5 búsquedas, lee el índice y se abstiene | 7 | 0,000451 | 7,5 |
| Ingesta del paper 6 | Wiki | 2 páginas creadas, 5 actualizadas, 0 citas eliminadas | 2 | 0,0083 | 38,1 |
| 6 | RAG | 68,160 con cita `2603.23848#s18.p3` | 1 | 0,000239 | 1,6 |
| 6 | Wiki | 68,160 con la misma cita | 3 | 0,000409 | 3,7 |

**Dos T4 de B corregidas por lo que mostró el ensayo.**
- La T4 de 2Wiki («el Recall@5 más alto que el corpus reporta para HippoRAG») era ambigua: el wiki
  respondió 93,9, que es «IRCoT + HippoRAG», una combinación de pasos múltiples. Se acotó la
  pregunta de 2Wiki y la de MuSiQue a «de un solo paso, sin combinaciones con recuperación
  iterativa como IRCoT». Con esa restricción el máximo pasa de 89,5 a 90,4 en 2Wiki y de 52,1 a
  53,2 en MuSiQue al entrar el paper de HippoRAG 2, y ningún otro paper del corpus reporta un valor
  mayor (el de WFM da 73,12 y 48,64).
- La T4 de RAPTOR en LongMemEval-S se sustituyó por la de MuSiQue: el paper de Harness también
  reporta RAPTOR (como M6, en escala 0–1: 0,507, 0,593 y 0,593), de modo que la respuesta cambia en
  tres pasos y no en dos, y los tres papers usan subconjuntos y protocolos distintos.

El banco de B sigue en 30 preguntas (13 T1, 5 T2, 5 T3, 2 T4, 5 T5), con 21 de las 25 de T1–T4 en
ingesta ≤ 30, en estado `borrador` hasta la verificación humana.

**Caso difícil, a modo de limitación.** En el paso 6, ninguno de los dos sistemas acierta la T4 de
MuSiQue: el RAG toma otra métrica (22,4, de AR@5) y el wiki da 51,9 en vez de 53,2. Es el tipo de
respuesta que la medida de respuestas obsoletas está pensada para detectar; con un solo caso no
permite concluir nada sobre cuál sistema actualiza mejor.

## 2026-11-09 (Juan Diego): métricas del piloto recalculadas sobre las respuestas guardadas

Al preparar la demostración en una máquina con Linux, `eval metricas` sobre
`results/piloto-1/respuestas.jsonl` no reproducía las cifras versionadas. La causa: tras probar la
reanudación (entrada del arnés, más arriba) se rehicieron las últimas 10 respuestas (5 preguntas T5
del paso 5 en los dos brazos), pero `evaluados.jsonl` y `metricas_por_paso.*` se habían calculado
con la primera tanda y no se regeneraron. `respuestas.jsonl` tiene 68 claves únicas: no hay filas
duplicadas.

Se regeneraron los tres archivos con la capa determinista (sin juez ni llamadas al modelo). El
cálculo es idempotente: una segunda pasada deja los archivos idénticos. Cambios en el paso 5:

| | Antes (primera tanda) | Ahora (respuestas guardadas) |
|---|---|---|
| Wiki, abstención correcta | 0,91 | 1,00 |
| Wiki, contexto medio | 3.558 tokens | 3.544 tokens |
| Wiki, tokens por acierto | 12.096 | 12.049 |
| Costo total RAG / wiki | 0,0035 / 0,0132 USD | 0,0027 / 0,0123 USD |

La cobertura no cambia (0,33 el RAG y 0,83 el wiki). La primera respuesta del wiki a AT5-T5-12,
que la entrada del piloto daba por perdida, sí quedó en `evaluados.jsonl` del commit `78d2683`:
«The corpus does not mention "HyperAddress"; the relevant method is HippoRAG 2. Its recall@5
averages 78.2…» con la cita `2502.14802#s14.p10`. Ante un método inexistente, el agente no se
abstuvo: lo sustituyó por otro del corpus y respondió con una cita válida. Sirve como ejemplo
de premisa falsa para el informe.

`scripts/verificar_demo.py` comprobaba que `data/gold/` tuviera exactamente 50 archivos `.md`, y
fallaba con los Gold de papers fuera del corpus (`2610.09348` y `2610.23313`). Ahora comprueba
que exista el Gold de cada paper del manifest.

Cambios en el panel (`src/wikillm/panel/`, de Juan David), hechos por Juan Diego: en Resultados la
salida de «Calcular» y «Estimar» se dibujaba debajo de la tabla de veredictos y no se veía; ahora
aparece bajo los botones. «Cargar el índice del RAG» con el índice ya en memoria decía «Cargando…
(0.0 s)»; ahora dice que ya estaba cargado. Se agregó una presentación automática en vivo
(«▶ Presentación automática» en el recorrido) que reinicia el wiki al paso 5 si hace falta, pregunta
por BeliefShift, ingiere el paper 6 y repite la pregunta con llamadas reales. Probada de punta a
punta: unos 3 minutos y 0,0255 USD en hora pico.
### 2026-11-09 · Mitad B verificada

Se aplicó `revision_B_por_B.json` (revisión por consenso de Juan David, 16 aceptadas y 14
corregidas) con `python -m wikillm.eval aplicar-revision --autor B`: las 30 preguntas de B pasan a
`verificado_b` y `banco.jsonl` queda con 60 preguntas verificadas por su autor (30 `verificado_a`
y 30 `verificado_b`); la mitad A no cambia. Dos ajustes de transcripción, hechos por Juan Diego:

- `ajustes_B.json` traía la pregunta del 7-nov para B001-T4-05 y B001-T4-06, y como los ajustes
  se aplican después de la revisión, pisaba la redacción nueva que excluye la fila de HippoRAG 2.
  Se quitó ese campo de los dos ajustes: la pregunta final es la de la revisión.
- La revisión pide renombrar B031-T3-02 a B031-T2-02 (el ajuste ya la había pasado a T2). El
  formato de la página no tiene campo para el id, así que se renombró en `borradores_B.jsonl`,
  `ajustes_B.json` y `revision_B_por_B.json`.

Se comprobó que las 14 correcciones de la revisión quedaron en `banco_B.jsonl`. Falta la
verificación cruzada (cada autor revisa la mitad del otro) para el estado `acordado`.

## 2026-11-09 (Juan David): revisión cruzada aplicada y banco acordado

**Mitad A.** Se aplicó la revisión cruzada de Juan David (`propuesta_ajustes_A.json`, 7-nov), que Juan
Diego autorizó por mensaje, fusionada con sus ajustes (`ajustes_A.json`): cambian 15 preguntas (cuatro
pasan a T1 por tener una sola fuente, las cinco T5 quedan con la frase de abstención exacta y el resto
ajusta respuestas y claves). A005-T3-02 se descarta (comparaba un método con resultados y un marco
conceptual sin ellos) y se reemplaza por **A018-T2-01**, que necesita WiCER y el paper posterior
(ingesta 17); sus claves `materiality signal` y `high-AER edit` no estaban en las dos evidencias y
pasan a `prediction` y `high-volatility news item`. Un primer reemplazo, A045-T3-02, se descartó
porque Juan Diego ya la había descartado y la fusión había pisado esa decisión.

**Mitad B.** Juan Diego revisó las 30 finales (`revision_B_por_A.json`: 28 aceptadas y 2 corregidas,
B002-T3-02 y B020-T3-05). Su observación es válida: la diferencia (22.8 y 36.5) no está escrita en los
papers y el 36.5% de la tabla A.10 de 2609.16073 es otra cifra, así que no puede ser clave. Se aceptó
su propuesta: las claves quedan en las cifras del paper (`74.7 | 51.9` y `20.3 | 56.8`) y la
diferencia se conserva en la respuesta de referencia (cambia solo `respuesta_clave` de esas dos).

**Acuerdo.** Nueva orden `eval acordar` (cambio OpenSpec `banco-acordado`). Resultados en
`results/banco/acuerdo_A.json` y `acuerdo_B.json`:

| Mitad | Preguntas decididas por ambos | Acuerdo | kappa |
|---|---|---|---|
| A | 26 | 69,2 % | 0,40 |
| B | 30 | 60,0 % | 0,15 |

Las cifras subestiman el acuerdo de fondo: cada autor decidió sobre la versión que tenía delante, y en B
las 12 discrepancias son preguntas que Juan David ya había corregido y Juan Diego aceptó tal cual; en
las dos de fondo (B002 y B020-T3-05) ambos pidieron ajustar y se resolvieron. En A, las 8 discrepancias son correcciones de
detalle de Juan David.

**Estado.** Las 60 preguntas quedan en `acordado` (26 T1, 12 T2, 8 T3, 4 T4 y 10 T5, con las dos mitades
revisadas por los dos autores). A018-T2-01, el reemplazo de A005-T3-02, se cerró por decisión de Juan
David por falta de tiempo, sin la lectura previa de Juan Diego; conviene decirlo si se pregunta. La
estimación de la corrida completa es de 4,67 USD como cota alta (1,50 de ingesta y 3,17 de preguntas)
y no lleva el aviso de «no vale para el informe». El banco queda cerrado.

### 2026-11-10 · El RAG pasa de Chroma a Qdrant (decisión 0005)

Por recomendación del profesor, y con el acuerdo de Juan David (dueño de `src/wikillm/rag/` y
`src/wikillm/panel/`), el índice del RAG pasa a Qdrant en modo local
(`openspec/changes/2026-11-09-rag-qdrant`). Se reconstruyó en `data/qdrant` con los mismos 5.430
fragmentos. `data/chroma` queda sin uso y se puede borrar.

El piloto se repitió como `results/piloto-2`, con las mismas 17 preguntas y pasos (0 y 5) que
`piloto-1`. Costó 0,0907 USD, en hora pico.

| Paso 5 | piloto-1 (Chroma) | piloto-2 (Qdrant) |
|---|---|---|
| RAG, cobertura | 0,33 | 0,33 |
| RAG, contexto medio | 1.217 tokens | 1.217 tokens |
| RAG, tokens por acierto | 10.341 | 10.341 |
| Wiki, cobertura | 0,83 | 0,83 |
| Wiki, abstención correcta | 1,00 | 0,91 |
| Wiki, contexto medio | 3.544 tokens | 3.495 tokens |

En las 17 preguntas del paso 5, el RAG con Qdrant tuvo el mismo `context_tokens`, las mismas citas y
la misma abstención que con Chroma: recuperó los mismos fragmentos. Las diferencias del wiki vienen
de que cada corrida reconstruye su wiki con nuevas llamadas al modelo, no de la base vectorial. Los
costos de piloto-2 son más altos porque corrió en hora pico (tarifa ×2).

La demostración se probó en vivo sobre Qdrant: antes de ingerir el paper 6, los dos sistemas se
abstienen ante la pregunta de BeliefShift; después, los dos responden citando `2603.23848#s18.p3`.
Durante esa prueba se encontró que la presentación automática se detenía si ya había una ingesta en
curso, y ahora la sigue.

## 2026-11-11 (Juan David): pista quitada de dos T4 y candidatas para ampliar el corpus

**Pista quitada.** A039-T4-03 y A016-T4-03 terminaban con «If more than one paper in the corpus
reports it, give the most recent report.». Se quitó la frase del banco (`banco.jsonl`, `banco_A.jsonl`
y `ajustes_A.json`) porque decirle al sistema qué regla seguir ante varios reportes hace a la propia
pregunta parte de la respuesta: es el RAG o el wiki quien debe decidir. `validar-banco` sigue en 60
preguntas, 0 problemas y 60 `acordado`; no se cambió el estado de ninguna. Cambia la huella del banco,
así que una corrida empezada antes con el banco anterior no se puede reanudar.

**Lo que se encontró al revisarlas (pendiente de decidir con Juan Diego).** La pista contradecía la
respuesta de referencia. El paper posterior de A039 (2609.18182, tabla 18) reporta HippoRAG 2 con
Recall@5 de **52,94** en MuSiQue, y la referencia es 74,7 (paper original de HippoRAG 2). El de A016
(2605.25480) reporta HippoRAG 2 con F1 de **0,831** en 2Wiki, y la referencia es 71,0. Son
evaluaciones con otra configuración, no una actualización que deje obsoleto el dato original.

Sin la pista, las dos preguntas admiten dos respuestas defendibles y las claves (`74.7`, `71.0`) dan
por mala la del paper posterior. Opciones: (a) acotar la pregunta a una configuración sin nombrar el
paper; (b) pasarlas a T3 («¿coinciden los papers del corpus sobre…?») con el desacuerdo como
respuesta; (c) aceptar cualquiera de las dos cifras si el sistema cita su fuente. No se eligió
ninguna: hay que acordarlo antes de la corrida.

**Parecidas, sin tocar.** B001-T4-05 y B001-T4-06 piden «the highest … that the corpus reports» (regla
del máximo, necesaria para que la respuesta sea única) y A018-T2-01 dice «the later paper», que ordena
los dos papers. Se dejan hasta decidir si cuentan como pista.

**Candidatas de ampliación.** `data/ampliacion/candidatas_citadas.csv`: 611 identificadores de arXiv
citados por los 50 papers y que no están en el corpus (de la bibliografía del HTML original), con los
papers que los citan y un nivel. 31 son de dic-2023 a 2025 y las citan 3 o más papers del corpus;
22 son anteriores a dic-2023 y no tienen HTML nativo en arXiv. No se comprobó la existencia del HTML.

## 2026-11-16 (Juan Diego): corrida oficial `oficial-1`, capa determinista

**Qué se corrió.** Las 60 preguntas `acordado` (huella del banco en `results/oficial-1/corrida.json`),
11 pasos de ingesta (0, 5, …, 50) y los dos brazos: 1.320 respuestas únicas, `deepseek-flash`,
temperatura 0 y razonamiento desactivado. Empezó el 16-nov a las 01:59 UTC (en hora pico, con tope
de 10 USD confirmado) y terminó esa misma madrugada.

**Incidente.** En el paso 20 la ingesta del wiki falló con `2606.06240`: la escritura llegó al tope
de 16.000 tokens de salida y el JSON quedó cortado en los dos intentos. Se subió el tope a 32.000
(decisión 0007) y se reanudó con la misma orden y el mismo nombre; los pasos 0–15 no se repitieron.
La escritura del paper 13 (`2605.18490`) también se había cortado una vez y se reintentó con
éxito, así que sus páginas salen de la segunda respuesta. El paper más grande (`2610.04794`) entró
sin problema con el tope nuevo. El commit registrado al iniciar es `0d5407fd`; el cambio del tope
llegó en `f3448c7`.

**Gasto.** 2,52 USD en total: RAG 0,12 (preguntas) y wiki 1,41 (ingesta) más 0,99 (preguntas). Muy
por debajo de la cota de 4,67 USD a tarifa normal y del tope de 10.

**Resultados deterministas** (`results/oficial-1/informe/`). Las 139 respuestas indeterminadas
(38 de RAG y 101 del wiki; 62 son T2) cuentan como no correctas, así que la cobertura es una **cota
inferior** hasta pasar por el juez.

| Paso | Cobertura RAG | Cobertura wiki | Contexto medio RAG | Contexto medio wiki |
|---|---|---|---|---|
| 5 | 0,23 | 0,54 | 1.284 | 3.861 |
| 25 | 0,44 | 0,62 | 1.296 | 4.690 |
| 40 | 0,49 | 0,72 | 1.245 | 4.166 |
| 50 | 0,44 | 0,56 | 1.241 | 4.650 |

**Pendiente.** Pasar las indeterminadas por el juez (Gemini) y calibrarlo, la evaluación auxiliar con
un segundo juez (decisión 0006) y el análisis de fallos. Las cifras de esta tabla no son todavía las
del informe final.

### 2026-11-16 · `oficial-1` con juez, evaluación auxiliar y análisis de fallos

**Juez (Gemini flash-lite).** El primer intento falló con un 429 tras 39 llamadas (unas 23 por
minuto) y, como `metricas` solo escribe al final, perdió ese avance. Se añadió un intervalo entre
llamadas (`JUDGE_MIN_INTERVAL_SECONDS`, por defecto 0) y se repitió a 6 s. Resolvió las 139
indeterminadas: 68 correctas y 71 incorrectas. Costo estimado: unos 0,05 USD (178 llamadas; la
corrida no lo registra en dólares).

**Cobertura con los veredictos finales** (`results/oficial-1/informe/`). Pares: preguntas
respondibles con respuesta de ambos brazos; IC95 por bootstrap sobre las preguntas y McNemar exacto.

| Paso | n | RAG | Wiki | Diferencia | IC95 | p (McNemar) |
|---|---|---|---|---|---|---|
| 10 | 17 | 0,41 | 0,71 | +0,29 | [0,12, 0,53] | 0,063 |
| 25 | 34 | 0,50 | 0,74 | +0,24 | [0,06, 0,41] | 0,039 |
| 40 | 47 | 0,57 | 0,83 | +0,26 | [0,11, 0,43] | 0,008 |
| 50 | 50 | 0,54 | 0,78 | +0,24 | [0,08, 0,40] | 0,012 |

El wiki supera a RAG en todos los pasos, y la diferencia es significativa desde el paso 25. Los
intervalos suponen preguntas independientes y no hay corrección por comparaciones múltiples; con pocas
preguntas respondibles en los pasos iniciales (13 en el paso 5) son orientativos.

**Evaluación auxiliar (decisión 0006).** Califiqué a ciegas 179 ítems (las 139 que resolvió el juez más
40 deterministas elegidos con semilla 1): acuerdo 93,3 % y kappa 0,865. En el origen determinista el
acuerdo fue 100 % (40 de 40); en el del juez 91,4 % (kappa 0,827). Hubo 12 discrepancias: en 8 el juez
principal fue más estricto y en 4 más permisivo. Siete son una sola pregunta (A003-T3-02, ColBERTv2 en
2WikiMultiHopQA): las respuestas de ambos brazos dan 65,6 como valor de ColBERTv2, pero en la tabla de
HippoRAG 65,6 es el **promedio** de los tres datasets y el de 2Wiki es 68,2; el «incorrecta» de Gemini
era el correcto y mi «correcta» fue demasiado permisiva. Mi calificación ciega se conserva tal cual; con
ese error contado como acuerdo, este sería de 97,2 %. La evaluación auxiliar no reemplaza el veredicto
principal ni cambia ninguna cobertura: sustituir el veredicto del juez por el mío deja iguales las
coberturas de los pasos 25 y 50.

**Por qué fallan los brazos** (`results/oficial-1/fallos/`; categorías por abstención, fuentes citadas
y marca de obsolescencia, sin llamar a ningún modelo).

| Sistema | No correctas | Abstención errónea | Fuente parcial | Obsoleta | No se abstuvo | Fuentes completas, error | Sin fuente |
|---|---|---|---|---|---|---|---|
| RAG | 169 | 157 | 4 | 0 | 1 | 2 | 5 |
| Wiki | 124 | 24 | 26 | 18 | 40 | 15 | 1 |

El fallo de RAG es casi siempre abstenerse cuando la respuesta sí estaba en el corpus (157 de 169, el
93 %): no recuperó el fragmento y no inventó. El wiki falla de forma más variada: responde cuando
debía abstenerse (40, de ellas 29 en T2, antes de ingerir todas las fuentes: da una respuesta
parcial en vez de la frase de abstención), cita solo parte de las fuentes (26) y deja respuestas
obsoletas (18). En un caso (i0081 de la muestra auxiliar) el agente devolvió una llamada a herramienta
como texto crudo en lugar de responder.

**Límites.** Preguntas verificadas por sus autores, con acuerdo entre ellos bajo (kappa 0,40 y 0,15);
T4 solo tiene 4 preguntas; el juez Gemini no se calibró contra etiquetas humanas, solo contra mi
calificación (el mismo contenido que las 139 que resolvió); y el wiki no es determinista, así que una
repetición podría dar otras cifras. El tope de salida del wiki se subió a 32.000 a mitad de la corrida
(decisión 0007).

## 2026-11-16 (Juan David): tablas escaladas y Gold de 100 papers reconstruido

**Hallazgo.** LaTeXML dibuja una tabla escalada con `\resizebox` como `<span class="ltx_tabular">` y el
conversor solo leía `<table class="ltx_tabular">`: esas tablas no llegaban al Gold. Al reconvertir el
Bronze, cambian cuatro papers y los otros 96 salen idénticos byte a byte: Hindsight (`2512.12818`, pasa de
0 a 4 tablas), BEAM (`2510.27246`, +7), GAM (`2511.18423`, +2) y una tabla de ablación de `2608.12888`.

**Qué se hizo.** `src/wikillm/ingest/markdown.py` reconoce filas y celdas en `<span>` (cambio
`2026-11-16-tablas-escaladas`, con prueba). El Gold de 100 papers se reconstruyó en `data/corpus100/`
con la ingesta normal, respetando los 15 s entre peticiones (una caída de conexión afectó a 15
papers y se reintentó). `spans.jsonl` de los otros 96 papers coincide con el que había.
Solo cambian los fragmentos de esos cuatro (+14 fragmentos) y los `tokens` de su fila del manifest.
Las 138 evidencias del banco de 100 resuelven a un fragmento con la misma huella. El Gold de 50 y la
corrida `oficial-1` no se tocaron: `oficial-1` se hizo con el conversor anterior.

**Banco.** `data/preguntas/banco_100.jsonl` tiene ahora 100 preguntas: las 60 acordadas más 20 de Juan
Diego y 20 de Juan David (`data/ampliacion/preguntas_borde_40.json`). Estimación del arnés para la
corrida `ampliado-1` (11 pasos, 2 brazos): 8,28 USD como cota alta (3,00 de ingesta y 5,28 de preguntas).

### 2026-11-16 · tres cargas por fases y wiki reutilizable (Juan David, con Claude)

**Orden.** El manifest de `corpus100` pasa a tener tres fases (33, 33 y 34 papers) con la cronología
como base y 10 excepciones (`data/corpus100/fases.json`). El arnés pregunta en los pasos 0, 33, 66 y 100.
Con ese orden se pueden contestar 19, 51 y 84 de las 84 preguntas con respuesta, y 32 de las 34 preguntas con
varias fuentes las reciben en cargas distintas. Razones y límites en la decisión 0009.

**Banco.** `ampliar-banco` recalculó `ingesta_minima` y los pasos de las T4 con el nuevo orden; el banco
valida sin problemas y sus 138 evidencias coinciden con el Gold. Estimación: 100 preguntas × 4 pasos × 2
brazos = 800 respuestas, 4,92 USD de cota alta (3,00 de ingesta y 1,92 de preguntas).

**Wiki reutilizable.** `arnes correr --wiki-de <corrida>` copia el wiki ya construido (sus copias `paso-N`)
y el brazo `wiki` lo recorre sin ingerir, para probar capas de consulta sin reconstruir el conocimiento.

### 2026-11-17 · dos corridas con el nombre `ampliado-1` (Juan David)

Al fusionar con la rama de Juan Diego aparecieron dos corridas con el mismo nombre. **`ampliado-1`** es la de él
(11 pasos, 80 preguntas, wiki propio) y conserva su carpeta tal cual. La nuestra (100 preguntas, pasos 33, 66 y 100,
conocimiento reutilizado de `construccion-1`) pasó a **`results/ampliado-fases-1`**, con el nombre actualizado dentro
de sus archivos; las carpetas locales `data/wiki` y `data/qdrant` se renombraron igual. Son experimentos distintos y
no se comparan como una sola corrida.

## 2026-11-16 — Corrida `ampliado-1` (100 papers, 80 preguntas), preliminar

- Corpus de 100 papers en orden cronológico (ADR 0008), banco de 80 preguntas (60 acordadas y 20
  de borde de Juan Diego, sin revisión cruzada). La corrida no vale para el informe.
- Dos fallos y una reanudación: (1) el índice del RAG comparaba contra el Gold de 50 papers
  (corregido); (2) en el paso 30 el modelo nombró distinto la página del paper 2510.04618 y la
  validación la rechazó; se repitió la misma orden y la ingesta pasó. Sin gasto perdido.
- Costo total 4.52 USD (cota estimada 7.22). Juez Gemini sobre las indeterminadas del wiki.
- Paso 100, pareado RAG frente a wiki (67 preguntas): cobertura 0.52 frente a 0.73, diferencia
  +0.21 IC95 [0.07, 0.36], McNemar p=0.009. Por tipo: T2 +0.46 (p=0.031); T1, T3 y T4 sin
  significancia con n pequeño.
- Cada brazo consigo mismo (paso 50 de `oficial-1` frente a paso 100 de `ampliado-1`, 50
  preguntas comunes): RAG 0.54 → 0.56, wiki 0.78 → 0.78, ninguna diferencia significativa. Las
  17 preguntas nuevas respondibles: RAG 0.41, wiki 0.59 (p=0.45), preliminar.
- Límites: orden y tamaño van mezclados, preguntas nuevas con un solo autor, wiki no
  determinista, una sola ejecución. Archivos en `results/ampliado-1/` y `results/comparacion-50-100/`.
