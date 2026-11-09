## ADDED Requirements

### Requirement: Last retrieval exposed
El brazo RAG SHALL exponer, tras cada pregunta, los fragmentos que recuperó (los identificadores de sus fragmentos citables y su distancia), SHALL dejar la lista vacía antes de la primera pregunta y SHALL reemplazarla en cada pregunta.

#### Scenario: Después de una pregunta
- **WHEN** el brazo responde una pregunta con k = 5
- **THEN** expone cinco fragmentos con sus identificadores y distancias

#### Scenario: Antes de preguntar
- **WHEN** aún no se ha hecho ninguna pregunta
- **THEN** la lista está vacía
