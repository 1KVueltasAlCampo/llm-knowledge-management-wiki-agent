## ADDED Requirements

### Requirement: Side-by-side comparison command
`python -m wikillm.arnes comparar "<pregunta>"` SHALL hacer la misma pregunta al RAG y al wiki, con el mismo cliente del modelo, y SHALL mostrar para cada sistema la respuesta, si se abstuvo, las citas con el comienzo del fragmento literal que cada una resuelve en el Gold, los tokens de entrada, de contexto y de salida, las llamadas, los segundos y los dólares, y al final una tabla con una fila por sistema. Las citas SHALL ser las que el sistema ya validó; el comando SHALL NOT añadir ni quitar ninguna.

#### Scenario: Una pregunta a los dos sistemas
- **WHEN** se ejecuta `comparar` con una pregunta y un wiki con 5 papers ingeridos
- **THEN** se imprime un bloque para el RAG, otro para el wiki y una tabla, y ambos sistemas recibieron exactamente la misma pregunta

#### Scenario: Cita con su fragmento
- **WHEN** un sistema cita `2405.14831#s12.p3`
- **THEN** la salida muestra ese identificador seguido del comienzo del texto del fragmento en el Gold

#### Scenario: Abstención
- **WHEN** un sistema responde con la frase de abstención
- **THEN** la salida lo indica y no lista citas para ese sistema

#### Scenario: Fallo del modelo
- **WHEN** el modelo falla o se alcanza el tope de gasto mientras se responde
- **THEN** la orden termina con código 1, imprime el motivo y no escribe ninguna línea de evidencia

### Requirement: Corpus state set by the wiki
La orden SHALL tomar como paso de ingesta el número de papers que tiene ingeridos el wiki indicado, SHALL poner el RAG en ese mismo estado ingiriendo los mismos papers en el orden del manifest, y SHALL comprobar que ambos brazos tienen exactamente los primeros N papers antes de preguntar. Si no es así, SHALL abortar con un mensaje y sin llamar al modelo.

#### Scenario: Wiki en el paso 5
- **WHEN** el wiki indicado tiene los 5 primeros papers del manifest
- **THEN** el RAG ingiere esos 5 papers y la comparación se hace en el paso 5

#### Scenario: Wiki fuera de orden
- **WHEN** el wiki tiene ingeridos papers que no son los primeros del manifest
- **THEN** la orden aborta con un mensaje y no hace ninguna llamada al modelo

#### Scenario: Wiki vacío
- **WHEN** el wiki no tiene ningún paper ingerido
- **THEN** la comparación se hace en el paso 0 y ambos sistemas responden sin contexto

### Requirement: Comparison evidence file
Cada comparación SHALL añadir una línea a `results/demo/comparaciones.jsonl` con la pregunta, el paso, el modelo, la fecha y, por sistema, la respuesta, las citas como identificadores, si se abstuvo, los tokens, las llamadas, los segundos, los dólares y la traza si el sistema la ofrece. La línea SHALL NOT incluir el texto de los fragmentos citados.

#### Scenario: Línea de evidencia
- **WHEN** termina una comparación
- **THEN** el archivo tiene una línea nueva con los dos sistemas y sus costos, y ninguna cita lleva texto de arXiv

#### Scenario: Comparaciones sucesivas
- **WHEN** se ejecutan dos comparaciones seguidas
- **THEN** el archivo conserva la primera línea y añade la segunda
