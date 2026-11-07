# rag-arm Specification

## Purpose
TBD - created by archiving change brazo-rag. Update Purpose after archive.

## Requirements

### Requirement: Chunking from Gold
El sistema SHALL dividir cada archivo Gold en fragmentos usando como primera frontera los encabezados `##` y, si un fragmento excede el máximo de tokens que admite el modelo de embeddings, subdividirlo por párrafos. Cada fragmento SHALL llevar como metadatos el identificador de arXiv, el título del paper y el nombre de la sección, y su texto SHALL empezar con el título y la sección para que sea autocontenido. Ningún fragmento SHALL superar el máximo configurado.

#### Scenario: Sección corta
- **WHEN** una sección cabe en el máximo de tokens
- **THEN** produce un solo fragmento con su título y su sección

#### Scenario: Sección larga
- **WHEN** una sección excede el máximo de tokens
- **THEN** se subdivide por párrafos y todos los fragmentos resultantes conservan el mismo identificador y nombre de sección

#### Scenario: Párrafo más largo que el máximo
- **WHEN** un solo párrafo o tabla excede el máximo de tokens
- **THEN** se parte en trozos que respetan el máximo

### Requirement: Persistent idempotent index
El sistema SHALL guardar los embeddings de los fragmentos en un índice vectorial persistente en disco y SHALL recalcularlos únicamente cuando el contenido de los archivos Gold cambie.

#### Scenario: Primera construcción
- **WHEN** se construye el índice y no existe uno previo
- **THEN** se calculan los embeddings de todos los fragmentos y se guardan

#### Scenario: Gold sin cambios
- **WHEN** se vuelve a construir el índice y los archivos Gold no cambiaron
- **THEN** no se recalculan embeddings

#### Scenario: Gold modificado
- **WHEN** cambia el contenido de algún archivo Gold
- **THEN** el índice se reconstruye por completo y no conserva fragmentos del contenido anterior

### Requirement: Embedding device
Los embeddings SHALL calcularse con el modelo `EMBEDDING_MODEL` en el dispositivo `EMBEDDING_DEVICE`. Si se pide `cuda` y no está disponible, el sistema SHALL fallar con un mensaje que indique cambiar `EMBEDDING_DEVICE` a `cpu`.

#### Scenario: GPU solicitada y no disponible
- **WHEN** `EMBEDDING_DEVICE` es `cuda` y la GPU no está disponible
- **THEN** se lanza un error que menciona `EMBEDDING_DEVICE=cpu`

### Requirement: Top-k retrieval
Dada una pregunta, el sistema SHALL recuperar los `k` fragmentos más cercanos del índice, con `k` configurable y 5 por defecto, ordenados del más al menos cercano.

#### Scenario: Recuperación
- **WHEN** se consulta una pregunta
- **THEN** se devuelven como máximo `k` fragmentos ordenados por cercanía, con sus metadatos

### Requirement: Single-call grounded generation
El brazo RAG SHALL hacer exactamente una llamada al modelo por pregunta, a través del cliente único del modelo, con etiqueta `rag`. El mensaje SHALL contener los fragmentos recuperados identificados por su paper y SHALL instruir al modelo a responder solo con ese contexto, a citar los papers con su identificador entre corchetes y a decir que el corpus no contiene la información cuando no la encuentre.

#### Scenario: Pregunta con contexto suficiente
- **WHEN** se pregunta algo que los fragmentos recuperados contestan
- **THEN** se hace una llamada al modelo cuyo mensaje incluye esos fragmentos y las instrucciones de fundamentación

#### Scenario: Una sola llamada
- **WHEN** el brazo responde cualquier pregunta
- **THEN** el resultado reporta exactamente 1 llamada

### Requirement: Sources from citations
Las fuentes del resultado SHALL ser los identificadores de arXiv que la respuesta cita entre corchetes y que están entre los fragmentos recuperados, sin repetir y en el orden en que se citan por primera vez. Un identificador citado que no esté entre los recuperados SHALL ignorarse.

#### Scenario: Respuesta que cita dos papers recuperados
- **WHEN** la respuesta cita `[2405.14831]` y luego `[2502.14802]`, ambos recuperados
- **THEN** las fuentes son esos dos identificadores en ese orden

#### Scenario: Cita de un paper que no se recuperó
- **WHEN** la respuesta cita un identificador que no está entre los fragmentos recuperados
- **THEN** ese identificador no aparece en las fuentes

#### Scenario: El corpus no contiene la respuesta
- **WHEN** la respuesta no cita ningún paper
- **THEN** las fuentes quedan vacías

### Requirement: Arm contract and timing
El brazo RAG SHALL cumplir el contrato `Brazo` con `nombre` igual a `rag`. Los segundos del resultado SHALL incluir la recuperación y la generación, y las métricas de tokens y costo SHALL provenir de la llamada al modelo.

#### Scenario: Resultado válido
- **WHEN** el brazo responde una pregunta
- **THEN** devuelve un `ResultadoBrazo` válido con los segundos totales de recuperar y generar
