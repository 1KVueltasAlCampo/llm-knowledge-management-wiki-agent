# harness Specification

## Purpose
TBD - created by archiving change arnes-comparacion. Update Purpose after archive.

## Requirements

### Requirement: Run command and cost gate
`python -m wikillm.arnes correr` SHALL imprimir, antes de la primera llamada al modelo, el número de preguntas, de pasos y de papers por ingerir, y una estimación del costo en dólares con la parte de ingesta y la de preguntas. Si la hora actual es de pico, SHALL avisarlo. Si la estimación supera 5 USD, la orden SHALL negarse a correr salvo que se pase `--confirmo-usd` con un valor mayor o igual a la estimación. Con `--estimar` SHALL imprimir y terminar sin crear brazos ni llamar al modelo.

#### Scenario: Solo estimar
- **WHEN** se ejecuta `correr --estimar`
- **THEN** se imprime la estimación, no se llama al modelo y no se crea ningún archivo de resultados

#### Scenario: Estimación mayor de 5 USD
- **WHEN** la estimación es de 8 USD y no se pasa `--confirmo-usd`
- **THEN** la orden termina con código 1 sin llamar al modelo y dice cuánto estima

#### Scenario: Estimación confirmada
- **WHEN** la estimación es de 8 USD y se pasa `--confirmo-usd 8`
- **THEN** la corrida comienza

### Requirement: Same conditions for both arms
El arnés SHALL dar a los dos brazos el mismo modelo (un único cliente con un único tope de gasto), las mismas preguntas, el mismo orden de papers y los mismos pasos. En cada paso SHALL ingerir primero en todos los brazos los papers que falten y luego hacer cada pregunta a todos los brazos, en el mismo orden de brazos, antes de pasar a la siguiente pregunta.

#### Scenario: Alternancia de brazos
- **WHEN** se corren dos brazos con dos preguntas en un paso
- **THEN** el orden de las llamadas es pregunta 1 al RAG, pregunta 1 al wiki, pregunta 2 al RAG y pregunta 2 al wiki

#### Scenario: Ingesta antes de preguntar
- **WHEN** el paso 5 sigue al paso 0
- **THEN** los cinco primeros papers del manifest se ingieren en ambos brazos, en `orden_ingesta`, antes de la primera pregunta del paso 5

### Requirement: Questions at every step
El arnés SHALL hacer cada pregunta seleccionada en cada paso de evaluación, incluidos los pasos en que sus fuentes todavía no se han ingerido, y SHALL NOT decidir por sí mismo si la respuesta es correcta. Los pasos SHALL ser un argumento de la orden con el valor por defecto 0, 5, 10, …, 50.

#### Scenario: Pregunta cuya fuente llega después
- **WHEN** una pregunta tiene `ingesta_minima` 13 y el paso es 5
- **THEN** se le hace a los dos brazos y el resultado se guarda como cualquier otro

#### Scenario: Paso cero
- **WHEN** el paso es 0
- **THEN** se pregunta con ambos brazos vacíos y las líneas llevan `ingest_step` 0

### Requirement: Question selection and validity
El arnés SHALL preguntar solo las preguntas del banco cuyo estado de verificación sea igual o posterior al estado mínimo pedido, por defecto `acordado`, y SHALL poder acotarlas por tipo y por identificador. `corrida.json` SHALL llevar `valida_para_informe` verdadero únicamente si todas las preguntas preguntadas están `acordado`. Cuando no lo sea, SHALL avisarlo al empezar y al terminar. Si ninguna pregunta cumple el filtro, la orden SHALL terminar con un error que lo diga.

#### Scenario: Estado por defecto
- **WHEN** el banco tiene preguntas `borrador` y `acordado` y no se pasa estado mínimo
- **THEN** solo se preguntan las `acordado` y `valida_para_informe` es verdadero

#### Scenario: Piloto con borradores
- **WHEN** se pasa `--estado-minimo borrador` y hay una pregunta `borrador`
- **THEN** se pregunta, `valida_para_informe` es falso y se imprime el aviso

#### Scenario: Ninguna pregunta cumple
- **WHEN** el banco no tiene preguntas `acordado` y no se pasa estado mínimo
- **THEN** la orden termina con código 1 sin llamar al modelo

### Requirement: Result files
Cada corrida SHALL escribir en `results/<corrida>/`: `respuestas.jsonl`, con una línea por (pregunta, sistema, paso) en el formato de `specs/contrato-resultados.md` que supera `leer_resultados`; `ingestas.jsonl`, con una línea por (sistema, paper) con su costo de ingesta; y `trazas.jsonl`, con una línea por pregunta y paso de cada brazo que ofrezca `traza()`, con las mismas claves de pregunta, sistema y paso. Las líneas SHALL escribirse y vaciarse una a una, a medida que se producen.

#### Scenario: Respuestas en el formato del contrato
- **WHEN** termina una corrida
- **THEN** `leer_resultados` lee `respuestas.jsonl` sin error y cada línea trae `run_id`, `system`, `ingest_step`, `citations`, `context_tokens` y el costo

#### Scenario: Costo de ingesta por paper
- **WHEN** el wiki ingiere el paper 3 en el paso 5
- **THEN** `ingestas.jsonl` tiene una línea de `system` `wiki` para ese paper con sus tokens, llamadas y dólares

#### Scenario: Traza solo de quien la ofrece
- **WHEN** el RAG no tiene `traza()` y el wiki sí
- **THEN** `trazas.jsonl` tiene líneas solo del wiki, con acciones, búsquedas, páginas leídas e incidencias

### Requirement: Run metadata
Al empezar, el arnés SHALL escribir `results/<corrida>/corrida.json` con el nombre y la fecha de la corrida, el commit de Git y si el árbol tenía cambios, el modelo, la temperatura y los precios, los pasos, los brazos con sus parámetros, el banco con su huella, el número de preguntas por estado y `valida_para_informe`. Al terminar SHALL añadir la fecha de fin y el gasto total.

#### Scenario: Metadatos al empezar
- **WHEN** comienza una corrida
- **THEN** `corrida.json` existe con el modelo, los pasos y la huella del banco antes de la primera pregunta

#### Scenario: Metadatos al terminar
- **WHEN** termina la corrida
- **THEN** `corrida.json` incluye la fecha de fin y el gasto acumulado

### Requirement: Resumable runs
Volver a lanzar la orden con el mismo `--corrida` SHALL continuar sin repetir lo hecho: SHALL saltar las respuestas cuya clave (pregunta, sistema, paso) ya consta en `respuestas.jsonl` y no SHALL escribir de nuevo líneas de ingesta ya registradas. Los brazos SHALL ponerse al día volviendo a ingerir los papers anteriores, que son idempotentes. Antes de preguntar en un paso, el arnés SHALL comprobar que cada brazo tiene ingeridos exactamente los primeros N papers del orden, y si no es así SHALL abortar con un mensaje.

#### Scenario: Reanudar a mitad de un paso
- **WHEN** una corrida cortada tenía 3 de 5 respuestas del paso 5 y se vuelve a lanzar
- **THEN** solo se hacen las 2 llamadas que faltan y el archivo no tiene líneas duplicadas

#### Scenario: Reanudar sin repetir ingestas
- **WHEN** se reanuda una corrida cuyos papers ya estaban ingeridos
- **THEN** no hay llamadas de ingesta al modelo ni líneas nuevas en `ingestas.jsonl`

#### Scenario: Un wiki más adelantado que el paso
- **WHEN** el wiki de la corrida tiene 12 papers y se debe preguntar en el paso 5
- **THEN** se aborta con un mensaje y no se hace ninguna pregunta

### Requirement: Failures stop the run
Si el modelo falla tras los reintentos del cliente o se alcanza el tope de gasto, el arnés SHALL detenerse, conservar todo lo escrito, imprimir cómo reanudar y terminar con código 1. SHALL NOT escribir una respuesta inventada ni omitir una pregunta en silencio.

#### Scenario: Tope de gasto
- **WHEN** el tope de gasto se alcanza durante una respuesta
- **THEN** la corrida termina con código 1, las líneas ya escritas se conservan y la que falló no se escribe

### Requirement: Isolated run state
Cada corrida SHALL usar su propia carpeta de wiki (`data/wiki/<corrida>`) y su propio índice vectorial (`data/chroma/<corrida>`), y SHALL NOT reutilizar el estado de otra corrida. Un nombre de corrida que ya tenga resultados SHALL tratarse como una reanudación.

#### Scenario: Corridas distintas
- **WHEN** se lanzan dos corridas con nombres distintos
- **THEN** cada una tiene su wiki y su índice, y ninguna ve las páginas de la otra

### Requirement: Summary at the end
Al terminar, el arnés SHALL imprimir, por sistema, el número de respuestas, el de abstenciones, el costo de ingesta, el costo de preguntas, la mediana de `context_tokens` y los segundos de ingesta y de respuesta, y SHALL indicar el comando para calcular las métricas con `python -m wikillm.eval metricas`.

#### Scenario: Resumen por sistema
- **WHEN** termina una corrida con dos brazos
- **THEN** se imprime una fila por sistema con sus costos, abstenciones y contexto mediano

### Requirement: Resumption must match the original run
Al reanudar una corrida, el arnés SHALL comprobar que los pasos, los parámetros de los brazos, el modelo, la temperatura, la huella del banco y las preguntas seleccionadas coinciden con los de `corrida.json`, y si algo difiere SHALL abortar con un mensaje sin hacer llamadas. SHALL registrar cada reanudación en `corrida.json`.

#### Scenario: Banco cambiado
- **WHEN** se reanuda una corrida y el archivo del banco ya no tiene la misma huella
- **THEN** la orden termina con código 1 y dice que el banco cambió

#### Scenario: Otros pasos
- **WHEN** se reanuda una corrida con pasos distintos a los originales
- **THEN** la orden termina con código 1 y no hace llamadas

#### Scenario: Reanudación registrada
- **WHEN** se reanuda una corrida correctamente
- **THEN** `corrida.json` incluye la fecha de la reanudación
