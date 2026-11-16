# Propuesta de ampliación: 25 papers (más 15 de reserva) para casos de borde

Fecha: 11 de noviembre de 2026. Complementa `candidatas_citadas.csv`.

## Cómo se evaluó
- **Pool:** 69 papers de dic-2023 a 2025 que citan 2 o más papers de los 50 del corpus (bibliografías del HTML original) más 5 clásicos del tema.
- **Disponibilidad:** `HEAD https://arxiv.org/html/<id>` a cada uno, con `robots.txt` y su Crawl-delay de 15 s, con el agente de usuario del proyecto. **Los 69 respondieron 200.** Un 200 solo dice que la página existe: la calidad de la conversión (tablas, fórmulas) se ve al pasarlos por Bronze y Silver y puede degradar alguno.
- **Metadatos:** API de arXiv, en un lote.
- **Evidencia en el corpus:** cuántos de los 50 papers mencionan cada método o benchmark y cuántos traen filas de tabla con sus cifras (dato que el original podría contradecir o confirmar).
- **No se leyó el texto completo de los 69.** Las preguntas son ideas: su respuesta se fija después de ingerir el paper y de que los dos autores la verifiquen con el texto.

## Las 25 elegidas

### A. Métodos que el corpus ya re-evalúa (10)
| # | arXiv | Paper | Mencionan / con tabla | Casos de borde | Pregunta de ejemplo |
|---|---|---|---|---|---|
| 1 | 2504.19413 | Mem0 | 27 / 10 | Cita de segunda mano, antiguo frente a nuevo, agregación | How well did the original Mem0 paper say Mem0 did on long conversations, and did other papers in the collection get similar results when they tested it? |
| 2 | 2501.13956 | Zep | 14 / 7 | Contradicción | Do the papers agree on whether Zep or Mem0 remembers conversations better? Where do they disagree? |
| 3 | 2502.12110 | A-MEM | 23 / 13 | Vocabulario distinto | Which memory tool works like a note-taking system where each note links to related notes? |
| 4 | 2410.05779 | LightRAG | 7 / 4 | Misma herramienta, escalas distintas | What scores do different papers report for LightRAG on the same question tests, and why do the numbers look so different? |
| 5 | 2404.16130 | GraphRAG | 18 / 5 | Vocabulario, distractor | Which method first builds a map of topics and summaries of a whole document collection before answering broad questions? |
| 6 | 2401.18059 | RAPTOR | 12 / 8 | Distractor frente al wiki | How is building a tree of summaries different from keeping a wiki of linked pages? |
| 7 | 2507.03724 | MemOS | 6 / 5 | Distractor por nombre parecido | Are MemOS and MemoryOS the same project? If not, how do they differ? |
| 8 | 2507.07957 | MIRIX | 5 / 2 | Detalle, agregación | How many kinds of memory does MIRIX keep, and what are they? |
| 9 | 2508.19828 | Memory-R1 | 5 / 1 | Vocabulario distinto | Which memory systems learn what to remember by trial and error instead of fixed rules? |
| 10 | 2510.18866 | LightMem | 7 / 5 | Contradicción, agregación | Which memory system claims the biggest savings in cost, and do other papers confirm it? |

### B. Benchmarks (7)
| # | arXiv | Paper | Mencionan / con tabla | Casos de borde | Pregunta de ejemplo |
|---|---|---|---|---|---|
| 11 | 2410.10813 | LongMemEval | 24 / 9 | Agregación | How many papers in the collection report results on LongMemEval, and which memory skills does it test? |
| 12 | 2402.17753 | LoCoMo | 24 / 9 | Contradicción en los datos del benchmark | How long are the conversations in LoCoMo, and do all the papers describe it the same way? |
| 13 | 2507.05257 | MemoryAgentBench | 14 / 6 | Vocabulario distinto | Which test checks whether an assistant can find facts, learn during a chat, follow a long story and fix outdated facts? (verificar las cuatro capacidades) |
| 14 | 2511.03506 | HaluMem | 4 / 3 | Abstracción | At which steps can a memory system make up false information? |
| 15 | 2510.17281 | MemoryBench | 5 / 3 | Vocabulario distinto | Which test checks whether an assistant keeps improving from user feedback over time? (verificar) |
| 16 | 2506.21605 | MemBench | 8 / 6 | Vocabulario distinto | Which test separates remembering plain facts from remembering opinions or reasons? (verificar) |
| 17 | 2510.27246 | BEAM («Beyond a Million Tokens») | 4 / — | Escala, marco temporal | What happens to memory tools when a conversation is millions of words long? |

### C. Revisiones y taxonomías (4)
| # | arXiv | Paper | Casos de borde | Pregunta de ejemplo |
|---|---|---|---|---|
| 18 | 2512.13564 | Memory in the Age of AI Agents | Vocabulario, antiguo frente a nuevo | How do recent surveys group the kinds of agent memory, and do they use the same groups? |
| 19 | 2505.00675 | Rethinking Memory in LLM-based Agents | Vocabulario | Which actions does this survey say a memory system must be able to do, such as store, update or forget? |
| 20 | 2404.13501 | A Survey on the Memory Mechanism of LLM-based Agents (2024) | Abstención, antiguo frente a nuevo | Does the 2024 memory survey mention keeping knowledge as linked pages that get rewritten over time? (se espera que no) |
| 21 | 2312.10997 | RAG for LLMs: A Survey (2023) | Abstención, distractor | Does the 2023 RAG survey describe a system that updates its own knowledge pages when new papers arrive? (se espera que no) |

### D. Contrastes con el wiki (4)
| # | arXiv | Paper | Casos de borde | Pregunta de ejemplo |
|---|---|---|---|---|
| 22 | 2412.15605 | Don't Do RAG (CAG) | Contradicción con WiCER, ya en el corpus | Is it better to put all documents in the model's memory or to search them? Do the papers agree? |
| 23 | 2403.08319 | Knowledge Conflicts for LLMs: A Survey | Vocabulario sobre contradicciones | What kinds of disagreement can happen between what a model remembers and what a document says? |
| 24 | 2511.17208 | A Simple Yet Strong Baseline for Long-Term Conversational Memory | Contradicción | Do the papers agree that complex memory designs are needed, or can a simple method be enough? |
| 25 | 2512.12818 | Hindsight is 20/20 | Agregación, afirmaciones de «mejor resultado» que se pisan | Which systems claim the best results on long-conversation tests, and do those claims overlap? |

## Reserva (15)
| arXiv | Paper | Pregunta de ejemplo |
|---|---|---|
| 2511.01448 | LiCoMemory | Which light memory tools say they cut cost while staying accurate? |
| 2511.18423 | General Agentic Memory | Which system builds its memory by researching past history when asked, instead of summarizing it up front? |
| 2507.02259 | MemAgent | Which approach reads very long text in pieces and keeps a short running memory? |
| 2506.15841 | MEM1 | Which agent keeps its memory the same size during long tasks? |
| 2509.25911 | Mem-α | Which approach trains the model to decide how to build its own memory? |
| 2502.13270 | REALTALK | Do real 21-day conversations change how well memory tools do compared with made-up chats? |
| 2504.14225 | PersonaMem | Which test checks whether an assistant remembers a user's changing preferences? |
| 2502.05589 | On Memory Construction and Retrieval | How does the size of the stored memory pieces change the answers? |
| 2504.15965 | From Human Memory to AI Memory | Which survey compares AI memory to types of human memory? |
| 2408.08921 | Graph RAG: A Survey | Does this survey include wiki-like systems among graph-based methods? (se espera que no) |
| 2501.00309 | Retrieval-Augmented Generation with Graphs | How do two surveys of graph-based search sort the methods differently? |
| 2404.06654 | RULER | What does it mean that a model's advertised memory size is not its real useful size? |
| 2402.14207 | STORM | Which earlier system writes article-style pages from sources, and how is it different from LLM-Wiki? |
| 2509.25140 | ReasoningBank | Which method keeps lessons from past successes and failures to help with new tasks? |
| 2506.07398 | G-Memory | Which memory design is made for teams of agents rather than a single one? |

## Descartados del pool por estar fuera de tema
Gemini 1.5, GPT-4o System Card, Llama 3, Qwen3 (modelo y embeddings), DeepSeekMath, τ-bench, Astraea, WorldMM, MemVerse, la revisión de agentes científicos, Search-R1 y similares.

## Costo estimado de ingerir los 25
Unos 0,25 USD (0,01 por paper, estimación propia calibrada hasta 15 papers). Si se ingieren las 40, unos 0,4 USD.
