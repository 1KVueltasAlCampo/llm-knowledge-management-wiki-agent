# tgrep y graphify: ¿bajan los tokens de la consulta del WikiLLM?

Evaluación exploratoria del 9 y 10 de noviembre de 2026. La consulta del wiki es un agente que busca páginas, las lee y responde; cada turno reenvía todo lo anterior, así que el consumo de tokens crece con el número de turnos y con lo que devuelve cada herramienta. Se probaron dos herramientas que el tutor propuso para reducirlo: [tgrep](https://github.com/microsoft/tgrep) (Microsoft) y [graphify](https://github.com/Graphify-Labs/graphify). El tutor pidió usar graphify «en función de los markdowns» del wiki y no del código; esta evaluación lo aplica como capa de navegación sobre los `.md` del wiki.

## Resumen

| | Resultado en esta prueba |
|---|---|
| **tgrep** (binario real v1.2.7) | Con su salida por defecto devuelve párrafos completos y no ahorra tokens (de +5 % a +33 % según el conjunto de preguntas). Con su opción de recortar líneas largas (`-M 300`) la entrada baja un 42 % en 3 preguntas con 9/9 aciertos, pero el mismo recorte hecho sin tgrep da −35 %: el ahorro viene de recortar la salida, no del índice de trigramas. |
| **graphify** (grafo de títulos y enlaces) | En 5 preguntas baja la entrada un 25 % (IC 95 %: −5,2 k a −1,4 k) con los mismos aciertos; el ahorro se concentra en las preguntas sin respuesta y en las fáciles cuesta más. En 3 preguntas que combinan dos papers no ahorra (+16 %) pero acierta 6/9 frente a 1/18 de la base. Cada consulta tarda 1,7 s y su modo semántico (con LLM) no terminó. |
| **Leer por secciones** | Cada lectura devuelve un 60 % menos de texto, pero el total solo baja entre 6 % y 18 % (no distinguible del ruido) y, con un esquema en la búsqueda, una pregunta pasó de 10/10 a 0/5 aciertos. |
| **Fragmentos en la búsqueda** (propia) | Devolver el párrafo más parecido de cada página y dejar responder sin abrirla baja la entrada un 10 % (IC −2,8 k a −0,4 k) con los mismos aciertos y un turno menos; en dólares no se distingue de la base. |

La evidencia es preliminar: de 3 a 5 preguntas por prueba, un solo wiki (15 de los 50 papers) y un solo modelo. Sirve para decidir qué probar a escala, no para afirmar un ahorro.

## Qué son

**tgrep** (microsoft/tgrep, v1.2.7 del 4-nov-2026, Rust, MIT). Un cliente/servidor que mantiene un índice de trigramas para acelerar búsquedas por expresión regular, integrado en GitHub Copilot CLI. Sus mediciones son de **tiempo de búsqueda** frente a ripgrep, con el índice ya construido: entre 0,93× y 51,9× más rápido en repositorios de 15.833 (Go) a 504.351 archivos (Chromium). Ni el README ni el benchmark informan tokens. Sí trae opciones para limitar la salida de un agente (`-M/--max-columns` con `--max-columns-preview`, `-m`, `-l`).

**graphify** (Graphify-Labs/graphify, v0.9.105, Apache-2.0). Construye un grafo de conocimiento de una carpeta y permite consultarlo (`query`, `path`, `explain`) en lugar de leer archivos. El código se analiza con tree-sitter sin LLM. Para Markdown tiene dos pasos: un extractor determinista (archivos, títulos de sección y enlaces `[[página]]`) y un paso semántico con LLM (conceptos y relaciones). Declara «71,5× menos tokens por consulta», pero frente a **leer los archivos crudos**, no frente a un agente que ya lee de forma selectiva como el nuestro. Sus benchmarks propios miden recuperación de memoria conversacional, no consumo de tokens de un agente sobre un wiki.

## Cómo está el wiki

15 papers ingeridos en 55 páginas: 15 de tipo paper (≈1.370 tokens, 5,7 secciones `##` y 3,5 enlaces `[[…]]` cada una) y 40 de tipo concepto (≈1.090 tokens, 6 secciones y 5,7 enlaces). Cada página lleva frontmatter con título, tipo y un resumen de una línea. `index.md` pesa ≈3.504 tokens (1.194 con 5 papers, ≈230 por paper). Ya está partido en archivos pequeños con índice, resúmenes y enlaces: partirlo más no daría información nueva al grafo, que solo ve archivos, títulos y enlaces.

## Qué se probó

- **Modelo:** el mismo `deepseek-flash` del proyecto, sobre el wiki `prueba-herramientas` (15 papers).
- **Variantes** (`scripts/comparar_herramientas.py`):
  - `actual`: el `ConsultaWiki` del proyecto. `generico`: las mismas herramientas en un agente propio (control de equivalencia; ver la nota de la ronda 3).
  - `grep`: búsqueda de líneas por expresión regular con el formato de tgrep (`archivo:línea:texto`, máx. 10 líneas) + lectura de páginas. `tgrep`: el binario real con índice en disco y `-M 300 --max-columns-preview`. `grep_recortado`: control sin tgrep que recorta cada línea a 300 caracteres.
  - `secciones` y `esquema`: lectura de una sección (`página#Título`), sin y con los títulos de sección en la búsqueda.
  - `graphify`: consulta al grafo determinista + lectura por secciones. `vecinos`: búsqueda léxica + herramienta `links` con las aristas `references` de `graph.json`.
  - `fragmentos`: la búsqueda devuelve el párrafo más parecido a la consulta de cada página (≤700 caracteres, con sus citas) y cuenta como lectura. `gist`: resumen + primer párrafo + enlaces de cada resultado, con lectura previa obligatoria (variante A3 de arXiv 2607.04576).
- **tgrep real:** se descargó `tgrep-v1.2.7-x86_64-pc-windows-msvc.zip` (5.806.983 bytes) del repositorio oficial y se verificó su SHA-256 (`62023fbe…cbe31`) contra el publicado. Se indexó el wiki fuera del repo (58 archivos, 13.102 trigramas, 0,06 s) y se comprobó que encuentra exactamente las mismas líneas que la emulación; cuando hay más de 10, cambia solo cuáles son las primeras 10, porque recorre los archivos en paralelo. Tarda 17–33 ms por búsqueda frente a 57–63 ms de la emulación.
- **Costo medido de las pruebas:** ronda 1, 0,175 USD (803 llamadas) y 0,247 USD en construir el wiki de 15 papers (estimado 0,08 USD sin hora pico; se hizo en hora pico y con papers largos); ronda 2, 0,074 USD; tgrep real y control, 0,007 USD; preguntas multi-fuente, 0,026 USD. El intento semántico de graphify no registra su consumo.

## Ronda 1: 5 preguntas × 5 repeticiones (150 corridas)

Preguntas del banco acordado: A002-T1-02 (T1, lista de cuatro acciones), B006-T1-01 (T1, valor en una tabla), A003-T3-02 (T3, dos papers), B001-T4-06 (T4) y BT5-T5-07 (T5, sin respuesta). `t. entrada` suma los tokens de entrada de todas las llamadas de una pregunta.

| Variante | Corridas | Aciertos | Llamadas | t. entrada | Mediana | USD por pregunta | Segundos |
|---|---:|---:|---:|---:|---:|---:|---:|
| línea base (actual + generico) | 50 | 30 (60 %) | 5,2 | 13.806 | 6.345 | 0,001184 | 7,0 |
| grep (emulado, línea entera) | 25 | 16 (64 %) | 5,0 | 18.301 | 11.473 | 0,001352 | 6,8 |
| secciones | 25 | 15 (60 %) | 6,0 | 12.953 | 10.918 | 0,001259 | 8,5 |
| esquema | 25 | 10 (40 %) | 5,3 | 11.319 | 5.329 | 0,001063 | 7,4 |
| graphify | 25 | 15 (60 %) | 5,3 | 10.313 | 9.233 | 0,000959 | 13,7 |

Diferencia frente a la línea base, promediando por pregunta (IC 95 % por remuestreo):

| Variante | Tokens de entrada | USD por pregunta |
|---|---|---|
| grep | +4.495 [+2.656, +6.569] | +0,0002 [−0,0001, +0,0004] |
| secciones | −853 [−2.955, +1.296] | +0,0001 [−0,0001, +0,0003] |
| esquema | −2.487 [−4.694, +30] | −0,0001 [−0,0003, +0,0001] |
| graphify | −3.494 [−5.247, −1.380] | −0,0002 [−0,0005, 0,0000] |

Mediana de tokens de entrada por pregunta (aciertos/corridas):

| Pregunta | Base | grep | secciones | esquema | graphify |
|---|---|---|---|---|---|
| A002-T1-02 (T1, lista) | 6.345 (10/10) | 9.814 (5/5) | 5.098 (5/5) | 5.329 (**0/5**) | 9.233 (5/5) |
| B006-T1-01 (T1, tabla) | 3.095 (10/10) | 2.837 (5/5) | 10.918 (5/5) | 3.000 (5/5) | 5.631 (5/5) |
| BT5-T5-07 (T5, sin respuesta) | 19.077 (10/10) | 23.456 (5/5) | 21.171 (5/5) | 17.513 (5/5) | **11.152** (5/5) |
| A003-T3-02 (T3) | 37.680 (0/10) | 41.652 (1/5) | 25.077 (0/5) | 17.341 (0/5) | 16.046 (0/5) |
| B001-T4-06 (T4) | 5.207 (0/10) | 11.473 (0/5) | 3.784 (0/5) | 3.647 (0/5) | 4.151 (0/5) |

Tokens que devuelve cada herramienta por llamada: lectura de páginas completas 2.234; lectura por secciones 574–995; búsqueda léxica 476 (753 con esquema); consulta al grafo 486; `grep` 1.001.

## Ronda 2: variantes propias, mismas 5 preguntas × 5 repeticiones (125 corridas)

Base de la misma sesión (actual + generico, 50 corridas) frente a las tres variantes nuevas.

| Variante | Aciertos | Llamadas | t. entrada | Diferencia frente a la base [IC 95 %] | Sin caché | % en caché | USD por corrida |
|---|---:|---:|---:|---|---:|---:|---:|
| base | 29/50 | 5,6 | 15.401 | — | 2.016 | 87 % | 0,000545 |
| fragmentos | 15/25 | **4,6** | 13.781 | **−1.620 [−2.783, −405]** | 2.590 | 81 % | 0,000526 |
| gist | 15/25 | 5,0 | 17.953 | +2.552 [−998, +5.658] | 3.059 | 83 % | 0,000615 |
| vecinos | 15/25 | 5,3 | 13.534 | −1.867 [−5.514, +1.575] | 3.724 | 72 % | 0,000742 |

- Los aciertos son idénticos en las cuatro (fallan las mismas A003 y B001).
- `fragmentos` ahorra un turno (4,6 frente a 5,6) y es un 22 % más rápida. Gana donde se puede responder sin abrir la página (B006: 1.893 frente a 7.346 tokens; A002: −42 %) y pierde en la pregunta sin respuesta (BT5: +20 %).
- En dólares ninguna se distingue de la base: más tokens de entrada son nuevos (sin caché) porque cada búsqueda devuelve texto más grande.
- `gist` empeora: su búsqueda pesa 1.209 tokens frente a 482 y, como la lectura sigue siendo obligatoria, se pagan las dos cosas.
- `vecinos` casi no se usó: la herramienta `links` se llamó una vez en 25 corridas, así que la navegación por vecinos no se pudo evaluar con estas preguntas.
- El porcentaje de caché varió de 72 % a 87 % sin que haya una razón de diseño; eso mueve el costo en dólares más que cualquier ahorro de tokens.
- Informe de graphify (`GRAPH_REPORT.md`): no aporta nada en este wiki. Las «comunidades» son las propias páginas y los «nodos centrales» son encabezados con 3 aristas.

## tgrep real: 3 preguntas × 3 repeticiones

A002-T1-02, B006-T1-01 y BT5-T5-07 (las que todas las variantes aciertan). Base de la ronda 2 (30 corridas de esas tres preguntas).

| Variante | Corridas | Aciertos | Llamadas | t. entrada | Diferencia frente a la base [IC 95 %] |
|---|---:|---:|---:|---:|---|
| base (misma sesión) | 30 | 29 | 5,8 | 11.284 | — |
| grep entero (emulado) | 15 | 15 | 4,6 | 11.890 | +606 [−752, +1.922] (+5 %) |
| grep recortado a 300, sin tgrep | 9 | 9 | 4,3 | 7.288 | −3.996 [−4.850, −3.155] (−35 %) |
| **tgrep real, `-M 300`** | 9 | 9 | 4,6 | **6.567** | **−4.717 [−5.675, −3.711] (−42 %)** |

tgrep real frente al control recortado: −720 [−1.319, −85] tokens (9 corridas por lado); de dónde sale esa diferencia no se estableció. Cada línea del wiki es un párrafo entero, así que por defecto tgrep devuelve ~1.000 tokens por llamada; el recorte lo baja a ~800, a costa de mostrar el inicio de la línea y no siempre la parte que coincide. Limitaciones: son preguntas que todas las variantes aciertan, y no se probaron las dos que fallan siempre.

## Preguntas que combinan dos papers: 3 preguntas × 3 repeticiones

B002-T3-02 (comparar una cifra entre dos papers), A013-T3-02 (dos papers con resultados que se contradicen) y A016-T2-01 (cómo difieren dos sistemas), con la base `generico` y la real `actual`.

| Pregunta | actual | generico | graphify | vecinos |
|---|---|---|---|---|
| B002-T3-02 | 0/3 · 14.457 | 0/3 · 14.390 | 0/3 · 25.923 | **3/3** · 27.002 |
| A013-T3-02 | 1/3 · 8.935 | 0/3 · 6.688 | **3/3** · 6.910 | 0/3 · 6.765 |
| A016-T2-01 | 0/3 · 11.373 | 0/3 · 13.207 | **3/3** · 7.390 | 0/3 · 5.528 |
| Total | 1/9 · 11.588 | 0/9 · 11.428 | **6/9** · 13.408 | 3/9 · 13.098 |

(aciertos/corridas · tokens de entrada medios). graphify no ahorra tokens en estas preguntas (+16 %) pero resuelve dos que la base no resuelve nunca. En la traza de A016 la consulta al grafo llevó a leer tres páginas de concepto que sintetizan varios papers, mientras que la búsqueda por palabras llevó a páginas de papers sueltos; es la observación de un caso, no un mecanismo demostrado. Cautelas: son 3 preguntas; a temperatura 0 las repeticiones de una pregunta no son independientes (da casi siempre 0/3 o 3/3); «correcta» es la presencia de frases clave, una medida débil para preguntas cualitativas, y el juez no se ejecutó; y graphify y vecinos ganan en preguntas distintas, de modo que depende de la pregunta.

Nota sobre la base: `actual` genera respuestas más largas que `generico` (622 frente a 419 tokens de salida en estas preguntas, y en la ronda 1 hasta 1.530 frente a 410 en A003), así que las comparaciones en dólares con `actual` no son limpias; el control de equivalencia solo se sostuvo en tokens de entrada en las preguntas deterministas.

## Lectura de los resultados

1. **tgrep no ahorra por ser tgrep.** La velocidad de búsqueda no es el problema del WikiLLM: con decenas de páginas ya tarda milisegundos (17–33 ms frente a 57–63 ms). Por defecto devuelve párrafos completos y no ahorra. Lo que ahorra es recortar la salida, algo que se puede hacer en la propia búsqueda sin depender del binario.
2. **graphify ahorra donde la base es cara y pierde donde es barata.** Para un término ausente (T5), el grafo responde «ningún nodo» en 6 tokens y el agente lee secciones pequeñas: 11.152 frente a 19.077 tokens (−42 %). En las dos preguntas fáciles consume más (A002 +46 %, B006 +82 %). El ahorro en las preguntas que ninguna variante acierta (A003, B001) es un fallo más barato, no eficiencia.
3. **El grafo determinista no guarda contenido.** Para 55 páginas tiene 386 nodos y 573 aristas (330 `contains` y 243 `references`), todos archivos, títulos o enlaces entre páginas. La consulta devuelve etiquetas y posiciones, nunca texto: hay que leer después. Se construye en 11 s y sin costo.
4. **El paso semántico no es viable con este modelo.** Con `deepseek-flash`, la extracción sobre 21 páginas se truncó una y otra vez (21 → 10 + 11 → 5 + 5 → 2 + 3, y aun así truncado); a los 15 minutos no había producido ningún nodo y se canceló.
5. **Leer por secciones reduce el texto devuelto, no necesariamente los tokens totales.** Con el esquema en la búsqueda, el agente eligió la sección equivocada de A002 y falló las 5 veces; la página completa evita ese riesgo.
6. **Las dos preguntas que fallan siempre, fallan por otra causa que la herramienta.** B001-T4-06 responde 89,1 en lugar de 90,4: el wiki conserva el 90,4 de HippoRAG 2, pero no la fila «HippoRAG (reproducido)» de la tabla de ese paper. En A003-T3-02 el agente responde con 65,6 (el promedio de ColBERTv2 en los tres conjuntos) en lugar de 68,2 (su R@5 en 2Wiki); los dos números están en la misma frase de `retrieval-augmented-generation`.
7. **El ruido es grande.** La misma implementación varía entre 713 y 41.140 tokens en una misma pregunta según la trayectoria del agente; por eso las conclusiones usan intervalos.
8. **En dólares el efecto es pequeño.** DeepSeek cobra la entrada repetida desde la caché a una fracción del precio: entre 72 % y 87 % de la entrada fue caché. Una consulta cuesta del orden de 0,0005–0,001 USD, mientras ingerir un paper costó ≈0,016 USD (0,247 USD por 15), unas 30 consultas. A esta escala el costo está sobre todo en construir el wiki, no en consultarlo.

## Limitaciones

- De 3 a 5 preguntas por prueba, 15 papers; ninguna conclusión por tipo de pregunta es firme. La métrica de acierto es la presencia de frases clave; el juez no se ejecutó.
- El costo de la consulta crece con el tamaño del wiki (el índice pasó de 1.194 a 3.504 tokens de 5 a 15 papers; a 50 rondaría los 11.000 si crece de forma lineal). La consulta al grafo está acotada por su presupuesto (≈500 tokens), así que su ventaja podría crecer con la escala, pero no se midió.
- `graphify` se invocó como proceso externo (1,7 s por consulta, casi todo arranque y carga del grafo), lo que hace al agente el doble de lento. Un uso en proceso (servidor MCP) quitaría ese costo; no se probó.
- El paso semántico se probó una sola vez, con un solo modelo y la configuración por defecto, y construir el conocimiento desde los Markdown de los papers (en vez de desde el wiki) no se probó: es otra arquitectura.
- Las trayectorias del agente no son deterministas; la comparación entre variantes mezcla cambios de herramienta con cambios de trayectoria.

## Qué sigue

1. **Preguntar al tutor** si «en función de los markdowns» significa usar el grafo como capa de navegación sobre el wiki (lo probado aquí) o construir el conocimiento desde los Markdown de los papers (otra arquitectura, no probada).
2. **Decidir antes de congelar** si la búsqueda del wiki recorta la salida o devuelve fragmentos (cambio propio, sin dependencias y sin reingerir): una prueba de ~12 preguntas en el wiki de 15 papers cuesta ≈0,05 USD.
3. **Repetir a escala** cuando exista el wiki de 50 papers (el estado final de la corrida completa sirve): unas 20 preguntas, incluidas las que combinan varios papers, para comprobar si la ventaja de graphify en preguntas entre documentos se sostiene.
4. **No adoptar lectura por secciones sola:** introduce fallos de selección.
5. Cualquier cambio de la consulta es del lado de la consulta y no obliga a reingerir; solo cambiar cómo se escriben las páginas obliga a rehacer el wiki desde cero.

## Reproducir

```powershell
# grafo determinista del wiki (en un entorno aparte con graphifyy instalado)
graphify update <copia de pages/ e index.md>

# ronda 1 (variantes por defecto)
uv run python scripts/comparar_herramientas.py --wiki data/wiki/prueba-herramientas \
    --grafo <graph.json> --graphify <graphify.exe> --repeticiones 5 \
    --salida results/herramientas/paso15
# ronda 2 y preguntas multi-fuente
uv run python scripts/comparar_herramientas.py --grafo <graph.json> \
    --variantes actual,generico,fragmentos,gist,vecinos --repeticiones 5 \
    --salida results/herramientas/paso15-ronda2
# tgrep real (índice creado antes con: tgrep index . --index-path <carpeta> --no-require-git)
uv run python scripts/comparar_herramientas.py --variantes tgrep --tgrep <tgrep.exe> \
    --tgrep-indice <carpeta> --preguntas A002-T1-02,B006-T1-01,BT5-T5-07 --repeticiones 3 \
    --salida results/herramientas/paso15-tgrep-real
uv run python scripts/analizar_herramientas.py results/herramientas/paso15
```

Las corridas están en `results/herramientas/` (`corridas.jsonl` con la trayectoria de cada pregunta; `resumen_paso15.txt` y `resumen_ronda2.txt` con las tablas). El registro de llamadas lleva texto del wiki y no se versiona.
