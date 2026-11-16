## ADDED Requirements

### Requirement: Report from saved results
El comando `wikillm.eval informe --corrida <carpeta>` SHALL leer `evaluados.jsonl` de esa carpeta, SHALL NOT llamar a ningún modelo ni a la red, y SHALL escribir en `<carpeta>/informe/` los archivos `por_sistema_paso.csv`, `por_tipo.csv`, `resumen.md` y las figuras `cobertura_por_paso.svg`, `contexto_por_paso.svg` y `costo_acumulado.svg`. Si falta `evaluados.jsonl` SHALL terminar con código distinto de cero y un mensaje que indique ejecutar antes `wikillm.eval metricas`.

#### Scenario: Informe de una corrida evaluada
- **WHEN** se ejecuta `informe` sobre una carpeta con `evaluados.jsonl`
- **THEN** se crean los cinco archivos en `informe/` y el comando termina con código 0

#### Scenario: Corrida sin evaluar
- **WHEN** la carpeta no tiene `evaluados.jsonl`
- **THEN** el comando termina con código 1 y no crea `informe/`

#### Scenario: Reproducible
- **WHEN** se ejecuta dos veces sobre los mismos datos
- **THEN** los archivos generados son idénticos byte a byte

### Requirement: Metrics sliced by question type
`por_tipo.csv` SHALL tener una fila por (sistema, tipo de pregunta, paso) con las mismas columnas y el mismo cálculo que `agregar`, más la columna `tipo`. Una celda sin denominador (por ejemplo cobertura sin preguntas respondibles) SHALL quedar vacía, nunca en 0.

#### Scenario: Corte por tipo
- **WHEN** los evaluados incluyen preguntas T1 y T5 de ambos sistemas
- **THEN** hay filas separadas por tipo y la cobertura de T5 (todas no respondibles) queda vacía

### Requirement: Figures without new dependencies
Las figuras SHALL ser archivos SVG válidos generados sin librerías de gráficas, con un trazo por sistema, ejes rotulados, leyenda y un `<title>` que identifique la corrida.

#### Scenario: Figura de cobertura
- **WHEN** hay filas de RAG y wiki en varios pasos
- **THEN** `cobertura_por_paso.svg` contiene una polilínea por sistema y los pasos en el eje horizontal
