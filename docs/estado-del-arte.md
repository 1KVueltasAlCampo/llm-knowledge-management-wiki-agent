# WikiLLM: estado del arte

Bases para un proyecto de maestría en Inteligencia Artificial Aplicada.
Revisión al 31 de agosto de 2026.

---

## 1. De qué estamos hablando

Un *WikiLLM* (o *LLM wiki*) es una base de conocimiento en texto plano —típicamente
markdown interenlazado— que un agente basado en un modelo de lenguaje **construye y
mantiene** de forma incremental a partir de fuentes crudas. La diferencia operativa
con RAG es dónde ocurre la síntesis:

| | RAG clásico | WikiLLM |
|---|---|---|
| Cuándo se sintetiza | En cada consulta | Una vez, al ingerir |
| Qué se almacena | Fragmentos crudos + embeddings | Páginas ya redactadas y enlazadas |
| Qué pasa entre consultas | Nada persiste | El conocimiento se acumula |
| Costo dominante | Inferencia por consulta | Inferencia por ingesta y por mantenimiento |
| Falla típica | Recuperar el fragmento equivocado | Propagar un error de síntesis pasado |

La formulación que catalizó el campo es de Andrej Karpathy, en un gist publicado el
4 de abril de 2026 y presentado por él mismo como "un archivo de ideas", no como
software. Su argumento central es económico más que técnico:

> "La parte tediosa de mantener una base de conocimiento no es leer ni pensar: es la
> contabilidad."

El gist observa que una pregunta que requiere sintetizar cinco documentos obliga al
modelo a reencontrar y recomponer los fragmentos *cada vez*, y que nada se construye.
La propuesta es invertir el orden: compilar una vez, consultar barato después.

En dos semanas el gist superó 5.000 estrellas y 4.000 forks, con decenas de
reimplementaciones. Conviene registrar el sesgo: gran parte de la literatura
disponible sobre WikiLLMs es **literatura gris** (blogs, posts de producto), no
revisada por pares. La contribución académica de un proyecto de maestría está
justamente en ese hueco.

---

## 2. Anatomía del patrón canónico

El gist prescribe tres capas:

```
raw/            # fuentes inmutables: artículos, PDFs, datos. El agente lee, nunca escribe.
wiki/           # generado y mantenido por el LLM
  index.md      # catálogo con enlaces y resumen de una línea
  log.md        # registro cronológico append-only de ingestas, consultas y lints
  overview.md   # página de síntesis
  sources/      # resúmenes de cada material ingerido
  entities/     # personas, organizaciones, herramientas
  concepts/     # teorías, métodos, patrones
  analyses/     # tablas comparativas, síntesis, investigaciones
CLAUDE.md       # el esquema: convenciones y flujos de trabajo para el agente
```

La tercera capa —el esquema, `CLAUDE.md` o `AGENTS.md`— es la pieza conceptualmente
interesante: es *prompt como configuración de sistema*. Define qué hace el agente en
cada operación.

**Las cuatro operaciones.**

1. **Ingest.** El agente lee la fuente, discute los hallazgos con el humano, crea una
   página de resumen, actualiza el índice, **revisa entre 10 y 15 páginas existentes**
   de entidades y conceptos, y añade una entrada al log. El diseño favorece ingesta de
   a una fuente, con el humano validando antes de escribir.
2. **Query.** Busca en las páginas relevantes, sintetiza con citas y opcionalmente
   archiva la respuesta valiosa como página nueva.
3. **Lint.** Pasada periódica que detecta contradicciones entre páginas, afirmaciones
   obsoletas superadas por fuentes nuevas, páginas huérfanas sin enlaces entrantes,
   referencias cruzadas faltantes y vacíos de datos.
4. **Output.** Genera artefactos derivados: informes, resúmenes, cronologías.

**Convenciones.** Frontmatter por página (tags, fechas, número de fuentes), consultable
con Dataview u similares. Log con prefijos parseables: `## [YYYY-MM-DD] operación | Título`.
Los enlaces suelen escribirse en formato dual `[[wikilink]]` + markdown estándar para
funcionar tanto en Obsidian como en GitHub o un editor de texto.

**El paso subestimado es el 1.c**: "revisa 10–15 páginas existentes". Ahí está el
problema difícil —y el más investigable— de todo el patrón. Ver §6.

---

## 3. Panorama de implementaciones

Instrumentos concretos, ordenados por lo que aportan conceptualmente. Los conteos de
estrellas provienen de literatura gris fechada en abril de 2026 y **deben verificarse
antes de citarlos** en un trabajo académico.

| Proyecto | Stack | Qué aporta |
|---|---|---|
| [nvk/llm-wiki](https://github.com/nvk/llm-wiki) | Plugins para Claude Code, Codex, OpenCode | La implementación más elaborada. Ver detalle abajo. |
| SamurAIGPT/llm-wiki-agent | Multiplataforma (Claude Code, Codex, Gemini CLI) | ~1.965 ⭐. Esquemas separados por plataforma. |
| AgriciDaniel/claude-obsidian | Claude Code + Obsidian | ~1.480 ⭐. Diez skills especializadas, incluye `/autoresearch`. |
| [lucasastorian/llmwiki](https://github.com/lucasastorian/llmwiki) | Web + MCP | Sube documentos y conecta la cuenta de Claude vía MCP. |
| [Astro-Han/karpathy-llm-wiki](https://github.com/Astro-Han/karpathy-llm-wiki) | Agent Skills | Compatible con Claude Code, Cursor y Codex. |
| llm-wiki-compiler (atomicmemory) | TypeScript | ~250 ⭐ |
| sage-wiki (xoai) | Go | ~276 ⭐ |
| obsidian-wiki (Ar9av) | Python | ~219 ⭐ |
| llm-wiki-skill (sdyckjq-lab) | Shell | ~366 ⭐ |

### 3.1 `nvk/llm-wiki` en detalle

Es el referente arquitectónico más completo y vale la pena leerlo antes de diseñar
nada. Modelo **hub-and-spoke**: un hub liviano (`~/wiki/`) con un registro, y
sub-wikis por tema bajo `topics/`, cada uno con su `raw/` inmutable, su `wiki/`
compilado y su `output/`. El hub no tiene contenido propio; todo vive en sub-wikis con
índices aislados.

El pipeline es: ingesta de fuentes → **investigación paralela multiagente** →
compilación con puntajes de confianza → consulta o generación de artefactos.

Los agentes se despachan en modos configurables: estándar (5 agentes: académico,
técnico, aplicado, noticias, contrarian), profundo (8, añade histórico, campo
adyacente, datos) y máximo (10). La investigación *dirigida por tesis* filtra agentes
por criterios de falsación para evitar el crecimiento indiscriminado del wiki.

Comandos: `/wiki:research`, `/wiki:thesis`, `/wiki:collect`, `/wiki:query`,
`/wiki:ingest`, `/wiki:output`.

Dos elementos poco comunes y relevantes para un proyecto académico: **captura de
sesión** (checkpoints redactados para rehidratar contexto) y **curaduría de feedback**
(correcciones y aprobaciones revisables bajo `.sessions/feedback/`). Esa segunda pieza
es la única infraestructura de *human-in-the-loop* explícita del panorama.

---

## 4. La línea académica: generación de artículos tipo wiki

Aquí sí hay literatura revisada por pares, anterior al patrón de Karpathy, y es la
que da respaldo bibliográfico al proyecto.

**STORM** (Stanford OVAL, [arXiv:2402.14207](https://arxiv.org/abs/2402.14207),
febrero de 2024) — *Synthesis of Topic Outlines through Retrieval and Multi-perspective
Question Asking*. Genera artículos largos tipo Wikipedia desde cero. Cuatro módulos:
curaduría de conocimiento, generación de esquema, generación del artículo y pulido.
Su aporte metodológico es atacar la **etapa de preescritura**: simula conversaciones
guiadas por perspectivas (varios expertos LLM haciendo preguntas distintas) y luego
aplica RAG dirigido por esquema. Frente a una línea base de RAG con esquema, sus
artículos resultan mejor organizados (+25 puntos absolutos) y con más cobertura (+10).
Los editores de Wikipedia consultados lo consideran útil en preescritura, no
publicable sin edición.

**Co-STORM** añade un protocolo de discurso colaborativo con gestión de turnos entre
expertos LLM, un moderador y el humano, más un **mapa mental dinámico** que organiza
la información en una jerarquía de conceptos para construir un espacio conceptual
compartido. Es el antecedente directo de cualquier diseño de WikiLLM con humano en el
bucle.

Instalación: `pip install knowledge-storm`. Soporta múltiples recuperadores (Bing,
Tavily, Brave, SearXNG, DuckDuckGo, VectorRM, Azure AI Search) y cualquier modelo vía
litellm, con asignación de modelos distintos por etapa para optimizar costo/calidad.
Esto último es directamente reutilizable como diseño experimental.

**WikiChat** (Stanford OVAL, EMNLP Findings 2023,
[arXiv:2305.14292](https://arxiv.org/abs/2305.14292)) — Semnani, Yao, Zhang y Lam.
Ataca la alucinación anclando en Wikipedia: genera una respuesta con el LLM, **retiene
solo los hechos fundamentados**, y los combina con información recuperada del corpus.
Reporta 97,3 % de precisión factual en conversaciones simuladas, con una metodología
de evaluación híbrida humano-LLM que es en sí misma un aporte reutilizable.

**WikiAutoGen** (ICCV 2025) — extiende la generación de artículos estilo Wikipedia al
caso multimodal.

**GraphRAG** (Microsoft Research, 2024) — la arquitectura de referencia para combinar
LLMs con grafos de conocimiento: construye el grafo desde texto no estructurado,
aplica detección de comunidades, genera resúmenes por comunidad y responde tanto a
nivel de entidad como de corpus. Es el competidor conceptual más serio del WikiLLM,
porque resuelve el mismo problema (síntesis global precomputada) con estructura
explícita en lugar de prosa.

---

## 5. RAG, GraphRAG y wiki: qué gana cada uno

La evaluación sistemática de Han et al. ([arXiv:2502.11371](https://arxiv.org/abs/2502.11371),
febrero de 2025, revisada en marzo de 2026) establece un protocolo unificado —misma
preparación de datos, misma configuración de recuperación y generación— y concluye que
**ninguno gana de forma absoluta**: las ventajas dependen de la tarea, y las
estrategias que combinan elementos de ambos rinden consistentemente mejor.

El desglose empírico reportado:

- Recuperación factual simple: fragmentos de texto y grafos rinden igual.
- Razonamiento complejo / multi-salto: los grafos aventajan por ~10 puntos.
- Resumen contextual y *global sensemaking*: ventaja de ~13 puntos para grafos.
- RAG vectorial gana en preguntas de un solo salto y orientadas al detalle.

El patrón dominante en producción durante 2025–2026 es **híbrido**: búsqueda vectorial,
recorrido de grafo y consulta SQL detrás de un enrutador de consultas.

Limitaciones documentadas de GraphRAG: construcción de grafo incompleta o ruidosa,
sobrecarga de cómputo y almacenamiento, y artefactos de evaluación como efectos de
posición en el LLM-como-juez para resumen.

**Implicación para el proyecto:** el WikiLLM ocupa una posición intermedia poco
caracterizada —estructura en prosa enlazada, no en tripletas— y esa caracterización
empírica *no existe todavía en la literatura*. Es una oportunidad concreta.

---

## 6. El problema difícil: mantener el wiki

Compilar una vez es fácil. Mantener coherente un corpus que crece es el problema real,
y donde converge la investigación reciente de memoria agéntica.

### 6.1 Memoria de agentes

| Sistema | Arquitectura | Nota |
|---|---|---|
| **MemGPT / Letta** | Inspirado en sistemas operativos: la ventana de contexto es memoria de trabajo, el almacenamiento externo es archivo, con operaciones explícitas de lectura y escritura entre niveles | El puente conceptual más directo con el patrón wiki |
| **Mem0** | Pipeline extraer–almacenar–recuperar | ECAI 2025; primera comparación amplia de diez enfoques sobre LoCoMo |
| **Zep** | Híbrido vector + grafo | Orientado a sesiones de larga duración |
| **A-Mem** | Notas estructuradas estilo **Zettelkasten**, enlazadas a memorias históricas, con red que evoluciona | Es, esencialmente, un WikiLLM con otro nombre — comparación obligada |
| **Memori** | Capa de memoria persistente ([arXiv:2603.19935](https://arxiv.org/pdf/2603.19935)) | |

Resultados sobre LoCoMo reportados en 2026: Memori 81,95 %, Zep 79,09 %, LangMem
78,05 %, Mem0 62,47 %. En abril de 2026 Mem0 publicó un algoritmo más eficiente en
tokens con +29,6 puntos en consultas temporales y +23,1 en razonamiento multi-salto.

Advertencia metodológica: estos números provienen en buena parte de blogs de los
propios proveedores. Se citan como señal del estado del campo, no como evidencia.

### 6.2 Consistencia, contradicción y obsolescencia

Esta es la línea más fértil para un proyecto académico porque el `lint` del gist está
enunciado pero no resuelto.

- **BeliefShift** ([arXiv:2603.23848](https://arxiv.org/abs/2603.23848), Myakala,
  Agrawal y Manche, marzo de 2026). Benchmark longitudinal de dinámica de creencias en
  interacción multisesión. Tres pistas: consistencia temporal de creencias, detección
  de contradicciones y revisión guiada por evidencia. 2.400 trayectorias anotadas por
  humanos en salud, política, valores y preferencias. Prueba siete modelos y encuentra
  una tensión de fondo: *los modelos que personalizan agresivamente resisten mal la
  deriva, y los muy anclados factualmente omiten actualizaciones legítimas de creencia.*
  Propone cuatro métricas —Belief Revision Accuracy, Drift Coherence Score,
  Contradiction Resolution Rate, Evidence Sensitivity Index— **directamente adaptables
  a la evaluación de un WikiLLM**.
- **STALE** ([arXiv:2605.06527](https://arxiv.org/pdf/2605.06527)) — ¿saben los agentes
  cuándo sus memorias dejaron de ser válidas? 400 escenarios de conflicto validados por
  expertos, 1.200 consultas.
- **TOKI** ([arXiv:2606.06240](https://arxiv.org/pdf/2606.06240)) — álgebra de
  operadores bitemporal para resolución de contradicciones en memoria persistente.
- **NeuSymMS** ([arXiv:2605.17596](https://arxiv.org/html/2605.17596v1)) — memoria
  neuro-simbólica híbrida: el LLM entiende lenguaje natural, pero la detección de
  contradicciones se resuelve de forma determinista, con *truth maintenance* automático
  que retracta hechos obsoletos.
- **Contradiction Detection in RAG** ([arXiv:2504.00180](https://arxiv.org/abs/2504.00180))
  — LLMs como validadores de contexto.
- **Fundamental Problems With Model Editing** ([arXiv:2406.19354](https://arxiv.org/pdf/2406.19354))
  — cómo *debería* funcionar la revisión racional de creencias en LLMs.
- **MemConflict** ([arXiv:2605.20926](https://arxiv.org/pdf/2605.20926)) y
  **MemSyco-Bench** ([arXiv:2607.01071](https://arxiv.org/pdf/2607.01071), sicofancia en
  memoria de agentes).

### 6.3 Por qué esto importa: el argumento de la deriva semántica

Formulado en el contexto empresarial pero general: cuando fragmentos de significado
viven dentro de cada agente y hay diez agentes, la organización ha hecho diez copias
privadas de sí misma, y las copias derivan. La recuperación no arregla el problema de
mantenimiento: un buscador semántico apuntado a una base obsoleta devuelve respuestas
redactadas con confianza a partir de documentos que dejaron de ser ciertos.

El WikiLLM es una apuesta a que una sola copia mantenida activamente es mejor que N
copias derivando. **Esa apuesta no está validada empíricamente.** Ese es el hueco.

---

## 7. Contexto: por qué el patrón aparece justo ahora

**Context rot** se consolidó como el problema de producción definitorio de los agentes
de larga duración en 2026: un agente falla no cuando se llena la ventana de contexto,
sino porque un contexto más largo hace que el modelo razone peor, aun con espacio de
sobra.

Pero hay un contrapunto empírico importante y contraintuitivo: **bajo prompt caching
moderno, conservar el historial completo superó a toda estrategia de compactación
probada, simultáneamente en costo, latencia y recuerdo.** Resumir reescribe el prefijo
cacheado, así que se paga el recómputo completo de lo que se intentaba ahorrar. La
recomendación resultante es que la compactación sea *condicional* —respuesta a una
restricción nombrada: una ventana que no cabe, un precio de entrada cacheada por encima
de ~0,55 USD por millón de tokens, o degradación de calidad medida— y no un default.

Esto se traslada casi literalmente al WikiLLM y merece ser una hipótesis explícita del
proyecto: **¿bajo qué condiciones la compilación anticipada gana sobre recuperar y
sintetizar en el momento?** Los ejes candidatos son la razón entre número de consultas
y número de fuentes, la tasa de cambio del corpus y el costo de la inferencia.

Riesgo adicional documentado: *Governance Decay*
([arXiv:2606.22528](https://arxiv.org/pdf/2606.22528)) muestra cómo la compactación de
contexto borra silenciosamente restricciones de seguridad en agentes de horizonte
largo. El análogo en un WikiLLM es la pérdida de matices y salvedades tras varias
rondas de reescritura de una misma página. Es medible.

---

## 8. Evaluación: qué existe y qué falta

**Datasets y benchmarks aplicables.**

- **FreshWiki** — 100 artículos de Wikipedia de alta calidad y edición frecuente
  (febrero de 2022 a septiembre de 2023). Evalúa esquema (preescritura) y artículo
  completo contra ground truth, con rúbrica de 5 puntos sobre: nivel de interés,
  coherencia y organización, relevancia y foco, cobertura, y verificabilidad.
- **WildSeek** — pares tema-objetivo de búsqueda web real, submuestreados por diversidad
  y calidad; sirve para estudiar comportamiento complejo de búsqueda de información.
- **LoCoMo** — el estándar de facto para memoria conversacional de largo plazo.
- **DeepScholar-Bench** ([arXiv:2508.20033](https://arxiv.org/html/2508.20033v1)) —
  benchmark vivo con evaluación automatizada de síntesis investigativa.
- **ResearchRubrics** (OpenReview) — 2.500+ rúbricas de grano fino escritas por expertos
  para agentes de investigación profunda: fundamentación factual, solidez del
  razonamiento, claridad.
- **HalluLens** ([arXiv:2504.17550](https://arxiv.org/pdf/2504.17550)) — alucinación.
- **GraphRAG-Bench** (ICLR 2026).

**Lo que ninguno mide.** Todos evalúan un artefacto *generado una vez*. Ninguno evalúa
la propiedad definitoria del WikiLLM: **cómo se degrada o mejora un corpus mantenido a
lo largo de N ingestas sucesivas.** No existe, hasta donde llega esta revisión, un
benchmark de mantenimiento incremental de bases de conocimiento generadas por LLM.

Construirlo —aunque sea a escala modesta— sería una contribución real.

---

## 9. Infraestructura y frameworks

- **MCP (Model Context Protocol)** — estándar ampliamente adoptado en 2026 para
  interfaces unificadas entre modelos y sistemas de conocimiento. Hay servidores MCP
  para Notion, Confluence y bases de memoria; ver
  [awesome-mcp-servers](https://github.com/TensorBlock/awesome-mcp-servers/blob/main/docs/knowledge-management--memory.md).
  Es la vía natural para conectar el agente a fuentes sin acoplarlo a ellas.
- **A2A (Agent-to-Agent, Google)** — especificación abierta para que agentes de
  distintos proveedores se deleguen tareas.
- **litellm** — abstracción sobre proveedores de modelos; permite asignar modelos
  distintos por etapa del pipeline. Clave para experimentos de costo/calidad.
- **Obsidian + Dataview** — capa de visualización y consulta sobre el markdown, sin
  lock-in. El formato dual `[[wikilink]]` + markdown es la convención de compatibilidad.
- **Runtimes de agente** — Claude Code, Codex, OpenCode, Gemini CLI. Las
  implementaciones existentes se distribuyen como *skills* o plugins de estos runtimes,
  no como aplicaciones autónomas. Decisión de diseño a tomar conscientemente: acoplarse
  a un runtime acelera el desarrollo pero compromete la reproducibilidad experimental.
- **Plataformas empresariales** — Glean (100+ aplicaciones en una capa de búsqueda
  consciente de permisos), Neo4j como capa de conocimiento. Relevantes como estado del
  arte industrial y como fuente de requisitos realistas (permisos, auditoría).

---

## 10. Vacíos de investigación

Cinco huecos identificados en esta revisión, ordenados por viabilidad para un proyecto
de un semestre:

1. **No hay evaluación del mantenimiento incremental.** Toda la evaluación existente es
   de generación única. Nadie mide qué le pasa a un wiki tras 50 ingestas.
2. **La operación `lint` está enunciada, no resuelta.** Detectar contradicciones,
   obsolescencia y huérfanos está listado como tarea del agente sin ninguna
   especificación de cómo hacerlo bien ni de cómo saber si funcionó.
3. **La frontera económica no está caracterizada.** Nadie ha determinado el punto de
   equilibrio entre compilar por adelantado y recuperar en el momento, en función de
   consultas/fuentes, volatilidad del corpus y precio de inferencia.
4. **La propagación de errores no está medida.** Si la ingesta 3 introduce un error de
   síntesis, ¿sobrevive hasta la ingesta 30? ¿Lo corrige alguna pasada de lint? Es el
   riesgo estructural del patrón y no hay datos.
5. **El diseño del human-in-the-loop es folclore.** El gist dice "el humano revisa antes
   de escribir"; nadie ha medido cuánta revisión hace falta ni dónde colocarla para
   maximizar calidad por minuto de atención humana.

---

## 11. Propuesta de encuadre para el proyecto

Esta sección es interpretación propia, no revisión bibliográfica. Es un punto de
partida para discutir con el docente, no una decisión tomada.

### 11.1 Pregunta de investigación recomendada

Elegir **una**. La 1 y la 2 son las más defendibles en un semestre.

**RQ1 — Degradación bajo mantenimiento.** ¿Cómo evoluciona la calidad de un WikiLLM
(cobertura, consistencia interna, fundamentación en fuentes) a lo largo de N ingestas
incrementales, y qué políticas de mantenimiento la preservan mejor?
*Contribución:* el primer benchmark de mantenimiento incremental. Ataca el vacío 1 y 4.

**RQ2 — Lint como tarea evaluable.** Formalizar la detección de contradicciones y
obsolescencia dentro de un wiki como tarea con ground truth, y comparar enfoques:
LLM puro, neuro-simbólico al estilo NeuSymMS, y comprobación bitemporal al estilo TOKI.
*Contribución:* convierte una operación folclórica en una tarea medible. Vacío 2.

**RQ3 — Frontera compilar vs. recuperar.** ¿Bajo qué régimen de consultas/fuentes,
volatilidad y costo, el WikiLLM supera a RAG y a GraphRAG?
*Contribución:* la caracterización empírica ausente en §5. Vacío 3. Más costosa en
cómputo.

### 11.2 Diseño experimental sugerido para RQ1

**Corpus.** Elegir un dominio con volatilidad real y verdad verificable. Wikipedia por
sí sola sesga a favor del sistema (los modelos ya la memorizaron). Alternativas mejores:
un dominio técnico con documentación versionada, o —aprovechando trabajo previo— un
corpus de fuentes sobre un evento en desarrollo, donde las contradicciones y la
obsolescencia son naturales y fechables.

**Protocolo.** Ordenar las fuentes cronológicamente. Ingerirlas de a una. Tras cada
ingesta, congelar un snapshot del wiki. Medir sobre cada snapshot.

**Métricas.** Adaptadas de FreshWiki y BeliefShift:

- *Cobertura* — proporción de hechos del gold set presentes y correctos.
- *Consistencia interna* — pares de afirmaciones contradictorias entre páginas. Requiere
  un detector; la calidad del detector es parte del trabajo.
- *Fundamentación* — proporción de afirmaciones rastreables a una fuente en `raw/`.
- *Tasa de resolución de contradicciones* (de BeliefShift) — cuando una fuente nueva
  contradice al wiki, ¿se actualiza?
- *Supervivencia del error* — se inyectan errores controlados en una ingesta y se mide
  cuántas ingestas después siguen presentes.
- *Costo* — tokens por ingesta y por consulta, contra la línea base RAG.

**Líneas base.** RAG vectorial simple, RAG con esquema, y GraphRAG. STORM como
referencia de generación de una sola pasada.

**Ablaciones.** Sin lint / lint cada N ingestas / lint cada ingesta. Sin humano / humano
solo aprobando / humano corrigiendo. Con y sin las páginas de análisis.

### 11.3 Arquitectura mínima

Construir el sistema **fuera** de un runtime de agente cerrado. Un pipeline propio en
Python con litellm da control sobre semillas, temperatura y contabilidad de tokens
—condiciones de reproducibilidad que un plugin de Claude Code no ofrece. Reusar el
*diseño* de `nvk/llm-wiki` y del gist; no reusar su acoplamiento al runtime.

```
ingesta → extracción de afirmaciones (con procedencia) → resolución de entidades
        → actualización de páginas → lint → snapshot versionado en git
```

Versionar cada snapshot en git es gratis y convierte el historial en el dataset del
experimento. Es la decisión de infraestructura más rentable del proyecto.

### 11.4 Alcance realista

Un semestre no alcanza para RQ1 completa con corpus grande. Recorte defendible: un solo
dominio, 30–50 fuentes, tres políticas de mantenimiento, dos líneas base. La
contribución es el protocolo y el primer conjunto de mediciones, no una respuesta
definitiva.

---

## 12. Fuentes

**Trabajo seminal y patrón**
- [Karpathy, A. — llm-wiki (gist, 4 de abril de 2026)](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
- [nvk/llm-wiki](https://github.com/nvk/llm-wiki)
- [lucasastorian/llmwiki](https://github.com/lucasastorian/llmwiki) · [Astro-Han/karpathy-llm-wiki](https://github.com/Astro-Han/karpathy-llm-wiki)

**Generación de artículos tipo wiki**
- [Shao et al. — Assisting in Writing Wikipedia-like Articles From Scratch with LLMs (STORM), arXiv:2402.14207](https://arxiv.org/abs/2402.14207) · [repo](https://github.com/stanford-oval/storm) · [proyecto](https://storm-project.stanford.edu/research/storm/)
- [Semnani et al. — WikiChat, EMNLP Findings 2023, arXiv:2305.14292](https://arxiv.org/abs/2305.14292) · [repo](https://github.com/stanford-oval/WikiChat)
- [Yang et al. — WikiAutoGen, ICCV 2025](https://openaccess.thecvf.com/content/ICCV2025/papers/Yang_WikiAutoGen_Towards_Multi-Modal_Wikipedia-Style_Article_Generation_ICCV_2025_paper.pdf)

**RAG, GraphRAG y comparaciones**
- [Han et al. — RAG vs. GraphRAG: A Systematic Evaluation and Key Insights, arXiv:2502.11371](https://arxiv.org/abs/2502.11371)
- [VentureBeat — Stop graphing everything: when GraphRAG actually beats vector RAG](https://venturebeat.com/orchestration/stop-graphing-everything-when-graphrag-actually-beats-vector-rag)

**Memoria de agentes, consistencia y revisión de creencias**
- [Myakala, Agrawal y Manche — BeliefShift, arXiv:2603.23848](https://arxiv.org/abs/2603.23848)
- [STALE, arXiv:2605.06527](https://arxiv.org/pdf/2605.06527) · [TOKI, arXiv:2606.06240](https://arxiv.org/pdf/2606.06240) · [NeuSymMS, arXiv:2605.17596](https://arxiv.org/html/2605.17596v1)
- [MemConflict, arXiv:2605.20926](https://arxiv.org/pdf/2605.20926) · [MemSyco-Bench, arXiv:2607.01071](https://arxiv.org/pdf/2607.01071) · [Memori, arXiv:2603.19935](https://arxiv.org/pdf/2603.19935)
- [Contradiction Detection in RAG Systems, arXiv:2504.00180](https://arxiv.org/abs/2504.00180)
- [Fundamental Problems With Model Editing, arXiv:2406.19354](https://arxiv.org/pdf/2406.19354)
- [Memory in the Age of AI Agents, arXiv:2512.13564](https://arxiv.org/pdf/2512.13564)
- [Always-On Agents: A Survey of Persistent Memory, State, and Governance, arXiv:2606.30306](https://arxiv.org/pdf/2606.30306)

**Contexto e ingeniería de contexto**
- [Bouchard, L. — Context Engineering in 2026: Why We Stopped Compacting Our Agent's Context](https://www.louisbouchard.ai/context-engineering-2026/)
- [Governance Decay, arXiv:2606.22528](https://arxiv.org/pdf/2606.22528) · [Self-Compacting Language Model Agents, arXiv:2606.23525](https://arxiv.org/pdf/2606.23525) · [Parallel Context Compaction, arXiv:2605.23296](https://arxiv.org/pdf/2605.23296)

**Evaluación**
- [DeepScholar-Bench, arXiv:2508.20033](https://arxiv.org/html/2508.20033v1) · [HalluLens, arXiv:2504.17550](https://arxiv.org/pdf/2504.17550) · [ResearchRubrics, OpenReview](https://openreview.net/forum?id=ErnvfmSX0P)

**Infraestructura y panorama industrial**
- [awesome-mcp-servers: knowledge management & memory](https://github.com/TensorBlock/awesome-mcp-servers/blob/main/docs/knowledge-management--memory.md)
- [Neo4j — The knowledge layer for enterprise AI](https://neo4j.com/blog/agentic-ai/enterprise-knowledge-layer/)
- [Falconer — The enterprise LLM wiki: scaling Karpathy's pattern to your org](https://falconer.com/guides/enterprise-llm-wiki-karpathy/)

**Literatura gris consultada** (útil para panorama, no citable como evidencia)
- [DataCamp — LLM Wiki](https://www.datacamp.com/blog/llm-wiki) · [MindStudio](https://www.mindstudio.ai/blog/what-is-llm-wiki-karpathy-knowledge-base-architecture) · [Kunal Ganglani](https://www.kunalganglani.com/blog/llm-wiki-karpathy-local-knowledge-base) · [Denser.ai](https://denser.ai/blog/llm-wiki-karpathy-knowledge-base/) · [note.com/wayne_chang](https://note.com/wayne_chang/n/nc6b1eef3fb90?hl=en)
- [Atlan — Best AI Agent Memory Frameworks 2026](https://atlan.com/know/best-ai-agent-memory-frameworks-2026/) · [Mem0 — State of AI Agent Memory 2026](https://mem0.ai/blog/state-of-ai-agent-memory-2026)

---

## Notas de verificación pendientes

Antes de citar en el documento final:

1. Confirmar conteos de estrellas y autoría de las implementaciones de §3 directamente
   en GitHub. Provienen de blogs.
2. Confirmar los números de LoCoMo de §6.1 en los papers originales, no en los blogs de
   los proveedores.
3. Verificar el estado de publicación (preprint vs. revisado por pares) de los arXiv de
   2026 citados en §6.2.
4. Localizar la referencia primaria de GraphRAG (Microsoft Research, 2024); aquí se cita
   de segunda mano.
