# Prompt para una opinión externa sobre la ampliación del corpus

**Cómo usarlo:** pega el texto que está entre las dos líneas `=====` en otro agente (idealmente uno con acceso a internet). Si puede recibir archivos, adjunta también `propuesta_25_papers.md`, `propuesta_25_papers_b.md` y `verificacion_candidatos.md`; el prompt ya lleva la tabla completa para funcionar sin adjuntos.

=====
## Rol y actitud
Actúa como un revisor externo, senior, experto en evaluación de sistemas de recuperación (RAG), memoria de agentes con LLM y diseño experimental. Quiero que seas **crítico, analítico y pesimista**: asume que este plan tiene fallas que sus autores no ven, que los datos favorecen sin querer a uno de los dos sistemas y que varias decisiones «razonables» son sesgos de selección. **No halagues.** A cada recomendación que hagas añádele al menos un «pero»: qué podría salir mal o qué supuesto no se ha comprobado. Prefiero que sugieras de más (alternativas, pruebas, cambios, papers) a que te quedes corto. Si algo te parece bien, di qué lo rompería.

## Contexto del proyecto
Tesis de maestría (Universidad Icesi, MIA) que compara experimentalmente **dos formas de poner conocimiento a disposición de un modelo de lenguaje**:
- **RAG simple:** búsqueda vectorial (fragmentos de hasta 400 tokens, embeddings bge-small, base Qdrant, top-5) y una sola llamada al modelo.
- **WikiLLM:** un LLM compila cada paper nuevo en un wiki de páginas Markdown enlazadas (integra, actualiza y marca lo superado) y un agente lo consulta con herramientas de búsqueda léxica (sin embeddings) y de lectura de páginas.

Mismo modelo para ambos (`deepseek-flash`), mismo corpus, mismas preguntas; lo único que cambia es la arquitectura. Hipótesis: el RAG recupera lo más parecido semánticamente aunque esté superado, mientras que un wiki mantenido de forma incremental puede reflejar lo más reciente; la contrapartida es un mayor costo de ingesta y de consulta. Cualquier resultado, incluso desfavorable al wiki, es válido y se reporta.

## Estado actual
- Corpus de **50 papers de arXiv** (casi todos de 2026, sobre memoria de agentes, RAG y wikis de LLM), procesados por capas (Bronze, Silver, Gold) con fragmentos citables.
- Banco de **60 preguntas** acordadas por los dos autores y con respuesta fijada por humanos desde el corpus: 26 T1 (dato puntual), 12 T2 (síntesis de varios papers), 8 T3 (comparación o contradicción), 4 T4 (actualización: el dato cambia al ingerir un paper posterior), 10 T5 (sin respuesta en el corpus, para medir abstención). Se descubrió que dos T4 eran ambiguas: dos papers reportan cifras distintas del mismo método por usar otra configuración, no por actualización.
- Métricas: correctitud (capa determinista de claves y, para lo indeterminado, un juez de otro proveedor aún sin calibrar), fundamentación de las citas, cobertura, abstención, respuestas obsoletas y contexto/costo/tiempo.
- Solo hay mediciones exploratorias con 15 papers y pocas preguntas.
- **Regla de la ingesta mínima:** antes del paso en que están ingeridas todas las fuentes de una pregunta, lo correcto es abstenerse (con una frase fija). Si la respuesta cambia al llegar un paper posterior, el banco guarda la clave por paso (`respuesta_por_paso`).
- **Mismas reglas de respuesta en los dos brazos:** usan el mismo texto de reglas y la misma frase de abstención. Lo desigual es el presupuesto: el wiki puede hacer hasta 8 acciones de búsqueda y lectura, y el RAG hace una sola llamada con los 5 fragmentos más cercanos. Es una limitación ya declarada.
- **Graphify y tgrep:** Graphify construye, sin llamar a ningún modelo, un grafo de los archivos `.md` del wiki (archivos, títulos y enlaces) y se usa solo como capa de consulta; tgrep es un `grep` con índice que se ofrece al agente como herramienta opcional, solo después de leer una página. Ninguno cambia cómo se escribe el wiki. En pruebas con 15 papers, Graphify ayudó en preguntas que combinan varios papers y tgrep no redujo el costo.
- **No existe todavía un brazo «RAG con fechas»** (mismo índice con la fecha de cada paper).

## Lo que pidió el tutor (reunión del 11-nov-2026, citas textuales corregidas)
- «enfoquémonos en identificar más casos de borde. Sí, hacer mucho más robusta la conclusión».
- «traigan de esos quince papers, busquen esos 15 papers de dónde provienen y tráiganse los anteriores a los que esos papers fueron citados».
- «la ley del mínimo esfuerzo, no por ser perezoso, sino porque necesito graduarlos».
- Su miedo es que las conclusiones queden ambiguas. Quiere poder concluir si, en los casos de borde (información antigua y reciente muy parecidas semánticamente), el WikiLLM es mejor que una búsqueda vectorial.

## Plan que se somete a tu crítica
1. Ampliar el corpus de 50 a **100 papers**, añadiendo **50 papers anteriores que citan los 50 actuales**. Los recomendados de los bloques A y B son de dic-2023 a 2025, porque arXiv solo ofrece HTML propio desde dic-2023 y el pipeline usa HTML. Los verdaderamente antiguos (2018 a nov-2023, como MemGPT, ReAct, el RAG original o HotpotQA) están en el bloque C: solo existen en ar5iv, y habría que hacer un cambio pequeño en la ingesta para pedirlos allí (el conversor ya los lee sin cambios). Decide si conviene sustituir parte de los bloques A y B por papers del bloque C.
2. Construir el wiki **una sola vez** (100 papers, uno a uno, en orden cronológico), guardando instantáneas de los `.md` hacia 1/3, 2/3 y el total («3 fases»), y **reutilizarlas** para todos los brazos (RAG; WikiLLM; WikiLLM + Graphify; WikiLLM + Graphify + tgrep) sin volver a ingerir.
3. Añadir **40 preguntas nuevas de casos de borde** (20 por autor) con respuesta verificable (lista de 3 a 5 datos), repartidas así: antiguo frente a nuevo (8), vocabulario distinto (6), abstención con distractores (6), contradicción (5), agregación (5), cita de segunda mano (4), marco temporal (3), detalle de tabla o anexo (3).
4. Hacer las preguntas solo en **3 tandas** más un paso 0 (corpus vacío).

Restricciones: exposición el 20-nov-2026 y todo cerrado el 27; saldo de unos 7,9 USD y costo estimado del experimento completo de 1,9 USD con dos brazos y 2,6 USD con cuatro; preguntas en inglés sencillo y poco técnico; las respuestas las fijan y verifican los dos autores; la rúbrica del curso exige además mitigación de riesgos éticos (seguridad, privacidad, sesgo) y evidencia de eficiencia.

## Datos que se te entregan
102 candidatos: 50 recomendados (25 del bloque A y 25 del bloque B), 35 de reserva (15 del bloque A y 20 del B; se quitaron 2 que no tienen HTML en arXiv) y 17 antiguos opcionales (bloque C, solo en ar5iv). «Verificación» significa que se comprobó contra el texto real descargado de arXiv: que el identificador existe y su título coincide, que el HTML se convierte sin error, tamaño en tokens, y que los términos en los que se apoya la pregunta de ejemplo aparecen en el texto. **No** significa que la respuesta de la pregunta esté fijada. «Corpus» es cuántos de los 50 papers actuales mencionan ese método o benchmark y cuántos traen filas de tabla con sus cifras.

| ID | Grupo | Nombre | Fecha | Tokens | Casos de borde propuestos | Verificación | Corpus (menciones/con tabla) |
|---|---|---|---|---|---|---|---|
| 2504.19413 | A-rec | Mem0 | 2025-04 | 14433 | Cita de segunda mano, antiguo frente a nuevo, agregación | ok | 27/10 |
| 2501.13956 | A-rec | Zep | 2025-01 | 9484 | Contradicción | ok | 14/7 |
| 2502.12110 | A-rec | A-MEM | 2025-02 | 19758 | Vocabulario distinto | ok | 23/13 |
| 2410.05779 | A-rec | LightRAG | 2024-10 | 14358 | Misma herramienta, escalas distintas | ok | 7/4 |
| 2404.16130 | A-rec | GraphRAG | 2024-04 | 18898 | Vocabulario, distractor | ok | 18/5 |
| 2401.18059 | A-rec | RAPTOR | 2024-01 | 14412 | Distractor frente al wiki | ok | 12/8 |
| 2507.03724 | A-rec | MemOS (artículo largo) | 2025-07 | 28988 | Distractor por nombre parecido | ok | 8/4 |
| 2507.07957 | A-rec | MIRIX | 2025-07 | 12055 | Detalle, agregación | ok | 5/2 |
| 2508.19828 | A-rec | Memory-R1 | 2025-08 | 14188 | Vocabulario distinto | ok | 5/1 |
| 2510.18866 | A-rec | LightMem | 2025-10 | 15402 | Contradicción, agregación | ok | 7/5 |
| 2410.10813 | A-rec | LongMemEval | 2024-10 | 19321 | Agregación | ok | 24/9 |
| 2402.17753 | A-rec | LoCoMo | 2024-02 | 13736 | Contradicción en los datos del benchmark | ok | 24/9 |
| 2507.05257 | A-rec | MemoryAgentBench | 2025-07 | 23455 | Vocabulario distinto | ok | 14/6 |
| 2511.03506 | A-rec | HaluMem | 2025-11 | 16347 | Abstracción | ok | 4/3 |
| 2510.17281 | A-rec | MemoryBench | 2025-10 | 31904 | Vocabulario distinto | ok | 5/3 |
| 2506.21605 | A-rec | MemBench | 2025-06 | 14149 | Vocabulario distinto | ok | 8/6 |
| 2510.27246 | A-rec | BEAM | 2025-10 | 23163 | Escala, marco temporal | ok | 7/4 |
| 2512.13564 | A-rec | Memory in the Age of AI Agents | 2025-12 | 74187 | Vocabulario, antiguo frente a nuevo | alerta: muchos errores de conversión | 1/0 |
| 2505.00675 | A-rec | Rethinking Memory | 2025-05 | 40831 | Vocabulario | ok | 0/0 |
| 2404.13501 | A-rec | Survey on the Memory Mechanism (2024) | 2024-04 | 25747 | Abstención, antiguo frente a nuevo | ok | 1/0 |
| 2312.10997 | A-rec | RAG Survey (2023) | 2023-12 | 18892 | Abstención, distractor | ok | 0/0 |
| 2412.15605 | A-rec | Don't Do RAG (CAG) | 2024-12 | 5966 | Contradicción parcial con WiCER (depende de la escala) | ok | 2/0 |
| 2403.08319 | A-rec | Knowledge Conflicts Survey | 2024-03 | 15940 | Vocabulario sobre contradicciones | ok | 2/0 |
| 2511.17208 | A-rec | Simple Yet Strong Baseline | 2025-11 | 13310 | Contradicción | ok | 0/0 |
| 2512.12818 | A-rec | Hindsight is 20/20 | 2025-12 | 18056 | Agregación, afirmaciones que se pisan | ok | 6/3 |
| 2511.01448 | A-res | LiCoMemory | 2025-11 | 12150 | Agregación | ok | 5/3 |
| 2511.18423 | A-res | General Agentic Memory | 2025-11 | 8001 | Vocabulario distinto | ok | 3/2 |
| 2507.02259 | A-res | MemAgent | 2025-07 | 10320 | Vocabulario distinto | ok | 4/2 |
| 2506.15841 | A-res | MEM1 | 2025-06 | 13261 | Vocabulario distinto | ok | 3/1 |
| 2509.25911 | A-res | Mem-α | 2025-09 | 14494 | Vocabulario distinto | ok | 0/0 |
| 2502.13270 | A-res | REALTALK | 2025-02 | 4238 | Contradicción (conversaciones reales frente a sintéticas) | ok | 3/2 |
| 2504.14225 | A-res | PersonaMem | 2025-04 | 11564 | Marco temporal (preferencias que cambian) | ok | 7/4 |
| 2502.05589 | A-res | On Memory Construction | 2025-02 | 14901 | Detalle | ok | 1/0 |
| 2504.15965 | A-res | From Human Memory to AI Memory | 2025-04 | 17530 | Vocabulario, antiguo frente a nuevo (revisión) | ok | 1/0 |
| 2408.08921 | A-res | Graph RAG: A Survey | 2024-08 | 29185 | Abstención | ok | 0/0 |
| 2501.00309 | A-res | RAG with Graphs | 2024-12 | 58606 | Vocabulario, contradicción entre revisiones | ok | 0/0 |
| 2404.06654 | A-res | RULER | 2024-04 | 18183 | Vocabulario (tamaño real del contexto) | ok | 6/0 |
| 2402.14207 | A-res | STORM | 2024-02 | 18458 | Distractor frente a LLM-Wiki | ok | 0/0 |
| 2509.25140 | A-res | ReasoningBank | 2025-09 | 16174 | Vocabulario distinto | ok | 3/0 |
| 2506.07398 | A-res | G-Memory | 2025-06 | 13969 | Distractor (multiagente) | ok | 7/0 |
| 2406.13805 | B-rec | WikiContradict | 2024-06 | 14932 | Contradicción | ok | 1/0 |
| 2408.12076 | B-rec | ConflictBank | 2024-08 | 16583 | Contradicción, antiguo frente a nuevo | ok | 2/0 |
| 2506.08184 | B-rec | Unable to Forget | 2025-06 | 20571 | Distractor, antiguo frente a nuevo | ok | 1/0 |
| 2406.19354 | B-rec | Fundamental Problems With Model Editing | 2024-06 | 20674 | Antiguo frente a nuevo (cambiar una creencia) | ok | 6/0 |
| 2506.06331 | B-rec | How Significant Are the Real Gains? (GraphRAG) | 2025-05 | 13483 | Contradicción con cifras reportadas, cita de segunda mano | ok | 0/0 |
| 2503.04338 | B-rec | In-depth Analysis of Graph-based RAG | 2025-03 | 36165 | Agregación, contradicción | ok | 0/0 |
| 2506.02404 | B-rec | GraphRAG-Bench | 2025-06 | 9413 | Agregación | ok | 0/0 |
| 2511.10523 | B-rec | ConvoMem | 2025-11 | 21100 | Contradicción con la necesidad de RAG, marco temporal | ok | 2/1 |
| 2510.23730 | B-rec | Evaluating Long-Term Memory for Long-Context QA | 2025-10 | 11897 | Agregación, vocabulario distinto | ok | 0/0 |
| 2505.24226 | B-rec | E2GraphRAG | 2025-05 | 10927 | Cita de segunda mano, agregación | ok | 1/1 |
| 2505.22101 | B-rec | MemOS (primer artículo) | 2025-05 | 5496 | Distractor por mismo nombre, antiguo frente a nuevo | ok | 8/4 |
| 2409.05591 | B-rec | MemoRAG | 2024-09 | 13888 | Vocabulario distinto | ok | 2/2 |
| 2510.04618 | B-rec | Agentic Context Engineering (ACE) | 2025-10 | 18497 | Antiguo frente a nuevo, detalle | ok | 1/0 |
| 2504.07952 | B-rec | Dynamic Cheatsheet | 2025-04 | 13922 | Vocabulario distinto | ok | 1/0 |
| 2407.12784 | B-rec | AgentPoison | 2024-07 | 16650 | Seguridad (rúbrica Cr7) | ok | 2/0 |
| 2503.03704 | B-rec | Memory Injection Attacks (MINJA) | 2025-03 | 24861 | Seguridad (rúbrica Cr7) | ok | 0/0 |
| 2511.14937 | B-rec | CIMemories | 2025-11 | 7844 | Privacidad (rúbrica Cr7) | ok | 0/0 |
| 2505.18279 | B-rec | Collaborative Memory | 2025-05 | 23811 | Privacidad (rúbrica Cr7) | ok | 3/0 |
| 2402.04624 | B-rec | MemoryLLM | 2024-02 | 11657 | Vocabulario distinto (memoria dentro del modelo) | ok | 2/0 |
| 2407.01178 | B-rec | Memory³ | 2024-07 | 27787 | Vocabulario distinto, distractor | ok | 1/0 |
| 2502.06975 | B-rec | Position: Episodic Memory | 2025-02 | 10533 | Vocabulario distinto, marco temporal | alerta: HTML sin título (identidad comprobada solo por el contenido) | 0/0 |
| 2511.07587 | B-rec | Generative Semantic Workspaces (GSW) | 2025-11 | 21627 | Distractor frente a HippoRAG, agregación | ok | 0/0 |
| 2511.20857 | B-rec | Evo-Memory | 2025-11 | 15620 | Agregación | ok | 1/1 |
| 2411.00489 | B-rec | Human-inspired Perspectives (revisión 2024) | 2024-11 | 31657 | Antiguo frente a nuevo (revisión) | ok | 0/0 |
| 2312.06648 | B-rec | Dense X Retrieval | 2023-12 | 13121 | Vocabulario distinto, distractor | ok | 0/0 |
| 2509.18868 | B-res | Memory in LLMs: Mechanisms, Evaluation and Evolution | 2025-09 | 47408 | Vocabulario, agregación | ok | 0/0 |
| 2512.23343 | B-res | AI Meets Brain | 2025-12 | 32159 | Vocabulario | ok | 0/0 |
| 2501.09136 | B-res | Agentic RAG: A Survey | 2025-01 | 21139 | Vocabulario | ok | 4/1 |
| 2407.21059 | B-res | Modular RAG | 2024-07 | 17807 | Vocabulario, distractor | ok | 1/1 |
| 2401.01286 | B-res | A Comprehensive Study of Knowledge Editing | 2024-01 | 29477 | Antiguo frente a nuevo | ok | 4/0 |
| 2403.04782 | B-res | Survey on Temporal Knowledge Graphs | 2024-03 | 19592 | Marco temporal | ok | 12/0 |
| 2510.13614 | B-res | MemoTime | 2025-10 | 20995 | Marco temporal | ok | 1/0 |
| 2510.02373 | B-res | A-MemGuard | 2025-09 | 17698 | Seguridad | ok | 0/0 |
| 2512.04668 | B-res | Topology Matters (fugas entre agentes) | 2025-12 | 16235 | Privacidad | ok | 1/1 |
| 2406.13144 | B-res | DialSim | 2024-06 | 16466 | Agregación | ok | 2/1 |
| 2510.01353 | B-res | MEMTRACK | 2025-10 | 14527 | Marco temporal, agregación | ok | 2/1 |
| 2512.12856 | B-res | Forgetful but Faithful | 2025-12 | 51767 | Privacidad, olvido | ok | 0/0 |
| 2508.10391 | B-res | LeanRAG | 2025-08 | 16729 | Distractor frente a GraphRAG | ok | 0/0 |
| 2503.21322 | B-res | HyperGraphRAG | 2025-03 | 16141 | Vocabulario distinto | ok | 1/0 |
| 2407.04363 | B-res | AriGraph | 2024-07 | 10941 | Distractor frente a HippoRAG | ok | 1/1 |
| 2512.12686 | B-res | Memoria | 2025-12 | 9512 | Vocabulario, distractor (mismo nombre en español) | ok | 0/0 |
| 2511.13593 | B-res | O-Mem | 2025-11 | 11854 | Vocabulario, marco temporal | ok | 7/1 |
| 2402.05136 | B-res | LV-Eval | 2024-02 | 15577 | Agregación | ok | 1/0 |
| 2409.02465 | B-res | DetectiveQA | 2024-09 | 9032 | Distractor | ok | 2/0 |
| 2510.09720 | B-res | Preference-Aware Memory Update | 2025-10 | 8507 | Antiguo frente a nuevo | ok | 0/0 |
| 2310.08560 | C-ar5iv | MemGPT | 2023-10 | 11151 | Cita de segunda mano, vocabulario (el más citado del corpus) | ok | 19/3 |
| 2304.03442 | C-ar5iv | Generative Agents | 2023-04 | 26725 | Antiguo frente a nuevo, vocabulario | ok | 8/1 |
| 2305.10250 | C-ar5iv | MemoryBank | 2023-05 | 8939 | Vocabulario, antiguo frente a nuevo | ok | 11/3 |
| 2303.11366 | C-ar5iv | Reflexion | 2023-03 | 9732 | Vocabulario distinto | ok | 10/0 |
| 2210.03629 | C-ar5iv | ReAct | 2022-10 | 14705 | Distractor, vocabulario | ok | 10/0 |
| 2305.16291 | C-ar5iv | Voyager | 2023-05 | 14347 | Vocabulario distinto (memoria de habilidades) | ok | 5/0 |
| 2310.05029 | C-ar5iv | Walking Down the Memory Maze | 2023-10 | 9829 | Distractor frente a RAPTOR y el wiki | ok | 2/0 |
| 2308.08239 | C-ar5iv | MemoChat | 2023-08 | 11877 | Vocabulario distinto | ok | 2/1 |
| 2306.03901 | C-ar5iv | ChatDB | 2023-06 | 10478 | Vocabulario distinto | ok | 1/0 |
| 2311.08719 | C-ar5iv | Think-in-Memory | 2023-11 | 7995 | Vocabulario distinto | ok | 0/0 |
| 2309.02427 | C-ar5iv | CoALA | 2023-09 | 19731 | Antiguo frente a nuevo (taxonomía de 2023) | ok | 1/0 |
| 2307.03172 | C-ar5iv | Lost in the Middle | 2023-07 | 12466 | Contradicción con «poner todo en el contexto» | ok | 6/0 |
| 2310.11511 | C-ar5iv | Self-RAG | 2023-10 | 48666 | Vocabulario, distractor | ok | 4/0 |
| 2208.03299 | C-ar5iv | Atlas | 2022-08 | 25080 | Antiguo frente a nuevo | ok | 3/0 |
| 2112.09118 | C-ar5iv | Contriever | 2021-12 | 16526 | Vocabulario | ok | 3/3 |
| 2005.11401 | C-ar5iv | RAG (Lewis et al., 2020) | 2020-05 | 11671 | Antiguo frente a nuevo, vocabulario (qué significaba RAG) | ok | 24/0 |
| 1809.09600 | C-ar5iv | HotpotQA | 2018-09 | 10574 | Agregación, detalle (el benchmark más usado) | ok | 11/1 |

## Evidencia ya comprobada (para que no la repitas ni la des por falsa)
- **Zep frente a Mem0:** en 10 tablas del corpus y del paper de Mem0 donde aparecen las dos filas, el promedio de Mem0 queda arriba en 6 y el de Zep en 4 (una de esas es de latencia, donde menos es mejor). El orden cambia de un paper a otro; el cálculo no distingue la dirección de la métrica.
- **LoCoMo:** los papers del corpus describen su tamaño de formas incompatibles (9K, 26k, 262K y 600k tokens; 600 y 77 turnos; 35 sesiones), quizá porque miden cosas distintas.
- **Nombres parecidos:** «MemOS» aparece en 6 papers del corpus y «MemoryOS» en 5, y uno los lista como baselines distintos junto a EverMemOS, MemU y MemMachine. Además hay dos artículos del mismo grupo llamados MemOS (2505.22101 y 2507.03724).
- **CAG frente a WiCER:** CAG limita su afirmación a bases de conocimiento acotadas; WiCER (ya en el corpus) dice que a mayor escala el contexto completo cae por debajo del RAG. Es una contradicción parcial que depende de la escala.
- **Verificación con el pipeline real:** de 104 candidatos, 100 pasan sin alertas. 2 no tienen HTML en arXiv (404) y se quitaron; 2 tienen alertas (uno con 78 errores de conversión de referencias cruzadas y otro sin título en el HTML). Una premisa que parecía fallar resultó ser un falso negativo de la búsqueda (el texto escribía el nombre en LaTeX): conviene desconfiar tanto de un ✓ como de un ✗ automático.
- **Costo calibrado con 15 ingestas reales** (0,015 USD por paper en promedio fuera de hora pico, sin crecimiento visible con el tamaño del wiki hasta 15 papers; no hay mediciones más allá).

## Qué debes hacer
1. **Decide cuáles 50** de los 102 deberían entrar. Para cada uno: MANTENER, CAMBIAR o DESCARTAR, con la razón y un «pero». Si propones traer papers de fuera de la lista, da el identificador de arXiv solo si estás seguro; si no, escribe «no verificado» y cómo comprobarlo. Recuerda la restricción de HTML (dic-2023 en adelante).
2. **Ataca la selección:** sesgos (todo es de 2024 a 2025 y lo cita el propio corpus, ¿hay circularidad?; ¿homogeneidad temática?; ¿se eligen papers que favorecen al wiki?), cobertura real de cada tipo de caso de borde, **casos de borde donde el RAG debería ganar** (¿están representados?), duplicados o casi duplicados, y papers que no sirven para generar preguntas verificables.
3. **Ataca el diseño del experimento:** tres tandas, una sola construcción del wiki (varianza de la ingesta sin medir), orden cronológico con lo antiguo primero, contaminación por el entrenamiento del modelo (los papers antiguos pueden estar en él), juez sin calibrar, métrica de palabras clave, wiki con 8 acciones frente a una llamada del RAG, ruido a temperatura 0 y preguntas T4 ambiguas.
4. **Evalúa las 40 preguntas nuevas:** ¿la taxonomía y el reparto son adecuados?, ¿qué preguntas no deberían hacerse porque no son verificables o favorecen a un sistema?, propón plantillas mejores en inglés sencillo y casos adversariales.
5. **Lista lo que falta** (categorías de papers o de datos) y cómo conseguirlo en pocos días sin romper la restricción de HTML.
6. **Riesgos para el 20 de noviembre:** qué recortarías primero.
7. **Preguntas que los autores deberían responder antes de ejecutar.**

## Reglas
- No inventes datos. Si no estás seguro de lo que dice un paper, escribe «no verificado» y qué habría que mirar. No confundas papers con nombres parecidos (hay dos artículos llamados MemOS y además un sistema distinto llamado MemoryOS).
- Cita identificadores de arXiv cuando hables de un paper.
- Sé concreto y prioriza; evita generalidades.
- Responde en español y deja las preguntas de ejemplo en inglés.

## Formato de salida
1. Veredicto en 5 líneas, lo más grave primero.
2. Los 10 mayores problemas, ordenados por gravedad, cada uno con su corrección.
3. Tabla por candidato: ID | decisión | razón | pero.
4. Lista final de 50 identificadores y matriz de casos de borde por paper (qué tipo cubre y cuántos papers lo cubren).
5. Lo que falta y dónde buscarlo.
6. «Red team» del experimento: cómo podría salir una conclusión ambigua o equivocada y qué control lo evitaría.
7. Preguntas para los autores.
=====
