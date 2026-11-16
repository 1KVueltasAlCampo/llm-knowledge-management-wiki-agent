## ADDED Requirements

### Requirement: Reuse a built wiki
`arnes correr --wiki-de` SHALL trabajar sobre una copia del wiki indicado, con todas sus etiquetas `paso-N`, y SHALL dejarla en el paso 0 al empezar y en la copia `paso-N` tras ingerir el paper N. SHALL terminar con error antes de gastar si el wiki no tiene la copia de algún paso pedido o si sus papers ingeridos en ese paso no son los primeros N del manifest. SHALL NOT modificar el wiki original, SHALL NOT contar costo de ingesta del brazo `wiki` y SHALL declarar `reutiliza_wiki_de` en `corrida.json`.

#### Scenario: Wiki con otro orden
- **WHEN** el manifest de la corrida pone en primer lugar otro paper que el wiki original
- **THEN** el comando termina con error y no se crea la carpeta de resultados

#### Scenario: Estimación
- **WHEN** se pide `--estimar` con `--wiki-de`
- **THEN** la estimación muestra 0.00 USD de ingesta
