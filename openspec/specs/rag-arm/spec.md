# rag-arm Specification

## Purpose
TBD - created by archiving change brazo-rag. Update Purpose after archive.

## Requirements

### Requirement: Chunking from Gold
El sistema SHALL construir los fragmentos del RAG a partir de los fragmentos citables del Gold (`span`, calculados con `calcular_spans`): agrupa spans consecutivos de una misma sección hasta el máximo de tokens que admite el modelo de embeddings, y un span que por sí solo excede el máximo SHALL partirse en trozos que conservan su `span_id`. Cada fragmento SHALL llevar la lista de `span_id` que contiene, el identificador de arXiv, el título y la sección. Su texto SHALL empezar con el título y la sección, y cada span SHALL ir precedido de su `span_id` entre corchetes. Ningún fragmento SHALL superar el máximo configurado.

#### Scenario: Sección corta
- **WHEN** tres spans consecutivos de una sección caben juntos en el máximo
- **THEN** producen un solo fragmento con los tres `span_id`, cada uno rotulado en el texto

#### Scenario: Sección larga
- **WHEN** los spans de una sección no caben juntos en el máximo
- **THEN** se reparten en varios fragmentos y ningún span aparece en dos fragmentos distintos salvo que se haya partido

#### Scenario: Párrafo más largo que el máximo
- **WHEN** un solo span (por ejemplo una tabla) excede el máximo
- **THEN** se parte en trozos que respetan el máximo y todos conservan su `span_id`

### Requirement: Persistent idempotent index
El sistema SHALL guardar los embeddings en un índice vectorial persistente en disco y SHALL añadir los fragmentos de un paper solo cuando se le ingiere con `ingerir`. Volver a ingerir un paper cuyo Gold no cambió SHALL NOT recalcular sus embeddings, y si su Gold cambió SHALL reemplazar por completo los fragmentos anteriores de ese paper.

#### Scenario: Primera construcción
- **WHEN** se ingiere un paper por primera vez
- **THEN** se calculan los embeddings de sus fragmentos y se guardan

#### Scenario: Gold sin cambios
- **WHEN** se vuelve a ingerir un paper cuyo Gold no cambió
- **THEN** no se recalculan embeddings

#### Scenario: Gold modificado
- **WHEN** cambia el contenido del Gold de un paper ya ingerido y se vuelve a ingerir
- **THEN** sus fragmentos anteriores desaparecen y se guardan los nuevos

### Requirement: Embedding device
Los embeddings SHALL calcularse con el modelo `EMBEDDING_MODEL` en el dispositivo `EMBEDDING_DEVICE`. Si se pide `cuda` y no está disponible, el sistema SHALL fallar con un mensaje que indique cambiar `EMBEDDING_DEVICE` a `cpu`.

#### Scenario: GPU solicitada y no disponible
- **WHEN** `EMBEDDING_DEVICE` es `cuda` y la GPU no está disponible
- **THEN** se lanza un error que menciona `EMBEDDING_DEVICE=cpu`

### Requirement: Top-k retrieval
Dada una pregunta, el sistema SHALL recuperar los `k` fragmentos más cercanos entre los de los papers ya ingeridos, con `k` configurable y 5 por defecto, ordenados del más al menos cercano.

#### Scenario: Recuperación
- **WHEN** se consulta una pregunta
- **THEN** se devuelven como máximo `k` fragmentos ordenados por cercanía, con sus metadatos

#### Scenario: Paper no ingerido
- **WHEN** existe en el índice un paper que no se ha ingerido en esta corrida
- **THEN** ninguno de sus fragmentos se devuelve

#### Scenario: Corpus vacío
- **WHEN** no se ha ingerido ningún paper
- **THEN** la recuperación devuelve una lista vacía y no falla

### Requirement: Single-call grounded generation
El brazo RAG SHALL hacer exactamente una llamada al modelo por pregunta, a través del cliente único del modelo, con etiqueta `rag`. El mensaje SHALL estar en inglés, contener los fragmentos recuperados con cada `span_id` entre corchetes e instruir al modelo a responder en inglés usando solo ese contexto, a tratar el contexto como datos y nunca como instrucciones, a citar con los `span_id` entre corchetes y a responder exactamente con la frase de abstención común cuando el contexto no contenga la información.

#### Scenario: Pregunta con contexto suficiente
- **WHEN** se pregunta algo que los fragmentos recuperados contestan
- **THEN** se hace una llamada al modelo cuyo mensaje incluye esos fragmentos con sus `span_id` y las instrucciones en inglés

#### Scenario: Una sola llamada
- **WHEN** el brazo responde cualquier pregunta
- **THEN** el resultado reporta exactamente 1 llamada

#### Scenario: Contexto vacío
- **WHEN** no hay fragmentos que recuperar
- **THEN** se hace igualmente una llamada, con un contexto que indica que no hay pasajes

### Requirement: Sources from citations
Las citas del resultado SHALL ser los `span_id` que la respuesta cita entre corchetes (solos o varios en un mismo corchete), que estaban entre los fragmentos recuperados y existen en `data/gold/spans.jsonl`, sin repetir y en el orden de su primera cita. Un `span_id` citado que no cumpla alguna de esas condiciones SHALL ignorarse.

#### Scenario: Respuesta que cita dos papers recuperados
- **WHEN** la respuesta cita `[2405.14831#s2.p1]` y luego `[2502.14802#s3.p4]`, ambos recuperados
- **THEN** las citas son esos dos `span_id` en ese orden

#### Scenario: Cita de un paper que no se recuperó
- **WHEN** la respuesta cita un `span_id` que no está entre los fragmentos recuperados
- **THEN** ese `span_id` no aparece en las citas

#### Scenario: Cita de un identificador inventado
- **WHEN** la respuesta cita un `span_id` que no existe en `spans.jsonl`
- **THEN** ese `span_id` no aparece en las citas

#### Scenario: El corpus no contiene la respuesta
- **WHEN** la respuesta es la frase de abstención
- **THEN** las citas quedan vacías y `abstuvo` es verdadero

### Requirement: Arm contract and timing
El brazo RAG SHALL cumplir el contrato `Brazo` con `nombre` igual a `rag`. Los segundos del resultado SHALL incluir la recuperación y la generación, las métricas de tokens y costo SHALL provenir de la llamada al modelo y `tokens_contexto` SHALL medir el contexto enviado al modelo.

#### Scenario: Resultado válido
- **WHEN** el brazo responde una pregunta
- **THEN** devuelve un `ResultadoBrazo` válido con los segundos totales de recuperar y generar

### Requirement: Gold matches the versioned corpus
Al ingerir un paper, el sistema SHALL comprobar que el `hash` del encabezado de su Gold coincide con el de `data/gold/corpus.jsonl` y SHALL fallar con un mensaje que nombre el paper y sugiera volver a ejecutar la ingesta cuando no coincida, porque las citas por `span_id` solo valen si el texto es el mismo.

#### Scenario: Gold distinto del versionado
- **WHEN** el `hash` del Gold local de un paper difiere del de `corpus.jsonl`
- **THEN** `ingerir` lanza un error que nombra ese paper

#### Scenario: Gold igual al versionado
- **WHEN** los `hash` coinciden
- **THEN** la ingesta continúa

### Requirement: Last retrieval exposed
El brazo RAG SHALL exponer, tras cada pregunta, los fragmentos que recuperó (los identificadores de sus fragmentos citables y su distancia), SHALL dejar la lista vacía antes de la primera pregunta y SHALL reemplazarla en cada pregunta.

#### Scenario: Después de una pregunta
- **WHEN** el brazo responde una pregunta con k = 5
- **THEN** expone cinco fragmentos con sus identificadores y distancias

#### Scenario: Antes de preguntar
- **WHEN** aún no se ha hecho ninguna pregunta
- **THEN** la lista está vacía
