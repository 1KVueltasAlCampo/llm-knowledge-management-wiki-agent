# Guion de la demostración en vivo: WikiLLM frente a RAG

Guion para mostrar el panel web (`uv run python -m wikillm.panel`, http://127.0.0.1:8765).
La barra **Recorrido** del panel sigue estos mismos 6 pasos y resalta el que toca.
Duración estimada: 10–12 minutos. Costo total en vivo: menos de 0,02 USD.

Las cifras de «Resultado esperado» salen del ensayo real del 2026-11-09 (21:10 UTC, en Linux con
una RTX 3050). El proveedor no garantiza respuestas idénticas, así que la redacción, el número
de pasos del agente y los centavos pueden variar un poco.

---

## 0. Antes de empezar (15 minutos antes, sin público)

| # | Qué hacer | Cómo saber que está bien |
|---|---|---|
| 1 | `uv run python -m wikillm.panel` | Se abre el navegador en http://127.0.0.1:8765 |
| 2 | Esperar a que cargue el índice del RAG (~15 s) | En **Sistema**: «Índice del RAG cargado en memoria» |
| 3 | **Sistema → Reiniciar el wiki** | La barra superior dice «Corpus: 5 de 50 papers ingeridos» |
| 4 | **Sistema → Verificar** | 11 de 11 en orden (10 si hay cambios sin commit en el repo) |
| 5 | Revisar la hora | Fuera de la hora pico de DeepSeek: 01–04 y 06–10 UTC (20–23 h y 01–05 h en Colombia) |
| 6 | Dejar el panel en **Preguntar**, con la barra Recorrido visible | El paso 2 «Preguntar antes» aparece resaltado |

**Si se reinstala el entorno.** `data/qdrant` (índice del RAG, en Qdrant local) y `data/wiki/dev2` (wiki base de
5 papers) no se versionan. Se reconstruyen así:
`uv run python -m wikillm.rag indexar` (gratis, unos 75 s en GPU) y
`uv run python -m wikillm.wiki ingerir --paso 5 --wiki data/wiki/dev2` (≈ 0,04 USD).

---

## Reparto sugerido

| Bloque | Pasos | Quién |
|---|---|---|
| A. La memoria y la abstención | 1–2 | Persona 1 |
| B. Ingesta en vivo y respuesta | 3–4 | Persona 2 |
| C. Evidencia y resultados | 5–6 | Persona 1 o las dos |

---

## Paso 1. El wiki en el paso 5 (≈ 1,5 min · sin costo)

**Clic:** Recorrido → «1 El wiki en el paso 5» (sección **Wiki**).

**Mostrar:**
- **El grafo del wiki** (tipo Obsidian): 18 páginas y 39 enlaces `[[...]]`. Las páginas de
  conceptos (verde) forman el núcleo y las de papers (índigo) cuelgan de ellos. Al pasar el
  cursor por un nodo se resaltan sus vecinos; al hacer clic se abre la página.
- El índice del wiki: unas 18 páginas, cada una con un resumen de una línea.
- Abrir una página de paper, por ejemplo la de HippoRAG. Cada afirmación lleva su `[span_id]`.
- «Abrir el registro» (`log.md`): una entrada por ingesta con citas eliminadas y enlaces rotos.
- «Ver el historial versionado»: etiquetas `paso-1` a `paso-5`.

**Qué decir:**
> «La memoria del WikiLLM no es una caja negra: es Markdown legible, con una cita por
> afirmación y una copia versionada por cada paper que entra. El RAG, en cambio, guarda vectores.»

---

## Paso 2. Preguntar antes de la ingesta (≈ 1,5 min · ≈ 0,0004 USD)

**Clic:** Recorrido → «2 Preguntar antes». Deja precargada la pregunta de BeliefShift:
*What is the total number of sessions in the BeliefShift dataset?* → **Preguntar** → confirmar.

**Resultado esperado:**
- Los **dos se abstienen**: «The ingested corpus does not contain this information.»
- La Lectura rápida dice: «Los dos se abstuvieron: el corpus ingerido no contiene la respuesta
  y ninguno la inventó.»
- RAG: recupera 5 fragmentos parecidos, pero de otros papers (distancia ≈ 0,33), y responde en
  1 llamada.
- WikiLLM: el agente busca 3 veces con palabras distintas («BeliefShift dataset sessions»,
  «BeliefShift»…), no encuentra páginas y se abstiene (4 llamadas).

**Qué decir:**
> «El paper de BeliefShift es el sexto en el orden de ingesta. Con 5 papers el corpus no tiene
> la respuesta, y lo correcto es abstenerse, no inventar. Los dos lo hacen bien.»

---

## Paso 3. Ingesta en vivo del paper 6 (≈ 2 min · ≈ 0,009 USD · ~40 s)

**Clic:** Recorrido → «3 Ingerir el paper 6» → **Ingerir el paper 6** → confirmar.

**Mientras corre (40 s), explicar las 4 etapas que se van marcando:**
1. **Plan:** el modelo decide qué páginas crear o actualizar.
2. **Escritura:** redacta las páginas con citas.
3. **Validación por código:** quita las citas que no resuelven a un fragmento real, deja como
   texto los enlaces sin destino y cuenta las cifras sin cita.
4. **Copia versionada:** etiqueta `paso-6`.

**Resultado esperado** (ensayo): 2 llamadas · 39 s · 0,0086 USD · **3 páginas creadas,
5 actualizadas** · 0 citas eliminadas · 0 enlaces rotos.

**Al terminar, ir a Wiki:** el grafo crece (21 páginas en el ensayo) y el anillo naranja
discontinuo marca las páginas que tocó la ingesta del paso 6. Así se ve que un paper nuevo no
solo agrega su página: también actualiza los conceptos con los que se conecta.

**Qué decir:**
> «El modelo propone; el código decide qué se guarda. Ninguna cita entra al wiki si no apunta a
> un fragmento real del corpus.»

---

## Paso 4. La misma pregunta después de la ingesta (≈ 2 min · ≈ 0,0007 USD)

**Clic:** Recorrido → «4 Preguntar después» → **Preguntar**.

**Resultado esperado:**
- Los dos responden **68,160** sesiones y citan el **mismo fragmento**: `2603.23848#s18.p3`.
- Lectura rápida (ensayo):
  - «Los dos respondieron y citan el mismo fragmento del corpus: 2603.23848#s18.p3.»
  - «El RAG usó 2,2× menos tokens de entrada (RAG 1.503 · WikiLLM 3.294).»
  - «El RAG usó 3,0× menos llamadas al modelo (RAG 1 · WikiLLM 3).»
- WikiLLM: buscó «BeliefShift dataset sessions» → leyó la página del paper → respondió.
- Hacer clic en la cita (`2603.23848#s18.p3`) dentro de la respuesta para resaltar el fragmento
  del corpus que la respalda.

**Qué decir:**
> «Misma respuesta, misma fuente, mismo modelo: lo único que cambia es la arquitectura. En una
> pregunta factual como esta el RAG es más barato. La apuesta del WikiLLM está en las preguntas
> que cruzan papers y en las que se actualizan cuando entra un paper nuevo, y eso lo mide el
> banco de preguntas, no una sola pregunta.»

---

## Paso 5. Evidencia (≈ 1 min · sin costo)

**Clic:** Recorrido → «5 Evidencia» (abre el visor de archivos).

**Mostrar:**
- `results/demo/comparaciones.jsonl`: una línea por comparación con respuestas, citas, costo y
  traza del agente.
- `results/piloto-1/corrida.json`: modelo, temperatura, fecha y commit de la corrida.
- En la ejecución: pestaña **Llamadas al modelo**, con tokens, segundos y dólares de cada llamada.

**Qué decir:**
> «Todo costo queda registrado y toda cifra del informe sale de una corrida guardada.»

---

## Paso 6. Resultados del piloto y costo (≈ 2 min · sin costo)

**Clic:** Recorrido → «6 Resultados».

**Mostrar el bloque «RAG frente a WikiLLM con 5 papers ingeridos»:**
- «El WikiLLM acierta más: 5 de 6 preguntas respondibles frente a 2. A cambio, el WikiLLM lee
  2,9× más contexto por pregunta.»
- Cobertura 0,33 (RAG) frente a 0,83 (WikiLLM) ✓; abstención correcta y fundamentación en 1,00
  para los dos.
- El ✓ marca el mejor valor de cada métrica. El RAG gana en contexto (1.217 frente a 3.544
  tokens), tokens por acierto (10.341 frente a 12.049) y costo (0,0027 frente a 0,0123 USD).
- «Métricas en la consola → Calcular» se puede pulsar: recalcula sobre las respuestas guardadas
  y da las mismas cifras que se ven en pantalla.
- Botones **Estimar**: piloto ≈ 0,51 USD; corrida completa (60 preguntas × 11 pasos × 2
  sistemas) ≈ **4,67 USD**.

**Qué decir (importante, con honestidad):**
> «Es un piloto con 17 preguntas: demuestra que la cadena de evaluación funciona de punta a
> punta, **no** es un resultado del informe. El banco tiene 60 preguntas: 30 ya verificadas por
> una persona y 30 en borrador. Solo cuentan cuando los dos autores las verifican contra el paper.»

---

## Plan B: si falla la conexión o el proveedor

- **Preguntar** e **Ingerir** → botón **Ejecuciones guardadas**: reproduce un ensayo sin llamar
  al modelo. El panel muestra el aviso «REPRODUCCIÓN… No es una ejecución en vivo»; dilo en voz
  alta.
- Los pasos 1, 5 y 6 nunca llaman al modelo.
- Si la ingesta en vivo falla a mitad: **Sistema → Reiniciar el wiki** y usar la reproducción.
- Tope de gasto de la sesión: 0,25 USD. La demo completa usa menos de 0,02 USD.

## Preguntas probables del jurado

| Pregunta | Respuesta corta |
|---|---|
| ¿Por qué el mismo modelo? | Es la única variable: cambia la arquitectura de la memoria, no el modelo (constitución, regla 1). |
| ¿El RAG no es más barato? | En preguntas puntuales, sí (Paso 4). El experimento mide si el wiki compensa en preguntas que cruzan papers y en la actualización de cifras (T4). |
| ¿Cómo saben que una cita es real? | Toda cita debe resolver a un `span_id` con la misma huella en el Gold; el código quita las que no. |
| ¿Quién juzga las respuestas? | Primero una capa determinista; lo indeterminado lo juzga un modelo distinto (gemini-3.1-flash-lite) del que responde y del que redactó las preguntas. |
| ¿Por qué el piloto «no vale»? | n pequeño y preguntas sin acordar entre los dos autores. |

## Después de la demo

- **Sistema → Reiniciar el wiki** para dejar todo otra vez en el paso 5. La evidencia de la
  sesión se aparta en `results/demo/ensayos/`.
