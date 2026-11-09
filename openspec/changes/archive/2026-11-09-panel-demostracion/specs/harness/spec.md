## ADDED Requirements

### Requirement: Retrieved fragments in the comparison
La comparación puntual SHALL mostrar, para el sistema que recupera fragmentos por similitud, los identificadores de los fragmentos recuperados con su distancia y marcar cuáles se citaron, y SHALL guardar en la línea de evidencia solo esos identificadores y distancias, sin texto de arXiv.

#### Scenario: Fragmentos recuperados
- **WHEN** el RAG recupera cinco fragmentos y cita uno
- **THEN** la salida lista los cinco con su distancia y marca el citado

#### Scenario: Sistema que no recupera
- **WHEN** un sistema no expone fragmentos recuperados
- **THEN** su bloque no incluye esa sección y la línea de evidencia no lleva el campo
