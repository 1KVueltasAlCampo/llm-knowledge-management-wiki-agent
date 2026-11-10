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
