## MODIFIED Requirements

### Requirement: Persistent idempotent index
El sistema SHALL guardar los embeddings en un índice vectorial persistente en disco, en **Qdrant en modo local embebido** (sin servidor), con distancia coseno, y SHALL añadir los fragmentos de un paper solo cuando se le ingiere con `ingerir`. Volver a ingerir un paper cuyo Gold no cambió SHALL NOT recalcular sus embeddings, y si su Gold cambió SHALL reemplazar por completo los fragmentos anteriores de ese paper. La búsqueda SHALL ser exacta (no aproximada), SHALL devolver los `k` fragmentos más cercanos entre los papers ingeridos en la corrida, ordenados de menor a mayor distancia, y la distancia SHALL ser `1 − similitud coseno` para que conserve el sentido que tenía con Chroma.

#### Scenario: Primera construcción
- **WHEN** se ingiere un paper por primera vez
- **THEN** se calculan los embeddings de sus fragmentos y se guardan

#### Scenario: Gold sin cambios
- **WHEN** se vuelve a ingerir un paper cuyo Gold no cambió
- **THEN** no se recalculan embeddings

#### Scenario: Gold modificado
- **WHEN** cambia el contenido del Gold de un paper ya ingerido y se vuelve a ingerir
- **THEN** sus fragmentos anteriores desaparecen y se guardan los nuevos

#### Scenario: Índice persistente entre procesos
- **WHEN** se construye el índice en una carpeta, se cierra y se vuelve a abrir en otro objeto `IndiceRag`
- **THEN** los fragmentos siguen ahí y una nueva ingesta del mismo paper no recalcula embeddings

#### Scenario: Recuperación limitada a los papers ingeridos
- **WHEN** el índice tiene fragmentos de dos papers pero en la corrida solo se ingirió uno
- **THEN** `recuperar` devuelve solo fragmentos de ese paper, ordenados por distancia creciente y con distancia en [0, 2]

## ADDED Requirements

### Requirement: Vector store declared in run parameters
Los parámetros del brazo RAG que el arnés guarda en `corrida.json` SHALL incluir `base_vectorial` con el valor `"qdrant"`, para que reanudar una corrida empezada con otra base vectorial se rechace por la comprobación de parámetros que ya existe.

#### Scenario: Corrida empezada con Chroma
- **WHEN** se intenta reanudar una corrida cuyo `corrida.json` tiene `brazos.rag` igual a `{"k": 5}` (sin `base_vectorial`)
- **THEN** la reanudación aborta con el mensaje de parámetros distintos, sin hacer llamadas al modelo
