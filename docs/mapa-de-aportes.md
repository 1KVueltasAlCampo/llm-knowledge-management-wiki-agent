# Categorización de la literatura por tipo de aporte

Agrupa cada artículo, repositorio o página revisada según el tipo de contribución que
hace — no según su fecha, su formato, ni si trae código. La pregunta que organiza el
documento es simple: ¿qué está tratando de resolver o de mostrar este trabajo?

Dos artículos publicados el mismo mes, sobre el mismo tema de portada, pueden estar
resolviendo problemas completamente distintos; dos con títulos que no se parecen en
nada pueden estar atacando exactamente la misma pregunta. Agrupar por aporte, en vez de
por tema o por fecha, es lo que deja ver esas relaciones.

Cada fuente aparece en la categoría a la que más aporta. Cuando hace una contribución
real a una segunda categoría, se marca al final de su línea con una nota "también en…".
Todo lo citado aquí —papers, implementaciones de código abierto, especificaciones,
bitácoras técnicas y cobertura de prensa— se trata con el mismo criterio: lo que importa
es qué tipo de pregunta responde, no qué tan formal es el medio donde se publicó.

---

## 1. Patrones y arquitecturas para construir y mantener conocimiento

Propuestas concretas de **cómo** construir o mantener, de forma continua, un cuerpo de
conocimiento con ayuda de un modelo de lenguaje — el mecanismo en sí, no su evaluación.

- **Karpathy — LLM Wiki** ([gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f), abr. 2026) — el patrón original: tres capas (fuentes / wiki / esquema) y cuatro operaciones (ingest / query / lint / output). No es software, es una idea publicada.
- **nvk/llm-wiki** — la implementación más elaborada del patrón: modelo *hub-and-spoke*, investigación multiagente paralela, curaduría de retroalimentación humana.
- **claude-obsidian** (AgriciDaniel) — plugin de Claude Code sobre Obsidian; bucle *ingest / query / lint / autoresearch*, con un *provenance ledger* propio para cada afirmación.
- **SamurAIGPT/llm-wiki-agent, lucasastorian/llmwiki, Astro-Han/karpathy-llm-wiki, llm-wiki-compiler, sage-wiki, obsidian-wiki, llm-wiki-skill** — variantes del mismo patrón en distintos *runtimes* y lenguajes; se diferencian en la plataforma soportada, no en la idea de fondo.
- **MemGPT / Letta** (Packer et al., [arXiv:2310.08560](https://arxiv.org/abs/2310.08560)) — memoria jerárquica inspirada en sistemas operativos: el propio modelo decide qué mover entre memoria de trabajo y almacenamiento externo. *También en §3: su tarea DMR es el precedente directo de medir memoria mantenida.*
- **HippoRAG** (Jiménez Gutiérrez et al., NeurIPS 2024, [arXiv:2405.14831](https://arxiv.org/abs/2405.14831); continuación HippoRAG 2, ICML 2025, [arXiv:2502.14802](https://arxiv.org/abs/2502.14802)) — grafo construido por extracción abierta de información, recuperado en un solo paso con *Personalized PageRank*, inspirado en la teoría del índice hipocampal. *También en §3.*
- **GraphRAG** (Edge et al., Microsoft, [arXiv:2404.16130](https://arxiv.org/abs/2404.16130)) — grafo de entidades más resumen jerárquico de comunidades, para responder preguntas de síntesis global sobre un corpus. *También en §3.*
- **fast-graphrag** (circlemind-ai) — variante de GraphRAG que sustituye el resumen de comunidades por recuperación con *Personalized PageRank*.
- **Mem0, Zep, A-Mem, Memori** — arquitecturas de memoria de agente con el mismo objetivo —persistir y recuperar conocimiento entre sesiones—, evaluadas entre sí sobre el banco de pruebas LoCoMo (§4).
- **Open Knowledge Format** (Google Cloud, [spec](https://github.com/GoogleCloudPlatform/open-knowledge-format)) — formaliza el patrón en un formato portable: markdown con frontmatter YAML, y desde v0.2, procedencia y confianza como campos opcionales consultables. *También en §2.*

## 2. Confiabilidad, procedencia y detección de error en una afirmación

¿Es cierto lo que dice esta página? ¿De dónde salió? ¿Sigue vigente? Trabajos que
definen, miden o detectan la calidad de una afirmación dentro de un cuerpo de
conocimiento, en vez de solo generarla.

- **FAIR Guiding Principles** (Wilkinson et al., 2016, *Scientific Data*, [doi:10.1038/sdata.2016.18](https://doi.org/10.1038/sdata.2016.18)) — el antecedente académico, revisado por pares: cuatro principios (*Findable, Accessible, Interoperable, Reusable*) para que datos y metadatos sean utilizables por máquinas, con la procedencia detallada como requisito explícito.
- **Garralda-Barrio — Knowledge-Centric Information Systems** ([arXiv:2607.02609](https://arxiv.org/abs/2607.02609)) — traduce cada garantía de la ingeniería de datos clásica (linaje, catálogo, calidad, gobierno) a su versión para artefactos de conocimiento. Artículo de visión, sin evaluación empírica propia.
- **BeliefShift, STALE, TOKI, NeuSymMS, MemConflict, MemSyco-Bench** — bancos de prueba y mecanismos para detectar contradicción, obsolescencia y sicofancia en memoria de agentes conversacionales, cada uno con su propio conjunto de datos anotado.
- **Contradiction Detection in RAG Systems, Fundamental Problems With Model Editing** — cómo debería —y cómo no debería— resolverse una contradicción cuando llega información nueva.
- **KnowHalu** (Zhang et al., [arXiv:2404.02935](https://arxiv.org/abs/2404.02935)) — separa la alucinación "por no-fabricación" (un hecho correcto que responde otra pregunta) de la alucinación factual, y permite un veredicto INCONCLUSIVO en vez de forzar sí/no.
- **HalluLens** ([arXiv:2504.17550](https://arxiv.org/pdf/2504.17550)) — banco de pruebas que distingue alucinación extrínseca de intrínseca, con conjuntos de prueba regenerados dinámicamente.
- **ReFinED** (Ayoola et al., NAACL 2022, [arXiv:2207.04108](https://arxiv.org/abs/2207.04108)) — vinculador de entidades *zero-shot* contra Wikipedia/Wikidata: decidir si dos menciones se refieren a la misma entidad es una precondición de cualquier procedencia confiable. *También en §7.*

## 3. Comparación empírica entre arquitecturas de recuperación

Mediciones directas de qué método gana, y bajo qué condiciones, cuando se enfrentan dos
o más formas de responder preguntas sobre un corpus.

- **Han et al. — RAG vs. GraphRAG: A Systematic Evaluation** ([arXiv:2502.11371](https://arxiv.org/abs/2502.11371)) — protocolo unificado de comparación; ningún enfoque gana de forma absoluta, la ventaja depende de la tarea.
- **GraphRAG-Bench / "When to Use Graphs in RAG"** (ICLR 2026, [arXiv:2506.05690](https://arxiv.org/abs/2506.05690)) — la misma pregunta, con un banco de pruebas de dominio específico (guías médicas y novelas) diseñado para exponer en qué etapa falla cada método.
- Los resultados propios de **GraphRAG** y de **HippoRAG** (§1) frente a RAG vectorial y a recuperación iterativa (IRCoT) son, en sí mismos, comparaciones de este tipo.

## 4. Generación de un artefacto en una sola pasada

Producir un buen resumen, artículo o informe una vez, sin ningún compromiso de
mantenerlo actualizado después. Es, en sentido estricto, lo opuesto de §1 — y es donde
vive casi toda la literatura revisada por pares que existe hoy sobre "escribir como una
wiki".

- **STORM / Co-STORM** (Shao et al., NAACL 2024, [arXiv:2402.14207](https://arxiv.org/abs/2402.14207)) — genera artículos largos tipo Wikipedia desde cero, simulando conversaciones guiadas por perspectivas distintas antes de escribir.
- **WikiChat** (Semnani et al., EMNLP Findings 2023, [arXiv:2305.14292](https://arxiv.org/abs/2305.14292)) — ancla la respuesta en Wikipedia, reteniendo solo los hechos fundamentados. *También en §2: su mecanismo es, en el fondo, control de alucinación.*
- **WikiAutoGen** (Yang et al., ICCV 2025, [arXiv:2503.19065](https://arxiv.org/abs/2503.19065)) — extiende la generación de artículos al caso multimodal (texto e imágenes).
- **FreshWiki, WildSeek** — bancos de prueba para evaluar ese tipo de artefacto generado una vez.
- **DeepScholar-Bench** ([arXiv:2508.20033](https://arxiv.org/html/2508.20033v1)) **y ResearchRubrics** (ICLR 2026, [arXiv:2511.07685](https://arxiv.org/abs/2511.07685)) — evaluación de agentes de investigación profunda que sintetizan y citan fuentes, también en una sola pasada.
- **LoCoMo** — el banco de pruebas de memoria conversacional de largo plazo que usan Mem0, Zep, A-Mem y Memori (§1) para medirse entre sí.

## 5. Aplicación a un caso de uso concreto y acotado

Instanciar cualquiera de los patrones anteriores sobre un dominio real, verificable y
con usuarios identificables, en vez de proponerlo en abstracto.

- **WikiSP** (Xu et al., EMNLP 2023, [arXiv:2305.14202](https://arxiv.org/abs/2305.14202)) — traduce preguntas a SPARQL sobre Wikidata, con recuperación de errores de vinculación de entidades vía menciones textuales.
- **Edisum** (Šakota et al., [arXiv:2404.03428](https://arxiv.org/abs/2404.03428)) — genera resúmenes de edición de Wikipedia a partir del *diff*; evaluado con jueces humanos frente a editores reales. *También en §1: es, en sustancia, la operación de escribir el registro de un cambio.*
- **Question-to-Question Retrieval** (Thottingal, [arXiv:2501.11301](https://arxiv.org/abs/2501.11301)) — indexa preguntas generadas por página, en vez del texto de la página, para Wikipedia y Wikidata. Preprint de un solo autor, sin revisión por pares confirmada.

## 6. Límites del contexto largo como motivación para compilar

Evidencia de por qué "meter todo en la ventana de contexto" no sustituye a compilar y
mantener una base aparte — el argumento de fondo detrás de por qué las secciones §1 y
§5 tienen sentido en primer lugar.

- **Lost in the Middle** (Liu et al., TACL 2023, [arXiv:2307.03172](https://arxiv.org/abs/2307.03172)) — curva de desempeño en forma de U según la posición de la información relevante en el contexto; persiste incluso con ventanas extendidas.
- **LongMamba** (jzhang38) — el mismo síntoma reproducido en una arquitectura sin mecanismo de atención (Mamba). Bitácora de exploración personal, no revisada por pares.
- **Llama-2-7B-32K-Instruct** (Together AI) — mitigación por el lado del entrenamiento: afinar el modelo con tareas explícitas de contexto largo, en vez de reducir lo que se le entrega en el *prompt*.
- **Governance Decay, Self-Compacting Language Model Agents, Parallel Context Compaction** — cómo compactar el contexto sin perder información crítica —en el primer caso, restricciones de seguridad— en agentes de horizonte largo.
- **Bouchard, L. — Context Engineering in 2026** — divulgación técnica sobre cuándo compactar el contexto sí conviene y cuándo no.

## 7. Herramientas, protocolos y estándares de soporte

Piezas reutilizables que cualquiera de los trabajos anteriores podría necesitar, pero
que no son, en sí mismas, un aporte de investigación — son la caja de herramientas.

- **ReFinED** — ver §2; también es, en la práctica, infraestructura que otros trabajos (GraphRAG, WikiSP) citan o afinan como componente.
- **Model Context Protocol (MCP), Agent-to-Agent (A2A), litellm** — estándares y librerías de interoperabilidad entre modelos, agentes y fuentes de datos.
- **Obsidian + Dataview** — capa de visualización y consulta sobre markdown, sin bloqueo de proveedor.
- **Glean, Neo4j** — plataformas empresariales de búsqueda y grafos de conocimiento; relevantes como estado del arte industrial y fuente de requisitos realistas (permisos, auditoría).

## 8. Divulgación y cobertura de prensa especializada

Blogs, hilos y artículos de producto que explican o promocionan el patrón, sin aportar
metodología propia ni evaluación. Se agrupan en un solo bloque porque, entre sí,
describen la misma idea sin añadir información nueva unos sobre otros — no porque
valgan menos, sino porque su aporte individual es el mismo aporte repetido.

- Cobertura general del patrón LLM Wiki: DataCamp, MindStudio, Kunal Ganglani,
  Denser.ai, note.com/wayne_chang.
- Cobertura de la comparación RAG / GraphRAG: VentureBeat.
- Cobertura de escalamiento empresarial del patrón: Falconer.
- Cobertura de frameworks de memoria de agentes: Atlan, blog de Mem0.

---

## Cómo leer este documento

Cada categoría es un tipo de pregunta distinto, no un nivel de calidad: un trabajo con
mucha compañía en su categoría no es mejor ni peor que uno con poca, solo indica cuánto
se ha escrito ya sobre esa pregunta específica. Las notas "también en…" señalan los
pocos trabajos que tienden un puente real entre dos categorías; son, casi siempre, el
lugar más interesante para empezar a mirar si se busca un ángulo que combine dos líneas
hasta ahora tratadas por separado.

El detalle completo de cada fuente —metodología, resultados exactos, limitaciones,
preguntas abiertas— vive en [fichas-lectura.md](fichas-lectura.md); el panorama
narrativo y las decisiones de encuadre del proyecto, en
[estado-del-arte.md](estado-del-arte.md). Este documento es el cruce entre ambos: no
reemplaza a ninguno, y no asume que ya se haya elegido un problema.

---

## 9. Patrones de cruce, más específicos

Las ocho categorías anteriores agrupan por el tipo general de pregunta. Lo que sigue es
un grano más fino: técnicas o decisiones de diseño concretas que comparte un grupo
pequeño de trabajos —casi siempre a caballo entre dos de las categorías de arriba—, y
que valen la pena nombrar aparte precisamente porque son pocos y específicos, no pese a
eso.

### 9.1 Procedencia integrada al mecanismo, no añadida después

La mayoría de las arquitecturas de §1 tratan la procedencia como un campo opcional que
se agrega al formato de salida. Un grupo pequeño la hace parte del mecanismo mismo,
desde el diseño:

- **Open Knowledge Format** — la procedencia (`sources`, `generated`, `verified`) no es
  un anexo: es la razón de ser de la versión 0.2 del formato completo.
- **NeuSymMS** — combina extracción neuronal de hechos con un sistema experto
  determinista que clasifica, deduplica y reconcilia esos hechos; el mantenimiento de
  verdad (*truth maintenance*) es parte del motor, no un paso posterior.
- **claude-obsidian** — llegó al mismo punto por la vía práctica, sin usar OKF: su
  *provenance ledger* registra atribución, frescura y confianza como parte del bucle
  normal de ingesta, no como una auditoría aparte.

### 9.2 Recuperación por *Personalized PageRank* sobre un grafo

Frente al resumen jerárquico de comunidades de GraphRAG, hay un linaje técnico más
angosto que usa un algoritmo de ranking distinto para el mismo problema — y uno de los
dos cita al otro explícitamente como fundamento:

- **HippoRAG** — introduce el mecanismo: grafo construido por extracción abierta de
  información, recuperado en un solo paso con *Personalized PageRank*.
- **fast-graphrag** — adopta el mismo algoritmo sobre una arquitectura más ligera,
  citando a HippoRAG en su propia documentación como la razón conceptual de por qué
  funciona.

### 9.3 Resolución de entidades como pieza compartida

Antes de que cualquier grafo o base estructurada sea confiable, alguien tiene que
decidir si dos menciones de texto son la misma entidad. Un mismo tipo de componente
aparece, con distinto grado de protagonismo, en varios trabajos de este corpus:

- **ReFinED** — el vinculador de entidades en sí: *zero-shot*, contra Wikipedia y
  Wikidata, en un solo paso hacia adelante.
- **WikiSP** — lo afina directamente para resolver menciones de Wikidata dentro de su
  propio analizador semántico.
- **GraphRAG** usa por defecto coincidencia exacta de cadenas para este paso, pero
  discute explícitamente la literatura de resolución de entidades como la vía para
  hacerlo de forma más flexible — ReFinED es exactamente ese tipo de herramienta,
  aunque el propio artículo no lo nombra.

### 9.4 Anclar a Wikidata en vez de construir el grafo desde el texto

Dos trabajos, por caminos distintos, evitan extraer una estructura propia del corpus y
en cambio aprovechan que Wikidata ya es una base de hechos estructurada:

- **WikiSP** — traduce la pregunta a SPARQL y consulta Wikidata directamente.
- **Question-to-Question Retrieval** — convierte cada tripleta de Wikidata en texto y la
  indexa junto con las páginas de Wikipedia, tratando ambas fuentes de la misma manera.

Ninguno de los dos construye un grafo de entidades desde cero, como sí hacen GraphRAG o
HippoRAG: lo dan por construido de antemano y concentran su aporte en la traducción o
el emparejamiento.
