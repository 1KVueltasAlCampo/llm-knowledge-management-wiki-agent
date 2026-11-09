## ADDED Requirements

### Requirement: Action detail in the trace
La traza del wiki SHALL incluir, además de los contadores, el detalle ordenado de las acciones del agente en la última pregunta: para cada una, el tipo (`search`, `read` o `answer`), su argumento (la consulta o las páginas pedidas) y un resumen de lo que devolvió la herramienta (los nombres de las páginas encontradas, o las leídas, las inexistentes y las no leídas por el tope). El detalle SHALL reiniciarse con cada pregunta.

#### Scenario: Detalle de una consulta
- **WHEN** el agente busca «recall», lee una página y responde
- **THEN** el detalle tiene tres elementos en ese orden, el primero con la consulta «recall» y los nombres de las páginas encontradas, el segundo con la página leída, y el tercero de tipo `answer`

#### Scenario: Página inexistente
- **WHEN** el agente pide leer una página que no existe
- **THEN** el elemento de lectura del detalle indica cuál no se encontró

#### Scenario: Detalle que se reinicia
- **WHEN** se hacen dos preguntas seguidas
- **THEN** el detalle describe solo la segunda
