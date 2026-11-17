# Graphify y el WikiLLM: revisión independiente

17-nov-2026. Gasto de API: **0 USD**. Todas las pruebas miden la recuperación sin llamar al modelo.

## 1. Qué dijo el tutor y cómo lo leo

Leí la transcripción completa del 11-nov. Tu lectura es correcta:

- Graphify es «un plus». La prioridad son más papers (los citados) y los casos de borde.
- «Se construye sobre la documentación», es decir, sobre los `.md` del wiki: «ya queda construido el
  grafo, tocaría ver cómo podemos buscar a través del grafo».
- La cadena que imagina es tgrep → Graphify → WikiLLM, un «retrieval no vectorial» que reduce
  tokens. Las opciones son 1 RAG, 2 WikiLLM, 3 WikiLLM+Graphify y 4 Wiki+Graphify+TGREP.
- **No define las aristas.** Lo único relacional que pide en concreto son las citas entre papers.

Mi interpretación: el tutor pide un recuperador no vectorial que aproveche la estructura del wiki.
No exige ningún tipo de arista en particular. Por eso la pregunta que importa es si alguna arista
disponible le añade al texto algo que el texto no tenga ya.

## 2. Qué es Graphify de verdad (lo vi en el clon local)

- **Aristas que construye sobre Markdown sin usar el LLM** (`graphify/extractors/markdown.py`):
  - nodos de página y de título de sección;
  - `contains` (página → sección);
  - `references` (enlaces `[...](...)` y `[[...]]`, y menciones de código si el corpus incluye código).
  - El frontmatter (`fuentes`, `resumen`) se guarda como atributo del nodo, no como arista.
  - En nuestro wiki salen 3.357 nodos y 6.732 aristas (3.936 `references` y 2.796 `contains`).
- **Extracción semántica** (`llm.py`): es opcional, la hace un LLM por archivo y produce conceptos y
  relaciones etiquetadas como `INFERRED`.
- **Consulta** (`serve.py`): puntúa los términos de la pregunta contra las etiquetas y el texto de
  los nodos (IDF, trigramas, bonificación por coincidencia exacta), elige de 1 a 3 semillas y hace
  un BFS de profundidad 2 con tope de tokens. `path` da el camino más corto entre dos nodos y
  `explain` muestra los vecinos de un nodo. El servidor MCP expone esas mismas operaciones.
- **Su benchmark** (`BENCHMARKS.md`), sobre LOCOMO, que es memoria de conversación y no documentos:
  - expandir por el grafo sobre semillas híbridas da recall@10 0,497 frente a 0,493 de la búsqueda
    híbrida sola (BM25 da 0,362);
  - en LongMemEval, una ablación con solo semillas iguala a la versión con grafo (0,848 frente a 0,844).
  - Es decir, en sus propios datos casi toda la ganancia viene de las semillas y no del grafo.

## 3. Qué dice la literatura

Estas referencias las cito de memoria y no las verifiqué en internet en esta sesión. Varias están en
el propio corpus (HippoRAG 2405.14831, LightRAG 2410.05779).

- **GraphRAG** (Edge et al., 2404.16130): gana en preguntas **globales** de sensemaking («¿cuáles
  son los temas principales?»), gracias a los resúmenes por comunidad. No gana en preguntas puntuales.
- **HippoRAG** (2405.14831) y **HippoRAG 2** (2502.14802): PageRank personalizado sobre un grafo de
  entidades. Las mayores ganancias están en tareas **multi-hop** (MuSiQue, 2Wiki). En tareas
  factuales simples apenas cambia.
- **LightRAG** (2410.05779): recuperación en dos niveles, entidades y temas. Se evalúa sobre todo con
  comparaciones de un LLM juez en preguntas amplias.
- **Zep/Graphiti** (2501.13956): grafo temporal para memoria de agentes. Ayuda en preguntas
  **temporales** y de actualización.
- **RAG vs GraphRAG** (Han et al., 2502.11371): RAG gana en preguntas de detalle y GraphRAG en las
  multi-hop y de razonamiento; combinarlos sirve en esas últimas.

Conclusión de la literatura: el grafo rinde en preguntas globales, multi-hop o temporales. Nuestro
banco tiene sobre todo T1 (dato puntual), y las T2/T3 suelen nombrar los papers en la pregunta.

## 4. Qué probé (formas que no se habían probado)

Lo anterior había probado mis propias reimplementaciones del grafo, entidades con PageRank, citas
como expansión y una herramienta `graph` para el agente. Esta vez probé tres cosas nuevas:

- **G1 – el motor de consulta nativo de Graphify** (`graphify query`, con su puntuación y su BFS)
  sobre el grafo determinista del wiki. Tomo las 5 primeras páginas distintas que devuelve.
- **G2 – lo mismo, con una capa de papers.** Añadí una página-stub por paper con `[[enlaces]]` a las
  páginas que lo tienen como fuente y a los papers que cita dentro del corpus. Así el propio
  Graphify construye aristas página↔paper y de cita, tal como pidió el tutor.
- **G3 – semillas híbridas con expansión** (como el modo graph-expand del benchmark de Graphify):
  3 páginas de texto completo más 2 páginas vecinas a través de la capa de papers (fuente compartida
  o paper citado), ordenadas por puntuación de texto.
- **B0 – control:** TF-IDF sobre el texto completo, 5 páginas.

**Preguntas, fijadas por regla antes de ver resultados** (`scripts/exploracion_grafo_2/preparar.py`):
las 12 primeras por id que no son T5 y tienen 2 o más fuentes requeridas (5 T2, 3 T3, 3 T4), más las
3 primeras T1 como control. Son 15 preguntas, todas tomadas del banco sin cambios.

**Métrica:** fracción de los `span_id` de evidencia citados en las 5 páginas; cuántas preguntas
quedan con toda su evidencia; tokens (caracteres/4).

## 5. Resultados

| Brazo | Fragmentos | Toda la evidencia | Tokens |
|---|---:|---:|---:|
| B0 texto completo (control) | **0,73** | **8/15** | 5.914 |
| G1 graphify query (wiki) | 0,36 | 2/15 | 6.438 |
| G2 graphify query (wiki + papers y citas) | 0,36 | 2/15 | 6.539 |
| G3 texto + vecinos por paper | 0,66 | 7/15 | 5.883 |

Por pregunta:

- G1 y G2 **nunca superan** a B0 y pierden en 8 de 15 preguntas. Por ejemplo, en A016-T4-03 y
  A018-T4-03 B0 tiene 1,00 y G1/G2 tienen 0.
- G3 empata con B0 en 14 preguntas y pierde 1 (A002-T1-02, un control T1, por sustituir páginas útiles).
- Diferencia pareada G3 − B0: −0,067 de fragmentos. **Ninguna pregunta mejora.**

Los datos por pregunta están en `resultados.json`, en la carpeta de trabajo.

No gasté nada en el modelo. Una confirmación de punta a punta solo tiene sentido si la recuperación
mejora, y aquí ningún brazo mejora en ninguna pregunta. Una tanda de 15 preguntas × 2 brazos habría
costado ≈ 0,03 USD, pero no podía mostrar una ganancia que la recuperación ya descarta.

## 6. Por qué no mejora

1. **La consulta nativa de Graphify busca por etiquetas.** Puntúa títulos de página y de sección,
   no el texto. Los datos de las respuestas están en los párrafos, y por eso G1 queda en la mitad
   del texto completo. Coincide con el 0,38 del informe anterior: este resultado es robusto.
2. **Añadir papers y citas no cambia la consulta nativa** (G2 = G1). El BFS sale de las mismas
   semillas por título, y los stubs solo agregan vecinos que caen fuera del tope de 5.
3. **Expandir por papers trae páginas que el texto ya trae.** En las preguntas con varias fuentes,
   las páginas de ambos papers ya aparecen entre las primeras por texto, porque la pregunta los
   nombra. Así que el grafo no aporta un segundo salto.
4. Esto coincide con la literatura y con el benchmark de Graphify: la ganancia del grafo aparece en
   preguntas multi-hop, globales o temporales, que nuestro banco casi no tiene. En LOCOMO la mejora
   de Graphify sobre sus semillas es de +0,004.

## 7. Robustez y límites

- Son 15 preguntas, sin repetición, y se mide la recuperación, no la respuesta.
- Con n = 15 no puedo descartar un efecto pequeño de G3 en un sentido u otro. Pero G1 y G2 pierden
  de forma consistente (0 ganadas, 8 perdidas; signo p ≈ 0,008).
- No probé la extracción semántica: el informe anterior la estimó en ≈ 1,3 USD y vio peor
  recuperación. Tampoco probé `path` como herramienta del agente.
- El control TF-IDF es una implementación mía y sencilla. Un BM25 mejor solo agrandaría la distancia.

## 8. Recomendación

**No recomiendo un experimento completo con Graphify como recuperador.** Para cumplir con el tutor
(opción 3/4) con poco costo, propongo:

- Reportar Graphify como brazo **exploratorio**, con esta evidencia de recuperación.
- Usar el grafo para lo que sí aporta información propia: **las citas entre papers**, como contexto
  o filtro de los papers a ampliar, que es la prioridad del tutor. No usarlo como recuperador.
- Si se quiere una prueba donde el grafo tenga oportunidad, primero hacen falta preguntas multi-hop
  reales, en las que el segundo paper no se nombre en la pregunta. Hoy el banco no las tiene, y
  crearlas excede este encargo.

## Reproducir

```bash
# entorno aparte con graphify (pip install <clon>)
.venv/Scripts/python.exe scripts/exploracion_grafo_2/preparar.py $W
(cd $W/solo_wiki && graphify update .); (cd $W/con_papers && graphify update .)
.venv/Scripts/python.exe scripts/exploracion_grafo_2/evaluar.py $W <ruta a graphify.exe>
```

## Extracción semántica con LLM

Prueba del 17-nov-2026, 14:00 hora de Colombia (fuera de la hora pico), con `deepseek-flash`. Los
scripts están en `scripts/exploracion_grafo_2/`: `lanzar_graphify.py` pasa la clave al subproceso sin
leer `.env` ni imprimirla; `subconjunto_sem.py` fija el subconjunto; `evaluar_sem.py` hace la
evaluación, que no llama al modelo.

### Calibración (4 páginas: A-Mem, HippoRAG, LightRAG y PageRank personalizado)

| Configuración | Truncamientos | Nodos (4 págs.) | Tokens entrada / salida | USD (precio del proyecto) |
|---|---:|---:|---:|---:|
| «thinking» por defecto | 0 | 26 | 7.662 / 15.251 | 0,0103 |
| sin «thinking» | 0 | 56 | 7.637 / 14.807 | 0,0100 |
| sin «thinking», `--token-budget 8000` | 0 | 46 | 7.637 / 10.962 | 0,0077 |

**Elegí sin «thinking» con `--token-budget 8000`.** Con «thinking» el modelo gasta la salida en
razonar y produce la mitad de nodos por el mismo costo. Con bloques de 8.000 tokens la salida por
nodo es la más baja y, en principio, los bloques se truncan menos.

### Gasto real

| Tanda | Entrada / salida | USD |
|---|---:|---:|
| Calibración (3 configuraciones) | 22.936 / 41.020 | 0,028 |
| Subconjunto (33 páginas) | 67.254 / 145.213 | 0,097 |
| **Total** | | **≈ 0,125** (tope 0,15) |

- Los precios son los del proyecto: 0,15 USD por millón de tokens de entrada y 0,60 por millón de
  salida. Graphify estima más (0,22 USD por la tanda grande) porque usa la tarifa de hora pico.
- La tanda grande salió un 45 % sobre mi estimación (0,067 USD). Aun con bloques de 8.000 tokens,
  **6 bloques se truncaron y se partieron en dos**, y repetirlos encareció la salida.
- Después de esta tanda dejé de gastar: no hubo prueba de punta a punta.

### Subconjunto (regla fijada antes de ver resultados)

- **Páginas T3:** recorro las preguntas T3 del banco ordenadas por id. Para cada una tomo, en orden
  alfabético, las páginas del wiki que citan algún `span_id` de su evidencia, hasta llegar a **25
  páginas**.
- **Distractoras:** 8 páginas al azar del resto, con `random.Random(20261117)`.
- Son 33 páginas en total, por debajo de las 40 previstas, para no pasar el tope.
- **Preguntas evaluadas:** las no-T5 que tienen toda su evidencia citada dentro del subconjunto y
  una consulta en `consultas_llm.json`. Quedan n = 27: 15 T1, 7 T3, 3 T4 y 2 T2.
- La consulta de cada pregunta son las entidades y palabras clave que escribió el LLM, igual que en
  `sem_eval2.py`.

**Grafo semántico obtenido:**
- 619 nodos y 733 aristas; las 33 páginas tienen nodos.
- Relaciones: `references` 554, `conceptually_related_to` 97, `implements` 41,
  `shares_data_with` 18, `cites` 12.
- Hay 463 etiquetas normalizadas distintas, y 86 aparecen en dos o más páginas.

### Resultados (n = 27, cobertura media)

| Método | Fragmentos @3 | Claves @3 | Fragmentos @5 | Claves @5 | Tokens @5 | Gana / pierde frente a texto (frag. @5) |
|---|---:|---:|---:|---:|---:|---|
| Búsqueda (TF-IDF sobre título y resumen) | 0,59 | 0,51 | 0,71 | 0,56 | 7.146 | 0 / 8 |
| **Texto completo (control)** | 0,88 | 0,71 | 0,96 | **0,78** | 7.029 | — |
| Grafo determinista (`graphify query`) | 0,62 | 0,51 | 0,70 | 0,65 | 7.733 | 0 / 9 |
| Grafo semántico (`graphify query`) | 0,78 | **0,77** | 0,86 | 0,77 | 8.099 | 1 / 5 |
| (a) Semántico con etiquetas unificadas | 0,74 | 0,62 | 0,77 | 0,64 | 4.591 | 1 / 8 |
| (a) + texto (fusión RRF) | **0,94** | **0,77** | **0,99** | **0,78** | 7.131 | 1 / 1 (en @3: 3 / 1) |
| (b) Texto 3 + 2 vecinas por aristas semánticas | 0,88 | 0,71 | 0,94 | 0,78 | 7.347 | 0 / 2 |

Sobre la búsqueda: el `search` real del wiki no está en el subconjunto, así que lo aproximé con
TF-IDF sobre el título y el resumen del frontmatter.

### Conclusión

- **El grafo semántico solo pierde frente al texto completo:** 0,86 contra 0,96 de fragmentos con 5
  páginas; gana en 1 pregunta y pierde en 5. Sí mejora mucho al grafo determinista (0,70), porque
  sus nodos tienen etiquetas de contenido y no solo títulos.
- **En claves con 3 páginas** el grafo semántico queda arriba (0,77 contra 0,71). Pero con 5 páginas
  se iguala (0,77 contra 0,78), y con n = 27 eso no se distingue del ruido.
- **(a) Unificar etiquetas, por sí sola, no ayuda** (0,77). Muchas entidades de la pregunta no
  coinciden con ninguna etiqueta del grafo.
- **(a) fusionada con el texto es lo mejor de la tabla**, pero por poco: +0,06 de fragmentos con 3
  páginas (gana 3 preguntas, pierde 1) y +0,03 con 5 (1 y 1). Una prueba de signos da p ≈ 0,6 con 3
  páginas. No es una mejora clara.
- **(b) Expandir con vecinos semánticos** a igual número de tokens **empata o pierde** frente a traer
  más texto (0,94 contra 0,96; pierde 2 preguntas y no gana ninguna).
- **Techo:** con solo 33 páginas, el texto completo ya cubre el 96 % de los fragmentos. Queda muy poco
  margen para cualquier mejora, y eso juega a favor del texto.
- **Costo:** construir el grafo semántico cuesta ≈ 0,003 USD por página (≈ 1,4 USD para las 461),
  con truncamientos que no se evitan del todo. El texto completo no cuesta nada.

**Veredicto:** con LLM, el grafo de Graphify **pierde** frente al texto completo como recuperador
único, y **empata** como complemento (fusión RRF), sin una ganancia que justifique su costo.
Ninguna variante superó con claridad al texto, así que no hice la prueba de punta a punta con el
modelo. Mantengo la recomendación de la sección 8. Si se quiere insistir, lo único que vale la pena
repetir con más preguntas es «(a) + texto» con 3 páginas, y requiere tener el grafo semántico de
todo el wiki.
