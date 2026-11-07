## ADDED Requirements

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
