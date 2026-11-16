## ADDED Requirements

### Requirement: Accept new questions by decision
Con `--acordar-por <decisión>`, `ampliar-banco` SHALL poner las preguntas nuevas en `acordado` y SHALL guardar en `revision.acordado` la fecha, la decisión (`por_decision`) y `revision_cruzada: false`. SHALL NOT modificar las preguntas del banco de entrada.

#### Scenario: Pregunta nueva aceptada
- **WHEN** se ejecuta `ampliar-banco --acordar-por 0010`
- **THEN** cada pregunta nueva queda `acordado` con `revision.acordado.revision_cruzada` en `false`
