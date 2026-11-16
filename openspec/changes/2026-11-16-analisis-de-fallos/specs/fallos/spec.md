## ADDED Requirements

### Requirement: Failure categories from stored data
`fallos` SHALL asignar a cada respuesta cuyo veredicto no es `correcta` una sola categoría, sin llamar a ningún modelo. Para preguntas respondibles en ese paso: `obsoleta` si la respuesta está marcada como obsoleta; si no, `indeterminada` si el veredicto es `indeterminada`; si no, `abstencion_erronea` si se abstuvo; si no, `sin_fuente` si ninguno de los papers que citó (el identificador antes de `#` en cada `span_id`) está entre las `fuentes_requeridas`; si no, `fuente_parcial` si cita algunas pero no todas; y `fuentes_completas_error` si cita todas. Para preguntas no respondibles, una respuesta no correcta SHALL ser `no_se_abstuvo`.

#### Scenario: Abstención errónea
- **WHEN** una pregunta respondible recibe una respuesta con `abstained` verdadero y veredicto no correcto
- **THEN** su categoría es `abstencion_erronea`

#### Scenario: Fuente parcial
- **WHEN** una pregunta con fuentes requeridas A y B recibe una respuesta incorrecta que solo cita A
- **THEN** su categoría es `fuente_parcial`

#### Scenario: Fuentes completas y error
- **WHEN** una respuesta incorrecta cita A y B
- **THEN** su categoría es `fuentes_completas_error`

#### Scenario: No se abstuvo
- **WHEN** una pregunta no respondible en ese paso recibe una respuesta no correcta
- **THEN** su categoría es `no_se_abstuvo`

### Requirement: Failure outputs
`fallos --corrida <carpeta>` SHALL escribir `<carpeta>/fallos/detalle.csv` (con `question_id`, `system`, `ingest_step`, `tipo` y `categoria`) y `<carpeta>/fallos/resumen.md` con los conteos por sistema y categoría y por sistema y tipo, y una nota que advierta que las categorías son una pista y no un diagnóstico. Si falta `evaluados.jsonl` SHALL terminar con código 1 sin crear la carpeta. Repetir el comando sobre los mismos datos SHALL producir archivos idénticos.

#### Scenario: Corrida sin evaluar
- **WHEN** la carpeta no tiene `evaluados.jsonl`
- **THEN** el comando termina con código 1 y no crea `fallos/`
