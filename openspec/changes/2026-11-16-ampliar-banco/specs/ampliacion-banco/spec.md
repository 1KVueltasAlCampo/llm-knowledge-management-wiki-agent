## ADDED Requirements

### Requirement: Recompute the minimum ingestion step from the new order
`ampliar-banco` SHALL recalcular `ingesta_minima` de cada pregunta existente con las posiciones `orden_ingesta` del manifest indicado: el mayor `orden_ingesta` de sus `fuentes_requeridas`, `null` en T5, y en T4 con `respuesta_por_paso` la primera fuente como `ingesta_minima` y la última como `desde` de cada tramo. SHALL NOT modificar el banco de entrada.

#### Scenario: Pregunta de una fuente
- **WHEN** una pregunta T1 cuya fuente pasa de la posición 7 a la 41 en el nuevo manifest
- **THEN** su `ingesta_minima` pasa a 41

#### Scenario: T4 con cambio
- **WHEN** una T4 tiene fuentes en las posiciones 10 y 60 del nuevo manifest
- **THEN** su `ingesta_minima` es 10 y el `desde` de su tramo es 60

#### Scenario: T5
- **WHEN** la pregunta es T5
- **THEN** su `ingesta_minima` sigue siendo `null`

### Requirement: Resolve literal quotes to fragments
Cada cita de una definición SHALL resolverse al primer fragmento (`span_id`) del paper indicado cuyo texto, normalizado (sin espacios repetidos ni marcas de formato `*`, `_`, `` ` ``, `$` y `\`), contiene la cita normalizada, y la evidencia SHALL guardar ese `span_id` y su `sha256`. Si ninguna cita se encuentra, o el paper no es una de las `fuentes_requeridas`, el comando SHALL terminar con código 1 sin escribir el banco.

#### Scenario: Cita encontrada
- **WHEN** la cita está en el tercer párrafo del paper
- **THEN** la evidencia apunta al `span_id` de ese párrafo con su huella

#### Scenario: Cita inexistente
- **WHEN** la cita no aparece en ningún fragmento del paper
- **THEN** el comando termina con código 1 y no escribe el banco

### Requirement: New questions are preliminary
Las preguntas creadas desde definiciones SHALL tener `estado_verificacion` `verificado_a` o `verificado_b` según su autor, SHALL NOT tener `revision.cruzada` y SHALL declarar en `revision.origen` el archivo de definiciones. El comando SHALL imprimir cuántas preguntas nuevas no están `acordado`.

#### Scenario: Estado
- **WHEN** se construye una pregunta nueva de Juan Diego
- **THEN** su estado es `verificado_a` y no existe `revision.cruzada`

### Requirement: Valid result
El banco escrito SHALL pasar `validar_banco` con el `orden` del nuevo manifest; si no, el comando SHALL imprimir los problemas y terminar con código 1 sin escribirlo.

#### Scenario: Banco válido
- **WHEN** todas las definiciones son coherentes con el manifest
- **THEN** el banco se escribe y `validar_banco` no devuelve problemas
