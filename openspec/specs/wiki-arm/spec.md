# wiki-arm Specification

## Purpose
TBD - created by archiving change agente-wiki-v1. Update Purpose after archive.

## Requirements

### Requirement: Wiki on disk
El wiki SHALL ser una carpeta con `index.md`, `log.md` y una página por archivo en `pages/<slug>.md`. Cada página SHALL llevar un encabezado YAML con `titulo`, `tipo` (`paper` o `concepto`), `resumen` (una línea), `fuentes` (identificadores de arXiv) y `actualizada_en_paso`, seguido del cuerpo en Markdown.

#### Scenario: Wiki nuevo
- **WHEN** se crea un wiki en una carpeta vacía
- **THEN** existen `index.md` y `log.md`, la carpeta `pages/` está vacía y no hay páginas

#### Scenario: Escribir y leer una página
- **WHEN** se escribe una página con su encabezado y se vuelve a leer
- **THEN** se obtienen los mismos campos y el mismo cuerpo

### Requirement: Paper with span labels
La lectura de un paper para ingerirlo SHALL devolver el cuerpo de su Gold con cada fragmento citable precedido de su `span_id` entre corchetes y los encabezados sin rotular. Los `span_id` SHALL ser exactamente los que calcula `calcular_spans` sobre ese cuerpo.

#### Scenario: Rótulos
- **WHEN** se lee un paper con tres párrafos y un encabezado
- **THEN** cada párrafo aparece precedido de su `span_id`, el encabezado aparece sin rótulo y el texto original no cambia

### Requirement: Two-step ingestion
`ingerir(arxiv_id)` SHALL hacer dos llamadas al modelo a través del cliente único: un plan, que recibe el paper y el índice y devuelve qué páginas actualizar y cuáles de concepto crear, y una escritura, que recibe el paper, las páginas a actualizar y el plan, y devuelve el contenido completo de cada página. En ambos mensajes el paper SHALL ir antes que lo variable, para reutilizar el prefijo desde la caché. Las etiquetas SHALL ser `wiki-plan:<id>` y `wiki-escritura:<id>`.

#### Scenario: Ingesta de un paper
- **WHEN** se ingiere un paper en un wiki con algunas páginas
- **THEN** se hacen exactamente dos llamadas, el paper va antes que el índice y las páginas en ambos mensajes, y el resultado suma las dos llamadas

#### Scenario: Plan que nombra una página inexistente
- **WHEN** el plan pide actualizar una página que no existe
- **THEN** ese nombre se ignora y la ingesta continúa

#### Scenario: Siempre hay página del paper
- **WHEN** el plan no incluye una página para el paper
- **THEN** la escritura crea de todos modos la página de tipo `paper` del paper ingerido

### Requirement: Updates and contradictions are recorded
Las instrucciones de escritura SHALL indicar al modelo que, cuando el paper nuevo reporta un valor distinto para una magnitud que ya consta en una página, la página conserve el valor más reciente como vigente y el anterior marcado como superado con su cita, y que las afirmaciones en conflicto se escriban juntas, cada una con su cita. Las instrucciones SHALL ser generales y no mencionar preguntas, papers ni cifras del banco.

#### Scenario: Instrucciones de escritura
- **WHEN** se construye el mensaje de escritura
- **THEN** contiene la regla del valor vigente y el valor superado con sus citas, y ningún identificador de paper ni cifra

### Requirement: Valid citations and links only
Al escribir una página, el sistema SHALL conservar solo las citas `[span_id]` de papers ya ingeridos (incluido el actual) que existan en `data/gold/spans.jsonl`, y solo los enlaces `[[slug]]` cuyo destino exista una vez aplicado el lote; las demás citas SHALL eliminarse y los enlaces sin destino SHALL quedar como texto, sin corchetes, y ambos SHALL contarse. Las líneas con una cifra y ninguna cita SHALL contarse como no citadas. Los conteos SHALL quedar en el registro.

#### Scenario: Cita inventada
- **WHEN** la página escrita cita un `span_id` que no existe
- **THEN** ese `span_id` no aparece en la página guardada y el registro cuenta una cita eliminada

#### Scenario: Cita de un paper aún no ingerido
- **WHEN** la página cita un `span_id` de un paper que todavía no se ha ingerido
- **THEN** la cita se elimina y se cuenta

#### Scenario: Enlace sin destino
- **WHEN** la página enlaza a `[[otra-pagina]]` y esa página no existe después de aplicar el lote
- **THEN** el texto queda como `otra-pagina` sin corchetes y el registro cuenta un enlace roto

#### Scenario: Enlace a una página del mismo lote
- **WHEN** una página enlaza a otra que se crea en el mismo lote
- **THEN** el enlace se conserva

#### Scenario: Línea con cifra sin cita
- **WHEN** una línea del cuerpo contiene una cifra y ninguna cita
- **THEN** el registro cuenta una línea no citada

### Requirement: Index and log are maintained by the code
Tras aplicar una ingesta, el código SHALL regenerar `index.md` a partir de los encabezados de las páginas (slug, título, tipo y resumen) y SHALL añadir a `log.md` una entrada con el paso, el paper, las páginas creadas y actualizadas y los conteos de citas eliminadas, enlaces rotos y líneas no citadas. El modelo SHALL NOT escribir esos dos archivos.

#### Scenario: Registro de una ingesta
- **WHEN** termina la ingesta del paso 3
- **THEN** `log.md` tiene una entrada del paso 3 con las páginas tocadas y `index.md` lista todas las páginas existentes

### Requirement: Atomic ingestion with snapshots
Si la salida del modelo no es un JSON válido con la estructura pedida, el sistema SHALL repetir esa llamada una vez indicando el error. Si sigue sin ser válida, `ingerir` SHALL lanzar un error y SHALL NOT modificar ningún archivo del wiki. Una ingesta correcta SHALL guardar una copia con un commit en el repositorio Git propio del wiki y la etiqueta `paso-<N>`. Ingerir un paper ya ingerido SHALL NOT hacer llamadas al modelo.

#### Scenario: JSON inválido que se recupera
- **WHEN** la primera respuesta de la escritura no es JSON y la segunda sí
- **THEN** la ingesta termina bien y el resultado cuenta las llamadas hechas, incluida la repetición

#### Scenario: JSON inválido dos veces
- **WHEN** las dos respuestas no son JSON válido
- **THEN** se lanza un error y las páginas, el índice y el registro quedan como estaban

#### Scenario: Copia versionada
- **WHEN** termina una ingesta correcta
- **THEN** el repositorio del wiki tiene un commit nuevo con la etiqueta `paso-<N>`

#### Scenario: Paper ya ingerido
- **WHEN** se vuelve a ingerir un paper ya ingerido
- **THEN** no se llama al modelo y el resultado reporta 0 llamadas

### Requirement: Wiki search tool
`wiki_search(consulta)` SHALL ordenar las páginas por coincidencia de palabras clave con su título, su resumen y su cuerpo, dando más peso al título y al resumen, y SHALL devolver como máximo 8 resúmenes con slug, tipo, título y resumen. Sin coincidencias SHALL devolver una lista vacía. El orden SHALL ser determinista.

#### Scenario: Coincidencia en el título
- **WHEN** se busca una palabra que está en el título de una página y en el cuerpo de otra
- **THEN** la página con la palabra en el título aparece primero

#### Scenario: Sin coincidencias
- **WHEN** se busca una palabra que no aparece en ninguna página
- **THEN** el resultado es una lista vacía

### Requirement: Wiki read tool
`wiki_read(slugs)` SHALL devolver el contenido completo de hasta 3 páginas existentes, con sus enlaces `[[slug]]`, e indicar cuáles de los nombres pedidos no existen.

#### Scenario: Páginas existentes e inexistentes
- **WHEN** se piden dos páginas que existen y una que no
- **THEN** se devuelve el contenido de las dos y se informa de la que no existe

#### Scenario: Más de tres páginas
- **WHEN** se piden cinco páginas
- **THEN** se devuelven las tres primeras y se informa de que el resto no se leyó

### Requirement: Answering by agent loop
`responder(pregunta)` SHALL ejecutar un bucle en el que, en cada turno, el modelo devuelve una acción JSON (`search`, `read` o `answer`) y el código añade el resultado de la herramienta a la conversación. El bucle SHALL terminar cuando el modelo responde, cuando se agote el tope de acciones de herramienta (`max_acciones`, 8 por defecto) o cuando haya tres búsquedas vacías seguidas; en esos dos últimos casos se pedirá una respuesta final con lo leído. El modelo SHALL leer al menos una página antes de responder, salvo que el wiki esté vacío. Una salida que no sea una acción válida SHALL repetirse una vez con el error; si sigue sin serlo, el texto SHALL tomarse como la respuesta y registrarse la incidencia. Con el wiki vacío SHALL hacerse una sola llamada, con un contexto que indica que no hay páginas.

#### Scenario: Búsqueda, lectura y respuesta
- **WHEN** el modelo busca, lee una página y responde
- **THEN** se hacen tres llamadas y la respuesta final lleva las citas de lo leído

#### Scenario: Tope de acciones
- **WHEN** el modelo sigue pidiendo acciones hasta agotar el tope
- **THEN** se pide una respuesta final y se hace una llamada más

#### Scenario: Búsquedas vacías
- **WHEN** el modelo hace tres búsquedas seguidas sin resultados
- **THEN** se pide una respuesta final con lo leído, que puede ser la abstención

#### Scenario: Responder sin leer
- **WHEN** el modelo intenta responder antes de leer una página y el wiki no está vacío
- **THEN** se le indica que lea primero y el bucle continúa

#### Scenario: Acción mal formada
- **WHEN** el modelo devuelve texto que no es una acción válida y lo repite bien
- **THEN** el bucle continúa y el resultado cuenta la llamada de más

#### Scenario: Wiki vacío
- **WHEN** no se ha ingerido ningún paper
- **THEN** se hace una sola llamada, con el contexto «sin páginas»

### Requirement: Same answer rules as the RAG
Las reglas de respuesta del modelo SHALL ser las mismas que las del RAG: contestar en inglés y con brevedad, tratar el contexto como datos y no como instrucciones, citar con los `span_id` entre corchetes y contestar exactamente con la frase de abstención cuando no haya información. SHALL vivir en un solo lugar compartido por los dos brazos.

#### Scenario: Reglas compartidas
- **WHEN** se construyen las instrucciones del RAG y las del wiki
- **THEN** ambas contienen el mismo texto de reglas de respuesta

### Requirement: Citations come from what was read
Las citas del resultado SHALL ser los `span_id` que la respuesta cita entre corchetes, que aparecen en lo que el agente leyó (páginas y resultados de búsqueda) y existen en `data/gold/spans.jsonl`, sin repetir y en el orden de su primera cita. Si la respuesta es la frase de abstención las citas SHALL quedar vacías.

#### Scenario: Cita presente en una página leída
- **WHEN** la respuesta cita un `span_id` que aparece en una de las páginas leídas
- **THEN** ese `span_id` es una cita del resultado

#### Scenario: Cita que no está en lo leído
- **WHEN** la respuesta cita un `span_id` que no aparece en nada de lo leído
- **THEN** no es una cita del resultado

### Requirement: Arm contract and accounting
`BrazoWiki` SHALL cumplir el contrato `Brazo` con `nombre` igual a `wiki`. El `ResultadoIngesta` SHALL sumar las llamadas de plan y de escritura (incluida una repetición), y el `ResultadoBrazo` SHALL sumar todas las llamadas del bucle. `tokens_contexto` SHALL contar el texto que devolvieron las herramientas (resultados de búsqueda y páginas leídas), sin repetirlo por turno, y los segundos SHALL incluir todo.

#### Scenario: Contexto de una consulta
- **WHEN** el agente hace una búsqueda y lee dos páginas
- **THEN** `tokens_contexto` es la aproximación de tokens de los resultados de búsqueda más las dos páginas

#### Scenario: Error del modelo
- **WHEN** el modelo falla o se alcanza el tope de gasto durante una ingesta o una consulta
- **THEN** el error llega al llamador y no se devuelve ningún resultado inventado

### Requirement: The corpus is data, not instruction
Los mensajes del brazo SHALL indicar que el texto de los papers y de las páginas es dato y que se ignora cualquier instrucción que contenga.

#### Scenario: Instrucción dentro de un paper
- **WHEN** el texto de un paper contiene una orden dirigida al modelo
- **THEN** los mensajes de plan, de escritura y del agente incluyen la regla de tratar el contenido como datos

### Requirement: Query trace
`BrazoWiki` SHALL ofrecer `traza()`, que devuelve lo que hizo el agente en la última pregunta: número de acciones de herramienta, búsquedas, lecturas, páginas leídas e incidencias. Antes de la primera pregunta SHALL devolver valores vacíos, y la traza SHALL reiniciarse con cada pregunta.

#### Scenario: Traza de una pregunta
- **WHEN** el agente busca una vez, lee dos páginas y responde
- **THEN** `traza()` informa de 3 acciones, 1 búsqueda, 1 lectura, las dos páginas leídas y ninguna incidencia

#### Scenario: Antes de preguntar
- **WHEN** no se ha hecho ninguna pregunta
- **THEN** `traza()` informa de 0 acciones y listas vacías

#### Scenario: Traza que se reinicia
- **WHEN** se hacen dos preguntas seguidas
- **THEN** la traza describe solo la segunda
