# Propuesta de ampliación, bloque B: 25 papers más (y 20 de reserva) para casos de borde

Fecha: 12 de noviembre de 2026. Segundo bloque, con el mismo formato que `propuesta_25_papers.md`. Juntos, los dos bloques de 25 suman los 50 papers que faltan para llegar a 100.

## Cómo se evaluó
- **Universo:** los 355 papers de dic-2023 a 2025 que citan los 50 del corpus (bibliografías del HTML original) y que no estaban en el primer bloque: los 288 restantes (casi todos citados por un solo paper del corpus), más los del primer pool de 69 que no entraron en el bloque A. De ahí se escogieron los que cubren casos de borde que el bloque A casi no toca: contradicciones y conocimiento que cambia, críticas que contradicen cifras publicadas, seguridad y privacidad (que también sirven para la rúbrica), y vocabulario que cambia de sentido.
- **Verificación real de cada uno** (detalle en `verificacion_candidatos.md`): HTML descargado de arXiv con `robots.txt` y su pausa de 15 s; convertido con el pipeline del propio proyecto; título del HTML contra el de la API; que no esté retirado; tokens, secciones y tablas; y que cada premisa de la pregunta de ejemplo aparezca en el texto real.
- **No se leyeron completos.** Las preguntas son ideas: su respuesta se fija leyendo el paper y la verifican los dos autores (regla 11).

### Conocimiento que se contradice o cambia (4)
| # | arXiv | Paper | Casos de borde | Pregunta de ejemplo | Verificación |
|---|---|---|---|---|---|
| 1 | 2406.13805 | WikiContradict | Contradicción | When two Wikipedia passages disagree about the same fact, what does this paper find about how language models handle it? | ✓ 14.9k tok · 7 sec · 5 tab |
| 2 | 2408.12076 | ConflictBank | Contradicción, antiguo frente a nuevo | What kinds of conflicting information does ConflictBank test, for example outdated facts? | ✓ 16.6k tok · 5 sec · 13 tab |
| 3 | 2506.08184 | Unable to Forget | Distractor, antiguo frente a nuevo | Why can old information a model saw earlier keep causing wrong answers even when newer information is clearly given? | ✓ 20.6k tok · 13 sec · 1 tab |
| 4 | 2406.19354 | Fundamental Problems With Model Editing | Antiguo frente a nuevo (cambiar una creencia) | Why is replacing an old fact with a new one inside a model harder than it looks? | ✓ 20.7k tok · 11 sec · 6 tab |

### Críticas y re-evaluaciones que pueden contradecir cifras publicadas (5)
| # | arXiv | Paper | Casos de borde | Pregunta de ejemplo | Verificación |
|---|---|---|---|---|---|
| 5 | 2506.06331 | How Significant Are the Real Gains? (GraphRAG) | Contradicción con cifras reportadas, cita de segunda mano | Do the improvements that graph-based retrieval methods claim still hold when they are tested in a fairer way? | ✓ 13.5k tok · 8 sec · 2 tab |
| 6 | 2503.04338 | In-depth Analysis of Graph-based RAG | Agregación, contradicción | Which graph-based retrieval methods were tested under the same conditions, and which worked best? | ✓ 36.2k tok · 11 sec · 77 tab |
| 7 | 2506.02404 | GraphRAG-Bench | Agregación | On which kinds of questions do graph-based methods help, and on which do they not? | ✓ 9.4k tok · 5 sec · 5 tab |
| 8 | 2511.10523 | ConvoMem | Contradicción con la necesidad de RAG, marco temporal | For short conversation histories, does the paper say a retrieval system is needed, and at what size does that change? | ✓ 21.1k tok · 5 sec · 2 tab |
| 9 | 2510.23730 | Evaluating Long-Term Memory for Long-Context QA | Agregación, vocabulario distinto | Which kinds of memory (facts, past events, skills) help most when answering questions about very long conversations? | ✓ 11.9k tok · 7 sec · 5 tab |

### Originales que el corpus cita como línea base, y nombres repetidos (5)
| # | arXiv | Paper | Casos de borde | Pregunta de ejemplo | Verificación |
|---|---|---|---|---|---|
| 10 | 2505.24226 | E2GraphRAG | Cita de segunda mano, agregación | How fast and how accurate does the original E2GraphRAG paper say it is, and do later papers in the collection report similar numbers? | ✓ 10.9k tok · 5 sec · 3 tab |
| 11 | 2505.22101 | MemOS (primer artículo) | Distractor por mismo nombre, antiguo frente a nuevo | Two different papers are both called MemOS; how does the earlier one differ from the later one? | ✓ 5.5k tok · 5 sec · 0 tab |
| 12 | 2409.05591 | MemoRAG | Vocabulario distinto | Which method keeps a compressed 'global memory' of a long text to help decide what to retrieve? | ✓ 13.9k tok · 6 sec · 4 tab |
| 13 | 2510.04618 | Agentic Context Engineering (ACE) | Antiguo frente a nuevo, detalle | What two problems does this paper say appear when a model keeps rewriting its own notes over time? | ✓ 18.5k tok · 8 sec · 22 tab |
| 14 | 2504.07952 | Dynamic Cheatsheet | Vocabulario distinto | Which system lets a model keep a growing cheat sheet of tips while it works, without changing the model itself? | ✓ 13.9k tok · 6 sec · 5 tab |

### Seguridad y privacidad (rúbrica R.6.2 Cr7) (4)
| # | arXiv | Paper | Casos de borde | Pregunta de ejemplo | Verificación |
|---|---|---|---|---|---|
| 15 | 2407.12784 | AgentPoison | Seguridad (rúbrica Cr7) | How can an attacker make an AI assistant misbehave by tampering with its memory or knowledge base? | ✓ 16.6k tok · 5 sec · 7 tab |
| 16 | 2503.03704 | Memory Injection Attacks (MINJA) | Seguridad (rúbrica Cr7) | Can someone who can only chat with an assistant still plant bad memories in it, and how? | ✓ 24.9k tok · 8 sec · 14 tab |
| 17 | 2511.14937 | CIMemories | Privacidad (rúbrica Cr7) | What does 'contextual integrity' mean for an assistant that remembers personal details, and how often do models share too much? | ✓ 7.8k tok · 7 sec · 3 tab |
| 18 | 2505.18279 | Collaborative Memory | Privacidad (rúbrica Cr7) | How does the system decide which memories each user is allowed to see when memory is shared? | ✓ 23.8k tok · 8 sec · 19 tab |

### «Memoria» con otro sentido y vocabulario distinto (5)
| # | arXiv | Paper | Casos de borde | Pregunta de ejemplo | Verificación |
|---|---|---|---|---|---|
| 19 | 2402.04624 | MemoryLLM | Vocabulario distinto (memoria dentro del modelo) | Which approach updates what the model itself knows by changing part of its internal memory, instead of keeping notes outside? | ✓ 11.7k tok · 7 sec · 2 tab |
| 20 | 2407.01178 | Memory³ | Vocabulario distinto, distractor | What does 'explicit memory' mean in this paper, and how is it different from the model's weights and from retrieved text? | ✓ 27.8k tok · 9 sec · 11 tab |
| 21 | 2502.06975 | Position: Episodic Memory | Vocabulario distinto, marco temporal | What does this position paper say is missing from today's assistant memory, and what properties does it list? | ⚠ 10.5k tok · 6 sec · 2 tab — HTML sin título (identidad comprobada solo por el contenido) |
| 22 | 2511.07587 | Generative Semantic Workspaces (GSW) | Distractor frente a HippoRAG, agregación | How does this episodic approach differ from HippoRAG's way of connecting facts? | ✓ 21.6k tok · 16 sec · 15 tab |
| 23 | 2312.06648 | Dense X Retrieval | Vocabulario distinto, distractor | What is a 'proposition' in retrieval, and why would searching over propositions give different results than searching over passages? | ✓ 13.1k tok · 11 sec · 9 tab |

### Benchmark y revisión (2)
| # | arXiv | Paper | Casos de borde | Pregunta de ejemplo | Verificación |
|---|---|---|---|---|---|
| 24 | 2511.20857 | Evo-Memory | Agregación | Which memory methods were compared on learning from experience while in use, and which learned best? | ✓ 15.6k tok · 5 sec · 6 tab |
| 25 | 2411.00489 | Human-inspired Perspectives (revisión 2024) | Antiguo frente a nuevo (revisión) | How does this 2024 survey link AI memory to human memory, and what does it leave out compared with later surveys? | ✓ 31.7k tok · 8 sec · 1 tab |

## Reserva (20)
| arXiv | Paper | Casos de borde | Pregunta de ejemplo | Verificación |
|---|---|---|---|---|
| 2509.18868 | Memory in LLMs: Mechanisms, Evaluation and Evolution | Vocabulario, agregación | How does this survey divide memory in language models, and does its split match other surveys? | ✓ 47.4k tok · 7 sec · 7 tab |
| 2512.23343 | AI Meets Brain | Vocabulario | Which survey explains AI memory using ideas from brain science? | ✓ 32.2k tok · 10 sec · 2 tab |
| 2501.09136 | Agentic RAG: A Survey | Vocabulario | What does 'agentic RAG' add to ordinary retrieval, according to this survey? | ✓ 21.1k tok · 13 sec · 5 tab |
| 2407.21059 | Modular RAG | Vocabulario, distractor | What does 'modular RAG' mean and how is it different from earlier RAG designs? | ✓ 17.8k tok · 7 sec · 1 tab |
| 2401.01286 | A Comprehensive Study of Knowledge Editing | Antiguo frente a nuevo | What ways of changing a model's knowledge does this study compare, and which keeps other knowledge intact best? | ✓ 29.5k tok · 11 sec · 7 tab |
| 2403.04782 | Survey on Temporal Knowledge Graphs | Marco temporal | How do knowledge graphs represent facts that change over time? | ✓ 19.6k tok · 7 sec · 3 tab |
| 2510.13614 | MemoTime | Marco temporal | How does this method keep facts tied to the time they were true? | ✓ 21.0k tok · 6 sec · 13 tab |
| 2510.02373 | A-MemGuard | Seguridad | How can an assistant defend its memory against planted bad entries? | ✓ 17.7k tok · 8 sec · 9 tab |
| 2512.04668 | Topology Matters (fugas entre agentes) | Privacidad | In which team layouts of agents does private information leak the most? | ✓ 16.2k tok · 8 sec · 9 tab |
| 2406.13144 | DialSim | Agregación | How does this test check understanding of long conversations with several speakers? | ✓ 16.5k tok · 6 sec · 14 tab |
| 2510.01353 | MEMTRACK | Marco temporal, agregación | What does this benchmark check about keeping track of changing facts across several apps? | ✓ 14.5k tok · 6 sec · 7 tab |
| 2512.12856 | Forgetful but Faithful | Privacidad, olvido | How can an assistant forget personal data on request and still stay useful? | ✓ 51.8k tok · 8 sec · 4 tab |
| 2508.10391 | LeanRAG | Distractor frente a GraphRAG | How does this method group information into levels to find answers faster? | ✓ 16.7k tok · 7 sec · 11 tab |
| 2503.21322 | HyperGraphRAG | Vocabulario distinto | What is a hypergraph and why is it used instead of a simple graph for facts? | ✓ 16.1k tok · 7 sec · 5 tab |
| 2407.04363 | AriGraph | Distractor frente a HippoRAG | How does AriGraph combine a map of facts with a record of events? | ✓ 10.9k tok · 7 sec · 4 tab |
| 2512.12686 | Memoria | Vocabulario, distractor (mismo nombre en español) | How does this framework personalize memory for each user? | ✓ 9.5k tok · 7 sec · 2 tab |
| 2511.13593 | O-Mem | Vocabulario, marco temporal | How does this system keep memory personal while the user's interests change? | ✓ 11.9k tok · 8 sec · 7 tab |
| 2402.05136 | LV-Eval | Agregación | How does this test measure long-context ability at different text lengths? | ✓ 15.6k tok · 6 sec · 12 tab |
| 2409.02465 | DetectiveQA | Distractor | Why do detective novels make a hard test for long-context reasoning? | ✓ 9.0k tok · 8 sec · 8 tab |
| 2510.09720 | Preference-Aware Memory Update | Antiguo frente a nuevo | How does this method decide whether new information should replace an old preference? | ✓ 8.5k tok · 6 sec · 7 tab |

Se quitaron de la reserva tras verificar, porque arXiv devolvió **404** en su versión HTML: 2410.12837 (A Comprehensive Survey of RAG), 2508.15294 (Multi-Memory Segment System, retirado por sus autores en arXiv). La comprobación con `HEAD` que había hecho antes solo cubría el primer bloque; por eso conviene descargar y convertir de verdad, no solo preguntar si la página existe.

## Bloque C (opcional): 17 papers antiguos de verdad, 2018 a nov-2023, vía ar5iv
arXiv solo ofrece HTML propio desde dic-2023, así que los papers de antes (incluido **MemGPT**, el más citado del corpus: lo citan 26 de los 50 papers) no entran por la ruta normal. Están en **ar5iv** (arXiv Labs, y su `robots.txt` lo permite). Se comprobó que **el conversor del proyecto los lee sin cambios**. Falta un cambio pequeño en la ingesta: pedirle el HTML a ar5iv cuando arXiv no lo tiene. Son los que más se parecen a lo que pidió el profesor («los anteriores a los que esos papers fueron citados»), porque son los fundamentos de los que parten los de 2026.

| # | arXiv | Paper | Año | Casos de borde | Pregunta de ejemplo | Verificación |
|---|---|---|---|---|---|---|
| 1 | 2310.08560 | MemGPT | 2023 | Cita de segunda mano, vocabulario (el más citado del corpus) | How does MemGPT make a limited context window behave like unlimited memory, and do later papers describe it the same way? | ✓ 11.2k tok · 6 sec · 3 tab |
| 2 | 2304.03442 | Generative Agents | 2023 | Antiguo frente a nuevo, vocabulario | What three parts let the characters in Generative Agents remember, reflect and plan? | ✓ 26.7k tok · 9 sec · 0 tab |
| 3 | 2305.10250 | MemoryBank | 2023 | Vocabulario, antiguo frente a nuevo | How does this system decide what to forget, and which theory of human memory is it based on? | ✓ 8.9k tok · 6 sec · 2 tab |
| 4 | 2303.11366 | Reflexion | 2023 | Vocabulario distinto | How can an agent learn from its mistakes by writing itself notes, without changing the model? | ✓ 9.7k tok · 8 sec · 7 tab |
| 5 | 2210.03629 | ReAct | 2022 | Distractor, vocabulario | What is the idea of mixing thinking steps and action steps, and what was it tested on? | ✓ 14.7k tok · 6 sec · 10 tab |
| 6 | 2305.16291 | Voyager | 2023 | Vocabulario distinto (memoria de habilidades) | What is the skill library in Voyager and why does it help the agent keep improving? | ✓ 14.3k tok · 8 sec · 6 tab |
| 7 | 2310.05029 | Walking Down the Memory Maze | 2023 | Distractor frente a RAPTOR y el wiki | How does a model walk through a tree of summaries to find an answer, and how is that different from searching chunks? | ✓ 9.8k tok · 7 sec · 6 tab |
| 8 | 2308.08239 | MemoChat | 2023 | Vocabulario distinto | How does this approach keep short memos of past chats and use them later? | ✓ 11.9k tok · 5 sec · 9 tab |
| 9 | 2306.03901 | ChatDB | 2023 | Vocabulario distinto | Why would an assistant keep its memory in a database and query it, instead of in plain text? | ✓ 10.5k tok · 5 sec · 5 tab |
| 10 | 2311.08719 | Think-in-Memory | 2023 | Vocabulario distinto | What does it mean to store the model's thoughts instead of the raw conversation? | ✓ 8.0k tok · 5 sec · 3 tab |
| 11 | 2309.02427 | CoALA | 2023 | Antiguo frente a nuevo (taxonomía de 2023) | Which kinds of memory does this 2023 framework list for language agents, and how do newer surveys name them? | ✓ 19.7k tok · 9 sec · 2 tab |
| 12 | 2307.03172 | Lost in the Middle | 2023 | Contradicción con «poner todo en el contexto» | Where in a long input do models tend to miss information, and why does it matter for putting everything in the prompt? | ✓ 12.5k tok · 8 sec · 7 tab |
| 13 | 2310.11511 | Self-RAG | 2023 | Vocabulario, distractor | How does a model decide by itself when to look things up and whether what it found is useful? | ✓ 48.7k tok · 7 sec · 10 tab |
| 14 | 2208.03299 | Atlas | 2022 | Antiguo frente a nuevo | How well can a small model that searches for information do with very few examples, according to the Atlas paper? | ✓ 25.1k tok · 6 sec · 21 tab |
| 15 | 2112.09118 | Contriever | 2021 | Vocabulario | How can a search model be trained without any labeled examples? | ✓ 16.5k tok · 7 sec · 15 tab |
| 16 | 2005.11401 | RAG (Lewis et al., 2020) | 2020 | Antiguo frente a nuevo, vocabulario (qué significaba RAG) | What did the original RAG paper mean by parametric and non-parametric memory? | ✓ 11.7k tok · 8 sec · 7 tab |
| 17 | 1809.09600 | HotpotQA | 2018 | Agregación, detalle (el benchmark más usado) | What makes a question multi-hop in HotpotQA, and what extra information comes with each answer? | ✓ 10.6k tok · 8 sec · 9 tab |

Quedaron fuera del bloque C los que son del área pero no aportan un caso de borde: el informe técnico de GPT-4, Mistral 7B, SWE-bench, WebArena y la librería Transformers.

## Qué se descartó del universo
Todo lo que habla de memoria multimodal, de vídeo, embodied o robótica (WorldMM, MemVerse, GCAgent, FindingDory y similares), de compresión de caché KV y de arquitectura de modelos (Infini-attention, ChunkKV, RetroInfer), y los informes técnicos de modelos. Son del tema «memoria», pero no generan un caso de borde que el RAG y el wiki puedan responder con texto.
