# Verificación de los candidatos

Fecha: 12 de noviembre de 2026. Cubre el bloque A (25 + 15), el bloque B (25 + 22, de los que 2 de la reserva no tienen HTML) y el bloque C de antiguos vía ar5iv (17). Datos crudos en `candidatas_verificadas.csv`.

**Resultado:** 104 candidatos revisados: **100 sin alertas**, 2 con alguna alerta a revisar, 2 con un problema que los bloquea.

## Qué verifiqué (automático, sobre el texto real)
- El identificador existe en la API de arXiv y trae sus metadatos (título, fecha, categoría, versión).
- Existe la versión HTML y se descargó completa (código 200 y tamaño), con la pausa de 15 s que pide `robots.txt` y el agente de usuario del proyecto.
- El HTML se convierte a Markdown con el pipeline del propio proyecto (capa Silver) sin error: tokens, secciones, tablas, ecuaciones y número de entradas de la bibliografía.
- El título del HTML coincide con el de la API (similitud de palabras), para descartar que el identificador apunte a otro paper.
- No está retirado (`withdrawn`) y no tiene decenas de errores de conversión de LaTeXML.
- **Premisas de la pregunta de ejemplo:** que los términos en los que se apoya la pregunta aparezcan en el texto (p. ej. «Zettelkasten» en A-MEM, los seis tipos de memoria de MIRIX, las cuatro capacidades de MemoryAgentBench).
- Evidencia dentro de los 50 papers: cuántos mencionan cada método o benchmark y cuántos traen filas de tabla con sus cifras.
- Que ninguno esté ya en el corpus (por identificador).

## Qué tienes que verificar tú (o los dos autores)
- **Las respuestas de las preguntas.** Mis preguntas son ideas; la respuesta se fija leyendo el paper y la verifican los dos autores (regla 11). Lo verificado arriba solo confirma que los términos de la pregunta existen en el texto, no que la respuesta sea la que imagino.
- **Las alertas de la tabla de abajo**, una a una (premisas que no aparecieron, títulos distintos, textos cortos).
- **La calidad de las tablas convertidas.** El pipeline puede aplanar tablas complejas. Abre el Silver de 3 o 4 papers con muchas tablas (los de más `tab` en la tabla) y compáralos con la página HTML antes de escribir preguntas sobre cifras.
- **Que el caso de borde sea real.** Por ejemplo, que Zep y Mem0 den cifras distintas para lo mismo, o que las del original no coincidan con las que repiten los papers de 2026. Se ve leyendo las dos tablas.
- **Contaminación.** Todos son anteriores a 2026 y el modelo puede conocerlos de su entrenamiento. Hay que pasar la sonda a libro cerrado (decisión 0003) sobre las preguntas nuevas. Cuesta centavos; la preparo cuando me lo pidas.
- **Licencia de cada paper en arXiv.** No descargué la página de resumen, que es donde figura. No afecta mientras el texto no se versione ni se redistribuya (regla 8).
- **Nombres repetidos.** Hay dos artículos llamados MemOS (2505.22101 y 2507.03724). Decidir si entran los dos o solo uno, y cómo se citan en las preguntas.
- **Las que salen de la bibliografía con una sola cita** (casi todo el bloque B): están ahí por el tema y no por haber sido muy citadas.
- **Descartes por tema.** Confirmar que seguridad y privacidad (AgentPoison, MINJA, CIMemories, Collaborative Memory) te sirven aunque estén lejos del tema central: están elegidas por la rúbrica (Cr7).
- **2512.13564 (Memory in the Age of AI Agents).** Es el único con errores de conversión: 78, de los que 69 son referencias cruzadas (`\Cref`) que quedaron sin resolver y el resto son macros de tablas. El texto se lee, pero las referencias a figuras y tablas salen rotas; además es el más largo (74 mil tokens). Mira si te compensa o si lo cambias por otra revisión.
- **2502.06975 (Position: Episodic Memory).** El HTML no trae título, así que comprobé su identidad solo por el contenido (aparecen «episodic memory» y «single-shot», como pide el tema). Ábrelo una vez para confirmarlo a ojo.
- **Bloque C (ar5iv).** Hay que decidir si se incluye. Requiere un cambio pequeño en la ingesta (pedir el HTML a ar5iv cuando arXiv no lo tiene) y revisar a ojo la conversión de 2 o 3 de ellos, porque ar5iv usa una versión más vieja de LaTeXML: por ejemplo, Generative Agents sale con 0 tablas.
- **Dos papers de la reserva del bloque B no tienen HTML** (2410.12837 y 2508.15294): ya están fuera de las tablas. Ningún recomendado se ve afectado.

## Alertas y problemas
| arXiv | Grupo | Nombre | Estado | Detalle |
|---|---|---|---|---|
| 2512.13564 | A · recomendada | Memory in the Age of AI Agents | REVISAR | paper largo (>60k tokens); muchos errores de conversión |
| 2502.06975 | B · recomendada | Position: Episodic Memory | REVISAR | HTML sin título (identidad comprobada solo por el contenido) |
| 2410.12837 | B · reserva | A Comprehensive Survey of RAG | SIN HTML | SIN HTML |
| 2508.15294 | B · reserva | Multi-Memory Segment System | SIN HTML | SIN HTML |

## Afirmaciones sobre casos de borde que sí se comprobaron con datos
- **Zep frente a Mem0 (contradicción).** En las 10 tablas del corpus (más las del propio paper de Mem0) donde aparecen las dos filas con cifras, Mem0 queda por encima en 6 y Zep en 4. Una de esas 4 es una tabla de latencia, donde menos es mejor, así que en realidad favorece a Mem0, y otra es un empate (8,37 frente a 8,38). El cálculo compara el promedio de cada fila y no distingue la dirección de la métrica: sirve para ver que el orden **no es el mismo en todos los papers**, no para decir quién gana.
- **LoCoMo (contradicción en los datos del benchmark).** Los papers del corpus describen su tamaño con valores distintos: 9K tokens, 26k tokens, 262K tokens, 600k tokens, 600 turnos, 77 turnos y 35 sesiones. Puede que midan cosas diferentes (por conversación, por sesión, en total); hay que leer cada contexto antes de convertirlo en pregunta.
- **MemOS y MemoryOS (distractor).** «MemOS» aparece en 6 papers del corpus y «MemoryOS» en 5; son sistemas distintos. Además hay dos artículos del mismo grupo llamados MemOS (2505.22101 y 2507.03724).
- **A-MEM y «Zettelkasten» (vocabulario distinto).** El término aparece en el texto de A-MEM y en 3 papers del corpus.
- **LightRAG (misma herramienta, cifras distintas).** 4 papers del corpus traen filas con sus cifras en escalas diferentes (por ejemplo 0,819 en una escala de 0 a 1 y 42,6 o 45,80 en puntos).
- **CAG frente a WiCER (contradicción parcial).** CAG limita su afirmación a «bases de conocimiento acotadas» (resultados comparables o superiores a RAG); WiCER, que ya está en el corpus, dice que a mayor escala el contexto completo cae por debajo del RAG por dilución de la atención. Son compatibles: la pregunta debe pedir el matiz de escala, no quién tiene razón.

## Todos los candidatos
| arXiv | Grupo | Nombre | Fecha | HTML | Tokens | Sec. | Tablas | Bib. | Premisas | Corpus (menciones / con tabla) | Estado |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2504.19413 | A · recomendada | Mem0 | 2025-04-28 | arxiv.org/html | 14433 | 6 | 2 | 30 | 4/4 | 27 / 10 | OK |
| 2501.13956 | A · recomendada | Zep | 2025-01-20 | arxiv.org/html | 9484 | 6 | 3 | 28 | 4/4 | 14 / 7 | OK |
| 2502.12110 | A · recomendada | A-MEM | 2025-02-17 | arxiv.org/html | 19758 | 7 | 8 | 39 | 2/2 | 23 / 13 | OK |
| 2410.05779 | A · recomendada | LightRAG | 2024-10-08 | arxiv.org/html | 14358 | 7 | 6 | 21 | 3/3 | 7 / 4 | OK |
| 2404.16130 | A · recomendada | GraphRAG | 2024-04-24 | arxiv.org/html | 18898 | 8 | 7 | 79 | 3/3 | 18 / 5 | OK |
| 2401.18059 | A · recomendada | RAPTOR | 2024-01-31 | arxiv.org/html | 14412 | 6 | 21 | 62 | 3/3 | 12 / 8 | OK |
| 2507.03724 | A · recomendada | MemOS (artículo largo) | 2025-07-04 | arxiv.org/html | 28988 | 8 | 8 | 106 | 2/2 | 8 / 4 | OK |
| 2507.07957 | A · recomendada | MIRIX | 2025-07-10 | arxiv.org/html | 12055 | 6 | 3 | 38 | 6/6 | 5 / 2 | OK |
| 2508.19828 | A · recomendada | Memory-R1 | 2025-08-27 | arxiv.org/html | 14188 | 6 | 5 | 41 | 3/3 | 5 / 1 | OK |
| 2510.18866 | A · recomendada | LightMem | 2025-10-21 | arxiv.org/html | 15402 | 7 | 9 | 56 | 3/3 | 7 / 5 | OK |
| 2410.10813 | A · recomendada | LongMemEval | 2024-10-14 | arxiv.org/html | 19321 | 8 | 13 | 53 | 6/6 | 24 / 9 | OK |
| 2402.17753 | A · recomendada | LoCoMo | 2024-02-27 | arxiv.org/html | 13736 | 9 | 7 | 68 | 3/3 | 24 / 9 | OK |
| 2507.05257 | A · recomendada | MemoryAgentBench | 2025-07-07 | arxiv.org/html | 23455 | 7 | 19 | 95 | 4/4 | 14 / 6 | OK |
| 2511.03506 | A · recomendada | HaluMem | 2025-11-05 | arxiv.org/html | 16347 | 7 | 6 | 28 | 4/4 | 4 / 3 | OK |
| 2510.17281 | A · recomendada | MemoryBench | 2025-10-20 | arxiv.org/html | 31904 | 6 | 23 | 69 | 2/2 | 5 / 3 | OK |
| 2506.21605 | A · recomendada | MemBench | 2025-06-20 | arxiv.org/html | 14149 | 8 | 12 | 29 | 2/2 | 8 / 6 | OK |
| 2510.27246 | A · recomendada | BEAM | 2025-10-31 | arxiv.org/html | 23163 | 7 | 6 | 73 | 2/2 | 7 / 4 | OK |
| 2512.13564 | A · recomendada | Memory in the Age of AI Agents | 2025-12-15 | arxiv.org/html | 74187 | 8 | 9 | 490 | 5/5 | 1 / 0 | REVISAR |
| 2505.00675 | A · recomendada | Rethinking Memory | 2025-05-01 | arxiv.org/html | 40831 | 7 | 21 | 383 | 5/5 | 0 / 0 | OK |
| 2404.13501 | A · recomendada | Survey on the Memory Mechanism (2024) | 2024-04-21 | arxiv.org/html | 25747 | 10 | 4 | 174 | 1/1 | 1 / 0 | OK |
| 2312.10997 | A · recomendada | RAG Survey (2023) | 2023-12-18 | arxiv.org/html | 18892 | 8 | 4 | 182 | 3/3 | 0 / 0 | OK |
| 2412.15605 | A · recomendada | Don't Do RAG (CAG) | 2024-12-20 | arxiv.org/html | 5966 | 4 | 3 | 12 | 3/3 | 2 / 0 | OK |
| 2403.08319 | A · recomendada | Knowledge Conflicts Survey | 2024-03-13 | arxiv.org/html | 15940 | 8 | 3 | 222 | 3/3 | 2 / 0 | OK |
| 2511.17208 | A · recomendada | Simple Yet Strong Baseline | 2025-11-21 | arxiv.org/html | 13310 | 6 | 6 | 19 | 2/2 | 0 / 0 | OK |
| 2512.12818 | A · recomendada | Hindsight is 20/20 | 2025-12-14 | arxiv.org/html | 18056 | 9 | 0 | 16 | 5/5 | 6 / 3 | OK |
| 2511.01448 | A · reserva | LiCoMemory | 2025-11-03 | arxiv.org/html | 12150 | 6 | 3 | 26 | 3/3 | 5 / 3 | OK |
| 2511.18423 | A · reserva | General Agentic Memory | 2025-11-23 | arxiv.org/html | 8001 | 5 | 5 | 19 | 2/2 | 3 / 2 | OK |
| 2507.02259 | A · reserva | MemAgent | 2025-07-03 | arxiv.org/html | 10320 | 6 | 4 | 78 | 3/3 | 4 / 2 | OK |
| 2506.15841 | A · reserva | MEM1 | 2025-06-18 | arxiv.org/html | 13261 | 5 | 4 | 71 | 2/2 | 3 / 1 | OK |
| 2509.25911 | A · reserva | Mem-α | 2025-09-30 | arxiv.org/html | 14494 | 5 | 9 | 58 | 2/2 | 0 / 0 | OK |
| 2502.13270 | A · reserva | REALTALK | 2025-02-18 | arxiv.org/html | 4238 | 9 | 8 | 53 | 2/2 | 3 / 2 | OK |
| 2504.14225 | A · reserva | PersonaMem | 2025-04-19 | arxiv.org/html | 11564 | 7 | 2 | 59 | 2/2 | 7 / 4 | OK |
| 2502.05589 | A · reserva | On Memory Construction | 2025-02-08 | arxiv.org/html | 14901 | 5 | 11 | 67 | 2/2 | 1 / 0 | OK |
| 2504.15965 | A · reserva | From Human Memory to AI Memory | 2025-04-22 | arxiv.org/html | 17530 | 6 | 3 | 155 | 2/2 | 1 / 0 | OK |
| 2408.08921 | A · reserva | Graph RAG: A Survey | 2024-08-15 | arxiv.org/html | 29185 | 11 | 1 | 204 | 1/1 | 0 / 0 | OK |
| 2501.00309 | A · reserva | RAG with Graphs | 2024-12-31 | arxiv.org/html | 58606 | 11 | 2 | 573 | 1/1 | 0 / 0 | OK |
| 2404.06654 | A · reserva | RULER | 2024-04-09 | arxiv.org/html | 18183 | 8 | 16 | 97 | 2/2 | 6 / 0 | OK |
| 2402.14207 | A · reserva | STORM | 2024-02-22 | arxiv.org/html | 18458 | 11 | 12 | 64 | 3/3 | 0 / 0 | OK |
| 2509.25140 | A · reserva | ReasoningBank | 2025-09-29 | arxiv.org/html | 16174 | 7 | 6 | 77 | 2/2 | 3 / 0 | OK |
| 2506.07398 | A · reserva | G-Memory | 2025-06-09 | arxiv.org/html | 13969 | 6 | 4 | 81 | 2/2 | 7 / 0 | OK |
| 2406.13805 | B · recomendada | WikiContradict | 2024-06-19 | arxiv.org/html | 14932 | 7 | 5 | 18 | 3/3 | 1 / 0 | OK |
| 2408.12076 | B · recomendada | ConflictBank | 2024-08-22 | arxiv.org/html | 16583 | 5 | 13 | 72 | 3/3 | 2 / 0 | OK |
| 2506.08184 | B · recomendada | Unable to Forget | 2025-06-09 | arxiv.org/html | 20571 | 13 | 1 | 11 | 2/2 | 1 / 0 | OK |
| 2406.19354 | B · recomendada | Fundamental Problems With Model Editing | 2024-06-27 | arxiv.org/html | 20674 | 11 | 6 | 84 | 2/2 | 6 / 0 | OK |
| 2506.06331 | B · recomendada | How Significant Are the Real Gains? (GraphRAG) | 2025-05-31 | arxiv.org/html | 13483 | 8 | 2 | 60 | 3/3 | 0 / 0 | OK |
| 2503.04338 | B · recomendada | In-depth Analysis of Graph-based RAG | 2025-03-06 | arxiv.org/html | 36165 | 11 | 77 | 105 | 4/4 | 0 / 0 | OK |
| 2506.02404 | B · recomendada | GraphRAG-Bench | 2025-06-03 | arxiv.org/html | 9413 | 5 | 5 | 23 | 2/2 | 0 / 0 | OK |
| 2511.10523 | B · recomendada | ConvoMem | 2025-11-13 | arxiv.org/html | 21100 | 5 | 2 | 20 | 3/3 | 2 / 1 | OK |
| 2510.23730 | B · recomendada | Evaluating Long-Term Memory for Long-Context QA | 2025-10-27 | arxiv.org/html | 11897 | 7 | 5 | 22 | 2/2 | 0 / 0 | OK |
| 2505.24226 | B · recomendada | E2GraphRAG | 2025-05-30 | arxiv.org/html | 10927 | 5 | 3 | 48 | 3/3 | 1 / 1 | OK |
| 2505.22101 | B · recomendada | MemOS (primer artículo) | 2025-05-28 | arxiv.org/html | 5496 | 5 | 0 | 39 | 2/2 | 8 / 4 | OK |
| 2409.05591 | B · recomendada | MemoRAG | 2024-09-09 | arxiv.org/html | 13888 | 6 | 4 | 59 | 2/2 | 2 / 2 | OK |
| 2510.04618 | B · recomendada | Agentic Context Engineering (ACE) | 2025-10-06 | arxiv.org/html | 18497 | 8 | 22 | 70 | 3/3 | 1 / 0 | OK |
| 2504.07952 | B · recomendada | Dynamic Cheatsheet | 2025-04-10 | arxiv.org/html | 13922 | 6 | 5 | 78 | 2/2 | 1 / 0 | OK |
| 2407.12784 | B · recomendada | AgentPoison | 2024-07-17 | arxiv.org/html | 16650 | 5 | 7 | 41 | 4/4 | 2 / 0 | OK |
| 2503.03704 | B · recomendada | Memory Injection Attacks (MINJA) | 2025-03-05 | arxiv.org/html | 24861 | 8 | 14 | 55 | 2/2 | 0 / 0 | OK |
| 2511.14937 | B · recomendada | CIMemories | 2025-11-18 | arxiv.org/html | 7844 | 7 | 3 | 41 | 3/3 | 0 / 0 | OK |
| 2505.18279 | B · recomendada | Collaborative Memory | 2025-05-23 | arxiv.org/html | 23811 | 8 | 19 | 25 | 3/3 | 3 / 0 | OK |
| 2402.04624 | B · recomendada | MemoryLLM | 2024-02-07 | arxiv.org/html | 11657 | 7 | 2 | 35 | 2/2 | 2 / 0 | OK |
| 2407.01178 | B · recomendada | Memory³ | 2024-07-01 | arxiv.org/html | 27787 | 9 | 11 | 134 | 2/2 | 1 / 0 | OK |
| 2502.06975 | B · recomendada | Position: Episodic Memory | 2025-02-10 | arxiv.org/html | 10533 | 6 | 2 | 113 | 2/2 | 0 / 0 | REVISAR |
| 2511.07587 | B · recomendada | Generative Semantic Workspaces (GSW) | 2025-11-10 | arxiv.org/html | 21627 | 16 | 15 | 87 | 3/3 | 0 / 0 | OK |
| 2511.20857 | B · recomendada | Evo-Memory | 2025-11-25 | arxiv.org/html | 15620 | 5 | 6 | 50 | 2/2 | 1 / 1 | OK |
| 2411.00489 | B · recomendada | Human-inspired Perspectives (revisión 2024) | 2024-11-01 | arxiv.org/html | 31657 | 8 | 1 | 336 | 2/2 | 0 / 0 | OK |
| 2312.06648 | B · recomendada | Dense X Retrieval | 2023-12-11 | arxiv.org/html | 13121 | 11 | 9 | 68 | 2/2 | 0 / 0 | OK |
| 2509.18868 | B · reserva | Memory in LLMs: Mechanisms, Evaluation and Evolution | 2025-09-23 | arxiv.org/html | 47408 | 7 | 7 | 179 | 1/1 | 0 / 0 | OK |
| 2512.23343 | B · reserva | AI Meets Brain | 2025-12-29 | arxiv.org/html | 32159 | 10 | 2 | 400 | 1/1 | 0 / 0 | OK |
| 2410.12837 | B · reserva | A Comprehensive Survey of RAG | 2024-10-03 | ar5iv | — | — | — | — | — | — | SIN HTML |
| 2501.09136 | B · reserva | Agentic RAG: A Survey | 2025-01-15 | arxiv.org/html | 21139 | 13 | 5 | 104 | 1/1 | 4 / 1 | OK |
| 2407.21059 | B · reserva | Modular RAG | 2024-07-26 | arxiv.org/html | 17807 | 7 | 1 | 60 | 1/1 | 1 / 1 | OK |
| 2401.01286 | B · reserva | A Comprehensive Study of Knowledge Editing | 2024-01-02 | arxiv.org/html | 29477 | 11 | 7 | 283 | 1/1 | 4 / 0 | OK |
| 2403.04782 | B · reserva | Survey on Temporal Knowledge Graphs | 2024-03-02 | arxiv.org/html | 19592 | 7 | 3 | 88 | 1/1 | 12 / 0 | OK |
| 2510.13614 | B · reserva | MemoTime | 2025-10-15 | arxiv.org/html | 20995 | 6 | 13 | 70 | 2/2 | 1 / 0 | OK |
| 2510.02373 | B · reserva | A-MemGuard | 2025-09-29 | arxiv.org/html | 17698 | 8 | 9 | 40 | 2/2 | 0 / 0 | OK |
| 2512.04668 | B · reserva | Topology Matters (fugas entre agentes) | 2025-12-04 | arxiv.org/html | 16235 | 8 | 9 | 16 | 2/2 | 1 / 1 | OK |
| 2406.13144 | B · reserva | DialSim | 2024-06-19 | arxiv.org/html | 16466 | 6 | 14 | 38 | 2/2 | 2 / 1 | OK |
| 2510.01353 | B · reserva | MEMTRACK | 2025-10-01 | arxiv.org/html | 14527 | 6 | 7 | 65 | 2/2 | 2 / 1 | OK |
| 2512.12856 | B · reserva | Forgetful but Faithful | 2025-12-14 | arxiv.org/html | 51767 | 8 | 4 | 53 | 2/2 | 0 / 0 | OK |
| 2508.10391 | B · reserva | LeanRAG | 2025-08-14 | arxiv.org/html | 16729 | 7 | 11 | 25 | 2/2 | 0 / 0 | OK |
| 2503.21322 | B · reserva | HyperGraphRAG | 2025-03-27 | arxiv.org/html | 16141 | 7 | 5 | 29 | 1/1 | 1 / 0 | OK |
| 2407.04363 | B · reserva | AriGraph | 2024-07-05 | arxiv.org/html | 10941 | 7 | 4 | 49 | 2/2 | 1 / 1 | OK |
| 2512.12686 | B · reserva | Memoria | 2025-12-14 | arxiv.org/html | 9512 | 7 | 2 | 13 | 2/2 | 0 / 0 | OK |
| 2508.15294 | B · reserva | Multi-Memory Segment System | 2025-08-21 | ar5iv | — | — | — | — | — | — | SIN HTML |
| 2511.13593 | B · reserva | O-Mem | 2025-11-17 | arxiv.org/html | 11854 | 8 | 7 | 48 | 2/2 | 7 / 1 | OK |
| 2402.05136 | B · reserva | LV-Eval | 2024-02-06 | arxiv.org/html | 15577 | 6 | 12 | 44 | 2/2 | 1 / 0 | OK |
| 2409.02465 | B · reserva | DetectiveQA | 2024-09-04 | arxiv.org/html | 9032 | 8 | 8 | 36 | 2/2 | 2 / 0 | OK |
| 2510.09720 | B · reserva | Preference-Aware Memory Update | 2025-10-10 | arxiv.org/html | 8507 | 6 | 7 | 24 | 2/2 | 0 / 0 | OK |
| 2310.08560 | C · antiguos (ar5iv) | MemGPT | 2023-10-12 | ar5iv | 11151 | 6 | 3 | 35 | 4/4 | 19 / 3 | OK |
| 2304.03442 | C · antiguos (ar5iv) | Generative Agents | 2023-04-07 | ar5iv | 26725 | 9 | 0 | 110 | 4/4 | 8 / 1 | OK |
| 2305.10250 | C · antiguos (ar5iv) | MemoryBank | 2023-05-17 | ar5iv | 8939 | 6 | 2 | 22 | 3/3 | 11 / 3 | OK |
| 2303.11366 | C · antiguos (ar5iv) | Reflexion | 2023-03-20 | ar5iv | 9732 | 8 | 7 | 31 | 3/3 | 10 / 0 | OK |
| 2210.03629 | C · antiguos (ar5iv) | ReAct | 2022-10-06 | ar5iv | 14705 | 6 | 10 | 40 | 3/3 | 10 / 0 | OK |
| 2305.16291 | C · antiguos (ar5iv) | Voyager | 2023-05-25 | ar5iv | 14347 | 8 | 6 | 92 | 3/3 | 5 / 0 | OK |
| 2310.05029 | C · antiguos (ar5iv) | Walking Down the Memory Maze | 2023-10-08 | ar5iv | 9829 | 7 | 6 | 40 | 3/3 | 2 / 0 | OK |
| 2308.08239 | C · antiguos (ar5iv) | MemoChat | 2023-08-16 | ar5iv | 11877 | 5 | 9 | 59 | 2/2 | 2 / 1 | OK |
| 2306.03901 | C · antiguos (ar5iv) | ChatDB | 2023-06-06 | ar5iv | 10478 | 5 | 5 | 37 | 3/3 | 1 / 0 | OK |
| 2311.08719 | C · antiguos (ar5iv) | Think-in-Memory | 2023-11-15 | ar5iv | 7995 | 5 | 3 | 36 | 2/2 | 0 / 0 | OK |
| 2309.02427 | C · antiguos (ar5iv) | CoALA | 2023-09-05 | ar5iv | 19731 | 9 | 2 | 237 | 4/4 | 1 / 0 | OK |
| 2307.03172 | C · antiguos (ar5iv) | Lost in the Middle | 2023-07-06 | ar5iv | 12466 | 8 | 7 | 47 | 3/3 | 6 / 0 | OK |
| 2310.11511 | C · antiguos (ar5iv) | Self-RAG | 2023-10-17 | ar5iv | 48666 | 7 | 10 | 58 | 3/3 | 4 / 0 | OK |
| 2208.03299 | C · antiguos (ar5iv) | Atlas | 2022-08-05 | ar5iv | 25080 | 6 | 21 | 90 | 2/2 | 3 / 0 | OK |
| 2112.09118 | C · antiguos (ar5iv) | Contriever | 2021-12-16 | ar5iv | 16526 | 7 | 15 | 65 | 2/2 | 3 / 3 | OK |
| 2005.11401 | C · antiguos (ar5iv) | RAG (Lewis et al., 2020) | 2020-05-22 | ar5iv | 11671 | 8 | 7 | 68 | 3/3 | 24 / 0 | OK |
| 1809.09600 | C · antiguos (ar5iv) | HotpotQA | 2018-09-25 | ar5iv | 10574 | 8 | 9 | 19 | 3/3 | 11 / 1 | OK |

## Detalle de premisas
### A · recomendada
- **2504.19413** Mem0: ✓ compara en LoCoMo (17); ✓ menciona a Zep (18); ✓ habla de latencia (28); ✓ variante con grafo (48)
- **2501.13956** Zep: ✓ usa LongMemEval (15); ✓ usa DMR (16); ✓ compara con MemGPT (14); ✓ grafo temporal (24)
- **2502.12110** A-MEM: ✓ menciona Zettelkasten (10); ✓ usa LoCoMo (45)
- **2410.05779** LightRAG: ✓ recuperación de dos niveles (17); ✓ actualización incremental (11); ✓ compara con GraphRAG (25)
- **2404.16130** GraphRAG: ✓ comunidades (106); ✓ resumen guiado por consulta (4); ✓ preguntas globales (50)
- **2401.18059** RAPTOR: ✓ árbol (89); ✓ agrupa (clustering) (41); ✓ resúmenes (65)
- **2507.03724** MemOS (artículo largo): ✓ MemCube (18); ✓ sistema operativo (17)
- **2507.07957** MIRIX: ✓ Core (9); ✓ Episodic (18); ✓ Semantic (23); ✓ Procedural (15); ✓ Resource (11); ✓ Knowledge Vault (8)
- **2508.19828** Memory-R1: ✓ aprendizaje por refuerzo (20); ✓ PPO o GRPO (101); ✓ LoCoMo (31)
- **2510.18866** LightMem: ✓ memoria sensorial (9); ✓ reducción de tokens (65); ✓ LongMemEval (15)
- **2410.10813** LongMemEval: ✓ extracción de información (5); ✓ razonamiento multi-sesión (11); ✓ actualización de conocimiento (5); ✓ razonamiento temporal (10); ✓ abstención (8); ✓ 500 preguntas (6)
- **2402.17753** LoCoMo: ✓ sesiones (14); ✓ 300 turnos (3); ✓ tokens por conversación (12)
- **2507.05257** MemoryAgentBench: ✓ recuperación precisa (19); ✓ aprendizaje en uso (19); ✓ comprensión de largo alcance (13); ✓ resolución de conflictos (26)
- **2511.03506** HaluMem: ✓ extracción (42); ✓ actualización (75); ✓ preguntas y respuestas (29); ✓ alucinación (88)
- **2510.17281** MemoryBench: ✓ aprendizaje continuo (27); ✓ retroalimentación del usuario (196)
- **2506.21605** MemBench: ✓ memoria factual (28); ✓ memoria reflexiva (38)
- **2510.27246** BEAM: ✓ 10 millones de tokens (35); ✓ 1 millón (26)
- **2512.13564** Memory in the Age of AI Agents: ✓ formas (32); ✓ funciones (34); ✓ dinámicas (26); ✓ paramétrica (47); ✓ latente (104)
- **2505.00675** Rethinking Memory: ✓ consolidación (78); ✓ actualización (105); ✓ indexado (52); ✓ olvido (39); ✓ recuperación (243)
- **2404.13501** Survey on the Memory Mechanism (2024): ✓ habla de memoria (448); ✓ no describe un wiki compilado
- **2312.10997** RAG Survey (2023): ✓ Naive RAG (14); ✓ Advanced RAG (9); ✓ Modular RAG (15); ✓ no describe un wiki compilado
- **2412.15605** Don't Do RAG (CAG): ✓ caché KV (25); ✓ precarga (25); ✓ compara con RAG (68)
- **2403.08319** Knowledge Conflicts Survey: ✓ conflicto contexto-memoria (11); ✓ conflicto entre contextos (8); ✓ conflicto en la memoria (14)
- **2511.17208** Simple Yet Strong Baseline: ✓ línea base simple (6); ✓ LoCoMo (23)
- **2512.12818** Hindsight is 20/20: ✓ retain (34); ✓ recall (42); ✓ reflect (36); ✓ LongMemEval (19); ✓ LoCoMo (15)

### A · reserva
- **2511.01448** LiCoMemory: ✓ cognitivo (23); ✓ grafo (73); ✓ LoCoMo (28)
- **2511.18423** General Agentic Memory: ✓ investigación profunda (5); ✓ memorizador e investigador (48)
- **2507.02259** MemAgent: ✓ sobrescribe memoria (7); ✓ trozos (chunks) (14); ✓ refuerzo (35)
- **2506.15841** MEM1: ✓ memoria de tamaño constante (9); ✓ estado interno (12)
- **2509.25911** Mem-α: ✓ refuerzo (20); ✓ construcción de memoria (15)
- **2502.13270** REALTALK: ✓ 21 días (4); ✓ conversaciones reales (13)
- **2504.14225** PersonaMem: ✓ perfil dinámico (15); ✓ persona (134)
- **2502.05589** On Memory Construction: ✓ resumen o unidad de memoria (103); ✓ granularidad o unidad (47)
- **2504.15965** From Human Memory to AI Memory: ✓ memoria humana (30); ✓ memoria de corto plazo (67)
- **2408.08921** Graph RAG: A Survey: ✓ Graph RAG (123); ✓ no describe un wiki compilado
- **2501.00309** RAG with Graphs: ✓ grafos (964)
- **2404.06654** RULER: ✓ tamaño real de contexto (3); ✓ aguja en un pajar (30)
- **2402.14207** STORM: ✓ esquema (outline) (62); ✓ Wikipedia (74); ✓ perspectivas (29)
- **2509.25140** ReasoningBank: ✓ éxitos y fallos (76); ✓ fallos (32)
- **2506.07398** G-Memory: ✓ multiagente (27); ✓ jerárquica (20)

### B · recomendada
- **2406.13805** WikiContradict: ✓ contradicciones (146); ✓ Wikipedia (33); ✓ RAG (16)
- **2408.12076** ConflictBank: ✓ desinformación (22); ✓ conflicto temporal (20); ✓ conflicto semántico (22)
- **2506.08184** Unable to Forget: ✓ interferencia proactiva (20); ✓ información antigua frente a nueva (30)
- **2406.19354** Fundamental Problems With Model Editing: ✓ revisión de creencias (36); ✓ racional (22)
- **2506.06331** How Significant Are the Real Gains? (GraphRAG): ✓ GraphRAG (69); ✓ evaluación sin sesgo (72); ✓ LightRAG (30)
- **2503.04338** In-depth Analysis of Graph-based RAG: ✓ marco unificado (20); ✓ LightRAG (44); ✓ HippoRAG (23); ✓ RAPTOR (64)
- **2506.02404** GraphRAG-Bench: ✓ GraphRAG-Bench (11); ✓ razonamiento (61)
- **2511.10523** ConvoMem: ✓ 150 conversaciones (14); ✓ RAG (63); ✓ memoria (162)
- **2510.23730** Evaluating Long-Term Memory for Long-Context QA: ✓ episódica, semántica o procedimental (76); ✓ LoCoMo (13)
- **2505.24226** E2GraphRAG: ✓ E2GraphRAG (27); ✓ LightRAG (20); ✓ más rápido (38)
- **2505.22101** MemOS (primer artículo): ✓ MemOS (30); ✓ generación aumentada con memoria (2)
- **2409.05591** MemoRAG: ✓ memoria global (25); ✓ contexto largo (57)
- **2510.04618** Agentic Context Engineering (ACE): ✓ sesgo a la brevedad (6); ✓ colapso del contexto (10); ✓ playbook (13)
- **2504.07952** Dynamic Cheatsheet: ✓ cheatsheet (17); ✓ aprendizaje en uso (11)
- **2407.12784** AgentPoison: ✓ envenenamiento (161); ✓ base de conocimiento (21); ✓ disparador (trigger) (129); ✓ puerta trasera (30)
- **2503.03704** Memory Injection Attacks (MINJA): ✓ inyección de memoria (13); ✓ solo por consultas (74)
- **2511.14937** CIMemories: ✓ integridad contextual (22); ✓ privacidad (17); ✓ filtración (72)
- **2505.18279** Collaborative Memory: ✓ control de acceso (8); ✓ permisos (25); ✓ multiusuario (25)
- **2402.04624** MemoryLLM: ✓ autoactualizable (36); ✓ pool de memoria (61)
- **2407.01178** Memory³: ✓ memoria explícita (65); ✓ pesos del modelo (58)
- **2502.06975** Position: Episodic Memory: ✓ memoria episódica (60); ✓ aprendizaje de un solo intento (9)
- **2511.07587** Generative Semantic Workspaces (GSW): ✓ GSW (133); ✓ HippoRAG (25); ✓ episódica (44)
- **2511.20857** Evo-Memory: ✓ Evo-Memory (24); ✓ aprendizaje en uso (20)
- **2411.00489** Human-inspired Perspectives (revisión 2024): ✓ memoria humana (76); ✓ memoria a largo plazo (206)
- **2312.06648** Dense X Retrieval: ✓ proposiciones (179); ✓ granularidad (31)

### B · reserva
- **2509.18868** Memory in LLMs: Mechanisms, Evaluation and Evolution: ✓ mecanismos de memoria (226)
- **2512.23343** AI Meets Brain: ✓ neurociencia (99)
- **2501.09136** Agentic RAG: A Survey: ✓ agentic RAG (96)
- **2407.21059** Modular RAG: ✓ modular RAG (38)
- **2401.01286** A Comprehensive Study of Knowledge Editing: ✓ edición de conocimiento (148)
- **2403.04782** Survey on Temporal Knowledge Graphs: ✓ grafo temporal (65)
- **2510.13614** MemoTime: ✓ temporal (284); ✓ MemoTime (103)
- **2510.02373** A-MemGuard: ✓ defensa (44); ✓ memoria (110)
- **2512.04668** Topology Matters (fugas entre agentes): ✓ fuga de memoria (114); ✓ multiagente (30)
- **2406.13144** DialSim: ✓ simulador de diálogo (25); ✓ varios hablantes (15)
- **2510.01353** MEMTRACK: ✓ MEMTRACK (25); ✓ plataformas (60)
- **2512.12856** Forgetful but Faithful: ✓ privacidad (202); ✓ olvido (63)
- **2508.10391** LeanRAG: ✓ LeanRAG (102); ✓ jerárquico (38)
- **2503.21322** HyperGraphRAG: ✓ hipergrafo (174)
- **2407.04363** AriGraph: ✓ AriGraph (47); ✓ episódica (52)
- **2512.12686** Memoria: ✓ Memoria (65); ✓ personalizado (26)
- **2511.13593** O-Mem: ✓ O-Mem (83); ✓ personalizado (43)
- **2402.05136** LV-Eval: ✓ LV-Eval (39); ✓ 256K (29)
- **2409.02465** DetectiveQA: ✓ DetectiveQA (34); ✓ novelas (49)
- **2510.09720** Preference-Aware Memory Update: ✓ actualización de memoria (32); ✓ preferencias (96)

### C · antiguos (ar5iv)
- **2310.08560** MemGPT: ✓ sistema operativo (5); ✓ contexto virtual (2); ✓ contexto principal y externo (22); ✓ llamadas a funciones (14)
- **2304.03442** Generative Agents: ✓ flujo de memoria (25); ✓ reflexión (50); ✓ planificación (23); ✓ Smallville (22)
- **2305.10250** MemoryBank: ✓ Ebbinghaus (11); ✓ curva del olvido (12); ✓ SiliconFriend (76)
- **2303.11366** Reflexion: ✓ refuerzo verbal (5); ✓ memoria episódica (6); ✓ HumanEval (20)
- **2210.03629** ReAct: ✓ razonar y actuar (103); ✓ HotpotQA (28); ✓ ALFWorld (26)
- **2305.16291** Voyager: ✓ biblioteca de habilidades (46); ✓ Minecraft (33); ✓ currículo (54)
- **2310.05029** Walking Down the Memory Maze: ✓ MemWalker (44); ✓ árbol de resúmenes (39); ✓ navegar (44)
- **2308.08239** MemoChat: ✓ memorandos (160); ✓ ajuste fino (25)
- **2306.03901** ChatDB: ✓ base de datos (63); ✓ SQL (23); ✓ memoria simbólica (46)
- **2311.08719** Think-in-Memory: ✓ pensamientos (69); ✓ recordar (31)
- **2309.02427** CoALA: ✓ memoria de trabajo (28); ✓ memoria episódica (24); ✓ memoria semántica (27); ✓ memoria procedimental (26)
- **2307.03172** Lost in the Middle: ✓ la mitad del contexto (21); ✓ posición (43); ✓ preguntas con varios documentos (44)
- **2310.11511** Self-RAG: ✓ tokens de reflexión (52); ✓ crítica (22); ✓ recuperar a demanda (79)
- **2208.03299** Atlas: ✓ pocos ejemplos (60); ✓ recuperación (177)
- **2112.09118** Contriever: ✓ no supervisado (33); ✓ aprendizaje contrastivo (42)
- **2005.11401** RAG (Lewis et al., 2020): ✓ memoria paramétrica (45); ✓ memoria no paramétrica (22); ✓ RAG-Sequence y RAG-Token (42)
- **1809.09600** HotpotQA: ✓ 113 mil preguntas (1); ✓ hechos de apoyo (36); ✓ multisalto (40)
