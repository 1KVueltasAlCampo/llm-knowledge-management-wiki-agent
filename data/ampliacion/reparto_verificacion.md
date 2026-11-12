# Reparto de la verificación: 50 papers nuevos y 40 preguntas de borde

Fecha: 12 de noviembre de 2026. Para Juan David y Juan Diego.

**Archivos:** `verificacion_ampliacion.xlsx` (el que se usa: hojas «Papers» y una de preguntas por autor), o los mismos datos en `hoja_verificacion.csv` y `preguntas_verificacion.csv`. Lo que ya comprobó la máquina está en `verificacion_candidatos.md`.

## 1. Qué hay que hacer
Ampliamos el corpus de 50 a 100 papers (sumamos 50 que los actuales citan) y sumamos 40 preguntas de caso de borde a las 60 ya acordadas. Cada uno hace dos cosas:

1. **Revisar sus 25 papers** (25 papers, 15 de prioridad 1) y decir solo si el paper **de verdad tiene la información o está relacionado** con lo que buscamos (columna «que_buscar» del Excel: caso de borde, de qué habla y cómo se relaciona con el corpus). Sí, No o Parcial.
2. **Escoger 20 preguntas de las 40 de su lista** (secciones 3 y 4) y comprobar con Ctrl+F que la respuesta que ya trae el Excel es verdad. Cada pregunta trae la respuesta que daría la wiki (escrita por Claude con los 100 papers) y los fragmentos de texto que la justifican.

Después cada uno revisa las 20 del otro y marca si está de acuerdo (regla 11 de la constitución). Claude ya comprobó con un script que cada paper existe, que su HTML se descarga y se convierte, que el título es el correcto y que los términos aparecen: no hace falta repetirlo.

## 2. Los 50 papers
Prioridad 1 = alimenta las preguntas núcleo; se mira primero. Prioridad 2 = fondo del corpus. La hoja «Papers» del Excel explica de qué habla cada paper y cómo se relaciona con el corpus actual. **Aviso:** en nuestra conversión Hindsight, Generative Agents y el primer MemOS salen sin tablas; hay que mirar si el original sí las tiene. Seis papers antiguos (MemGPT, Generative Agents, MemoryBank, Lost in the Middle, RAG de Lewis y HotpotQA) solo están en ar5iv y requieren un cambio en la ingesta que hace Claude.

### Juan David (25 papers, 386.003 tokens)
| # | arXiv | Paper | Prio. | Qué buscar |
|---|---|---|---|---|
| 1 | 2310.08560 | MemGPT | 1 | Cita de segunda mano, vocabulario (el más citado del corpus) |
| 2 | 2402.17753 | LoCoMo | 1 | Contradicción en los datos del benchmark |
| 3 | 2410.10813 | LongMemEval | 1 | Agregación |
| 4 | 2501.13956 | Zep | 1 | Contradicción |
| 5 | 2504.19413 | Mem0 | 1 | Cita de segunda mano, antiguo frente a nuevo, agregación |
| 6 | 2505.22101 | MemOS (primer artículo) | 1 | Distractor por mismo nombre, antiguo frente a nuevo |
| 7 | 2510.18866 | LightMem | 1 | Contradicción, agregación |
| 8 | 2305.10250 | MemoryBank | 1 | Vocabulario, antiguo frente a nuevo |
| 9 | 2502.12110 | A-MEM | 1 | Vocabulario distinto |
| 10 | 2506.21605 | MemBench | 1 | Vocabulario distinto |
| 11 | 2510.27246 | BEAM | 1 | Escala, marco temporal |
| 12 | 2511.01448 | LiCoMemory | 1 | Agregación |
| 13 | 2304.03442 | Generative Agents | 1 | Antiguo frente a nuevo, vocabulario |
| 14 | 2511.03506 | HaluMem | 1 | Abstracción |
| 15 | 2511.18423 | General Agentic Memory | 1 | Vocabulario distinto |
| 16 | 2406.13805 | WikiContradict | 2 | Contradicción |
| 17 | 2503.04338 | In-depth Analysis of Graph-based RAG | 2 | Agregación, contradicción |
| 18 | 2505.24226 | E2GraphRAG | 2 | Cita de segunda mano, agregación |
| 19 | 2510.09720 | Preference-Aware Memory Update | 2 | Antiguo frente a nuevo |
| 20 | 2510.13614 | MemoTime | 2 | Marco temporal |
| 21 | 2511.10523 | ConvoMem | 2 | Contradicción con la necesidad de RAG, marco temporal |
| 22 | 2511.13593 | O-Mem | 2 | Vocabulario, marco temporal |
| 23 | 2312.06648 | Dense X Retrieval | 2 | Vocabulario distinto, distractor |
| 24 | 2510.01353 | MEMTRACK | 2 | Marco temporal, agregación |
| 25 | 2511.20857 | Evo-Memory | 2 | Agregación |

### Juan Diego (25 papers, 385.994 tokens)
| # | arXiv | Paper | Prio. | Qué buscar |
|---|---|---|---|---|
| 1 | 2507.03724 | MemOS (artículo largo) | 1 | Distractor por nombre parecido |
| 2 | 2401.18059 | RAPTOR | 1 | Distractor frente al wiki |
| 3 | 2507.05257 | MemoryAgentBench | 1 | Vocabulario distinto |
| 4 | 2404.16130 | GraphRAG | 1 | Vocabulario, distractor |
| 5 | 2410.05779 | LightRAG | 1 | Misma herramienta, escalas distintas |
| 6 | 2502.13270 | REALTALK | 1 | Contradicción (conversaciones reales frente a sintéticas) |
| 7 | 2504.14225 | PersonaMem | 1 | Marco temporal (preferencias que cambian) |
| 8 | 2512.12818 | Hindsight is 20/20 | 1 | Agregación, afirmaciones que se pisan |
| 9 | 2307.03172 | Lost in the Middle | 1 | Contradicción con «poner todo en el contexto» |
| 10 | 2404.06654 | RULER | 1 | Vocabulario (tamaño real del contexto) |
| 11 | 2005.11401 | RAG (Lewis et al., 2020) | 1 | Antiguo frente a nuevo, vocabulario (qué significaba RAG) |
| 12 | 2406.19354 | Fundamental Problems With Model Editing | 1 | Antiguo frente a nuevo (cambiar una creencia) |
| 13 | 2408.12076 | ConflictBank | 1 | Contradicción, antiguo frente a nuevo |
| 14 | 2409.05591 | MemoRAG | 1 | Vocabulario distinto |
| 15 | 2503.03704 | Memory Injection Attacks (MINJA) | 1 | Seguridad (rúbrica Cr7) |
| 16 | 2510.04618 | Agentic Context Engineering (ACE) | 2 | Antiguo frente a nuevo, detalle |
| 17 | 1809.09600 | HotpotQA | 2 | Agregación, detalle (el benchmark más usado) |
| 18 | 2312.10997 | RAG Survey (2023) | 2 | Abstención, distractor |
| 19 | 2402.14207 | STORM | 2 | Distractor frente a LLM-Wiki |
| 20 | 2407.12784 | AgentPoison | 2 | Seguridad (rúbrica Cr7) |
| 21 | 2412.15605 | Don't Do RAG (CAG) | 2 | Contradicción parcial con WiCER (depende de la escala) |
| 22 | 2506.06331 | How Significant Are the Real Gains? (GraphRAG) | 2 | Contradicción con cifras reportadas, cita de segunda mano |
| 23 | 2504.07952 | Dynamic Cheatsheet | 2 | Vocabulario distinto |
| 24 | 2506.02404 | GraphRAG-Bench | 2 | Agregación |
| 25 | 2511.14937 | CIMemories | 2 | Privacidad (rúbrica Cr7) |

## 3. Reglas para escoger y escribir preguntas
- **Cada autor escoge 20 de sus 40.** Meta: unas 2 de cada tipo del cuadro de la sección 5 (no es estricto; cubrir la mayoría de tipos basta). Si una pregunta no se puede responder con el paper, se descarta, no se fuerza.
- **Sin pistas de política:** la pregunta no dice «el más reciente» ni «si no existe responde X». Eso va en la clave.
- **Respuesta verificable:** de 3 a 5 datos concretos y el lugar donde está (sección o tabla).
- **Contradicción y segunda mano:** apuntar benchmark, versión, métrica y su dirección, modelo base y configuración. Si no coinciden, es una diferencia de protocolo y la clave debe dar las dos cifras con su contexto.
- **Agregación:** solo con un conjunto cerrado de papers (lista exacta).
- **Abstención:** la máquina no encontró ningún bloque con los dos nombres a la vez; confirmar leyendo. Claude hará la búsqueda exhaustiva en los 100 textos.
- **Nombres ambiguos con ID:** hay dos artículos llamados MemOS (2505.22101 y 2507.03724).
- Las preguntas de papers muy famosos (MemGPT, Generative Agents) pueden descartarse en la sonda a libro cerrado: no importa, es parte del plan.

## 4. Las listas de preguntas
Cada tabla trae las 40 candidatas del autor. En el Excel cada pregunta incluye además los papers donde mirar, la respuesta de la wiki, los fragmentos para Ctrl+F y una nota de Claude (por ejemplo, si las cifras cambian según el modelo base o si falta una tabla).

### Lista de Juan David: escoge 20
| # | Tipo | Pregunta |
|---|---|---|
| JD-01 | Antiguo frente a nuevo | What accuracy has been reported for Zep on the DMR benchmark? |
| JD-02 | Antiguo frente a nuevo | What overall J score has been reported for Mem0 on LoCoMo with gpt-4o-mini? |
| JD-03 | Antiguo frente a nuevo | How many sessions can a LoCoMo conversation have? |
| JD-04 | Antiguo frente a nuevo | With GPT-4o-mini, what accuracy does LightMem reach on LongMemEval-S and how does it compare with A-MEM? |
| JD-05 | Antiguo frente a nuevo | With GPT-4o-mini, how well does A-MEM do on the multi-hop questions of LoCoMo? |
| JD-06 | Antiguo frente a nuevo | What single-hop LLM-judge score does MemOS report for itself on LoCoMo? |
| JD-07 | Vocabulario distinto | Which paper makes stored conversation memories fade over time, in a way inspired by how people forget? |
| JD-08 | Vocabulario distinto | Which paper links an agent's notes to each other, following a note-taking method from a German sociologist? |
| JD-09 | Vocabulario distinto | Which paper copies the stages of human sleep and short-term versus long-term storage to cut the number of tokens a memory system uses? |
| JD-10 | Vocabulario distinto | Which benchmark checks whether a memory system invents false facts when it stores, updates or answers? |
| JD-11 | Vocabulario distinto | Which paper stores facts in a graph where each fact carries the time during which it was true? |
| JD-12 | Vocabulario distinto | Which paper simulates characters in a small virtual town who remember, think about their memories and plan their days? |
| JD-13 | Abstención | What accuracy does Zep reach on MemBench? |
| JD-14 | Abstención | What score does LightMem get on HaluMem? |
| JD-15 | Abstención | What F1 score does Mem0 reach on MuSiQue? |
| JD-16 | Abstención | What accuracy does LiCoMemory reach on BEAM? |
| JD-17 | Abstención | How does MemOS perform on REALTALK? |
| JD-18 | Abstención | What score does MemGPT get on BEAM? |
| JD-19 | Contradicción | How many conversations does LoCoMo contain? |
| JD-20 | Contradicción | What single-hop score has Mem0 been reported with on LoCoMo? |
| JD-21 | Contradicción | How many tokens does a LoCoMo dialogue have? |
| JD-22 | Contradicción | What accuracy does Mem0 get on LongMemEval? |
| JD-23 | Agregación | Which papers in the collection mention MEMTRACK? |
| JD-24 | Agregación | Which papers in the collection mention HaluMem? |
| JD-25 | Agregación | Which papers in the collection mention REALTALK? |
| JD-26 | Agregación | Which papers in the collection mention ConvoMem? |
| JD-27 | Segunda mano | What accuracy does Zep get on LongMemEval according to the Zep paper, and what do later papers report for it? |
| JD-28 | Segunda mano | What overall J does the Mem0 paper give for its graph variant, and what do later papers report for it? |
| JD-29 | Segunda mano | What accuracy is reported for A-MEM on LongMemEval, and which paper reports it? |
| JD-30 | Segunda mano | What does the MemGPT paper report on DMR, and what does the Zep paper report for MemGPT? |
| JD-31 | Marco temporal | How many questions does the LoCoMo benchmark contain? |
| JD-32 | Marco temporal | Which memory system has the highest reported accuracy on the DMR benchmark? |
| JD-33 | Detalle de tabla | How many memory tokens do Mem0, its graph variant and Zep use per conversation in the Mem0 paper? |
| JD-34 | Detalle de tabla | In the Zep paper's LongMemEval table, what latency and context size does Zep have with gpt-4o-mini? |
| JD-35 | Detalle de tabla | In the A-MEM paper, what memory usage and retrieval time does A-MEM have with 10,000 memories? |
| JD-36 | Detalle de tabla | In the MemBench paper, what accuracy does the retrieval memory mechanism reach on the factual-memory participation scenario at 100k tokens? |
| JD-37 | Identificador exacto | Which paper uses the dataset called InfiniteChoice? |
| JD-38 | Identificador exacto | Which paper introduces the dataset called HaluMem-Long? |
| JD-39 | Dato antiguo vigente | Which five abilities does LongMemEval test? |
| JD-40 | Dato antiguo vigente | Which three scores does Generative Agents use to choose which memories to bring back? |

### Lista de Juan Diego: escoge 20
| # | Tipo | Pregunta |
|---|---|---|
| JDi-01 | Antiguo frente a nuevo | What accuracy does RAPTOR reach on QuALITY when paired with GPT-4? |
| JDi-02 | Antiguo frente a nuevo | What accuracy has been reported for Hindsight on LongMemEval? |
| JDi-03 | Antiguo frente a nuevo | What accuracy has been reported for Hindsight on LoCoMo? |
| JDi-04 | Antiguo frente a nuevo | How often does GraphRAG's global approach beat plain vector retrieval on comprehensiveness? |
| JDi-05 | Antiguo frente a nuevo | What win rate does LightRAG have against the naive retrieval baseline overall on the Agriculture dataset? |
| JDi-06 | Antiguo frente a nuevo | What effective context length does RULER report for GPT-4, compared with its claimed length? |
| JDi-07 | Vocabulario distinto | Which paper builds a tree by repeatedly grouping pieces of text and summarising each group, so questions can be answered at different levels of detail? |
| JDi-08 | Vocabulario distinto | Which paper answers broad questions about a whole collection of texts by first summarising groups of closely connected entities? |
| JDi-09 | Vocabulario distinto | Which paper found that models answer worse when the useful passage sits in the middle of a long input? |
| JDi-10 | Vocabulario distinto | Which paper skips retrieval altogether by loading the whole knowledge base into the model's precomputed state? |
| JDi-11 | Vocabulario distinto | Which paper uses a light long-term memory to draft clues about what is needed before searching the database? |
| JDi-12 | Vocabulario distinto | Which paper lets a model keep improving a growing playbook of strategies, adding small changes so it does not collapse into short summaries? |
| JDi-13 | Abstención | What score does Hindsight get on MemoryAgentBench? |
| JDi-14 | Abstención | What accuracy does Hindsight reach on PersonaMem? |
| JDi-15 | Abstención | How does LightRAG perform on REALTALK? |
| JDi-16 | Abstención | What score does GraphRAG get on HaluMem? |
| JDi-17 | Abstención | What accuracy does RAPTOR reach on MemBench? |
| JDi-18 | Abstención | What score does GraphRAG get on RULER? |
| JDi-19 | Contradicción | How many turns does a LoCoMo conversation have? |
| JDi-20 | Contradicción | What accuracy does Zep get on LoCoMo? |
| JDi-21 | Contradicción | Do the papers agree on whether Zep or Mem0 scores higher on LongMemEval? |
| JDi-22 | Contradicción | Does Mem0 or Zep score higher overall on MemoryAgentBench, and is it the same on LoCoMo? |
| JDi-23 | Agregación | Which papers in the collection mention NovelQA? |
| JDi-24 | Agregación | Which papers in the collection mention UltraDomain? |
| JDi-25 | Segunda mano | What overall LoCoMo score does the Mem0 paper publish for Mem0, and how does a later paper treat it? |
| JDi-26 | Segunda mano | What accuracy do GraphRAG (local) and LightRAG reach on NovelQA with Qwen2.5-7B-Instruct according to the E2GraphRAG paper? |
| JDi-27 | Segunda mano | What does GAM report for RULER multi-hop tracing with GPT-4o-mini, compared with a long-context baseline? |
| JDi-28 | Segunda mano | What overall score does MemoryAgentBench report for Mem0, and for GPT-4o-mini with a 128K context? |
| JDi-29 | Marco temporal | Which method has the best reported accuracy on NovelQA? |
| JDi-30 | Marco temporal | What is the best accuracy reported on QuALITY? |
| JDi-31 | Marco temporal | What is the best score reported at the 128K setting in the RULER paper? |
| JDi-32 | Marco temporal | Which agent has the highest overall score in the main MemoryAgentBench table? |
| JDi-33 | Detalle de tabla | How many documents and how many tokens does the Agriculture dataset have in the LightRAG paper? |
| JDi-34 | Detalle de tabla | In the RULER paper, what are the claimed and effective context lengths of Llama3.1 (70B), and its score at 128K? |
| JDi-35 | Detalle de tabla | In the Lost in the Middle paper, what closed-book and oracle accuracy does GPT-3.5-Turbo get? |
| JDi-36 | Detalle de tabla | In the GAM paper, what F1 does GAM get on HotpotQA with a 56K context and GPT-4o-mini? |
| JDi-37 | Identificador exacto | Which paper introduces the benchmark called FactConsolidation? |
| JDi-38 | Identificador exacto | Which paper presents the test set called UltraDomain? |
| JDi-39 | Dato antiguo vigente | Which four abilities does MemoryAgentBench test? |
| JDi-40 | Dato antiguo vigente | Which four criteria does the GraphRAG paper use to judge answers? |

## 5. Cuotas de referencia (de 40 candidatas a 20 escogidas)
| Tipo | Candidatas JD | Candidatas JDi | Meta al escoger (cada uno) |
|---|---|---|---|
| Antiguo frente a nuevo | 6 | 6 | 3 |
| Vocabulario distinto | 6 | 6 | 3 |
| Abstención | 6 | 6 | 3 |
| Contradicción | 4 | 4 | 2 |
| Agregación | 4 | 2 | 1 o 2 |
| Segunda mano | 4 | 4 | 2 |
| Marco temporal | 2 | 4 | 1 o 2 |
| Detalle de tabla | 4 | 4 | 2 |
| Identificador exacto | 2 | 2 | 1 |
| Dato antiguo vigente | 2 | 2 | 1 |

## 6. Cierre
Cada pregunta la escribe un autor y la verifica el otro **antes de ver cualquier respuesta de los sistemas**. Si no están de acuerdo, se corrige o se descarta; el desacuerdo cuenta para el kappa. Antes de la primera corrida se congelan preguntas y claves con fecha y huella.
