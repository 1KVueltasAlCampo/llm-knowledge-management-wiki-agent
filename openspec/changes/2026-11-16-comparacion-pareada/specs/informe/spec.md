## ADDED Requirements

### Requirement: Paired comparison of the two arms
`informe` SHALL escribir `informe/comparacion_pareada.csv` con una fila por paso de ingesta (`tipo` vacío) y por (tipo, paso), con las columnas `ingest_step`, `tipo`, `n`, `cobertura_rag`, `cobertura_wiki`, `diferencia`, `ic95_inf`, `ic95_sup`, `solo_rag`, `solo_wiki` y `p_mcnemar`. Los pares SHALL ser las preguntas respondibles en ese paso que tienen respuesta evaluada de ambos brazos, y una respuesta cuenta como acierto solo si su veredicto es `correcta`. La diferencia SHALL ser cobertura del wiki menos cobertura de RAG.

#### Scenario: Pares discordantes
- **WHEN** en un paso 5 preguntas las acierta solo el wiki, 1 solo RAG y 4 las aciertan ambos
- **THEN** la fila tiene `solo_wiki` 5, `solo_rag` 1 y `n` 10 si hay 10 preguntas respondibles

### Requirement: Exact McNemar test
`p_mcnemar` SHALL ser el valor p bilateral exacto de la prueba binomial sobre los pares discordantes (`solo_rag` y `solo_wiki`), con valor máximo 1, y 1 cuando no hay pares discordantes.

#### Scenario: Todo a favor de un brazo
- **WHEN** `solo_rag` es 0 y `solo_wiki` es 5
- **THEN** `p_mcnemar` es 0,0625

#### Scenario: Empate
- **WHEN** `solo_rag` es 3 y `solo_wiki` es 3
- **THEN** `p_mcnemar` es 1

### Requirement: Reproducible bootstrap interval
`ic95_inf` e `ic95_sup` SHALL ser los percentiles 2,5 y 97,5 de la diferencia de cobertura en 2.000 remuestreos con reemplazo de las preguntas, con semilla fija, de modo que repetir `informe` sobre los mismos datos produce archivos idénticos.

#### Scenario: Repetición
- **WHEN** se ejecuta `informe` dos veces sobre los mismos evaluados
- **THEN** `comparacion_pareada.csv` es idéntico byte a byte

### Requirement: Declared limitations
`resumen.md` SHALL incluir una sección «Comparación pareada» con la tabla por paso y una nota que diga que los intervalos suponen preguntas independientes y que no hay corrección por comparaciones múltiples.

#### Scenario: Nota presente
- **WHEN** se escribe `resumen.md`
- **THEN** contiene «Comparación pareada» y «comparaciones múltiples»
