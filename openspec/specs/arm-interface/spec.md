# arm-interface Specification

## Purpose
TBD - created by archiving change interfaz-responder. Update Purpose after archive.

## Requirements

### Requirement: Common arm interface
Todo brazo (RAG o wiki) SHALL exponer un `nombre`, un método `ingerir(arxiv_id)` que incorpora un paper a su corpus y devuelve un `ResultadoIngesta`, y un método `responder(pregunta)` que devuelve un `ResultadoBrazo` usando solo lo ingerido hasta ese momento. El arnés de comparación SHALL depender solo de esta interfaz y no de detalles internos de ningún brazo.

#### Scenario: Dos brazos distintos, misma llamada
- **WHEN** el arnés ingiere los mismos papers en un brazo RAG y en un brazo wiki y llama a `responder(pregunta)` en ambos
- **THEN** ambos devuelven un `ResultadoBrazo` con los mismos campos

#### Scenario: Responder usa solo lo ingerido
- **WHEN** se han ingerido dos papers y se hace una pregunta
- **THEN** todas las citas del resultado pertenecen a esos dos papers

#### Scenario: Un objeto que no cumple la interfaz
- **WHEN** un objeto no tiene `nombre`, `ingerir` o `responder`
- **THEN** no se reconoce como `Brazo`

### Requirement: Answer and sources
`ResultadoBrazo` SHALL contener la respuesta como texto no vacío; las citas (`citas`) como una lista de `span_id` con la forma `<arxiv_id>#s<N>.p<M>`, sin repetir y en el orden en que el brazo las usó; y `abstuvo`, verdadero cuando la respuesta contiene la frase de abstención común. Las citas MAY estar vacías. Cuando `abstuvo` es verdadero las citas SHALL estar vacías. `ResultadoBrazo` SHALL ofrecer `fuentes`, derivada de las citas: los identificadores de arXiv sin repetir.

#### Scenario: Respuesta con fuentes
- **WHEN** el brazo responde citando dos fragmentos de un mismo paper y uno de otro
- **THEN** `citas` contiene los tres `span_id` sin repetir y `fuentes` los dos papers

#### Scenario: Respuesta sin sustento en el corpus
- **WHEN** el brazo responde con la frase de abstención
- **THEN** el resultado es válido con `abstuvo` verdadero y `citas` vacías

#### Scenario: Abstención con citas
- **WHEN** se crea un resultado con `abstuvo` verdadero y alguna cita
- **THEN** se lanza un error que lo indica

### Requirement: Cost metrics per question
`ResultadoBrazo` SHALL reportar, sumados sobre todas las llamadas al modelo hechas para esa pregunta: tokens de entrada (con y sin caché), tokens de salida, costo en dólares y número de llamadas. SHALL reportar además los segundos totales de la pregunta, incluida la recuperación o lectura previa a la generación, y `tokens_contexto`: los tokens, aproximados con `aproximar_tokens`, del contexto que el brazo recuperó o leyó.

#### Scenario: Brazo que llama al modelo varias veces
- **WHEN** un brazo hace tres llamadas al modelo para una sola pregunta
- **THEN** los tokens, el costo y el número de llamadas del resultado son la suma de las tres

#### Scenario: Brazo que hace una sola llamada
- **WHEN** un brazo hace una llamada con 800 tokens de entrada sin caché, 200 en caché y 50 de salida
- **THEN** el resultado reporta 1.000 de entrada, 50 de salida y 1 llamada

#### Scenario: Contexto leído
- **WHEN** un brazo lee un contexto de 4.000 caracteres para responder
- **THEN** `tokens_contexto` es 1.000

### Requirement: Result validation
`ResultadoBrazo` SHALL rechazar al crearse una respuesta vacía, una métrica negativa, una cita que no tenga la forma de un `span_id`, una cita repetida y una abstención con citas, indicando el motivo.

#### Scenario: Respuesta vacía
- **WHEN** se crea un resultado con la respuesta en blanco
- **THEN** se lanza un error que lo indica

#### Scenario: Fuente con formato inválido
- **WHEN** se crea un resultado con una cita que es solo un identificador de arXiv
- **THEN** se lanza un error que nombra esa cita

### Requirement: Serialization
`ResultadoBrazo` SHALL poder convertirse en un diccionario de tipos simples, con exactamente sus campos, para escribirlo como una línea JSON.

#### Scenario: Conversión a diccionario
- **WHEN** se convierte un resultado válido en diccionario
- **THEN** se puede serializar a JSON y contiene los campos `respuesta`, `citas`, `abstuvo`, `tokens_contexto`, `tokens_entrada`, `tokens_salida`, `segundos`, `usd` y `llamadas`

### Requirement: Failures are not hidden
Si el modelo falla o se alcanza el tope de gasto mientras un brazo responde, el error SHALL propagarse al llamador y el brazo SHALL NOT inventar un resultado.

#### Scenario: Tope de gasto durante una pregunta
- **WHEN** el tope de gasto se alcanza antes de la llamada al modelo
- **THEN** `responder` lanza el error de tope de gasto y no devuelve resultado

### Requirement: Common abstention phrase
El sistema SHALL definir una frase de abstención única, `The ingested corpus does not contain this information.`, y una función que decida si un texto se abstiene, comparando sin diferencias de mayúsculas, espacios ni puntuación.

#### Scenario: Frase con otra puntuación
- **WHEN** la respuesta es `the ingested corpus does not contain this information`
- **THEN** se reconoce como abstención

#### Scenario: Respuesta que no se abstiene
- **WHEN** la respuesta da una cifra y no contiene la frase
- **THEN** no se reconoce como abstención

### Requirement: Ingestion result
`ingerir` SHALL devolver un `ResultadoIngesta` con tokens de entrada, tokens de salida, segundos, dólares y número de llamadas, sin valores negativos, sumados sobre todas las llamadas al modelo hechas para ese paper. Un brazo que no llama al modelo al ingerir (como el RAG) SHALL reportar cero tokens, cero dólares y los segundos reales.

#### Scenario: Ingesta sin modelo
- **WHEN** el RAG ingiere un paper
- **THEN** el resultado reporta 0 llamadas, 0 tokens y 0 dólares, y segundos mayores que cero

#### Scenario: Ingesta con varias llamadas
- **WHEN** un brazo hace tres llamadas al ingerir un paper
- **THEN** el resultado suma sus tokens, dólares y llamadas

### Requirement: Result lines for the harness
El sistema SHALL convertir un `ResultadoBrazo` y sus metadatos (`run_id`, `question_id`, `system`, `ingest_step`, `model`, `temperature`, `timestamp`) en una línea con exactamente los campos de `specs/contrato-resultados.md` §1, y un `ResultadoIngesta` en una línea de `ingestas.jsonl` con `run_id`, `system`, `ingest_step`, `arxiv_id`, sus métricas, `model` y `timestamp`. Las líneas de resultados SHALL ser aceptadas por `leer_resultados` de `wikillm.eval`.

#### Scenario: Línea de resultado
- **WHEN** se convierte un resultado válido en su línea
- **THEN** la línea contiene los campos del contrato, `citations` es la lista de `span_id`, `input_tokens` suma los tokens con y sin caché, y `leer_resultados` la acepta

#### Scenario: Línea de ingesta
- **WHEN** se convierte el resultado de ingerir un paper
- **THEN** la línea nombra el paper y el paso, y se puede serializar a JSON
