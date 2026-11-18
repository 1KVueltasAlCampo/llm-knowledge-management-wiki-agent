## ADDED Requirements

### Requirement: Report quality against cost and time
El análisis SHALL calcular, solo con resultados guardados, el costo y el tiempo acumulados de construir el wiki por paso, el costo y el tiempo por consulta de cada sistema, el costo por respuesta correcta y el costo total de atender N consultas con el corpus completo. SHALL declarar la procedencia de cada cifra (corrida o registro) y SHALL NOT llamar a ningún modelo.

#### Scenario: Costo por respuesta correcta
- **WHEN** se calcula con los resultados del paso 100
- **THEN** cada sistema muestra su exactitud, su costo por consulta y su costo por respuesta correcta, y el wiki añade el costo fijo de construcción en los escenarios
