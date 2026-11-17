## ADDED Requirements

### Requirement: Select the arms of a run
`arnes correr --brazos` SHALL ejecutar solo los brazos indicados, en el orden `rag`, `wiki`, brazo con grafo. Sin la opción SHALL conservar el comportamiento anterior. SHALL terminar con error antes de gastar si un nombre es desconocido, si se pide el brazo con grafo sin `--graphify` o sin `wiki`, si se da `--graphify` sin incluir ese brazo, o si se da `--wiki-de` sin `wiki`. `corrida.json` SHALL declarar solo los brazos elegidos y la estimación SHALL contarlos solo a ellos.

#### Scenario: Solo el RAG
- **WHEN** se pide `--brazos rag --k 10`
- **THEN** solo responde el RAG con 10 fragmentos, `corrida.json` declara únicamente `rag` y no se abre el wiki

#### Scenario: Brazo con grafo sin wiki
- **WHEN** se pide `--brazos wiki_grafo --graphify <ejecutable>`
- **THEN** el comando termina con error y no se crea la carpeta de resultados
