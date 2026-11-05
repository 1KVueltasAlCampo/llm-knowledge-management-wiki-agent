# arm-interface Specification

## Purpose
TBD - created by archiving change interfaz-responder. Update Purpose after archive.

## Requirements

### Requirement: Common arm interface
Todo brazo (RAG o wiki) SHALL exponer un `nombre` y un método `responder(pregunta)` que recibe el texto de una pregunta y devuelve un `ResultadoBrazo`. El arnés de comparación SHALL depender solo de esta interfaz y no de detalles internos de ningún brazo.

#### Scenario: Dos brazos distintos, misma llamada
- **WHEN** el arnés llama a `responder(pregunta)` en un brazo RAG y en un brazo wiki
- **THEN** ambos devuelven un `ResultadoBrazo` con los mismos campos

#### Scenario: Un objeto que no cumple la interfaz
- **WHEN** un objeto no tiene `nombre` o no tiene `responder`
- **THEN** no se reconoce como `Brazo`

### Requirement: Answer and sources
`ResultadoBrazo` SHALL contener la respuesta como texto no vacío y las fuentes como una lista de identificadores de arXiv sin repetir, en el orden en que el brazo las usó. La lista de fuentes MAY estar vacía cuando el brazo declara que el corpus no contiene la respuesta.

#### Scenario: Respuesta con fuentes
- **WHEN** el brazo responde apoyándose en dos papers
- **THEN** `fuentes` contiene los dos identificadores, cada uno una sola vez

#### Scenario: Respuesta sin sustento en el corpus
- **WHEN** el brazo responde que el corpus no tiene la información
- **THEN** el resultado es válido con `fuentes` vacío

### Requirement: Cost metrics per question
`ResultadoBrazo` SHALL reportar, sumados sobre todas las llamadas al modelo hechas para esa pregunta: tokens de entrada (con y sin caché), tokens de salida, costo en dólares y número de llamadas. SHALL reportar además los segundos totales de la pregunta, incluida la recuperación o lectura previa a la generación.

#### Scenario: Brazo que llama al modelo varias veces
- **WHEN** un brazo hace tres llamadas al modelo para una sola pregunta
- **THEN** los tokens, el costo y el número de llamadas del resultado son la suma de las tres

#### Scenario: Brazo que hace una sola llamada
- **WHEN** un brazo hace una llamada con 800 tokens de entrada sin caché, 200 en caché y 50 de salida
- **THEN** el resultado reporta 1.000 de entrada, 50 de salida y 1 llamada

### Requirement: Result validation
`ResultadoBrazo` SHALL rechazar al crearse una respuesta vacía, una métrica negativa, una fuente que no sea un identificador de arXiv o una fuente repetida, indicando el motivo.

#### Scenario: Respuesta vacía
- **WHEN** se crea un resultado con la respuesta en blanco
- **THEN** se lanza un error que lo indica

#### Scenario: Fuente con formato inválido
- **WHEN** se crea un resultado con una fuente que no es un identificador de arXiv
- **THEN** se lanza un error que nombra esa fuente

### Requirement: Serialization
`ResultadoBrazo` SHALL poder convertirse en un diccionario de tipos simples, con exactamente los campos del contrato, para escribirlo como una línea JSON.

#### Scenario: Conversión a diccionario
- **WHEN** se convierte un resultado válido en diccionario
- **THEN** se puede serializar a JSON y contiene los campos `respuesta`, `fuentes`, `tokens_entrada`, `tokens_salida`, `segundos`, `usd` y `llamadas`

### Requirement: Failures are not hidden
Si el modelo falla o se alcanza el tope de gasto mientras un brazo responde, el error SHALL propagarse al llamador y el brazo SHALL NOT inventar un resultado.

#### Scenario: Tope de gasto durante una pregunta
- **WHEN** el tope de gasto se alcanza antes de la llamada al modelo
- **THEN** `responder` lanza el error de tope de gasto y no devuelve resultado
