# Graphify sobre el wiki de 100 papers: qué se probó y qué dio

Evaluación del 17 de noviembre de 2026 sobre el wiki ya construido (`data/wiki/construccion-1`,
461 páginas, estado `paso-100`) y el banco de 100 preguntas. Continúa
[docs/evaluacion-tgrep-graphify.md](evaluacion-tgrep-graphify.md) (15 papers). Gasto total de las
pruebas con modelo: **≈ 0,85 USD** (0,77 en consultas del agente, 0,006 en consultas del LLM y ≈ 0,07
en la extracción semántica de graphify).

## Qué pidió el tutor

Según la transcripción de la reunión del 11-nov (`transcripcion-reunion-tutor-2026-11-11.md`, que no
está versionada en el repositorio): Graphify es «un plus» que va después de la corrida
estándar; «se construye sobre la documentación»; «ya queda construido el grafo. Entonces tocaría ver
cómo podemos buscar a través del grafo»; y la cadena sería *consulta escrita por el LLM → tgrep →
Graphify → WikiLLM*, un «retrieval no vectorial». También pidió extraer **las citas** entre papers.
**No dice qué aristas debe tener el grafo.** Open Knowledge Format (OKF), que menciona, define cada
concepto como un `.md` con frontmatter y enlaces cruzados: son los mismos `[[enlaces]]` que ya tiene
el wiki.

## Resumen

1. **Ningún grafo recupera mejor que el texto completo.** Con 5 páginas, el grafo de títulos y enlaces
   cubre 0,38 de los fragmentos de evidencia frente a 0,67 del `search` actual y 0,80 del texto
   completo. Probados también: entidades con PageRank personalizado (HippoRAG), hechos por entidad,
   secciones por co-ocurrencia, grafo semántico con el LLM, vecinos por enlaces. Ninguno supera al texto.
2. **A igual número de tokens, expandir con vecinos del grafo es lo mismo que traer más páginas de
   texto** (0,76 contra 0,75 de cobertura). El propio benchmark de Graphify muestra una ganancia
   chica de la expansión (recall@10 0,497 contra 0,493 de su búsqueda híbrida).
3. **La única arista con información propia son las citas entre papers.** En 30 de las 34 preguntas con
   varias fuentes, esas fuentes están conectadas por citas, y el 72 % de los pares se citan
   directamente (14 % esperable al azar). Ayuda a recuperar en T2 (todas las claves: 0,53 → 0,73,
   15 preguntas), pero en la prueba de punta a punta el efecto es pequeño y no significativo.
4. **Una cadena con texto completo reduce llamadas y latencia** (T1: 1,0 llamadas contra 3,9; 1,6 s
   contra 6,0 s) y acierta *algo* más (T1: 38 contra 35 de 47, p = 0,38). En el conjunto sin
   seleccionar de preguntas con varias fuentes queda igual (10 contra 11 de 34). **No hay una mejora de
   aciertos demostrada.**

## Cómo se midió

- **Recuperación sin modelo** (84 preguntas respondibles). Para cada método se miden las N primeras
  páginas devueltas: *fragmentos* (los `span_id` de la evidencia del banco que aparecen citados en
  esas páginas), *claves* (fracción de `respuesta_clave` presente en el texto) y *tokens*. Es un
  proxy: cubrir la evidencia no garantiza responder bien.
- **Techo.** Con todo el wiki a la vista, las claves completas están en el 87 % de las preguntas
  (T1 0,89, T2 0,93, T3 0,78, T4 0,75). El 13 % restante no puede responderse con ningún método porque
  el wiki no conservó el dato (por ejemplo, la fila de A-Mem con 10.000 memorias).
- **De punta a punta**, con `deepseek-flash` y el agente de `scripts/comparar_herramientas.py`
  (misma lógica de acciones, tope y paciencia que `ConsultaWiki`). Una repetición (temperatura 0: las
  repeticiones salen casi iguales). Acierto = la `respuesta_clave` está en la respuesta (capa 1, sin
  el juez), y se reporta también la fracción de claves.

## Recuperación (84 preguntas, 5 páginas salvo que se indique)

| Método | Fragmentos | Claves | Todas las claves | Tokens |
|---|---:|---:|---:|---:|
| `search` actual (resúmenes) | 0,67 | 0,75 | 0,65 | 6.650 |
| Grafo determinista de graphify (títulos y enlaces) | 0,38 | — | — | 6.150 |
| Entidades + PageRank personalizado | 0,46 | 0,56 | 0,44 | 7.480 |
| Texto completo (TF-IDF por página) | **0,80** | **0,83** | **0,73** | 8.150 |
| Texto + PageRank (fusión RRF) | 0,73 | 0,77 | 0,64 | 8.480 |
| Frases con su cita (25) | 0,68 | 0,75 | 0,64 | **1.420** |
| Secciones por palabras (8) | 0,65 | 0,71 | 0,62 | 2.100 |
| Hechos por entidades (25 frases) | 0,50 | 0,46 | 0,33 | 1.250 |

Con las consultas escritas por el LLM (entidades, palabras clave y tres consultas; 0,006 USD las 84)
se repite el patrón: texto completo 0,76/0,82, búsqueda 0,65/0,74, grafo 0,45/0,56, y
«texto + grafo» (RRF) empeora a 0,62/0,70.

**Expansión a igual presupuesto** (semillas de texto + vecinos del grafo contra más páginas de texto):

| Método | Fragmentos | Claves | Tokens |
|---|---:|---:|---:|
| texto, 5 páginas | 0,75 | 0,80 | 8.090 |
| texto, 3 + 2 vecinos (concepto primero) | 0,76 | 0,79 | 8.140 |
| texto, 7 páginas | 0,78 | 0,82 | 11.390 |
| texto, 3 + 4 vecinos (por texto) | 0,77 | 0,82 | 11.310 |

**Grafo semántico** (graphify con `deepseek-flash`, 24 páginas): 9 minutos, ≈ 100.000 tokens de salida,
truncamientos y 3 páginas omitidas. Cada página crea sus propios nodos (el nodo «Mem0» no se unifica
entre páginas). Ordenando las páginas por cuántas entidades de la pregunta contiene cada una, recupera igual que
el `search` (0,56 de fragmentos con 5 páginas, 29 preguntas), algo mejor que el grafo determinista
(0,50) y peor que el texto completo (0,74); fusionarlo con el texto (0,70) no supera al texto solo.
(Con el orden de aparición en el grafo, que se usó primero, daba 0,30: era un error de evaluación.)
Extrapolado a las 461 páginas serían ≈ 1,3 USD y ≈ 3 h.

**Citas entre papers.** 686 aristas de cita dentro del corpus (densidad 0,14). Las fuentes requeridas
de las preguntas con varias fuentes están conectadas en 15/15 (T2), 11/15 (T3) y 4/4 (T4). Usando las
citas como expansión de las semillas de texto: claves 0,80 → 0,82, todas las claves 0,70 → 0,74 y, en
T2, 0,53 → 0,73. Las citas vienen de la bibliografía del paper, información que el wiki no conserva.

## De punta a punta

| Prueba | Base | Variantes | Resultado |
|---|---|---|---|
| Herramienta `graph` opcional junto a `search` (3 rondas, 7 + 21 + 33 preguntas) | 26/66 en T2/T3 | `g_busqueda`: 23/66; `base_mas_grafo`: 24/66 | Sin mejora. El agente llamó a `graph` en solo 3–12 % de las corridas, así que estas variantes eran la base con ruido. −24 % de tokens de entrada (IC 95 % que excluye 0) con el mismo costo en dólares |
| `graph` que **sustituye** a `search` y lee por secciones | 3/18 y 16/18 | `graphify`, `g_sin_indice`, `g_rico`: 0–2/18 y 15–16/18 | Igual o peor; de +5 % a +35 % de tokens en las preguntas normales; ahorra solo en las de abstención (−30 % a −53 %) |
| Cadena (consulta del LLM → texto completo → WikiLLM), 21 preguntas **elegidas** por recuperación | 10/21 | precarga de 3 páginas completas: 14/21; resúmenes: 12/21; ordenada por `search`: 12/21; con vecinos del grafo: 13–14/21 | Mejora en el conjunto elegido (4 ganadas, 0 perdidas); el grafo no suma |
| Cadena sobre las **34 preguntas con varias fuentes** (sin elegir) | 11/34 | texto completo: 10/34; con citas: 11/34 | Sin diferencia. Fracción de claves 0,49 / 0,52 / 0,54 (diferencia con citas: +0,055 [−0,04, +0,16]) |
| Cadena sobre las **47 T1** y **16 T5** (sin elegir) | T1 35/47, T5 16/16 | T1 38/47, T5 15/16 | T1: 4 ganadas y 1 perdida (p = 0,38). T5: 1 perdida. 1,0 llamadas contra 3,9 en T1 |

## Lectura

- El banco es mayoritariamente de **dato puntual** (47 T1 de 100) y de comparaciones entre dos papers
  que la propia pregunta nombra (12 de las 15 T2). La literatura coincide en que en ese terreno una buena
  búsqueda de texto gana y los grafos ayudan en razonamiento **multi-hop** y global
  ([RAG vs GraphRAG, arXiv 2502.11371](https://arxiv.org/pdf/2502.11371); HippoRAG, arXiv 2405.14831,
  con las mayores ganancias en MuSiQue y 2WikiMultiHopQA). No hay en el banco preguntas de ese tipo.
- Los fallos que quedan son sobre todo **contenido que el wiki no conservó** (13 % del banco) y
  **composición de la respuesta** (listas incompletas, abstención). Una mejor recuperación no los arregla.
- La parte de la cadena que sí aporta es **buscar en el texto completo** (el papel de tgrep), no el grafo.

## Limitaciones

- Una repetición por celda y 21 a 63 preguntas: las diferencias de 1 a 4 preguntas no son significativas.
- La mejora de 10 a 14 sobre 21 preguntas salió en un conjunto elegido por criterios de recuperación
  (regresión a la media); en los conjuntos sin elegir desaparece o se reduce a +3 sobre 47.
- El grafo semántico se probó con una sola configuración (sin «thinking») y 24 páginas.
- La métrica de acierto es la presencia de las claves, no el juez del experimento.

## Reproducir

Los scripts están en `scripts/exploracion_grafo/` (necesitan una carpeta de trabajo `S` con los
grafos de graphify y `consultas_llm.json`); las corridas de punta a punta, en
`results/herramientas/paso100-*` (los registros de llamadas no se versionan).

```bash
# grafo determinista del wiki, en un entorno aparte con graphifyy instalado
graphify update $S/g100/fuente            # pages/ e index.md copiados
graphify update $S/g100/fuente_sin_indice # solo pages/

# recuperación sin modelo
S=... uv run python scripts/exploracion_grafo/recuperacion.py
S=... PYTHONPATH=scripts/exploracion_grafo uv run python scripts/exploracion_grafo/grafos_eval.py
S=... PYTHONPATH=scripts/exploracion_grafo uv run python scripts/exploracion_grafo/citas_recup.py

# de punta a punta (variantes pipe_* de comparar_herramientas.py)
uv run python scripts/comparar_herramientas.py --consultas results/herramientas/paso100-consultas/consultas_llm.json \
    --variantes actual,pipe_paginas,pipe_paginas_citas --manifest data/corpus100/manifest.jsonl ...
```
