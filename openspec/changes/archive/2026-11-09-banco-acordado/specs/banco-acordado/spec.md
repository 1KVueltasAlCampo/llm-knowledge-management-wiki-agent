## ADDED Requirements

### Requirement: Agreement measure between authors
`eval acordar` SHALL medir el acuerdo entre las dos revisiones de una mitad del banco como el porcentaje y el kappa de Cohen de «aceptar o ajustar» sobre las preguntas que ambos autores decidieron, y SHALL listar las preguntas en las que no coinciden.

#### Scenario: Corregir y descartar cuentan igual
- **WHEN** un autor corrige una pregunta y el otro la descarta
- **THEN** ambos cuentan como «ajustar» y no se reporta discrepancia

#### Scenario: Pregunta sin decisión de un autor
- **WHEN** un autor no tiene decisión para una pregunta
- **THEN** esa pregunta no entra en la medida

### Requirement: Move to agreed on explicit order
`eval acordar` SHALL cambiar el estado a `acordado` solo con `--ejecutar`, SHALL dejar sin cambios las preguntas nombradas en `--pendientes`, SHALL guardar en cada pregunta acordada la fecha y el acuerdo, y SHALL escribir el resumen de la mitad en `results/banco/acuerdo_<mitad>.json`.

#### Scenario: Simulación
- **WHEN** se ejecuta sin `--ejecutar`
- **THEN** informa el acuerdo y no modifica ningún archivo

#### Scenario: Pendientes
- **WHEN** se ejecuta con `--ejecutar` y una pregunta pendiente
- **THEN** esa pregunta conserva su estado y las demás pasan a `acordado`

#### Scenario: Pendiente inexistente
- **WHEN** un pendiente no está en el banco
- **THEN** la orden falla con un mensaje y no escribe nada
