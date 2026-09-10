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
