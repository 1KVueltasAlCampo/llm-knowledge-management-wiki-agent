# Fichas de lectura

Bibliografía anotada sobre gestión de conocimiento asistida por modelos de lenguaje:
memoria de agentes, bases de conocimiento mantenidas por LLM (patrón *LLM Wiki*),
formatos portables de conocimiento y su evaluación.

Cada ficha sigue la misma estructura:

1. Ficha rápida
2. Definición general
3. Problemas que aborda y necesidades que abre
4. Sustento tecnológico
5. Contexto de aplicación
6. Experimentos
7. Conclusiones
8. Conceptos y términos que introduce
9. Citas textuales clave
10. Relación con el patrón *LLM Wiki* y el Open Knowledge Format
11. Preguntas abiertas que deja
12. Enlace y cita APA

Cuando una sección no aplica al tipo de trabajo, se indica explícitamente.

---

## 1. MemGPT: Towards LLMs as Operating Systems

### 1.1 Ficha rápida

| | |
|---|---|
| Autores | Packer, Wooders, Lin, Fang, Patil, Stoica, Gonzalez (UC Berkeley) |
| Tipo | Artículo de investigación con evaluación empírica y código liberado |
| Publicación | arXiv:2310.08560 · v1 oct 2023 · v2 feb 2024 · sin venue formal, ampliamente citado |
| Continuación | El proyecto se renombró **Letta** (letta-ai) y sigue en desarrollo activo |
| Código | Sí — código, datasets y prompts en research.memgpt.ai (CC-BY-4.0) |

### 1.2 Definición general

MemGPT aborda la limitación de la ventana de contexto tratando al modelo como un sistema
operativo que **gestiona su propia memoria**. Divide el estado en dos niveles: *main
context* (lo que está en el prompt) y *external context* (almacenamiento fuera del
prompt), y expone al modelo funciones para mover información entre ambos —igual que un
sistema operativo pagina entre memoria física y disco—. El modelo decide qué retener,
qué archivar y cuándo buscar, mediante llamadas a funciones encadenadas.

Lo relevante del trabajo es que formaliza, con una metáfora precisa y una evaluación
concreta, el mecanismo por el cual un agente **construye y mantiene de forma autónoma
una memoria persistente**. Es el antecedente directo de las bases de conocimiento
autoeditadas por un modelo.

### 1.3 Problemas que aborda y necesidades que abre

- **Problema del artículo:** la ventana de contexto es finita, extenderla tiene costo
  cuadrático, y los modelos de contexto largo aprovechan mal el contexto adicional
  ("lost in the middle", Liu et al. 2023). Se necesita una alternativa a "escalar
  contexto".
- **Necesidad que queda abierta:** MemGPT almacena hechos en su *working context* y su
  *archival storage*, pero **no registra de dónde salió cada hecho, quién lo introdujo
  ni si sigue siendo válido**. Cuando dos fuentes se contradicen, la memoria se
  sobrescribe sin dejar rastro. La consistencia y la trazabilidad de una memoria
  autoeditada a lo largo del tiempo quedan sin resolver ni medir.

### 1.4 Sustento tecnológico

**Arquitectura:**

- *Main context* = System Instructions (solo lectura) + Working Context (lectura y
  escritura; hechos estructurados sobre el usuario o la tarea) + FIFO Queue (historial
  rodante de mensajes; el primer puesto guarda un resumen recursivo de lo desalojado).
- *External context* = Archival Storage (base general de lectura/escritura) + Recall
  Storage (historial de eventos de conversación).
- Componentes: *Queue Manager*, *Function Executor*, procesador LLM.
- **Heartbeats:** el modelo emite `request_heartbeat=true` para encadenar varias
  funciones en un mismo turno (buscar → leer → editar → detenerse).
- Los eventos disparan inferencia: mensajes del usuario, mensajes de sistema y **eventos
  programados**, que permiten al agente actuar "sin ser preguntado".
- Avisos automáticos cuando el prompt se acerca al límite de tokens, que fuerzan
  desalojo o resumen.

**Reproducibilidad:** reimplementar el diseño exige tres piezas: un almacén externo con
búsqueda que devuelva resultados paginados, un esquema de metadata para los hechos que
viven en el contexto de trabajo, y un bucle de *function calling* con encadenamiento por
heartbeat. No depende del runtime concreto (el propio proyecto migró de una
implementación a otra conservando el diseño).

### 1.5 Contexto de aplicación

TIC / ingeniería de software: IA conversacional (agentes con memoria de largo plazo) y
análisis de documentos. Demostrado sobre chat multisesión y preguntas y respuestas sobre
Wikipedia. No es un dominio vertical (no médico, no financiero); es infraestructura de
propósito general.

### 1.6 Experimentos

**Agentes conversacionales — dataset Multi-Session Chat (MSC, Xu et al.):**

- Tarea nueva *Deep Memory Retrieval* (DMR): se pregunta al agente algo respondido en
  una sesión anterior (1–5), con un rango de respuesta muy estrecho.

  | Modelo | Exactitud | ROUGE-L |
  |---|---|---|
  | GPT-3.5 Turbo | 38,7 % | 0,394 |
  | GPT-4 | 32,1 % | 0,296 |
  | GPT-4 Turbo | 35,3 % | 0,359 |
  | **GPT-4 + MemGPT** | **92,5 %** | **0,814** |

- Tarea *conversation opener* (engagement): MemGPT genera aperturas de conversación que
  recogen más facetas de la persona simulada que las escritas por un humano.

**Análisis de documentos:**

- Preguntas y respuestas sobre Wikipedia: los *baselines* de contexto fijo se degradan
  al truncar documentos; MemGPT itera la búsqueda (varias consultas al *archival
  storage*) y no está limitado por cuántos fragmentos caben en el prompt.
- Tarea nueva *nested key-value retrieval* (multi-salto sintético): GPT-3.5 no completa
  la variante anidada; GPT-4 y GPT-4 Turbo caen a 0 % de exactitud en 3 niveles de
  anidamiento; **MemGPT con GPT-4 la completa de forma consistente más allá de 2
  niveles** encadenando consultas. MemGPT+GPT-4 supera a MemGPT+GPT-4 Turbo, y
  MemGPT+GPT-3.5 se degrada notablemente: el bucle depende de la capacidad de *function
  calling* del modelo base.
- Método de evaluación reutilizable: pares pregunta-respuesta generados por otro LLM con
  rango de respuesta estrecho, más un juez LLM con rúbrica binaria CORRECT/INCORRECT.

### 1.7 Conclusiones

Técnicas de sistema operativo —jerarquía de memoria e interrupciones— permiten
aprovechar el potencial del modelo sin agrandar la ventana de contexto. El aporte
central es la **memoria jerárquica por niveles usando un LLM de contexto largo como
"memoria principal"**. Los autores señalan como trabajo futuro: otros dominios de
contexto ilimitado, integrar otras tecnologías de almacenamiento (bases de datos,
cachés) y **mejorar las políticas de gestión de memoria**.

### 1.8 Conceptos y términos que introduce

`virtual context management` · `main context` / `external context` · `working context`
· `FIFO queue` con resumen recursivo · `archival storage` / `recall storage` ·
`heartbeat` (encadenamiento de funciones) · `queue manager` · tarea `Deep Memory
Retrieval (DMR)` · tarea `nested key-value retrieval`.

### 1.9 Citas textuales clave

> "we propose virtual context management, a technique drawing inspiration from
> hierarchical memory systems in traditional operating systems which provide the
> illusion of an extended virtual memory via paging between physical memory and disk."
> — §Abstract

> "Using function calls, LLM agents can read and write to external data sources, modify
> their own context, and choose when to return responses to the user." — §1

### 1.10 Relación con el patrón *LLM Wiki* y el Open Knowledge Format

MemGPT describe **cómo** un agente mantiene una memoria persistente; el patrón *LLM
Wiki* de Karpathy describe el mismo mecanismo pero como paso de compilación en lugar de
en tiempo de consulta; el Open Knowledge Format describe **con qué metadata** debería
registrarse esa memoria (procedencia, autoría, verificación). Las tres líneas convergen
en la misma operación. Ninguna, MemGPT incluido, evalúa si la base así mantenida sigue
siendo fiel a sus fuentes después de sucesivas ediciones: sus tareas (DMR, nested-KV)
miden *recuperación* dentro de la memoria, no *conservación* a lo largo del
mantenimiento.

### 1.11 Preguntas abiertas que deja

1. ¿Cuánto se degrada una memoria autoeditada cuando el modelo base es más débil? (se
   observa con GPT-3.5 pero no se cuantifica de forma sistemática).
2. ¿Qué política de desalojo y resumen preserva mejor la información? (trabajo futuro
   explícito de los autores).
3. ¿Cómo se comporta el sistema cuando las fuentes se contradicen entre sí? (no se
   prueba).

### 1.12 Enlace y cita APA

- Artículo: https://arxiv.org/abs/2310.08560 · PDF: https://arxiv.org/pdf/2310.08560
- Código y sucesor: https://github.com/letta-ai/letta

> Packer, C., Wooders, S., Lin, K., Fang, V., Patil, S. G., Stoica, I., & Gonzalez,
> J. E. (2023). *MemGPT: Towards LLMs as operating systems* (arXiv:2310.08560). arXiv.
> https://arxiv.org/abs/2310.08560

> Letta AI. (2024). *Letta (formerly MemGPT)* [Software]. GitHub.
> https://github.com/letta-ai/letta

---

## 2. Knowledge-Centric Information Systems

*Generalizing Data Engineering Principles for Executable Organizational Knowledge*

### 2.1 Ficha rápida

| | |
|---|---|
| Autor | Mariano Garralda‑Barrio (investigador independiente, Lleida, España; agradece al L2IA — Minsait / Indra) |
| Tipo | Artículo de visión / posición — sin experimentos, sin revisión por pares |
| Publicación | arXiv:2607.02609v1 [cs.SE] · 1 jul 2026 · 10 páginas, 3 figuras, 2 tablas |
| Continuación | Dos artículos hermanos del mismo autor sobre runtimes de agentes (arXiv:2605.27328, arXiv:2606.23797) |
| Código | No aplica |

### 2.2 Definición general

Sostiene que la ingeniería de datos pasó décadas construyendo garantías arquitectónicas
para los datos —integración, gobierno, validación, catálogo, servicio— y que los modelos
de lenguaje no eliminan esas preocupaciones sino que las amplían. Propone una disciplina,
**"knowledge architecture"**, y ofrece un modelo conceptual y una taxonomía que traduce
cada garantía clásica de datos a su versión para *artefactos de conocimiento*.

Lo relevante del trabajo es que ordena bajo un mismo marco fenómenos que hoy se tratan
por separado (formatos de conocimiento, grafos, memoria de agentes, RAG), sitúa la
**procedencia** como preocupación de primera clase y afirma explícitamente que **RAG es
una técnica de servicio, no una arquitectura completa**.

### 2.3 Problemas que aborda y necesidades que abre

- **Problema del artículo:** cuando el conocimiento organizacional se vuelve "ejecutable"
  —lo consumen agentes, flujos y modelos para actuar— hace falta gobernarlo con el mismo
  rigor que una plataforma de datos. Hoy se ataca por partes, sin arquitectura.
- **Necesidad que queda abierta:** su agenda de investigación (§12) enuncia, entre
  otras, *"¿cómo pueden las organizaciones medir la fiabilidad, frescura, cobertura y
  utilidad de las arquitecturas de conocimiento?"*. La evaluación de estas bases de
  conocimiento mantenidas es un hueco declarado.

### 2.4 Sustento tecnológico

**(No aplica.)** Es un artículo de visión: no presenta implementación ni código. Su
contribución operativa es una taxonomía que traduce cada garantía de la ingeniería de
datos a su equivalente para artefactos de conocimiento:

| Garantía de datos | Versión de conocimiento | Qué cambia |
|---|---|---|
| ETL | Ingestión de conocimiento | parsear, enlazar, resumir, enriquecer **sin perder significado ni evidencia** |
| CDC (captura de cambios) | Detección de cambio de conocimiento | el cambio puede ser semántico: una política, una autoridad o un procedimiento cambia aunque la estructura no |
| Linaje | **Procedencia** | rastrear fuentes, extracción, síntesis mediada por modelo, aprobación humana, ensamblaje en runtime |
| Catálogos | Catálogos de conocimiento | el descubrimiento debe incluir "aptitud para la acción" |
| Vistas materializadas | Vistas de conocimiento | *bundles* de contexto por tarea, proyecciones legibles por agentes |
| Arquitectura medallón (bronce/plata/oro) | Capas *raw – curated – operational* | la transformación incluye resumen, enlace semántico, anotación de políticas |
| CQRS | Separación lectura/escritura de conocimiento | separar autoría y curaduría del consumo en runtime |
| Calidad | Calidad de conocimiento | frescura, consistencia, *grounding*, **gestión de contradicciones**, seguridad para actuar |
| Gobierno | Gobierno de conocimiento | quién puede crear, aprobar, activar o exponer conocimiento a agentes |

### 2.5 Contexto de aplicación

Empresa en general: manuales, decisiones de diseño, tickets, contratos, código,
especificaciones de API, métricas, historiales de chat, *runbooks*. Cita señales
industriales concretas: GitHub Copilot Workspace, Microsoft Copilot Studio (fuentes de
conocimiento para agentes) y Google Cloud (Open Knowledge Format y Knowledge Catalog).
No es un dominio vertical.

### 2.6 Experimentos

**(No aplica.)** El artículo no presenta experimentos. Su evidencia es conceptual —la
recurrencia de las garantías clásicas bajo semántica nueva— más las señales industriales
de convergencia (§7). Debe citarse como marco, no como evidencia empírica.

### 2.7 Conclusiones

Los datos siguen siendo esenciales, pero el conocimiento se está convirtiendo en el
siguiente activo arquitectónico. Las garantías de la ingeniería de datos no desaparecen:
deben "elevarse" a una unidad de gestión nueva, el *knowledge artifact*. El patrón *LLM
Wiki* y el Open Knowledge Format son síntomas y aceleradores del cambio, no el cambio:
*"si OKF o cualquier estándar sucesor desapareciera, el problema de fondo seguiría
ahí"*.

### 2.8 Conceptos y términos que introduce

`knowledge architecture` · `executable organizational knowledge` (Def. 1) · `knowledge
artifact` como unidad de gestión · `unit shift` (de registro a artefacto) · `knowledge
ingestion / change detection / provenance / views / governance` · capas
*raw–curated–operational* · `knowledge read/write split` (CQRS de conocimiento).

### 2.9 Citas textuales clave

> "lineage becomes provenance, catalogs become knowledge catalogs, materialized views
> become knowledge views, and medallion architectures become raw–curated–operational
> knowledge layers." — §Abstract

> "knowledge architecture should not be reduced to retrieval-augmented generation. RAG
> is a serving technique, not a complete architecture." — §11

> "Provenance must trace sources, extraction, synthesis, human approval, and runtime
> assembly into context. Provenance becomes especially important when large language
> models synthesize new artifacts from existing ones, because synthesized knowledge can
> obscure its evidential basis." — §9.4

### 2.10 Relación con el patrón *LLM Wiki* y el Open Knowledge Format

El artículo es el marco que ordena ambos. Sitúa al Open Knowledge Format en la capa de
representación e interoperabilidad, y al patrón *LLM Wiki* como una base de conocimiento
mantenible que los agentes leen y actualizan; los trata como "evidencia temprana de una
transición, no como su punto final". Deja claro que la representación es **una** capa de
la arquitectura, no toda: la sincronización semántica, la procedencia a través de la
síntesis, el gobierno, la calidad y la evaluación quedan fuera de lo que un formato
resuelve por sí solo.

### 2.11 Preguntas abiertas que deja (§12)

1. *Representación:* ¿qué metadata mínima y qué modelo de relaciones hacen
   interoperables a los artefactos de conocimiento?
2. *Sincronización:* ¿cómo se detecta la deriva semántica entre documentos, código,
   interfaces y bases de datos?
3. *Procedencia:* ¿cómo preserva la evidencia y la responsabilidad el conocimiento
   sintetizado?
4. *Calidad:* ¿qué métricas determinan si un artefacto de conocimiento es apto para uso
   operativo?
5. *Evaluación:* ¿cómo medir la fiabilidad, la frescura, la cobertura y la utilidad de
   una arquitectura de conocimiento?

### 2.12 Enlace y cita APA

- Artículo: https://arxiv.org/abs/2607.02609 · PDF: https://arxiv.org/pdf/2607.02609

> Garralda‑Barrio, M. (2026). *Knowledge-centric information systems: Generalizing data
> engineering principles for executable organizational knowledge* (arXiv:2607.02609).
> arXiv. https://arxiv.org/abs/2607.02609

---

## 3. Open Knowledge Format (OKF)

### 3.1 Ficha rápida

| | |
|---|---|
| Origen | Google Cloud — anuncio por Sam McVeety y Amir Hormati; especificación abierta y versionada |
| Tipo | Especificación técnica + implementaciones de referencia. No es artículo académico; sin revisión por pares |
| Publicación | v0.1 anunciada el 12 jun 2026 (Google Cloud Blog); **v0.2 vigente** en el repo canónico `GoogleCloudPlatform/open-knowledge-format` |
| Continuación | Versionada y "explícitamente diseñada para crecer con compatibilidad hacia atrás" |
| Código | Sí — agente de enriquecimiento de referencia, visualizador HTML autocontenido, cuatro *bundles* de ejemplo |

### 3.2 Definición general

OKF formaliza el patrón *LLM Wiki* en un formato portable e interoperable: un directorio
de archivos markdown con *frontmatter* YAML y un conjunto mínimo de convenciones
acordadas, de modo que wikis escritas por distintos productores puedan ser consumidas
por distintos agentes **sin capa de traducción**. No hay runtime, ni SDK, ni esquema
central obligatorio.

Lo relevante del trabajo es doble: es el primer intento con respaldo industrial de
estandarizar la *representación* del conocimiento para agentes, y en v0.2 eleva
**procedencia, confianza y frescura a campos consultables del frontmatter** —los
metadatos que una base mantenida por un agente necesita para seguir siendo fiable sin
un runtime a medida—.

### 3.3 Problemas que aborda y necesidades que abre

- **Problema:** en la mayoría de organizaciones el conocimiento que consumen los
  modelos es interno y vive fragmentado en sistemas mutuamente incompatibles —catálogos
  con su propia API, wikis, comentarios de código, la cabeza de unos pocos ingenieros
  senior—. Cada constructor de agentes resuelve el mismo problema de ensamblaje de
  contexto desde cero; cada wiki se parece a las demás (markdown, frontmatter, enlaces)
  pero ninguna está diseñada para cooperar con otra.
- **Necesidad que queda abierta:** OKF define *"la superficie de interoperabilidad, no
  el modelo de contenido"*. Qué tipos de concepto existen, qué métricas de calidad
  aplican, cómo se detecta que una página quedó obsoleta y cómo se evalúa si el *bundle*
  sigue siendo fiel a sus fuentes: todo eso queda fuera del formato, a cargo del
  productor.

### 3.4 Sustento tecnológico

**Estructura de un *bundle*:** un directorio de archivos markdown, cada uno un
*concepto* (la ruta del archivo es su identidad). Los enlaces markdown —recomendados
relativos a la raíz del *bundle*, `/tables/customers.md`— forman un grafo dirigido más
rico que la jerarquía de carpetas.

**Nombres reservados:** `index.md` (listado del directorio, revelación progresiva) y
`log.md` (historial cronológico de cambios). Todo otro `.md` es un concepto.

**Frontmatter:**

- **Requerido:** solo `type` (cadena que identifica la clase de concepto).
- **Recomendado:** `title`, `description`, `resource` (URI del activo), `tags`.
- **Opcional:** todas las familias de procedencia, confianza, ciclo de vida y cómputo,
  más cualquier clave definida por el productor.

**Familias añadidas en v0.2 (opcionales, consultables):**

| Familia | Campos | Para qué |
|---|---|---|
| Procedencia | `sources[]` con `resource` (obligatorio por entrada) y señales opcionales `author`, `usage_count`, `last_modified`; `usage_window` | de qué materiales deriva un concepto; atribución por afirmación con notas al pie que casan con `sources[].id` |
| Confianza | `generated: {by, at}` (quién produjo el contenido y cuándo cambió por última vez); `verified: [{by, at}]` (eventos de verificación independiente) | de aquí el consumidor deriva un **nivel de confianza**: sin `verified` → *unverified*; verificado solo por actores no humanos → *machine-confirmed*; verificado por `human:<id>` → *human-reviewed* |
| Frescura | `status` (`draft` / `stable` / `deprecated`; ausente = `stable`); `stale_after` (ISO-8601) | el concepto se considera obsoleto cuando la fecha actual supera `stale_after` |

**Convención de actor:** `<productor>/<versión>` para agentes y herramientas,
`human:<id>` para personas, `process:<id>` para procesos automáticos. El consumidor
clasifica la confianza detectando el prefijo `human:`.

**`type: Attested Computation`:** concepto que empareja una definición con un método de
cómputo sancionado (`runtime`, `parameters`, `computation`, `executor` con `receipt`,
`attester`), para verificar que *"este número se produjo como dijimos"*. El agente solo
aporta valores de parámetros; nunca modifica el cómputo.

**Conformidad (§11):** un *bundle* es conforme si todo `.md` no reservado tiene
frontmatter YAML parseable con `type` no vacío, e `index.md` / `log.md` siguen su
estructura cuando existen. El consumidor **no debe** rechazar conceptos por familias
opcionales ausentes, tipos o claves desconocidos, enlaces rotos o índices faltantes.

**Implementaciones de referencia:** un agente de enriquecimiento en dos pasadas
(metadata de BigQuery, luego rastreo web de documentación autoritativa para añadir
citas, esquemas y rutas de *join*); un visualizador que convierte cualquier *bundle* en
un grafo interactivo en un único archivo HTML sin backend; y cuatro *bundles* de ejemplo
(GA4 e-commerce, Stack Overflow, Bitcoin, Acme Retail).

**Reproducibilidad:** producir OKF a mano es escribir markdown; consumirlo es leer
archivos. Un productor automático necesita recorrer una fuente, emitir un `.md` por
concepto y, opcionalmente, una segunda pasada que enriquezca con procedencia y citas.

### 3.5 Contexto de aplicación

Datos empresariales y catálogos de metadatos: el ejemplo canónico son tablas, *datasets*
y métricas de BigQuery, pero el formato es explícitamente agnóstico —*runbooks*,
*playbooks*, APIs, *notebooks*, decisiones—. Compone con herramientas que ya hablan
markdown + frontmatter (Notion, Obsidian, MkDocs, Hugo, Jekyll). No es un dominio
vertical.

### 3.6 Experimentos

**(No aplica.)** Es una especificación, no un estudio. Las implementaciones de
referencia y los cuatro *bundles* de ejemplo son pruebas de concepto declaradas
(*"These are proofs of concept, deliberately"*), no evaluaciones con métricas ni
comparación contra alternativas.

### 3.7 Conclusiones

*"El formato en sí es la contribución"*; las herramientas existen para hacerlo tangible
y bajar el costo de probarlo. v0.1 / v0.2 es un punto de partida, no un estándar
terminado: evolucionará *"a medida que colectivamente aprendamos qué representaciones
de conocimiento necesitan los agentes en la práctica"*. El valor de un formato de
conocimiento viene de cuántas partes lo hablan, no de quién lo posee.

### 3.8 Conceptos y términos que introduce

`OKF bundle` · `concepto` (un archivo = un concepto; la ruta es la identidad) ·
frontmatter requerido / recomendado / opcional · `sources` con señales de credibilidad ·
`generated` / `verified` · niveles de confianza (`unverified` / `machine-confirmed` /
`human-reviewed`) · `status` / `stale_after` · convención de actor (`human:<id>`,
`process:<id>`) · `Attested Computation` · `index.md` (revelación progresiva) /
`log.md` · *"interoperability surface, not content model"*.

### 3.9 Citas textuales clave

> "The answer to this problem isn't another knowledge service. You need a format, a way
> to represent knowledge that anyone can produce, without an SDK [and] anyone can
> consume, without an integration." — Blog, §*What's missing is a format*

> "Trust, provenance, and freshness are first-class. v0.2 puts queryable signals in
> frontmatter (…) so an agent-maintained corpus stays trustable without any bespoke
> runtime." — README del repositorio, §*Why OKF?*

> "The spec defines the interoperability surface, not the content model." — Blog,
> §*Three principles*

### 3.10 Relación con el patrón *LLM Wiki* y el Open Knowledge Format

OKF es la formalización directa del *gist* de Karpathy: toma markdown + frontmatter +
enlaces cruzados + `index.md` / `log.md` y fija el conjunto mínimo de convenciones que
los hace interoperables entre productores y consumidores distintos. Respecto de MemGPT
(runtime, memoria en tiempo de consulta), OKF cubre la persistencia y la representación.
Respecto del marco de arquitectura de conocimiento, OKF ocupa **una sola capa** —la de
representación—: no resuelve la sincronización semántica, el gobierno ni la evaluación,
y su propia documentación lo reconoce explícitamente.

### 3.11 Preguntas abiertas que deja

1. ¿Basta `type` como único campo obligatorio para lograr interoperabilidad real, o los
   consumidores terminan necesitando un vocabulario de tipos compartido?
2. ¿Cómo se detecta que un concepto quedó obsoleto más allá de un `stale_after` fijado
   a mano?
3. ¿Cómo se mide si un *bundle* mantenido por un agente sigue siendo fiel a sus fuentes?
   El formato registra la procedencia pero no define ninguna métrica de calidad.
4. ¿Cómo evolucionan los niveles de confianza cuando un mismo concepto es editado muchas
   veces por actores distintos?

### 3.12 Enlace y cita APA

- Blog: https://cloud.google.com/blog/products/data-analytics/how-the-open-knowledge-format-can-improve-data-sharing
- Especificación y repo canónico: https://github.com/GoogleCloudPlatform/open-knowledge-format
- *Snapshot* congelado de v0.1: https://github.com/GoogleCloudPlatform/knowledge-catalog/tree/main/okf

> McVeety, S., & Hormati, A. (2026, 12 de junio). *Introducing the Open Knowledge
> Format*. Google Cloud Blog.
> https://cloud.google.com/blog/products/data-analytics/how-the-open-knowledge-format-can-improve-data-sharing

> Google Cloud. (2026). *Open Knowledge Format (OKF) specification* (Versión 0.2)
> [Especificación]. GitHub. https://github.com/GoogleCloudPlatform/open-knowledge-format

---

## 4. claude-obsidian (patrón *LLM Wiki* como plugin de Claude Code)

### 4.1 Ficha rápida

| | |
|---|---|
| Origen | Repositorio open-source `AgriciDaniel/claude-obsidian`; punto de entrada: hilo divulgativo de `@SpikeCalls` en X (24 jun 2026) |
| Tipo | Implementación de referencia del patrón *LLM Wiki* + *walkthrough* de divulgación (literatura gris). Sin evaluación, sin revisión por pares |
| Publicación | Repositorio activo · licencia MIT · ≈14,8 k estrellas (el hilo citaba 6.800; ha crecido) |
| Continuación | Desarrollo activo; se apoya en *skills* oficiales de Obsidian (`kepano/obsidian-skills`) |
| Código | Sí — plugin de Claude Code + *skills*; markdown plano en un *vault* de Obsidian |

### 4.2 Definición general

Implementa el patrón de Karpathy como un plugin de Claude Code sobre un *vault* de
Obsidian. El usuario deja caer una fuente; el modelo la lee, extrae entidades y
conceptos, los enlaza de forma cruzada y los archiva en páginas markdown. Las consultas
se responden leyendo un índice y las páginas relevantes, con citas a las fuentes. Todo
el conocimiento es markdown plano en disco, sin base de datos ni backend.

Lo relevante del trabajo es que es la instancia más madura y difundida del patrón a
escala de usuario individual: muestra en concreto el bucle de operaciones (*ingest* /
*query* / *lint* / *autoresearch*) y —de forma notable— incorpora *provenance ledgers*
con atribución de fuente, frescura de la afirmación, nivel de confianza y estado de
revisión **sin usar OKF**, lo que sugiere que esas familias de metadatos reaparecen de
forma independiente cuando el patrón se lleva a la práctica.

### 4.3 Problemas que aborda y necesidades que abre

- **Problema:** las aplicaciones de notas son *"cementerios"* —cientos de notas que
  nunca se enlazan ni se vuelven a encontrar—. El trabajo de mantenimiento (enlazar,
  actualizar referencias cruzadas, marcar contradicciones) es lo que hace que los
  humanos abandonen sus wikis.
- **Necesidad que queda abierta:** las afirmaciones de valor —*"responde en 2
  segundos"*, *"en la semana 2 el grafo es una telaraña"*— son testimoniales, sin
  medición. No hay evaluación de si el *vault*, tras decenas de ingestas, sigue siendo
  coherente y fiel a las fuentes; el propio `lint` *"saca a la superficie
  contradicciones"* pero no se reporta con qué exactitud.

### 4.4 Sustento tecnológico

**Runtime:** Claude Code (agente) + Obsidian (visualización) + Python 3.11+; MCP
opcional para que el agente lea y escriba el *vault* directamente en lugar de recibir
las fuentes pegadas.

**Operaciones (*skills*):** `wiki` (inicialización y enrutado), `wiki-ingest`,
`wiki-query`, `wiki-lint`, `save` (convierte la conversación actual en nota),
`autoresearch` (investigación web autónoma en rondas), `wiki-fold`, `wiki-retrieve`,
`wiki-cli`, `canvas`, `defuddle`; *skills* de referencia `obsidian-markdown`,
`obsidian-bases`, `think`.

**Almacenamiento:** markdown con *wikilinks* + frontmatter; *provenance ledgers* que
registran atribución de fuente, frescura, confianza y estado de revisión; *content-
addressed byte capture* (la fuente se guarda direccionada por hash) y *operation
transaction bundles*. Archivos especiales: `index.md`, `hot.md` (caché de contexto
reciente que se refresca al final de cada sesión) y sub-índices por dominio. Un *ingest*
produce entre 8 y 15 páginas enlazadas; admite ingesta en lote con agentes en paralelo.

**Reproducibilidad:** es una *skill* de Claude Code; el patrón se puede reimplementar
sobre cualquier runtime de agente con acceso a archivos, un índice navegable y un bucle
*ingest* / *query* / *lint*.

### 4.5 Contexto de aplicación

Gestión de conocimiento personal (*segundo cerebro*): notas propias, artículos
clipeados, PDFs de investigación, transcripciones. También se propone como base de
conocimiento compartida entre varios proyectos de código, apuntando cada archivo de
convenciones (`CLAUDE.md`) al mismo *vault*. TIC / productividad individual; no es un
dominio vertical.

### 4.6 Experimentos

**(No aplica.)** El material es un *walkthrough* promocional. Las únicas afirmaciones
cuantitativas —"responde en 2 segundos", conteos de estrellas, la progresión "día 1 /
semana 2 / mes 2"— son testimoniales: sin protocolo, sin línea base, sin métrica.

### 4.7 Conclusiones

La tesis del autor: el cuello de botella de un wiki personal es el mantenimiento
—enlazar, actualizar referencias cruzadas, marcar contradicciones—, y eso es
exactamente lo que un modelo de lenguaje hace sin cansarse. El valor *"se compone como
interés compuesto"* con cada fuente añadida, y el usuario conserva cada byte en markdown
plano en su disco.

### 4.8 Conceptos y términos que introduce

`segundo cerebro autoorganizado` · bucle `ingest` / `query` / `lint` / `autoresearch` /
`save` · `hot cache` (`hot.md`) · `provenance ledger` · `content-addressed byte
capture` · `operation transaction bundle` · *callouts* `[!contradiction]` · modo PARA
(proyectos / áreas / recursos / archivos) · *"note apps are graveyards"*.

### 4.9 Citas textuales clave

> "Most note apps are graveyards. You dump 400 notes in, you never link them, you never
> find them again." — Hilo de `@SpikeCalls`

> "Self-organizing AI second brain for Obsidian + Claude Code. Drop any source and
> Claude reads, links, and files it into one connected knowledge graph of plain Markdown
> you own." — Descripción del repositorio

> "Run lint the wiki once a week. It surfaces contradictions as [!contradiction]
> callouts with both sources." — Hilo de `@SpikeCalls`

### 4.10 Relación con el patrón *LLM Wiki* y el Open Knowledge Format

Es una implementación directa del *gist* de Karpathy orientada a un solo usuario. **No
adopta OKF** —usa *wikilinks* de Obsidian y *callouts* nativos en lugar de la convención
de enlaces relativos a la raíz—, pero llega de forma independiente a las mismas familias
de metadatos que OKF v0.2 formaliza (procedencia, frescura, confianza, estado de
revisión). Frente a MemGPT comparte el bucle de autoedición, pero lo expone como
comandos explícitos al usuario en lugar de funciones internas del agente.

### 4.11 Preguntas abiertas que deja

1. ¿Con qué exactitud detecta el `lint` las contradicciones y las afirmaciones
   obsoletas? Se afirma que lo hace; no se mide.
2. ¿Cómo evoluciona la calidad del *vault* tras decenas o cientos de ingestas?
3. ¿Qué ocurre cuando dos fuentes fiables se contradicen: se marca, se resuelve, se
   propaga?
4. ¿El *provenance ledger* se mantiene consistente cuando el modelo reescribe una misma
   página muchas veces?

### 4.12 Enlace y cita APA

- Hilo: https://x.com/SpikeCalls/article/2069815843186176126
- Repositorio: https://github.com/AgriciDaniel/claude-obsidian

> Spike [@SpikeCalls]. (2026, 24 de junio). *Claude + Obsidian turned 400 dead notes
> into a brain that answers in 2 seconds* [Publicación]. X.
> https://x.com/SpikeCalls/article/2069815843186176126

> Agrici, D. (2026). *claude-obsidian: Self-organizing AI second brain for Obsidian +
> Claude Code* [Software]. GitHub. https://github.com/AgriciDaniel/claude-obsidian

---

## 5. The FAIR Guiding Principles for Scientific Data Management and Stewardship

### 5.1 Ficha rápida

| | |
|---|---|
| Autores | Wilkinson, M. D. et al. — 51 autores, consorcio interdisciplinario FORCE11 (bioinformática, bibliotecas, editoriales científicas) |
| Tipo | *Comment* con revisión por pares — primera publicación formal de un conjunto de principios ya trabajados en un taller previo |
| Publicación | *Scientific Data* (Nature), vol. 3, artículo 160018. Recibido 10 dic 2015 · aceptado 12 feb 2016 · publicado 15 mar 2016. DOI 10.1038/sdata.2016.18 |
| Continuación | Dio origen a un ecosistema completo (indicadores de madurez FAIR, FAIRsharing, la comunidad GO FAIR); uno de los artículos más citados de la ciencia de datos |
| Código | No aplica directamente —no es software—, pero documenta implementaciones ejemplares (Dataverse, FAIRDOM, ISA, Open PHACTS, wwPDB, UniProt) |

### 5.2 Definición general

Publica formalmente cuatro principios —*Findable*, *Accessible*, *Interoperable*,
*Reusable* (FAIR)— para la gestión y curaduría de datos científicos, con énfasis
explícito en que **las máquinas, no solo los humanos, puedan descubrir y usar los datos
de forma autónoma**. Nace de un taller en Leiden (2014, *"Jointly Designing a Data
Fairport"*) y se refina después en la comunidad FORCE11.

Lo relevante del trabajo es que es el artículo fundacional detrás de casi todo lo que
hoy se llama "metadata de calidad" o "trazabilidad de datos". Da el vocabulario preciso
—accionabilidad por máquina, identificadores persistentes, procedencia detallada,
licencia clara— para argumentar por qué un recurso de conocimiento necesita algo más
que texto bien escrito para ser confiable y reutilizable.

### 5.3 Problemas que aborda y necesidades que abre

- **Problema del artículo:** el ecosistema de publicación de datos científicos está
  fragmentado —cada repositorio tiene su propio modelo, formato y esquema de
  metadatos— sin integración entre ellos. El artículo ilustra con un caso concreto
  (un investigador que busca datos de poliadenilación diferencial sin repositorio
  especializado disponible) cuántas semanas de esfuerzo técnico se pierden reuniendo
  datos que ya existen en alguna parte. El problema no es falta de tecnología: es que no
  se cuida a los objetos digitales con la atención que merecen al crearlos y
  preservarlos.
- **Necesidad que queda abierta:** los principios son deliberadamente independientes de
  cualquier implementación —no prescriben una tecnología ni un estándar concreto—. Eso
  deja sin resolver cómo verificar, de forma automática y comparable entre repositorios
  distintos, qué tan "FAIR" es en realidad un recurso dado; el propio artículo reconoce
  que faltan indicadores de madurez, algo que la comunidad desarrollaría en trabajo
  posterior.

### 5.4 Sustento tecnológico

**(No aplica como implementación propia.)** El artículo lo afirma explícitamente: *"los
Principios preceden las decisiones de implementación... no sugieren ninguna tecnología,
estándar o solución de implementación específica"*. Su aporte operativo son los quince
sub-principios agrupados en cuatro ejes:

| Eje | Sub-principios (resumidos) |
|---|---|
| **Findable** | identificador global y persistente · metadatos ricos · el metadato incluye explícitamente el identificador del dato · (meta)datos indexados en un recurso buscable |
| **Accessible** | recuperable por protocolo estandarizado, abierto y gratuito, con autenticación cuando haga falta · los metadatos siguen accesibles aunque el dato ya no lo esté |
| **Interoperable** | lenguaje de representación de conocimiento formal y ampliamente aplicable · vocabularios que a su vez sean FAIR · referencias calificadas a otros (meta)datos |
| **Reusable** | metadatos ricos con atributos precisos y relevantes · licencia de uso clara y accesible · **procedencia detallada** · conformidad con estándares de la comunidad |

Documenta además implementaciones ejemplares con trazabilidad letra por letra de FAIR:
Dataverse, FAIRDOM, ISA, Open PHACTS, wwPDB y UniProt, cada una anotada según qué
principios satisface y con qué mecanismo concreto (DOIs, RDF, ontologías compartidas,
metadatos en tres niveles).

### 5.5 Contexto de aplicación

Ciencias de la vida y ciencia en general —genómica, biología estructural, farmacología,
astronomía—, que es el dominio de los ejemplos, pero el artículo declara explícitamente
que los principios aplican también a "objetos de investigación" no-dato: algoritmos,
herramientas y flujos de trabajo analíticos. No es un dominio vertical de TIC
empresarial, aunque el marco se ha extrapolado ampliamente a ese terreno en años
posteriores.

### 5.6 Experimentos

**(No aplica.)** No es un estudio empírico; es un documento de principios con ejemplos
ilustrativos de adopción, descritos de forma cualitativa (qué letra de FAIR satisface
cada implementación), sin métrica ni comparación cuantitativa entre ellas.

### 5.7 Conclusiones

La buena gestión y curaduría de datos no es un fin en sí mismo: es la condición previa
para el descubrimiento y la innovación. FAIR ofrece *"hitos en el camino"* hacia la
accionabilidad por máquina, no un estándar cerrado; los principios son modulares y
separables, y pueden adoptarse en cualquier combinación y de forma incremental. El
artículo cierra convocando a toda la comunidad de productores y editores de datos a
examinarlos e implementarlos.

### 5.8 Conceptos y términos que introduce

`FAIR` (*Findable* / *Accessible* / *Interoperable* / *Reusable*) · *machine-actionable*
(accionabilidad por máquina, como continuo, no como estado binario) · notación
`(meta)data` (el principio aplica tanto al dato como a su metadato) · identificador
global y persistente · procedencia detallada como requisito de reusabilidad (R1.2) ·
*research object* (datos, algoritmos, herramientas y flujos de trabajo como ciudadanos
de primera clase de la publicación científica).

### 5.9 Citas textuales clave

> "Good data management is not a goal in itself, but rather is the key conduit leading
> to knowledge discovery and innovation." — Introducción

> "the FAIR Principles put specific emphasis on enhancing the ability of machines to
> automatically find and use the data, in addition to supporting its reuse by
> individuals." — Resumen

> "These high-level FAIR Guiding Principles precede implementation choices, and do not
> suggest any specific technology, standard, or implementation-solution." —
> §*The Principles precede implementation*

### 5.10 Relación con el patrón *LLM Wiki* y el Open Knowledge Format

FAIR es el ancestro conceptual directo de las familias de metadatos que el Open
Knowledge Format formaliza dos décadas después: *Findable* (identificador único,
metadatos ricos, indexado) se corresponde con `type` / `resource` / `tags` y con
`index.md`; *Interoperable* (vocabularios compartidos, referencias calificadas) con los
enlaces cruzados entre conceptos; y R1.2 —*"(meta)data are associated with detailed
provenance"*— es, en sustancia, el campo `sources` de OKF antes de que el formato
existiera. Frente al patrón *LLM Wiki*, FAIR aporta el criterio de evaluación que el
patrón nunca definió: cuando se pide que una base de conocimiento tenga "citas y
trazabilidad", FAIR ya había convertido esa intuición en cuatro principios verificables
y en un vocabulario preciso para auditarlos.

### 5.11 Preguntas abiertas que deja

1. ¿Cómo se mide de forma objetiva y comparable el grado de "FAIRness" de un recurso?
   El artículo deja esto explícitamente para trabajo posterior de la comunidad.
2. ¿Cómo se aplican los principios a datos sensibles o de acceso restringido, donde
   publicar metadatos ricos puede chocar con requisitos de privacidad?
3. ¿Qué ocurre con la interoperabilidad cuando comunidades distintas adoptan
   vocabularios FAIR incompatibles entre sí?

### 5.12 Enlace y cita APA

- Artículo: https://www.nature.com/articles/sdata201618

> Wilkinson, M. D., Dumontier, M., Aalbersberg, I. J., Appleton, G., Axton, M., Baak, A.,
> Blomberg, N., Boiten, J.-W., da Silva Santos, L. B., Bourne, P. E., Bouwman, J.,
> Brookes, A. J., Clark, T., Crosas, M., Dillo, I., Dumon, O., Edmunds, S., Evelo, C. T.,
> Finkers, R., … Mons, B. (2016). The FAIR Guiding Principles for scientific data
> management and stewardship. *Scientific Data*, *3*, Article 160018.
> https://doi.org/10.1038/sdata.2016.18

---

## 6. From Local to Global: A Graph RAG Approach to Query-Focused Summarization

### 6.1 Ficha rápida

| | |
|---|---|
| Autores | Edge, Trinh, Cheng, Bradley, Chao, Mody, Truitt, Metropolitansky, Ness, Larson (Microsoft Research / Microsoft Strategic Missions and Technologies / Microsoft Office of the CTO) |
| Tipo | Artículo de investigación con evaluación empírica extensa y código abierto |
| Publicación | arXiv:2404.16130 · v1 abr 2024 · v2 19 feb 2025 · *"Preprint. Under review."* |
| Continuación | Código abierto en `microsoft/graphrag`; extensiones publicadas en LangChain, LlamaIndex, NebulaGraph y Neo4j |
| Código | Sí — repositorio de Microsoft, con los *prompts* completos de cada etapa publicados en el apéndice del propio artículo |

### 6.2 Definición general

GraphRAG combina extracción de grafos de conocimiento con resumen orientado a consulta
para responder preguntas de *"sensemaking global"* sobre corpus completos de texto
—preguntas del tipo *"¿cuáles son los temas principales del dataset?"*—, que el RAG
vectorial convencional no puede responder bien porque es una tarea de síntesis global,
no de recuperación de hechos puntuales. Construye el índice en dos etapas: primero
deriva un grafo de entidades del corpus, luego pre-genera resúmenes de comunidades de
entidades estrechamente relacionadas; en consulta, cada resumen de comunidad produce
una respuesta parcial y todas se combinan (*map-reduce*) en una respuesta final.

Lo relevante del trabajo es que resuelve, con un mecanismo concreto y evaluado
empíricamente, la idea de recuperar sobre la estructura de un grafo en lugar de sobre
fragmentos aislados por similitud: en vez de rankear nodos individuales, agrupa el grafo
en comunidades y resume cada una, dando una vía distinta —y con resultados medidos— al
mismo problema que otros enfoques atacan con algoritmos de centralidad como PageRank.

### 6.3 Problemas que aborda y necesidades que abre

- **Problema del artículo:** el RAG vectorial falla en preguntas globales porque
  recupera un número fijo de fragmentos semánticamente cercanos a la consulta, y ninguna
  combinación pequeña de fragmentos "cubre" un corpus entero. Los métodos previos de
  resumen orientado a consulta, por su parte, no escalan a los volúmenes de texto que
  indexa un sistema RAG típico.
- **Necesidad que queda abierta:** la evaluación se hizo sobre corpus de
  aproximadamente un millón de tokens y solo dos dominios (transcripciones de pódcast y
  artículos de noticias); los propios autores señalan que falta entender cómo generaliza
  el método a otros dominios y casos de uso, y que la comparación de tasas de
  fabricación (contenido inventado) con métodos dedicados a ello queda pendiente. El
  índice de grafo, además, se construye una sola vez sobre un corpus fijo: el artículo no
  evalúa qué ocurre cuando el corpus se actualiza de forma incremental.

### 6.4 Sustento tecnológico

**Pipeline de cinco etapas:**

1. Los documentos fuente se dividen en fragmentos de texto.
2. Un LLM extrae entidades, relaciones y afirmaciones ("*claims*") verificables de cada
   fragmento, con un paso de autorreflexión donde el modelo revisa si dejó entidades sin
   detectar.
3. Las instancias repetidas de una misma entidad se funden en nodos de un grafo,
   usando coincidencia exacta de cadenas para la resolución de entidades (el artículo cita
   explícitamente el problema de la resolución de entidades como una decisión de diseño
   donde caben técnicas más flexibles).
4. Se detectan comunidades jerárquicas de nodos fuertemente conectados con el algoritmo
   de Leiden, particionando el grafo en niveles de granularidad creciente.
5. Se generan resúmenes de cada comunidad, de abajo hacia arriba, hasta cubrir toda la
   jerarquía.

En consulta: los resúmenes de comunidad del nivel elegido se mezclan aleatoriamente, se
generan respuestas parciales en paralelo con un puntaje de utilidad de 0 a 100, se
descartan las de puntaje 0, y el resto se combina en una respuesta final.

**Reproducibilidad:** publicado como software abierto, con los *prompts* completos de
extracción de entidades, generación de resúmenes de comunidad y generación de
respuestas incluidos en el propio artículo — el detalle de implementación más completo
entre los trabajos fichados hasta ahora.

### 6.5 Contexto de aplicación

TIC / procesamiento de lenguaje natural sobre corpus privados o no vistos previamente
por el modelo. Evaluado en dos dominios de uso general: transcripciones de pódcast
(conversaciones sobre ciencia y tecnología) y artículos periodísticos (salud, negocios,
deportes, tecnología). No es un dominio vertical especializado, aunque el propio
artículo anota que dominios con conocimiento técnico denso (ciencia, medicina, derecho)
se beneficiarían de ejemplos de extracción adaptados a ese dominio.

### 6.6 Experimentos

Dos experimentos sobre dos corpus (≈1 y ≈1,7 millones de tokens), comparando seis
condiciones: GraphRAG en cuatro niveles de granularidad de comunidad (C0 a C3, de
resúmenes más generales a más específicos), resumen del texto fuente sin grafo (TS), y
RAG vectorial convencional (SS).

- **Evaluación por juez-LLM** sobre 125 preguntas de *sensemaking* global por corpus
  (generadas con un procedimiento propio de personas y tareas simuladas), en cuatro
  criterios: *comprehensiveness*, *diversity*, *empowerment* y *directness* (criterio de
  control). Resultado principal: **todas las condiciones de GraphRAG superan al RAG
  vectorial en comprehensividad (72–83 % de tasa de victoria, p < 0,001) y diversidad
  (62–82 %, p < 0,01 o mejor)**; el RAG vectorial gana en *directness*, como se
  esperaba, lo que valida el diseño de la evaluación.
- **Verificación independiente con afirmaciones extraídas:** de las respuestas se
  extrajeron 47.075 afirmaciones factuales verificables con un método propio
  (*Claimify*). GraphRAG y el resumen de texto fuente producen más afirmaciones y más
  diversidad de afirmaciones (medida por agrupamiento) que el RAG vectorial, de forma
  estadísticamente significativa en la mayoría de comparaciones. El veredicto del
  juez-LLM coincidió con esta medida independiente en 78 % de los casos para
  comprehensividad y 69–70 % para diversidad.
- **Costo:** el nivel más alto de la jerarquía de comunidades requiere hasta 97 % menos
  tokens de contexto por consulta que resumir el texto fuente directamente, con una
  caída de desempeño modesta frente a los niveles más detallados.

### 6.7 Conclusiones

GraphRAG combina generación de grafos de conocimiento y resumen orientado a consulta
para dar soporte a la comprensión global de corpus completos. Para consultas globales
repetidas sobre el mismo conjunto de datos, los resúmenes de comunidades de nivel raíz
ofrecen un índice superior al RAG vectorial y competitivo con otros métodos globales, a
una fracción del costo en tokens. Como impacto más amplio, los autores señalan el riesgo
de que las respuestas no reflejen fielmente los datos fuente, y recomiendan divulgación
clara del uso de IA junto con el sistema.

### 6.8 Conceptos y términos que introduce

*sensemaking* global (frente a recuperación de hechos puntuales) · *"vector RAG"*
(nombre explícito para el RAG convencional, en contraste con GraphRAG) · grafo de
entidades extraído por LLM · detección de comunidades jerárquica (Leiden) · resumen de
comunidad · combinación *map-reduce* de respuestas parciales · generación adaptativa de
preguntas de evaluación vía personas y tareas simuladas · `Claimify` (extracción de
afirmaciones factuales verificables) · juez-LLM con los criterios *comprehensiveness*,
*diversity*, *empowerment*, *directness*.

### 6.9 Citas textuales clave

> "RAG fails on global questions directed at an entire text corpus, such as 'What are
> the main themes in the dataset?', since this is inherently a query-focused
> summarization (QFS) task, rather than an explicit retrieval task." — Resumen

> "Compared to vector RAG, however, GraphRAG shows promise as a way to mitigate these
> downstream risks for questions of a global nature, which might otherwise be answered
> by samples of retrieved facts falsely presented as global summaries." — §6, *Broader
> impacts*

> "Root-level community summaries (C0) required dramatically fewer tokens per query (9x
> –43x)." — Tabla 2

### 6.10 Relación con el patrón *LLM Wiki* y el Open Knowledge Format

GraphRAG resuelve con un mecanismo concreto y evaluado la intuición de "encontrar lo que
condensa el corpus": en lugar de rankear nodos individuales, agrupa el grafo en
comunidades y resume cada una, el equivalente estructural más cercano a un documento que
sintetiza a los demás. Comparte con el Open Knowledge Format y el patrón *LLM Wiki* la
idea de un grafo de conocimiento como capa intermedia entre las fuentes y las
respuestas, pero lo construye y consulta en un índice cerrado que se rehace por
completo, sin la capa de metadatos de procedencia por concepto que define a OKF: sus
nodos y comunidades no llevan verificación humana, nivel de confianza ni fecha de
vigencia — son resúmenes generados y reemplazados en cada indexación completa, no
mantenidos de forma incremental afirmación por afirmación.

### 6.11 Preguntas abiertas que deja

1. ¿Cómo se actualiza el grafo y sus resúmenes de comunidad cuando llegan documentos
   nuevos, sin reconstruir el índice completo desde cero?
2. ¿Cómo se cuantifica la tasa de fabricación de las respuestas, más allá de las
   medidas de comprehensividad y diversidad usadas aquí? Señalado explícitamente por los
   autores como trabajo pendiente.
3. ¿Qué ocurre cuando la resolución de entidades por coincidencia exacta de cadenas
   falla y fusiona o separa incorrectamente nodos del grafo?
4. ¿Cómo generaliza el método a corpus de dominios especializados, distintos de los dos
   evaluados?

### 6.12 Enlace y cita APA

- Artículo: https://arxiv.org/abs/2404.16130 · PDF: https://arxiv.org/pdf/2404.16130
- Código: https://github.com/microsoft/graphrag

> Edge, D., Trinh, H., Cheng, N., Bradley, J., Chao, A., Mody, A., Truitt, S.,
> Metropolitansky, D., Ness, R. O., & Larson, J. (2024). *From local to global: A graph
> RAG approach to query-focused summarization* (arXiv:2404.16130). arXiv.
> https://arxiv.org/abs/2404.16130

---

## 7. HippoRAG: Neurobiologically Inspired Long-Term Memory for Large Language Models

### 7.1 Ficha rápida

| | |
|---|---|
| Autores | Bernal Jiménez Gutiérrez, Yiheng Shu, Yu Gu, Michihiro Yasunaga, Yu Su (Ohio State University NLP Group) |
| Tipo | Artículo de investigación con evaluación empírica extensa y código abierto |
| Publicación | *NeurIPS 2024* · arXiv:2405.14831 · v1 23 may 2024 · revisado ene 2025 |
| Continuación | **HippoRAG 2** — *From RAG to Memory: Non-Parametric Continual Learning for Large Language Models* (mismo grupo + Qi y Zhou; ICML 2025, arXiv:2502.14802). Es la versión que hoy mantiene el repositorio. |
| Código | Sí — `github.com/osu-nlp-group/hipporag`, licencia MIT, instalable por `pip` |

### 7.2 Definición general

Propone una arquitectura de memoria de largo plazo para modelos de lenguaje inspirada en
la **teoría del índice hipocampal** de la memoria humana: el hipocampo actúa como un
índice que asocia recuerdos dispersos en el neocórtex, sin almacenar el contenido en sí.
HippoRAG traduce esa idea en dos componentes —extracción abierta de información (OpenIE)
que construye un grafo de conocimiento en la fase de indexación (*offline*), y
*Personalized PageRank* sobre ese grafo en la fase de consulta (*online*) para encontrar,
en un solo paso, los nodos relevantes a una pregunta, incluidas las que exigen integrar
información repartida entre varios documentos.

Lo relevante del trabajo es que es de los primeros en usar PageRank personalizado como
mecanismo de recuperación multi-salto sobre un grafo construido por un LLM, con una
analogía neurobiológica explícita y una evaluación cuantitativa sólida contra líneas
base estándar y contra recuperación iterativa.

### 7.3 Problemas que aborda y necesidades que abre

- **Problema del artículo:** el RAG estándar recupera fragmentos por similitud aislada y
  no logra integrar conocimiento disperso entre varios pasajes —lo que el artículo llama
  preguntas de *"path-finding multi-hop"*, donde ni la pregunta ni ningún pasaje
  individual contienen pistas léxicas que conecten los conceptos necesarios—. Los
  métodos de recuperación iterativa (como IRCoT) sí logran esa integración, pero a un
  costo computacional mucho mayor, porque llaman al LLM en cada paso.
- **Necesidad que queda abierta:** los propios autores señalan que la mayoría de los
  errores del sistema provienen de la extracción (reconocimiento de entidades y OpenIE),
  no del algoritmo de ranking; que ningún componente recibe todavía ajuste fino
  específico; y, lo más relevante para un proyecto de mantenimiento incremental, que
  *"la escalabilidad de HippoRAG aún requiere más validación"* — no se ha probado
  empíricamente qué pasa con el índice hipocampal sintético cuando crece mucho más allá
  de los *benchmarks* evaluados.

### 7.4 Sustento tecnológico

**Indexación (offline):** un LLM aplica extracción abierta de información sobre cada
pasaje para producir tripletas sujeto-relación-objeto —el *prompt* publicado en el
apéndice pide explícitamente resolver pronombres a nombres concretos y anclar cada
tripleta a la lista de entidades nombradas del pasaje—. Las tripletas se convierten en
nodos y aristas de un grafo de conocimiento.

**Recuperación (online):** dada una consulta, se extrae un conjunto de nodos semilla y
se ejecuta *Personalized PageRank* sobre el grafo, que difunde relevancia desde esos
nodos siguiendo las conexiones existentes, recuperando en un solo paso pasajes que
ningún método de similitud aislada encontraría.

**Implementación de referencia (HippoRAG 2, lo que hoy corre el repositorio):** soporta
múltiples proveedores de LLM (OpenAI, endpoints compatibles con OpenAI, Amazon Bedrock,
un enrutador propio, despliegue local con vLLM) y varios *backends* de almacenamiento
vectorial (Parquet local, Qdrant, ChromaDB, Milvus). El índice queda ligado a la
identidad exacta del modelo y la configuración que lo produjo: reindexar es obligatorio
si cualquiera de esos parámetros cambia, y el sistema rechaza mezclar silenciosamente
estados incompatibles.

**Reproducibilidad:** paquete instalable (`pip install hipporag`), API mínima de tres
llamadas (`HippoRAG(...)`, `.index(docs)`, `.rag_qa(queries)`), con *scripts* de
reproducción de los experimentos del artículo y los datasets de referencia publicados en
HuggingFace.

### 7.5 Contexto de aplicación

TIC / procesamiento de lenguaje natural, con evaluación centrada en preguntas y
respuestas de dominio abierto sobre pasajes de Wikipedia. No es un dominio vertical,
aunque HippoRAG 2 amplía la evaluación a memoria factual (NaturalQuestions, PopQA),
comprensión narrativa (NarrativeQA) y contextos largos (LV-Eval), acercándose a un caso
de uso de memoria de largo plazo de propósito general.

### 7.6 Experimentos

Recuperación de un solo paso sobre tres *benchmarks* de preguntas multi-salto (MuSiQue,
2WikiMultiHopQA, HotpotQA), medida con recall@2 y recall@5 (R@2 / R@5) contra ocho
líneas base (BM25, Contriever, GTR, ColBERTv2, RAPTOR, Proposition, entre otras):

| Método | MuSiQue R@2/R@5 | 2Wiki R@2/R@5 | HotpotQA R@2/R@5 | Promedio R@2/R@5 |
|---|---|---|---|---|
| Mejor línea base (ColBERTv2) | 37,9 / 49,2 | 59,2 / 68,2 | **64,7 / 79,3** | 53,9 / 65,6 |
| **HippoRAG (ColBERTv2)** | **40,9 / 51,9** | **70,7 / 89,1** | 60,5 / 77,7 | **57,4 / 72,9** |

HippoRAG supera a todas las líneas base en MuSiQue y 2WikiMultiHopQA, y rinde de forma
comparable —sin superarla— en HotpotQA, el *dataset* menos exigente en integración
multi-salto. Combinado con el método de recuperación iterativa IRCoT, aporta mejoras
complementarias de hasta 20 puntos de R@5, siendo entre 10 y 30 veces más barato y entre
6 y 13 veces más rápido que ejecutar IRCoT solo. Un experimento cualitativo adicional
(*"path-finding multi-hop questions"*, preguntas donde ningún pasaje individual conecta
léxicamente los conceptos) muestra que tanto ColBERTv2 como IRCoT fallan mientras
HippoRAG recupera el pasaje correcto siguiendo asociaciones en el grafo.

La continuación (HippoRAG 2) evalúa además tres dimensiones —memoria factual,
comprensión de sentido y asociatividad— y reporta una mejora del 7 % en tareas
asociativas sobre el mejor modelo de *embeddings*, manteniendo el desempeño factual,
frente a HippoRAG, GraphRAG, RAPTOR y RAG estándar.

### 7.7 Conclusiones

El enfoque, aunque sencillo, muestra que un grafo construido por LLM más un algoritmo de
ranking clásico puede superar a la recuperación densa estándar en tareas que exigen
integrar conocimiento disperso, con una eficiencia muy superior a la recuperación
iterativa. Los autores lo describen como un término medio entre RAG estándar y memoria
paramétrica, con capacidad de actualizarse continuamente, aunque advierten que aún no
está validado a gran escala.

### 7.8 Conceptos y términos que introduce

Teoría del índice hipocampal aplicada a sistemas de recuperación · *Personalized
PageRank* como mecanismo de recuperación de un solo paso · OpenIE (extracción abierta de
información) para construir el grafo de indexación · preguntas *path-following* vs.
*path-finding* multi-hop · *"synthetic hippocampal index"* · integración de conocimiento
como capacidad distinta de la recuperación simple.

### 7.9 Citas textuales clave

> "HippoRAG synergistically orchestrates LLMs, knowledge graphs, and the Personalized
> PageRank algorithm to mimic the different roles of neocortex and hippocampus in human
> memory." — Resumen

> "[HippoRAG] achieves comparable or better performance than iterative retrieval like
> IRCoT while being 10-30 times cheaper and 6-13 times faster during online retrieval."
> — §5

> "We are yet to empirically prove the efficiency and efficacy of our synthetic
> hippocampal index as its size grows way beyond current benchmarks." — §7,
> *Conclusions & Limitations*

### 7.10 Relación con el patrón *LLM Wiki* y el Open Knowledge Format

HippoRAG comparte con GraphRAG y con la propuesta de PageRank de la literatura de
recuperación la misma intuición: usar la estructura del grafo, no solo la similitud,
para recuperar. Frente a GraphRAG (que resume comunidades por adelantado en la fase de
indexación), HippoRAG no pre-resume nada: indexa tripletas crudas y deja que
*Personalized PageRank* encuentre la ruta relevante en el momento de la consulta, lo que
traslada trabajo de la indexación —costosa, exhaustiva— a la consulta —más barata por
consulta individual, aunque repetida en cada una—. Ninguno de los dos formatos, ni
HippoRAG ni GraphRAG, lleva metadatos de procedencia, verificación o vigencia por
concepto como sí exige el Open Knowledge Format: el grafo se reconstruye o se actualiza
como estructura interna del sistema, no como archivos versionables y auditables por un
humano.

### 7.11 Preguntas abiertas que deja

1. ¿Cómo se comporta la precisión del grafo hipocampal sintético a una escala mucho
   mayor que los *benchmarks* evaluados (miles o millones de pasajes)? Señalado
   explícitamente por los autores como pendiente.
2. ¿Qué política de actualización incremental usa el sistema cuando llegan documentos
   nuevos que contradicen entidades o relaciones ya indexadas?
3. ¿Cuánto se degrada el desempeño cuando el ajuste fino de los componentes (NER,
   OpenIE) no está disponible, en dominios distintos a los evaluados?

### 7.12 Enlace y cita APA

- Artículo: https://arxiv.org/abs/2405.14831 · PDF: https://arxiv.org/pdf/2405.14831
- Continuación: https://arxiv.org/abs/2502.14802
- Código: https://github.com/osu-nlp-group/hipporag

> Jiménez Gutiérrez, B., Shu, Y., Gu, Y., Yasunaga, M., & Su, Y. (2024). *HippoRAG:
> Neurobiologically inspired long-term memory for large language models*
> (arXiv:2405.14831). En *Advances in Neural Information Processing Systems 37 (NeurIPS
> 2024)*. https://arxiv.org/abs/2405.14831

> Jiménez Gutiérrez, B., Shu, Y., Qi, W., Zhou, S., & Su, Y. (2025). *From RAG to
> memory: Non-parametric continual learning for large language models*
> (arXiv:2502.14802). En *Proceedings of the 42nd International Conference on Machine
> Learning (ICML 2025)*. https://arxiv.org/abs/2502.14802

---

## 8. fast-graphrag

### 8.1 Ficha rápida

| | |
|---|---|
| Origen | Circlemind — proyecto open-source con servicio gestionado de pago sobre el mismo motor |
| Tipo | Implementación open-source. Sin artículo propio ni evaluación con protocolo publicado — literatura técnica de repositorio |
| Publicación | Repositorio activo, licencia MIT |
| Continuación | Circlemind ofrece un servicio gestionado (*managed service*) sobre el mismo motor, con capa gratuita limitada |
| Código | Sí — Python, instalable por PyPI, con ejemplos y *benchmarks* propios de costo frente a GraphRAG y LightRAG |

### 8.2 Definición general

fast-graphrag es una reimplementación ligera del patrón GraphRAG que sustituye el
resumen de comunidades por recuperación con *Personalized PageRank* —el mismo algoritmo
de HippoRAG (ficha 7), al que cita explícitamente como fundamento teórico—. Construye un
grafo de entidades y relaciones a partir de texto insertado por el usuario, guiado por un
dominio en lenguaje natural, unas consultas de ejemplo y una lista de tipos de entidad, y
explora ese grafo con PageRank en vez de con el proceso de detección de comunidades y
resumen jerárquico de GraphRAG.

Lo relevante del trabajo es que es evidencia de que la comunidad ya combina, fuera de
cualquier artículo, las dos líneas fichadas antes —extracción de grafo al estilo
GraphRAG, recuperación al estilo HippoRAG— como herramienta de producción, con una
promesa explícita de menor costo.

### 8.3 Problemas que aborda y necesidades que abre

- **Problema:** GraphRAG es efectivo pero costoso de indexar: construye jerarquías
  completas de comunidades y las resume todas por adelantado, incluidas las que ninguna
  consulta futura llegará a necesitar. fast-graphrag busca la misma capacidad de
  exploración de grafo con un costo de indexación e inferencia mucho menor.
- **Necesidad que queda abierta:** el proyecto ofrece "actualizaciones incrementales" y
  "datos dinámicos" como características, pero no publica ninguna medición de cómo se
  comporta la calidad del grafo a medida que se acumulan inserciones sucesivas — es una
  promesa de producto, no un resultado medido.

### 8.4 Sustento tecnológico

Motor en Python, completamente asíncrono y tipado. El usuario define un dominio en
lenguaje natural, consultas de ejemplo y una lista de tipos de entidad esperados; el
sistema extrae el grafo de cualquier texto insertado (`grag.insert(texto)`) y responde
consultas (`grag.query(pregunta)`) explorando el grafo con *Personalized PageRank*.
Soporta cualquier proveedor compatible con la API de OpenAI (incluye ejemplos con
Gemini). Ofrece un parámetro de consulta para incluir referencias a la información usada
en la respuesta (`with_references=True`) y un mecanismo de *checkpointing* para evitar
corrupción irreversible de los datos.

**Reproducibilidad:** instalable por PyPI (`pip install fast-graphrag`) o desde código
fuente; el propio repositorio incluye un directorio de *benchmarks* con *scripts*
propios.

### 8.5 Contexto de aplicación

TIC / flujos de recuperación dirigidos por agentes, de propósito general —el ejemplo del
repositorio usa un texto literario (*A Christmas Carol*) para extraer personajes,
lugares y eventos, pero se presenta explícitamente como aplicable a cualquier dominio
mediante la configuración de tipos de entidad—. No es un dominio vertical.

### 8.6 Experimentos

**(No aplica formalmente.)** El repositorio reporta una comparación de costo no
protocolizada: sobre el texto de referencia *"The Wizard of Oz"*, fast-graphrag cuesta
0,08 USD frente a 0,48 USD de GraphRAG —una afirmación de "6 veces más barato"
presentada como nota del proyecto, sin metodología publicada, sin métrica de calidad de
respuesta asociada, y sin comparación bajo las mismas condiciones que sí exige, por
ejemplo, la evaluación de GraphRAG (ficha 6). El historial del repositorio menciona
además *benchmarks* contra LightRAG, tampoco publicados con protocolo verificable.

### 8.7 Conclusiones

La tesis del proyecto es que la mayoría de aplicaciones de IA generativa no necesitan la
complejidad de diseñar flujos agénticos a medida: un grafo interpretable, navegable y
consultable con PageRank personalizado basta como capa de recuperación, y debe poder
ejecutarse a bajo costo y en tiempo real conforme los datos cambian.

### 8.8 Conceptos y términos que introduce

Grafo *"interpretable y depurable"* como argumento de diseño, frente a un índice opaco ·
configuración de dominio + consultas de ejemplo + tipos de entidad como forma de dirigir
la extracción · *checkpointing* contra corrupción de datos · actualizaciones
incrementales del grafo · referencias citadas en la respuesta (`with_references`).

### 8.9 Citas textuales clave

> "Fast GraphRAG currently exploits the personalized pagerank algorithm to explore the
> graph and find the most relevant pieces of information to answer your query." —
> README, §*Philosophy*

> "Interpretable and Debuggable Knowledge: Graphs offer a human-navigable view of
> knowledge that can be queried, visualized, and updated." — README, §*Features*

> "Using The Wizard of Oz, fast-graphrag costs $0.08 vs. graphrag $0.48 — a 6x costs
> saving that further improves with data size and number of insertions." — README

### 8.10 Relación con el patrón *LLM Wiki* y el Open Knowledge Format

Es la síntesis práctica de las fichas 6 y 7: adopta la extracción de grafo de GraphRAG y
la recuperación por PageRank de HippoRAG, sin adoptar la capa de metadatos de
procedencia del Open Knowledge Format ni la organización en archivos markdown legibles
por humanos del patrón *LLM Wiki* — el grafo vive en una base propia del motor, no en un
*bundle* de archivos versionables. Su promesa de "conocimiento navegable por humanos" se
refiere a la posibilidad de visualizar el grafo, no a que el conocimiento esté escrito
como texto revisable, que es la diferencia central frente al patrón *LLM Wiki*.

### 8.11 Preguntas abiertas que deja

1. ¿Bajo qué protocolo y con qué métrica de calidad se sostiene la comparación de costo
   frente a GraphRAG? No se publica.
2. ¿Cómo se compara la precisión de recuperación —no solo el costo— entre la
   exploración por PageRank de fast-graphrag y el resumen de comunidades de GraphRAG,
   sobre el mismo corpus?
3. ¿Qué ocurre con la calidad del grafo tras muchas inserciones incrementales
   sucesivas?

### 8.12 Enlace y cita APA

- Repositorio: https://github.com/circlemind-ai/fast-graphrag

> Circlemind. (2024). *fast-graphrag* [Software]. GitHub.
> https://github.com/circlemind-ai/fast-graphrag

---

## 9. Fine-tuned LLMs Know More, Hallucinate Less with Few-Shot Sequence-to-Sequence Semantic Parsing over Wikidata

### 9.1 Ficha rápida

| | |
|---|---|
| Autores | Silei Xu, Shicheng Liu, Theo Culhane, Elizaveta Pertseva, Meng-Hsi Wu, Sina J. Semnani, Monica S. Lam (Stanford OVAL) |
| Tipo | Artículo de investigación con evaluación empírica, revisado por pares |
| Publicación | *EMNLP 2023* (Main) · arXiv:2305.14202 · v1 23 may 2023 · v2 5 nov 2023 |
| Continuación | Trabajo posterior del mismo grupo en *Findings of EMNLP 2024*, con un agente interactivo en línea |
| Código | Sí — `github.com/stanford-oval/wikidata-emnlp23`, incluye el *dataset* WikiWebQuestions y modelos publicados en HuggingFace |

### 9.2 Definición general

Presenta **WikiSP**, un analizador semántico *sequence-to-sequence* que traduce
preguntas en lenguaje natural a consultas SPARQL sobre Wikidata, y
**WikiWebQuestions**, un banco de pruebas de preguntas reales con anotación SPARQL
derivado de WebQuestions (originalmente construido para Freebase). La contribución
técnica central es doble: sustituir los identificadores opacos de Wikidata (QIDs, PIDs)
por nombres de dominio y propiedad legibles en la consulta SPARQL objetivo, y entrenar
al analizador para que use tanto el resultado de un vinculador de entidades como las
*menciones* textuales directas de la pregunta —de modo que si el vinculador de
entidades falla, el analizador aún puede generar la consulta correcta a partir del
nombre mencionado y resolverlo después con una heurística—.

Lo relevante del trabajo es que mide, con un banco de pruebas propio, cuánto reduce la
alucinación anclar las respuestas a una base de conocimiento estructurada y verificable
(Wikidata, con más de 12.000 millones de hechos), y cómo recuperarse cuando el paso
previo de identificar las entidades mencionadas —una fuente de error real, documentada
en el propio artículo— falla.

### 9.3 Problemas que aborda y necesidades que abre

- **Problema del artículo:** los LLM pueden responder correctamente muchas preguntas,
  pero también alucinan. Wikidata ofrece una base de hechos verificable a la cual
  anclarlos, pero traducir lenguaje natural a SPARQL de forma fiable —y recuperarse
  cuando el paso previo de vinculación de entidades falla— no estaba resuelto con
  evaluación real.
- **Necesidad que queda abierta:** el sistema depende de la calidad del vinculador de
  entidades y de las heurísticas de resolución de menciones; el propio ejemplo del
  artículo (una consulta sobre los Giants y las World Series) muestra que, aun con la
  recuperación por menciones, el proceso completo sigue siendo sensible a errores de
  vinculación en cascada. Queda abierto también qué ocurre con dominios o formulaciones
  de pregunta muy alejados del estilo de WikiWebQuestions.

### 9.4 Sustento tecnológico

**Modificación de sintaxis:** el SPARQL objetivo de entrenamiento usa nombres de
dominio y de propiedad (`wd:world_series`) en lugar de identificadores opacos
(`wd:Q265538`), lo que hace la consulta generada más fácil de aprender y de depurar.

**Doble señal de entrada:** el analizador se entrena tanto con el resultado de un
vinculador de entidades (ReFinED, afinado para el dominio) como con datos donde debe
generar directamente la *mención* textual cuando el vinculador falla; en inferencia,
una heurística resuelve la mención predicha al QID real de Wikidata.

**Modelo base:** LLaMA afinado, añadiendo los datos de entrenamiento propios al
conjunto usado para entrenar Alpaca; publicado en HuggingFace, listo para descargar y
servir con la librería de inferencia de Hugging Face.

**Respaldo verificable + GPT-3:** las consultas SPARQL generadas son verificables por
construcción —se pueden ejecutar y auditar—; cuando el analizador no logra generar una
consulta útil, el sistema recurre a una respuesta de GPT-3 como respaldo no verificado,
combinando certeza verificable con cobertura.

**Reproducibilidad:** repositorio con los datos de entrenamiento de cada modelo del
artículo, los resultados de predicción publicados, un *script* de evaluación, y los
pesos de los dos modelos LLaMA afinados descargables desde HuggingFace.

### 9.5 Contexto de aplicación

TIC / preguntas y respuestas de dominio abierto sobre una base de conocimiento
estructurada de propósito general —Wikidata cubre prácticamente cualquier tema con
representación en Wikipedia—. No es un dominio vertical.

### 9.6 Experimentos

- **WikiWebQuestions** (banco de pruebas propio, portado de WebQuestions/Freebase a
  Wikidata con anotación SPARQL): el modelo alcanza **76 % de exactitud en desarrollo y
  65 % en prueba**.
- Combinando el analizador (resultados verificables) con GPT-3 como respaldo para las
  preguntas que el analizador no resuelve: **respuestas útiles al 96 % de las preguntas
  del conjunto de desarrollo**.
- **QALD-7** (banco de pruebas externo sobre Wikidata): el método **supera el estado del
  arte anterior en 3,6 puntos de F1**.
- El artículo incluye además ablaciones tabuladas frente a variantes sin menciones
  (entrenadas solo con vinculador oráculo o con ReFinED) y frente al formato de SPARQL
  con identificadores originales; los valores exactos de esas ablaciones no están en el
  fragmento verificado aquí y conviene revisarlos en el artículo antes de citarlos.

### 9.7 Conclusiones

Afinar un LLM con pocos ejemplos para generar SPARQL legible, entrenado para usar tanto
el resultado de vinculación de entidades como las menciones textuales, produce un
analizador semántico preciso y verificable para Wikidata; combinado con un modelo
generativo como respaldo, cubre casi todas las preguntas manteniendo una base de
respuestas auditables. El resultado establece una línea base fuerte y supera el estado
del arte previo en un banco de pruebas externo.

### 9.8 Conceptos y términos que introduce

`WikiWebQuestions` (banco de pruebas SPARQL-anotado sobre Wikidata) · `WikiSP` (el
analizador) · SPARQL con nombres de dominio en lugar de identificadores · recuperación
de errores de vinculación de entidades vía *menciones* · combinación de respuesta
verificable (SPARQL) con respaldo generativo no verificado (GPT-3) · afinamiento con
pocos ejemplos sobre un conjunto ya afinado (Alpaca).

### 9.9 Citas textuales clave

> "While large language models (LLMs) can answer many questions correctly, they can
> also hallucinate and give wrong answers. Wikidata, with its over 12 billion facts, can
> be used to ground LLMs to improve their factuality." — Resumen

> "By pairing our semantic parser with GPT-3, we combine verifiable results with
> qualified GPT-3 guesses to provide useful answers to 96% of the questions in dev." —
> Resumen

### 9.10 Relación con el patrón *LLM Wiki* y el Open Knowledge Format

Wikidata funciona aquí como la base de conocimiento externa con procedencia estructural
ya incorporada —cada hecho es una tripleta con su propio identificador y su propio
historial de edición—, que es justamente lo que el patrón *LLM Wiki* y el Open Knowledge
Format intentan reconstruir con markdown y frontmatter para conocimiento que no nace
estructurado. WikiSP muestra el caso donde la base de conocimiento *ya* está
estructurada y el problema se reduce a traducir lenguaje natural a esa estructura de
forma fiable; el problema que atacan HippoRAG, GraphRAG y el patrón *LLM Wiki* es el
inverso: construir esa estructura a partir de texto libre cuando no existe de antemano.

### 9.11 Preguntas abiertas que deja

1. ¿Cómo se comporta el analizador ante formulaciones de pregunta muy distintas al
   estilo de WikiWebQuestions?
2. ¿Qué tan bien generaliza la recuperación por menciones a bases de conocimiento con
   convenciones de nombres muy distintas a Wikidata?
3. ¿Cómo evoluciona la exactitud si Wikidata cambia sus datos entre el momento de
   entrenamiento y el de consulta? El artículo no evalúa desactualización.

### 9.12 Enlace y cita APA

- Artículo: https://arxiv.org/abs/2305.14202 · Publicación:
  https://aclanthology.org/2023.emnlp-main.353
- Código: https://github.com/stanford-oval/wikidata-emnlp23

> Xu, S., Liu, S., Culhane, T., Pertseva, E., Wu, M.-H., Semnani, S. J., & Lam, M.
> (2023). Fine-tuned LLMs know more, hallucinate less with few-shot sequence-to-sequence
> semantic parsing over Wikidata. En H. Bouamor, J. Pino, & K. Bali (Eds.), *Proceedings
> of the 2023 Conference on Empirical Methods in Natural Language Processing*
> (pp. 5778–5791). Association for Computational Linguistics.
> https://aclanthology.org/2023.emnlp-main.353

---

## 10. Question-to-Question Retrieval for Hallucination-Free Knowledge Access

*An Approach for Wikipedia and Wikidata Question Answering*

### 10.1 Ficha rápida

| | |
|---|---|
| Autor | Santhosh Thottingal (autor único; agradece a colaboradores de la Fundación Wikimedia en los reconocimientos, sin declarar afiliación formal) |
| Tipo | Preprint de arXiv, sin *venue* de publicación declarado y sin revisión por pares confirmada |
| Publicación | arXiv:2501.11301 · v1 20 ene 2025 · v3 21 feb 2025 |
| Continuación | No declarada |
| Código | **No disponible.** El artículo describe una implementación de prototipo interna, sin repositorio público |

### 10.2 Definición general

Propone responder preguntas sobre Wikipedia y Wikidata emparejando **pregunta contra
pregunta**, en vez de pregunta contra pasaje. Para cada unidad de contenido (un párrafo
de Wikipedia, o una tripleta de Wikidata convertida a texto), un LLM instruido genera de
antemano un conjunto de preguntas que ese contenido respondería; esas preguntas
generadas se vectorizan y se indexan. En consulta, la pregunta del usuario se compara
contra ese índice de preguntas —no contra el texto original— y el contenido asociado a
la pregunta más similar se devuelve directamente, sin que ningún modelo genere la
respuesta.

Lo relevante del trabajo es que ataca un problema estructural del RAG denso poco
discutido en las demás fichas: las preguntas y los pasajes tienen formas gramaticales
distintas (interrogativa vs. declarativa), lo que baja la similitud coseno entre ambos
incluso cuando el contenido es correcto —el artículo reporta rangos típicos de 0,4 a
0,7—. Comparar pregunta contra pregunta, en cambio, compara formas gramaticales
iguales.

### 10.3 Problemas que aborda y necesidades que abre

- **Problema del artículo:** en RAG convencional, la similitud entre el vector de una
  pregunta (*"¿Dónde está la Torre Eiffel?"*) y el vector de un pasaje declarativo
  (*"La Torre Eiffel está en París"*) es estructuralmente más baja de lo que la
  relevancia semántica justificaría, por la asimetría gramatical entre pregunta y
  pasaje. Esto dificulta la recuperación de alta precisión y, según el artículo, es una
  causa directa de que el paso de generación termine alucinando cuando el pasaje
  correcto no fue recuperado.
- **Necesidad que queda abierta:** el método es explícitamente extractivo. El propio
  autor limita su alcance a la recuperación de un hecho o un párrafo, y reconoce que las
  preguntas que exigen razonamiento multi-salto, agregación o síntesis de varias fuentes
  *"podrían requerir avances adicionales"* — la misma necesidad de integración de
  conocimiento disperso que atacan HippoRAG y GraphRAG, aquí dejada explícitamente fuera
  de alcance.

### 10.4 Sustento tecnológico

Para cada unidad de contenido, un LLM ajustado por instrucciones genera un conjunto de
preguntas candidatas —variando fraseo, nivel de detalle y errores ortográficos
ocasionales, para mayor robustez—; cada pregunta generada se vectoriza y se guarda junto
con un identificador de huella (SHA-256) hacia el contenido de origen, lo que permite
reindexar solo lo que cambió cuando la fuente se actualiza. En consulta, se calcula
similitud coseno entre la pregunta del usuario y todas las preguntas indexadas, y se
recupera el contenido de la pregunta con mayor similitud.

Para Wikidata específicamente: se extraen todas las declaraciones de un elemento (QID)
mediante una consulta SPARQL (publicada en el apéndice del artículo), cada tripleta
sujeto-predicado-objeto se convierte a una representación textual simple (*"India:
Independencia: 15 de agosto de 1947"*), y se generan preguntas para esa representación
igual que para un párrafo de Wikipedia — lo que extiende el método a contenido
multimedia (imágenes, audio, modelos 3D) tratándolo como metadato textual indexable de
la misma forma.

La implementación experimental usó `llama-3.1-8b-instruct-awq` para generar preguntas y
`baai/bge-small-en-v1.5` (vectores de 384 dimensiones) para los *embeddings*, indexando
menos de 1.000 artículos de Wikipedia como prototipo, corriendo como tarea en segundo
plano.

### 10.5 Contexto de aplicación

Enciclopedias y bases de conocimiento de acceso público de propósito general — el caso
de uso explícito es Wikipedia y Wikidata, con extensión declarada a contenido multimedia
a través de sus metadatos estructurados en Wikidata. No es un dominio vertical.

### 10.6 Experimentos

Limitados y sin comparación cuantitativa contra líneas base. El artículo reporta
**similitud coseno superior a 0,9 para pares de preguntas relevantes** (frente al rango
de 0,4 a 0,7 típico de comparar pregunta contra pasaje), ilustrado con ejemplos
tabulados que incluyen variantes con errores ortográficos y reformulaciones. No se
reporta precisión, exhaustividad ni ninguna métrica de sistema completo sobre un
conjunto de preguntas de evaluación, ni comparación directa bajo las mismas condiciones
contra un sistema RAG denso convencional — el propio autor lo reconoce en las
limitaciones.

### 10.7 Conclusiones

Comparar pregunta contra pregunta, en lugar de pregunta contra pasaje, produce
coincidencias de muy alta similitud y elimina el paso de generación de respuesta, lo
que —según el autor— hace al sistema rápido, económico (sin llamadas al LLM en tiempo
de consulta) y libre de alucinación por construcción, ya que nunca genera texto nuevo:
solo recupera contenido existente.

### 10.8 Conceptos y términos que introduce

Recuperación *pregunta-a-pregunta* (frente a *pregunta-a-pasaje*) · generación
anticipada de preguntas por unidad de contenido · indexación con seguimiento por huella
para reindexación selectiva · preguntas y respuestas pseudo-multimodales vía metadatos
de Wikidata · eliminación del paso de generación como estrategia de "cero alucinación
por diseño".

### 10.9 Citas textuales clave

> "Instead of embedding document content, we generate a comprehensive set of questions
> for each logical content unit using an instruction-tuned LLM." — Resumen

> "The most important advantage is that the response is hallucination-free, since we
> directly retrieve the original content instead of relying on generated answers." —
> §4.2, *Advantages*

> "The system focuses on direct fact retrieval (extractive). Answering more complex
> questions that require multi-hop reasoning, aggregation, or synthesis might require
> further advancements." — §4.3, *Limitations*

### 10.10 Relación con el patrón *LLM Wiki* y el Open Knowledge Format

Ataca un problema distinto y complementario al de las demás fichas: no busca integrar
conocimiento disperso entre documentos (como HippoRAG y GraphRAG) ni versionar
procedencia (como OKF y FAIR), sino resolver el desajuste estructural entre cómo se
formula una pregunta y cómo está escrito el conocimiento que la responde. Es aplicable
como capa de recuperación dentro de un wiki mantenido por LLM: cada página o afirmación
podría indexarse con sus propias preguntas generadas, sin cambiar en nada el formato de
las páginas ni su procedencia.

### 10.11 Preguntas abiertas que deja

1. ¿Qué precisión y exhaustividad reales tiene el sistema completo sobre un conjunto de
   evaluación con respuesta conocida, más allá de la similitud coseno de ejemplos
   ilustrativos?
2. ¿Cómo se compara, bajo las mismas condiciones, contra un sistema RAG denso
   convencional? El artículo no lo mide.
3. ¿Cómo se comporta en los más de 300 idiomas en que existe Wikipedia, dado que el
   propio autor reconoce que los LLM son eficientes solo en un subconjunto pequeño de
   ellos y que el método no se evaluó fuera del inglés?
4. ¿Cómo se extiende a preguntas que requieren varios saltos o síntesis de varias
   unidades de contenido, que el autor deja explícitamente fuera de alcance?

### 10.12 Enlace y cita APA

- Artículo: https://arxiv.org/abs/2501.11301

> Thottingal, S. (2025). *Question-to-question retrieval for hallucination-free
> knowledge access: An approach for Wikipedia and Wikidata question answering*
> (arXiv:2501.11301). arXiv. https://arxiv.org/abs/2501.11301

---

## 11. ReFinED: An Efficient Zero-shot-capable Approach to End-to-End Entity Linking

### 11.1 Ficha rápida

| | |
|---|---|
| Autores | Tom Ayoola, Shubhi Tyagi, Joseph Fisher, Christos Christodoulopoulos, Andrea Pierleoni (Amazon) |
| Tipo | Artículo de investigación con evaluación empírica y código abierto de nivel productivo |
| Publicación | *NAACL 2022* (pista de industria) · arXiv:2207.04108 · presentado 8 jul 2022 |
| Continuación | Extensión el mismo año — *Improving Entity Disambiguation by Reasoning over a Knowledge Base* (Ayoola, Fisher, Pierleoni; NAACL 2022; arXiv:2207.04106), que incorpora información de la base de conocimiento de forma diferenciable |
| Código | Sí — `github.com/alexa/refined`, Apache 2.0, modelos preentrenados descargables, instalable por `pip` |

### 11.2 Definición general

Sistema de vinculación de entidades (*entity linking*) de extremo a extremo: detecta
menciones, les asigna un tipo de entidad de grano fino (más de 1.000 clases, frente a
las ~26 categorías genéricas de un NER clásico como spaCy) y las desambigua contra
Wikipedia o Wikidata (más de 30 millones de entidades), todo en un único paso hacia
adelante de un modelo Transformer. Es capaz de vinculación *zero-shot*: puede resolver
entidades que nunca vio en entrenamiento porque las representa por su descripción
textual, no por un identificador aprendido, lo que permite añadir entidades nuevas al
sistema sin reentrenar.

Lo relevante del trabajo es que es el vinculador de entidades que GraphRAG cita como
alternativa a la coincidencia exacta de cadenas (ficha 6), y el que WikiSP afina para
resolver menciones de Wikidata (ficha 9). Es, en la práctica, la pieza de
infraestructura que varias fichas anteriores dan por sentada sin detallar cómo funciona.

### 11.3 Problemas que aborda y necesidades que abre

- **Problema del artículo:** los sistemas de vinculación de entidades previos eran
  precisos pero lentos, o rápidos pero limitados a un conjunto fijo y pequeño de tipos de
  entidad —como los ~26 de spaCy—, lo que dificulta desambiguar casos donde el tipo
  grueso no basta. El ejemplo del propio artículo: "Inglaterra" y "México" son ambos
  {GPE - país} para spaCy, pero ReFinED distingue "selección nacional de fútbol" de
  "país", lo que reduce el espacio de candidatos y mejora la desambiguación.
- **Necesidad que queda abierta:** el sistema resuelve bien la vinculación de una
  entidad ya existente en la base, pero no aborda —porque no es su problema— la fusión
  de dos menciones distintas que deberían unirse en un solo nodo de un grafo de
  conocimiento cuando ninguna de las dos tiene entrada previa en Wikipedia o Wikidata;
  ese es el terreno de la resolución de entidades "abierta", más que el de la
  vinculación a una base cerrada.

### 11.4 Sustento tecnológico

**Arquitectura:** un único modelo Transformer realiza detección de menciones,
tipificación de entidad de grano fino y desambiguación de entidad para todas las
menciones de un documento en un solo paso hacia adelante.

**Entrenamiento:** conjunto de datos propio generado a partir de hiperenlaces de
Wikipedia, con más de 150 millones de menciones de entidades.

**Zero-shot:** usa descripciones textuales de las entidades —no solo su
identificador— para la desambiguación, lo que permite añadir entidades nuevas sin
reentrenar el modelo, solo actualizando los archivos de datos.

**Cuatro modelos preentrenados publicados:** `wikipedia_model` (el del artículo),
`wikipedia_model_with_numbers` (añade tipos numéricos de spaCy: fecha, cantidad,
dinero…), `aida_model` (afinado en el *dataset* AIDA para vinculación de extremo a
extremo) y `questions_model` (afinado en texto de preguntas cortas — el mismo tipo de
dato que usa WikiSP, ficha 9).

**Reproducibilidad:** instalable por `pip`, *script* de replicación de resultados, de
evaluación, guías de entrenamiento y de ajuste fino, y un *script* para regenerar todos
los archivos de datos desde el volcado más reciente de Wikipedia/Wikidata —lo que
permite añadir entidades personalizadas sin reentrenar.

### 11.5 Contexto de aplicación

TIC / procesamiento de lenguaje natural, con foco explícito en extracción de entidades
a escala web. No es un dominio vertical, aunque su publicación como pista de industria y
su origen en Amazon apuntan a un caso de uso de producción, no solo de investigación.

### 11.6 Experimentos

Desambiguación de entidades (con la mención ya detectada) sobre seis bancos de pruebas
estándar, comparando el conjunto de entidades de resolución "wikipedia" (~6M) contra
"wikidata" (~33M):

| Modelo | Entidades | AIDA | MSNBC | AQUAINT | ACE2004 | CWEB | WIKI |
|---|---|---|---|---|---|---|---|
| `wikipedia_model` | wikipedia | 87,4 | 94,5 | 91,9 | 91,4 | 77,7 | 88,7 |
| `wikipedia_model` | wikidata | 85,6 | 92,8 | 90,4 | 91,1 | 76,3 | 88,2 |

El artículo reporta superar el estado del arte anterior en un promedio de 3,7 puntos F1
en estos bancos de pruebas, siendo más de 60 veces más rápido que los sistemas
competitivos previos. Para la tarea de extremo a extremo (detectar y vincular en un solo
paso), el modelo afinado en AIDA (`aida_model`) alcanza 85,0 F1 en AIDA y 75,1 en MSNBC;
el repositorio documenta además que gran parte de los errores en AIDA son en realidad
errores de anotación del propio *dataset* (menciones etiquetadas como "sin página de
Wikipedia" cuando sí la tienen), y que al filtrar esos casos el F1 en AIDA sube a 90,2.
En velocidad: el modelo procesa las 231 noticias del conjunto de prueba de AIDA en 6,5
segundos sobre una GPU V100.

### 11.7 Conclusiones

La combinación de velocidad, precisión y escala —resolver contra decenas de millones de
entidades sin perder capacidad de tiempo real— hace de ReFinED un sistema efectivo y de
bajo costo para extraer entidades de conjuntos de datos a escala web, y su capacidad
*zero-shot* le permite mantenerse actualizado con entidades nuevas sin reentrenamiento.

### 11.8 Conceptos y términos que introduce

Vinculación de entidades de extremo a extremo en un solo paso hacia adelante ·
tipificación de entidad de grano fino (más de 1.000 clases, frente a las genéricas de
NER clásico) · vinculación *zero-shot* vía descripciones textuales de entidad ·
menciones NIL (sin entidad candidata en la base) · filtrado de menciones NIL para
depurar la evaluación.

### 11.9 Citas textuales clave

> "The model performs mention detection, fine-grained entity typing, and entity
> disambiguation for all mentions within a document in a single forward pass." — README,
> §*Model Architecture*

> "The combination of accuracy, speed, and scalability of ReFinED means the system is
> capable of being deployed to extract entities from web-scale datasets with higher
> accuracy and an order of magnitude lower cost than existing approaches." — README,
> §*Overview*

> "ReFinED is capable of zero-shot entity linking, which means the data files (which
> will include recently added entities) can be updated without having retrained the
> model." — README, §*Generating and updating the data files*

### 11.10 Relación con el patrón *LLM Wiki* y el Open Knowledge Format

ReFinED es la pieza de infraestructura que hace posible, en la práctica, la resolución
de entidades que HippoRAG resuelve por coincidencia exacta de cadenas (ficha 7) y que
GraphRAG cita como alternativa más flexible a su propio método (ficha 6): decidir si dos
menciones de texto se refieren al mismo nodo del grafo. Frente al patrón *LLM Wiki* y
OKF, resuelve un problema distinto y anterior —vincular una mención a una entidad ya
existente en una base cerrada (Wikipedia/Wikidata)—, mientras que el patrón *LLM Wiki*
construye sus propias páginas de concepto sin una base de referencia externa a la cual
anclarlas; combinar ambos permitiría que cada página nueva del wiki se vinculara, cuando
corresponda, a la entidad de Wikidata equivalente en lugar de crear siempre una página
nueva.

### 11.11 Preguntas abiertas que deja

1. ¿Qué tan bien generaliza el modelo a dominios muy alejados de Wikipedia —texto
   científico, jerga técnica—, dado que su entrenamiento proviene enteramente de
   hiperenlaces de Wikipedia?
2. ¿Cómo se comporta cuando dos menciones deberían fusionarse en una entidad nueva que
   no existe todavía en Wikipedia ni Wikidata — el caso de resolución de entidades
   "abierta" que el sistema no está diseñado para resolver?
3. ¿Cuánto se degrada la precisión con el paso del tiempo si los archivos de datos no
   se regeneran contra volcados recientes de Wikipedia/Wikidata?

### 11.12 Enlace y cita APA

- Artículo: https://arxiv.org/abs/2207.04108
- Extensión: https://arxiv.org/abs/2207.04106
- Código: https://github.com/alexa/refined

> Ayoola, T., Tyagi, S., Fisher, J., Christodoulopoulos, C., & Pierleoni, A. (2022).
> ReFinED: An efficient zero-shot-capable approach to end-to-end entity linking. En
> *Proceedings of the 2022 Conference of the North American Chapter of the Association
> for Computational Linguistics: Human Language Technologies (Industry Track)*
> (arXiv:2207.04108). https://arxiv.org/abs/2207.04108

---

## 12. Lost in the Middle: How Language Models Use Long Contexts

### 12.1 Ficha rápida

| | |
|---|---|
| Autores | Nelson F. Liu, Kevin Lin, John Hewitt, Ashwin Paranjape, Michele Bevilacqua, Fabio Petroni, Percy Liang (Stanford) |
| Tipo | Artículo de investigación con evaluación empírica extensa y código abierto |
| Publicación | *Transactions of the Association for Computational Linguistics (TACL)*, 2023 · arXiv:2307.03172 · v1 6 jul 2023 · v3 20 nov 2023 |
| Continuación | Motivó una línea de trabajo completa sobre degradación de contexto largo (*"context rot"*, pruebas de "aguja en el pajar") que otras fichas de este documento citan |
| Código | Sí — `github.com/nelson-liu/lost-in-the-middle`, MIT, con los datos de los experimentos publicados |

### 12.2 Definición general

Mide de forma sistemática cómo usan realmente los modelos de lenguaje un contexto largo
cuando la información relevante está en distintas posiciones dentro de ese contexto. El
hallazgo central es una **curva en forma de U**: el desempeño es más alto cuando la
información relevante está al principio o al final del contexto, y cae de forma marcada
cuando está en el medio —incluso en modelos diseñados explícitamente para contextos
largos—.

Lo relevante del trabajo es que es la fuente primaria que fichas anteriores de este
documento (MemGPT, GraphRAG) citan de segunda mano para justificar por qué "meter todo
en el contexto" no es una solución al problema de la memoria; aquí el hallazgo queda
respaldado con datos propios, tarea por tarea y posición por posición.

### 12.3 Problemas que aborda y necesidades que abre

- **Problema del artículo:** se sabía que los modelos podían aceptar contextos largos
  como entrada, pero se sabía poco sobre si realmente **usan** esa información de forma
  uniforme a lo largo de todo el contexto, o si la posición importa.
- **Necesidad que queda abierta:** los autores muestran el fenómeno y proponen nuevos
  protocolos de evaluación para modelos de contexto largo, pero no resuelven el
  problema —el artículo es un diagnóstico, no una solución—. Queda abierto cómo diseñar
  sistemas y estrategias de recuperación que coloquen deliberadamente la información
  relevante en los extremos del contexto, o que eviten depender de la posición.

### 12.4 Sustento tecnológico

Dos tareas experimentales, ambas con datos y *scripts* de generación publicados:

- **Preguntas y respuestas multi-documento:** se coloca el documento que contiene la
  respuesta en una posición controlada (índice 0, 4, 9… hasta 29) dentro de un conjunto
  de 10, 20 o 30 documentos recuperados, y se mide la exactitud de la respuesta según
  esa posición.
- **Recuperación de clave-valor:** una tarea sintética donde el modelo debe recuperar el
  valor asociado a una clave dentro de una lista ordenada de pares clave-valor, con la
  clave objetivo también en una posición controlada — aísla el efecto de posición del
  efecto de comprensión semántica del texto.

**Reproducibilidad:** repositorio con los datos exactos de ambas tareas en formato JSON
documentado, *scripts* para generar nuevos ejemplos con otro número de documentos o de
pares clave-valor, y *scripts* de evaluación para reproducir los resultados con varios
modelos (Claude-1.3, GPT-3.5-Turbo, MPT-30B-Instruct, LongChat-13B, con instrucciones
añadidas después para LLaMA-2).

### 12.5 Contexto de aplicación

TIC / procesamiento de lenguaje natural, evaluación de modelos de propósito general
sobre preguntas de dominio abierto (basadas en NaturalQuestions). No es un dominio
vertical; su hallazgo es transversal a cualquier sistema que dependa de meter mucho
contexto recuperado en un *prompt*.

### 12.6 Experimentos

Resultados completos publicados en el apéndice, con el patrón de la U consistente en
todos los tamaños evaluados. Con 20 documentos totales, por ejemplo:

| Modelo | Índice 0 (inicio) | Índice 9 (medio) | Índice 19 (final) |
|---|---|---|---|
| Claude-1.3 | 59,9 % | 56,8 % | 60,1 % |
| GPT-3.5-Turbo | 75,8 % | 53,8 % | 63,2 % |
| MPT-30B-Instruct | 53,7 % | 52,2 % | 56,3 % |
| LongChat-13B (16K) | 68,6 % | 55,3 % | 55,0 % |

La caída en la posición central se repite con 10 y con 30 documentos, y persiste en
modelos con ventanas de contexto explícitamente extendidas (Claude-1.3 100K,
GPT-3.5-Turbo 16K, LongChat-13B 16K) — extender la ventana no corrige el sesgo de
posición. El artículo reporta además que, en la tarea de preguntas y respuestas, el
desempeño con **más documentos recuperados no mejora de forma monótona**: en algunos
casos añadir más contexto (30 documentos frente a 10) degrada el desempeño incluso
cuando la respuesta correcta sigue presente.

### 12.7 Conclusiones

Los modelos de lenguaje actuales no usan la información de un contexto largo de forma
robusta: la posición de la información relevante importa tanto como su presencia. Esto
tiene implicaciones directas para el diseño de sistemas de recuperación —dónde colocar
los documentos recuperados dentro del *prompt* no es neutro— y motiva nuevos protocolos
de evaluación que midan explícitamente el efecto de la posición, no solo la exactitud
promedio.

### 12.8 Conceptos y términos que introduce

Curva de desempeño en forma de **U** según la posición de la información relevante ·
tarea de recuperación clave-valor sintética como control del efecto de posición ·
degradación no monótona con más documentos recuperados · evaluación explícita por
posición, frente a exactitud promedio agregada.

### 12.9 Citas textuales clave

> "Performance is often highest when relevant information occurs at the beginning or
> end of the input context, and significantly degrades when models must access relevant
> information in the middle of long contexts." — Resumen

> "Current language models do not robustly make use of information in long input
> contexts." — Conclusión

### 12.10 Relación con el patrón *LLM Wiki* y el Open Knowledge Format

Este hallazgo es el argumento técnico detrás de una decisión de diseño que varias fichas
de este documento comparten: MemGPT lo cita para justificar por qué paginar información
dentro y fuera del contexto es mejor que intentar mantenerlo todo cargado, y GraphRAG lo
cita para justificar por qué prefiere resúmenes de comunidad compactos en vez de
concatenar todo el corpus. El patrón *LLM Wiki* hereda la misma lógica de forma
implícita: compilar el conocimiento en páginas breves y enlazadas, en lugar de depender
de que un modelo lea correctamente un documento largo sin importar dónde esté la
información dentro de él, es una respuesta directa a este problema.

### 12.11 Preguntas abiertas que deja

1. ¿Por qué ocurre el sesgo en forma de U a nivel arquitectónico? El artículo lo
   documenta empíricamente pero no explica el mecanismo interno que lo produce.
2. ¿Se mantiene el mismo patrón en tareas distintas a preguntas y respuestas y
   recuperación clave-valor —por ejemplo, síntesis o razonamiento multi-salto—?
3. ¿Qué estrategias de reordenamiento de contexto mitigan el efecto sin rediseñar el
   modelo?

### 12.12 Enlace y cita APA

- Artículo: https://arxiv.org/abs/2307.03172
- Código: https://github.com/nelson-liu/lost-in-the-middle

> Liu, N. F., Lin, K., Hewitt, J., Paranjape, A., Bevilacqua, M., Petroni, F., & Liang,
> P. (2023). Lost in the middle: How language models use long contexts
> (arXiv:2307.03172). *Transactions of the Association for Computational Linguistics*.
> https://arxiv.org/abs/2307.03172

---

## 13. LongMamba

### 13.1 Ficha rápida

| | |
|---|---|
| Autor | Jia Zhang (usuario de GitHub `jzhang38`) — exploración técnica individual, no artículo formal |
| Tipo | Bitácora de investigación documentada en un README — literatura gris, sin revisión por pares; el propio autor advierte que el código "no está pulido de ninguna manera" |
| Publicación | Repositorio de GitHub, sin fecha de publicación formal declarada |
| Continuación | No declarada; se apoya en el repositorio oficial de Mamba y en el repositorio *yarn* para partes del código |
| Código | Sí, pero explícitamente experimental y sin pulir |

### 13.2 Definición general

Documenta una serie de experimentos personales sobre si Mamba —una arquitectura de
espacio de estados alternativa al Transformer, sin mecanismo de atención— puede extender
su ventana de contexto de entrenamiento (2.048 *tokens*) más allá de ese límite. Prueba
primero que Mamba, igual que un Transformer, sufre una degradación fuerte de perplejidad
fuera de su longitud de entrenamiento; luego entrena el modelo directamente en
secuencias más largas (hasta 16.384 *tokens* con 8 GPU A100) y confirma la capacidad de
recuperación con una prueba de "aguja en el pajar" (recuperar una clave insertada en un
texto largo).

Lo relevante del trabajo es que es evidencia empírica informal de que el problema de
contexto largo no es exclusivo de los Transformers —el mismo síntoma de degradación
aparece en una arquitectura distinta—, y de que entrenar directamente en secuencias más
largas sí mejora la recuperación, aunque a costa de memoria de GPU.

### 13.3 Problemas que aborda y necesidades que abre

- **Problema:** no estaba claro si el sesgo de posición y la degradación fuera de la
  longitud de entrenamiento —documentados para Transformers en "Lost in the Middle",
  ficha 12— eran un problema específico del mecanismo de atención o algo más general de
  los modelos de secuencia. El autor lo prueba directamente sobre Mamba, que no usa
  atención.
- **Necesidad que queda abierta:** el propio autor reconoce que el entrenamiento al
  estilo Transformer-XL —para escalar la longitud de contexto sin límite teórico,
  aprovechando que el estado oculto de Mamba no crece con el contexto— todavía no es
  estable, y que la implementación actual de Mamba no soporta esa característica de
  forma nativa.

### 13.4 Sustento tecnológico

Parte de `state-spaces/mamba-2.8b-slimpj` (modelo preentrenado de Mamba). Explora
primero un ajuste manual del parámetro de discretización (`delta`) de los modelos de
espacio de estados —análogo, según el autor, a la interpolación posicional de los
Transformers— sin resultado favorable; luego entrena directamente en 16.384 *tokens* de
contexto con paralelismo FSDP sobre 8 GPU A100 de 80 GB, en 9 horas. Prueba la capacidad
de memoria con una variante propia de recuperación de clave-valor de un solo paso,
distinta de la prueba estándar de "aguja en el pajar" que usa documentos reales
(referencia explícitamente ambas). Explora, sin implementarlo por completo, un esquema
de entrenamiento al estilo Transformer-XL que reutilizaría el estado oculto entre lotes
para escalar el contexto sin límite de memoria teórico — una ventaja estructural de
Mamba frente a un Transformer, cuya caché de claves y valores sí crece con el contexto.

### 13.5 Contexto de aplicación

TIC / arquitecturas de modelos de lenguaje de propósito general. No es un dominio
vertical; es investigación de infraestructura de modelos, no de una aplicación final.

### 13.6 Experimentos

**(No aplica un protocolo formal.)** Los resultados son gráficas de perplejidad y de
exactitud de recuperación sobre un modelo propio, sin comparación tabulada contra otras
arquitecturas bajo las mismas condiciones, sin conjunto de prueba estándar de la
literatura, y sin revisión externa. El propio autor presenta el trabajo como una
bitácora de exploración, no como un estudio concluyente: reporta que el modelo
"recupera casi perfectamente" en 16.384 *tokens* y empieza a degradarse en 32.768, y
que —a diferencia de un Transformer— Mamba olvida el *inicio* del contexto al crecer la
longitud, en vez del medio.

### 13.7 Conclusiones

Entrenar directamente en secuencias más largas mejora sustancialmente la capacidad de
recuperación de Mamba, sin necesidad de ajustar manualmente los parámetros de
discretización. La arquitectura recurrente de Mamba ofrece, en teoría, una ventaja de
memoria sobre el Transformer para escalar el contexto de forma indefinida, pero esa
ventaja no está todavía implementada de forma estable.

### 13.8 Conceptos y términos que introduce

Modelos de espacio de estados (Mamba) como alternativa al Transformer para contexto
largo · parámetro de discretización (`delta`) como análogo del *embedding* posicional ·
prueba de recuperación de clave con un solo paso, variante de "aguja en el pajar" ·
entrenamiento al estilo Transformer-XL sobre una arquitectura recurrente, con estado
oculto que no crece con el contexto.

### 13.9 Citas textuales clave

> "At the end of this study, we managed to make state-spaces/mamba-2.8b-slimpj retrieve
> nearly perfectly on a context length of 16384." — README

> "It is interesting to see how Mamba starts to forget the beginning of the context when
> we increase the context length, which is very different from the Transformer that
> lost in the middle." — README

> "I have not polished the code in any way, so please bear with the spaghetti." — README

### 13.10 Relación con el patrón *LLM Wiki* y el Open Knowledge Format

Es una exploración del mismo problema de fondo que documenta "Lost in the Middle"
(ficha 12) —qué tan bien usa un modelo la información según su posición en el
contexto—, pero desde una arquitectura alternativa al Transformer. No tiene relación
directa con el patrón *LLM Wiki* ni con OKF: no propone ninguna forma de representar o
versionar conocimiento, solo estudia cuánto contexto crudo puede sostener un modelo
antes de degradarse — el problema exacto que el patrón *LLM Wiki* evita por diseño, al
compilar el conocimiento en páginas breves en lugar de depender de ventanas de contexto
cada vez más grandes.

### 13.11 Preguntas abiertas que deja

1. ¿Es estable y reproducible el entrenamiento al estilo Transformer-XL sobre Mamba,
   más allá de la exploración preliminar documentada?
2. ¿Se sostiene la ventaja de "olvidar el inicio en vez del medio" en tareas distintas a
   la recuperación de una sola clave?
3. ¿Cómo se compara formalmente contra Transformers de contexto largo bajo el mismo
   protocolo que usa "Lost in the Middle"?

### 13.12 Enlace y cita APA

- Repositorio: https://github.com/jzhang38/LongMamba

> Zhang, J. (2024). *LongMamba* [Software]. GitHub. https://github.com/jzhang38/LongMamba

---

## 14. Llama-2-7B-32K-Instruct

### 14.1 Ficha rápida

| | |
|---|---|
| Autores | Yucheng Lu (usuario `EugeneLYC`), equipo de Together AI |
| Tipo | Receta técnica de ajuste fino documentada en un README y un blog — literatura técnica de producto, sin revisión por pares ni evaluación comparativa publicada |
| Publicación | Repositorio de GitHub, con entrada de blog asociada de Together AI |
| Continuación | No declarada; construida sobre `Llama-2-7B-32K`, el modelo base de contexto extendido de Together AI |
| Código | Sí — Apache 2.0, con los *scripts* del flujo completo (destilación, entrenamiento, prueba, despliegue) publicados |

### 14.2 Definición general

Documenta el proceso completo para afinar Llama-2-7B con una ventana de contexto de 32K
*tokens* hasta convertirlo en un modelo de instrucciones, combinando tres fuentes de
datos de entrenamiento: 19.000 conversaciones de una y varias rondas generadas por
destilación desde Llama-2-70B-Chat —siguiendo el mismo paradigma de Alpaca, Vicuna y
WizardLM: usar un modelo grande para generar los datos de entrenamiento de uno más
pequeño—, resumen de contexto largo con el *dataset* BookSum, y preguntas y respuestas
multi-documento (MQA) — la misma familia de tarea que usa "Lost in the Middle" (ficha
12) para medir el sesgo de posición.

Lo relevante del trabajo es que es un caso concreto y documentado de cómo se entrena un
modelo para que de verdad aproveche una ventana de contexto larga —no solo que la
acepte—, mezclando explícitamente entrenamiento de instrucciones con entrenamiento de
comprensión de contexto largo, en vez de asumir que esa capacidad emerge sola al
extender la ventana.

### 14.3 Problemas que aborda y necesidades que abre

- **Problema:** un modelo con una ventana de contexto técnicamente más grande no
  necesariamente sabe usarla bien para seguir instrucciones sobre contenido largo —
  aceptar más *tokens* no es lo mismo que razonar bien sobre ellos, que es precisamente
  el fenómeno que documenta "Lost in the Middle"—. La receta busca cerrar esa brecha con
  datos de entrenamiento específicos para contexto largo, no solo con arquitectura.
- **Necesidad que queda abierta:** el repositorio no publica ninguna evaluación
  cuantitativa de si el modelo resultante efectivamente mitiga el sesgo de posición
  documentado en "Lost in the Middle", ni una comparación contra el modelo base sin este
  ajuste fino adicional — la receta se documenta, pero su efectividad no se mide con el
  mismo rigor que otras fichas de este documento.

### 14.4 Sustento tecnológico

Flujo de cuatro pasos, cada uno con *script* o comando publicado:

1. **Destilar:** generar datos de instrucción consultando Llama-2-70B-Chat a través de
   una API de inferencia, con instrucciones extraídas de ShareGPT-90K.
2. **Entrenar:** subir el conjunto de datos combinado (50 % instrucciones + 25 % BookSum
   + 25 % MQA) y lanzar el trabajo de ajuste fino mediante una API de entrenamiento
   gestionada.
3. **Probar:** validar el modelo resultante en un entorno de prueba interactivo antes de
   desplegarlo.
4. **Desplegar:** exponer el modelo afinado a través de la misma API de inferencia.

**Reproducibilidad:** *script* de recolección de instrucciones de 122 líneas publicado,
formato de datos documentado (`jsonl` con el patrón `[INST] ... [/INST]`), y el
conjunto de datos de instrucciones publicado aparte para reutilización.

### 14.5 Contexto de aplicación

TIC / modelos de lenguaje de propósito general con contexto extendido, orientado
explícitamente a un flujo de producción de extremo a extremo —afinar, probar y
desplegar— sobre una plataforma comercial de inferencia y ajuste fino. No es un dominio
vertical.

### 14.6 Experimentos

**(No aplica.)** El repositorio documenta el proceso de construcción del modelo, no una
evaluación de su desempeño: no hay tabla de resultados, ni comparación contra líneas
base, ni métrica reportada sobre las tareas de contexto largo que el propio modelo usa
para entrenarse. Es una receta de ingeniería, no un experimento medido.

### 14.7 Conclusiones

Un modelo de contexto extendido se beneficia de una mezcla deliberada de datos de
instrucciones generales y de tareas específicas de contexto largo —resumen, preguntas
multi-documento— durante el ajuste fino, y el proceso completo, desde la generación de
datos hasta el despliegue, puede documentarse como una receta reproducible sobre una
plataforma de entrenamiento gestionada.

### 14.8 Conceptos y términos que introduce

Destilación de instrucciones desde un modelo mayor, siguiendo el paradigma
Alpaca/Vicuna/WizardLM/Orca · mezcla de datos de entrenamiento por proporción
(instrucciones + resumen de contexto largo + preguntas multi-documento) · flujo de
cuatro pasos destilar–entrenar–probar–desplegar sobre una plataforma gestionada.

### 14.9 Citas textuales clave

> "Llama-2-7B-32K-Instruct is fine-tuned over a combination of two data sources: [...]
> Long-context Summarization and Long-context QA." — README

> "The final data mixture used for model finetuning is: 19K instruction (50%) + BookSum
> (25%) + MQA (25%)." — README

### 14.10 Relación con el patrón *LLM Wiki* y el Open Knowledge Format

Ataca el mismo síntoma que documenta "Lost in the Middle" (ficha 12) desde el lado del
entrenamiento, en vez del lado de la arquitectura de recuperación: si el modelo aprende
explícitamente, durante el ajuste fino, a resolver preguntas multi-documento y a resumir
contenido largo, quizás use mejor el contexto que se le da. Es una apuesta alternativa
—y no excluyente— a la que hacen HippoRAG, GraphRAG y el patrón *LLM Wiki*, que en
cambio reducen lo que hay que meter en el contexto en primer lugar, en vez de entrenar
al modelo para que use mejor un contexto grande.

### 14.11 Preguntas abiertas que deja

1. ¿El modelo resultante mitiga de forma medible el sesgo de posición documentado en
   "Lost in the Middle", o solo mejora en las tareas específicas de su mezcla de
   entrenamiento?
2. ¿Cómo se compara contra el modelo base `Llama-2-7B-32K` sin este ajuste fino
   adicional, bajo el mismo protocolo?
3. ¿Qué tan bien generaliza la mezcla de datos a tareas de contexto largo distintas de
   resumen y preguntas multi-documento?

### 14.12 Enlace y cita APA

- Repositorio: https://github.com/togethercomputer/llama-2-7b-32k-instruct

> Together AI. (2023). *Llama-2-7B-32K-Instruct* [Software]. GitHub.
> https://github.com/togethercomputer/llama-2-7b-32k-instruct

---

## 15. Edisum: Summarizing and Explaining Wikipedia Edits at Scale

### 15.1 Ficha rápida

| | |
|---|---|
| Autores | Marija Šakota, Isaac Johnson, Guosheng Feng, Robert West (EPFL + Wikimedia Foundation) |
| Tipo | Artículo de investigación con evaluación automática y humana, y código abierto |
| Publicación | arXiv:2404.03428 · v1 4 abr 2024 · v2 18 ago 2024 |
| Continuación | No declarada; modelos y conjunto de datos publicados en HuggingFace |
| Código | Sí — `github.com/epfl-dlab/edisum`, MIT, con el *dataset* y cinco modelos entrenados descargables |

### 15.2 Definición general

Propone un modelo que sugiere resúmenes de edición para Wikipedia —el comentario corto
que un editor deja explicando qué cambió y por qué en una edición—, generándolo
directamente a partir del *diff* (la diferencia entre la versión anterior y la nueva de
un artículo). Es una tarea de mantenimiento real y a gran escala: Wikipedia recibe más
de 3 millones de ediciones al mes solo en inglés, y estos resúmenes son lo primero que
ve un moderador para decidir si acepta o rechaza un cambio.

Lo relevante del trabajo es que es un caso medido, en un wiki real y a escala de
producción, de un problema que otras fichas de este documento dan por hecho: cómo
generar automáticamente el registro de qué cambió y por qué en un cuerpo de
conocimiento mantenido de forma continua — el equivalente directo del `log.md` que el
patrón *LLM Wiki* pide llevar, pero aquí evaluado empíricamente en el mayor wiki
mantenido del mundo.

### 15.3 Problemas que aborda y necesidades que abre

- **Problema del artículo:** muchos resúmenes de edición faltan, son incompletos, o son
  "enlatados" —frases genéricas como *"Corregido typo"* que no describen realmente el
  cambio—. El análisis cualitativo propio de los autores (100 ediciones codificadas por
  dos anotadores) encuentra que ~35 % de los resúmenes existentes son engañosos o
  demasiado vagos, y que solo el 30–40 % intenta explicar el *por qué* del cambio,
  frente a un ~80 % que describe el *qué*.
- **Necesidad que queda abierta:** los propios autores reconocen que el "por qué" de
  una edición a menudo requiere contexto externo que el modelo no tiene —qué fuente se
  añadió, qué evento del mundo real motivó el cambio—. El sistema resuelve
  razonablemente el "qué", no el "por qué": es la misma limitación de fondo que
  enfrenta cualquier sistema que documente cambios de conocimiento a partir solo del
  *diff*, sin acceso a la intención de quien editó.

### 15.4 Sustento tecnológico

**Restricción de diseño clave:** no basta con pedirle a un LLM comercial que resuelva
la tarea, porque Wikipedia necesita un modelo pequeño, rápido —casi en tiempo real, ya
que el resumen se genera en el momento de la edición— y ejecutable en CPU, dado el
acceso limitado de la fundación a GPUs.

**Generación de datos sintéticos:** se usa `gpt-3.5-turbo` (con *prompt* de cinco
ejemplos) para generar resúmenes de alta calidad a partir de *diffs* reales. Los
autores explican por qué un LLM comercial no sirve como producto final pese a resolver
bien la tarea: no sigue las normas de estilo propias de la comunidad de Wikipedia.

**Modelo final:** `LongT5` (220 millones de parámetros, elegido por su capacidad de
manejar entradas más largas que otros modelos pequeños, ya que el 4,6 % de las
ediciones supera los 512 *tokens* estándar), afinado con distintas proporciones de
datos sintéticos frente a datos humanos reales (0 %, 25 %, 50 %, 75 %, 100 %) — cinco
variantes llamadas `Edisum[S%]`.

**Representación de entrada:** el *diff* se reduce a las oraciones que cambiaron,
separadas con marcadores `<old_text>` / `<new_text>` y `<sent_sep>`, en vez de pasar
las revisiones completas — mantiene el *prompt* corto y centrado en lo que importa.

**Reproducibilidad:** repositorio con *scripts* de entrenamiento e inferencia, los
cinco modelos y el conjunto de datos publicados en HuggingFace, y una herramienta para
probar cualquier edición real de Wikipedia por enlace, o cualquier texto de entrada
arbitrario.

### 15.5 Contexto de aplicación

Gestión de conocimiento colaborativo a gran escala — moderación de contenido en
Wikipedia. Caso de uso muy específico dentro de TIC, pero generalizable a cualquier
plataforma de edición colaborativa que necesite explicar automáticamente sus cambios.

### 15.6 Experimentos

**Evaluación automática (MoverScore, similitud semántica entre el resumen generado y
el existente):** GPT-4 (0,724) y GPT-3,5 (0,722) superan a todas las variantes de
Edisum; entre ellas, `Edisum[75%]` y `Edisum[100%]` rinden mejor que `Edisum[0%]`
—entrenado solo con datos humanos existentes—, lo que confirma que entrenar con datos
sintéticos de mayor calidad ayuda más que entrenar solo con los resúmenes reales, que
son de calidad mixta.

**Evaluación humana** (100 ediciones, 3 anotadores independientes; cada uno elige el
mejor y el peor resumen entre cuatro: editor humano, `Edisum[0%]`, `Edisum[100%]` y
GPT-4): GPT-4 es elegido "mejor" con más frecuencia y "peor" con menos frecuencia;
`Edisum[0%]` muestra el patrón opuesto. **Los editores humanos y `Edisum[100%]` quedan
empatados en un término medio**, sin diferencia estadísticamente significativa entre
ambos —test binomial, p = 0,883, sobre las 46 de 99 muestras donde no hubo empate
directo—. El acuerdo entre anotadores (Kendall's τ) fue de 0,588, 0,556 y 0,562 entre
los tres pares de anotadores — acuerdo moderado a fuerte.

**Análisis de error:** el modelo pequeño (220M parámetros) tiene más dificultad que
GPT-4 en tareas complejas de resumen de edición; los errores de Edisum y GPT-4 son en
su mayoría resúmenes poco exhaustivos, mientras que los errores de editores humanos
tienden a ser resúmenes poco claros o poco específicos.

### 15.7 Conclusiones

Un modelo pequeño (220M parámetros), afinado con una mezcla curada de datos humanos y
sintéticos, rinde al mismo nivel que los editores humanos en la evaluación con jueces
humanos —aunque con menos varianza—, aunque un LLM comercial grande sigue rindiendo
mejor en la métrica automática. Los LLM comerciales resuelven bien la tarea pero no son
aptos para desplegar en Wikipedia por razones de costo, velocidad y alineación con las
normas de código abierto de la comunidad; los modelos abiertos pequeños evaluados
(Llama 3 8B) fallan en la tarea sin ajuste fino.

### 15.8 Conceptos y términos que introduce

Resumen de edición (*edit summary*) como género de texto con dos componentes —qué se
hizo, por qué se hizo— y grado de "generabilidad" distinto para cada uno · generación
de datos sintéticos con un LLM grande para afinar un modelo pequeño de despliegue ·
representación de un *diff* como conjunto de oraciones añadidas o eliminadas, no como
texto completo · Plackett-Luce (generalización de Bradley-Terry) para modelar rankings
con empates en evaluación humana.

### 15.9 Citas textuales clave

> "Edit summaries are crucial for maintaining the encyclopedia: they are the first
> thing seen by content moderators and they help them decide whether to accept or
> reject an edit." — Resumen

> "Our model performs on par with human editors. Commercial large language models are
> able to solve this task better than human editors, but are not well suited for
> Wikipedia, while open-source ones fail on this task." — Resumen

> "These results indicate that Edisum[100%] performs equally well as human editors, but
> with less variance." — §6.2

### 15.10 Relación con el patrón *LLM Wiki* y el Open Knowledge Format

Edisum resuelve, con datos reales y a escala de producción, la operación que el patrón
*LLM Wiki* asume sin especificar cómo hacerla: escribir la entrada del `log.md` que
explica qué cambió y por qué en cada actualización de una base de conocimiento
mantenida. Es también evidencia directa a favor de uno de los campos que OKF v0.2
formaliza como opcional (`generated`, la procedencia de un cambio): aquí se muestra que
generar automáticamente esa explicación es una tarea viable y medible, que una
comunidad de mantenimiento real —Wikipedia— ya necesita resolver hoy, no una función
teórica del formato.

### 15.11 Preguntas abiertas que deja

1. ¿Cómo cerrar la brecha entre el modelo pequeño desplegable y GPT-4, sin perder la
   velocidad y el costo que hacen viable el despliegue a escala de Wikipedia? Señalado
   explícitamente como trabajo futuro.
2. ¿Aprende el modelo entrenado mayoritariamente con datos sintéticos las normas y
   abreviaciones propias de la comunidad editora, o solo imita el estilo de las
   demostraciones del LLM que generó los datos?
3. ¿Qué tan bien generaliza a ediciones "exóticas", dado que el conjunto de
   entrenamiento se limitó a editores con al menos 30 ediciones previas?

### 15.12 Enlace y cita APA

- Artículo: https://arxiv.org/abs/2404.03428 · PDF: https://arxiv.org/pdf/2404.03428
- Código: https://github.com/epfl-dlab/edisum

> Šakota, M., Johnson, I., Feng, G., & West, R. (2024). *Edisum: Summarizing and
> explaining Wikipedia edits at scale* (arXiv:2404.03428). arXiv.
> https://arxiv.org/abs/2404.03428

---

## 16. KnowHalu: Hallucination Detection via Multi-Form Knowledge Based Factual Checking

### 16.1 Ficha rápida

| | |
|---|---|
| Autores | Jiawei Zhang, Chejian Xu (UIUC), Yu Gai, Dawn Song (UC Berkeley), Freddy Lecue (JPMorganChase AI Research), Bo Li (UChicago y UIUC) |
| Tipo | Artículo de investigación con evaluación empírica extensa y código abierto |
| Publicación | arXiv:2404.02935 · presentado 3 abr 2024 |
| Continuación | No declarada |
| Código | Sí — `github.com/javyduck/knowhalu` |

### 16.2 Definición general

Propone un método de dos fases para detectar alucinaciones en respuestas generadas por
un LLM: primero una comprobación de **alucinación por no-fabricación** —la respuesta da
un hecho real, pero que no responde a la pregunta formulada, un tipo de error que las
verificaciones factuales estándar no capturan porque el hecho en sí es correcto—, y
después una comprobación factual de cinco pasos que combina conocimiento estructurado
(tripletas extraídas) y no estructurado (pasajes recuperados) para juzgar cada
sub-afirmación.

Lo relevante del trabajo es que es la primera ficha de este documento que le da nombre
y mecanismo propio a un tipo de error que ninguna otra distingue: una respuesta puede
ser factualmente correcta y aun así ser una alucinación, si responde a otra cosa
distinta de lo que se preguntó.

### 16.3 Problemas que aborda y necesidades que abre

- **Problema del artículo:** los métodos previos de detección de alucinaciones se
  apoyan en la autoconsistencia del LLM —generar varias respuestas y ver si se
  contradicen— o en el conocimiento interno del modelo, y ambos enfoques están
  limitados por lo que el modelo ya "sabe". Los métodos de verificación factual con
  conocimiento externo mejoran esto, pero, según los autores, aun con conocimiento
  extraído correctamente, el modelo tiene dificultades para razonar sobre afirmaciones
  complejas con varias partes.
- **Necesidad que queda abierta:** el propio artículo reconoce que en aproximadamente
  el 10 % del conjunto de prueba, el modelo se niega a generar las subconsultas
  necesarias —por alineación ética del modelo comercial, o por dificultad genuina para
  descomponer contenido con matices—, lo que introduce un sesgo en la medición del
  desempeño real del método.

### 16.4 Sustento tecnológico

**Fase 1 — comprobación de no-fabricación:** extrae de la respuesta el hecho específico
que se está afirmando y verifica si ese hecho responde realmente a lo que la pregunta
pedía, antes de gastar ningún paso de verificación factual sobre una respuesta que ya
es irrelevante por diseño.

**Fase 2 — comprobación factual de cinco pasos:**

1. Razonamiento paso a paso que descompone la consulta original en subconsultas más
   pequeñas.
2. Recuperación de conocimiento para cada subconsulta, combinando RAG sobre Wikipedia
   —implementado con **WikiChat** como motor de recuperación, el mismo linaje de
   Stanford OVAL de la ficha 9— para conocimiento no estructurado, y extracción de
   tripletas para conocimiento estructurado.
3. Optimización del conocimiento recuperado: se resume y refina con un LLM antes de
   usarse.
4. Juicio basado en cada forma de conocimiento por separado.
5. Agregación de los juicios de las distintas formas de conocimiento en un veredicto
   final, que puede ser SÍ, NO o **INCONCLUSIVO** — una tercera opción que los métodos
   de referencia, forzados a un juicio binario, no tienen disponible.

**Reproducibilidad:** repositorio con *scripts* separados para cada paso del *pipeline*
—consulta, recuperación, juicio— tanto para preguntas y respuestas como para resumen.

### 16.5 Contexto de aplicación

TIC / verificación factual de contenido generado por modelos de lenguaje, evaluado
sobre dos tareas de dominio abierto: preguntas y respuestas, y resumen de texto. No es
un dominio vertical.

### 16.6 Experimentos

Dos tareas, con respuestas alucinadas generadas artificialmente para tener verdad de
referencia: **preguntas y respuestas** sobre HotpotQA (con respuestas alucinadas
generadas por ChatGPT) y **resumen de texto** sobre CNN/Daily Mail. Comparado contra
varias líneas base de la literatura (HaluEval en sus variantes *Vanilla*,
*Chain-of-Thought* y *Knowledge*, y WikiChat), medido con tasa de verdaderos positivos
(TPR), tasa de verdaderos negativos (TNR) y exactitud promedio.

Para el modelo Starling-7B en preguntas y respuestas, por ejemplo:

| Método | TPR | TNR | Exactitud promedio |
|---|---|---|---|
| HaluEval (Knowledge) | 68,1 % | 65,6 % | 66,85 % |
| **KnowHalu (No estructurado)** | 68,7 % | 75,9 % | **72,30 %** |

El resumen del artículo reporta una mejora promedio de **+15,65 puntos porcentuales en
preguntas y respuestas y +5,50 en resumen** frente a los métodos existentes —una cifra
agregada sobre distintos modelos y configuraciones, no una sola fila de la tabla—. Los
propios autores señalan que la métrica de exactitud es "ligeramente injusta" con
KnowHalu, porque su opción INCONCLUSIVO —que los métodos de referencia no tienen—
evita forzar un juicio binario cuando el conocimiento recuperado no basta para decidir.

### 16.7 Conclusiones

Separar la detección en dos fases —primero relevancia, después veracidad— y combinar
conocimiento estructurado y no estructurado en la fase de veracidad mejora la detección
de alucinaciones frente a métodos que usan un solo tipo de conocimiento o ninguno.
Permitir un veredicto de "inconcluso" en lugar de forzar sí/no produce juicios más
informativos, aunque penaliza la métrica de exactitud tal como está definida en la
comparación.

### 16.8 Conceptos y términos que introduce

Alucinación por no-fabricación (*non-fabrication hallucination*) — hecho correcto pero
irrelevante a la pregunta · conocimiento "multi-forma" (estructurado en tripletas + no
estructurado en pasajes) como señales complementarias · optimización del conocimiento
recuperado antes de juzgar · agregación de juicios entre formas de conocimiento ·
veredicto INCONCLUSIVO como tercera opción frente al binario sí/no.

### 16.9 Citas textuales clave

> "It identifies non-fabrication hallucinations — responses that, while factually
> correct, are irrelevant to the question or instruction." — Resumen

> "KnowHalu allows the INCONCLUSIVE option to provide more informative judgments based
> on our capable framework." — §4, discusión de resultados

### 16.10 Relación con el patrón *LLM Wiki* y el Open Knowledge Format

KnowHalu ataca, con nombre y mecanismo propios, el mismo problema que este documento ha
ido acumulando desde varias fichas: distinguir una afirmación bien fundamentada de una
que no lo está. Su distinción entre conocimiento estructurado (tripletas) y no
estructurado (pasajes recuperados con WikiChat) es, en esencia, la misma dualidad que
OKF codifica entre el *frontmatter* consultable y el cuerpo en prosa de una página. Su
tercera opción, INCONCLUSIVO, es el equivalente funcional de dejar una página del wiki
marcada como `status: draft` o sin verificar, en vez de forzarla a una afirmación
categórica sin respaldo suficiente.

### 16.11 Preguntas abiertas que deja

1. ¿Cómo se corrige el sesgo de evaluación introducido por el ~10 % de casos donde el
   modelo se niega a descomponer la consulta?
2. ¿Cómo escala el costo del *pipeline* de cinco pasos —con varias llamadas al LLM por
   subconsulta— frente a métodos de una sola pasada, en un escenario de verificación
   continua y no solo de evaluación puntual?
3. ¿Se sostiene la mejora sobre dominios de conocimiento más especializados que
   HotpotQA y CNN/Daily Mail, donde el conocimiento estructurado disponible es más
   escaso?

### 16.12 Enlace y cita APA

- Artículo: https://arxiv.org/abs/2404.02935 · PDF: https://arxiv.org/pdf/2404.02935
- Código: https://github.com/javyduck/knowhalu

> Zhang, J., Xu, C., Gai, Y., Lecue, F., Song, D., & Li, B. (2024). *KnowHalu:
> Hallucination detection via multi-form knowledge based factual checking*
> (arXiv:2404.02935). arXiv. https://arxiv.org/abs/2404.02935
