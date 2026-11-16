## ADDED Requirements

### Requirement: Additional arm that shares the wiki
`arnes correr` SHALL aceptar `--graphify <ejecutable>` y, junto con él, `--tgrep <ejecutable>`. Con `--graphify` SHALL añadir un tercer brazo (`wiki_grafo`, o `wiki_grafo_tgrep` con tgrep) que consulta el mismo wiki del brazo `wiki`, SHALL NOT ingerir ni sumar costo de ingesta, SHALL declararse en `brazos` de `corrida.json` con sus capas y SHALL contarse en la estimación de costo. Sin esas opciones, `corrida.json` y la estimación SHALL ser idénticos a los de una corrida de dos brazos. `--tgrep` sin `--graphify` SHALL rechazarse.

#### Scenario: Sin opciones
- **WHEN** se ejecuta `arnes correr --estimar` sin `--graphify`
- **THEN** la estimación y los brazos declarados son los de `rag` y `wiki`

#### Scenario: Con graphify
- **WHEN** se ejecuta con `--graphify`
- **THEN** hay tres brazos, la ingesta de los papers solo la paga el brazo `wiki` y las respuestas del tercer brazo llevan su nombre en `system`

#### Scenario: tgrep sin grafo
- **WHEN** se indica `--tgrep` sin `--graphify`
- **THEN** la orden termina con un error que pide usar `--graphify`
