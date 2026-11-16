## ADDED Requirements

### Requirement: Paired comparison of one arm across two runs
`comparar-corridas` SHALL, para cada sistema, emparejar por `question_id` las respuestas de la corrida base en `--paso-base` con las de la ampliada en `--paso-ampliada`, usando solo las preguntas respondibles en ambos pasos que están en las dos corridas. SHALL escribir `comparacion.csv` con `sistema`, `tipo` (vacío para el total), `n`, `cobertura_base`, `cobertura_ampliada`, `diferencia` (ampliada menos base), `ic95_inf`, `ic95_sup`, `solo_base`, `solo_ampliada` y `p_mcnemar`, con el bootstrap y el McNemar exacto del módulo de estadística.

#### Scenario: Pares discordantes
- **WHEN** una pregunta la acierta solo la corrida base y dos solo la ampliada
- **THEN** `solo_base` es 1 y `solo_ampliada` es 2 para ese sistema

#### Scenario: Preguntas solo de una corrida
- **WHEN** una pregunta existe únicamente en la ampliada
- **THEN** no entra en los pares y aparece en la sección de preguntas nuevas

### Requirement: New questions are shown apart and as preliminary
`comparacion.md` SHALL incluir una sección «Preguntas nuevas (preliminares)» con las preguntas que solo están en la ampliada: cobertura de cada brazo en `--paso-ampliada`, diferencia wiki menos RAG y los pares discordantes, y SHALL decir que no tienen revisión cruzada.

#### Scenario: Sección de preliminares
- **WHEN** hay preguntas solo en la corrida ampliada
- **THEN** el informe las lista aparte y contiene la palabra «preliminares»

### Requirement: Cost and context per run
`comparacion.md` SHALL mostrar, por corrida y sistema, el contexto medio y el costo medio por respuesta en el paso indicado y el costo total de respuestas y de ingesta leídos de `respuestas.jsonl` e `ingestas.jsonl` (cero si no existe el archivo).

#### Scenario: Costos
- **WHEN** ambas corridas tienen `respuestas.jsonl` e `ingestas.jsonl`
- **THEN** la tabla de costos tiene una fila por corrida y sistema

### Requirement: Declared limits and reproducibility
`comparacion.md` SHALL declarar que el orden y el tamaño del corpus difieren entre corridas y que no hay corrección por comparaciones múltiples, y repetir el comando sobre los mismos datos SHALL producir archivos idénticos. Si falta `evaluados.jsonl` en alguna corrida, SHALL terminar con código 1 sin escribir nada.

#### Scenario: Falta una corrida
- **WHEN** `--ampliada` no tiene `evaluados.jsonl`
- **THEN** el comando termina con código 1 y no crea la carpeta de salida
