# demo-panel Specification

## Purpose
TBD - created by archiving change panel-demostracion. Update Purpose after archive.

## Requirements

### Requirement: Local single-page server
`python -m wikillm.panel` SHALL servir una página única que no depende de recursos externos, SHALL escuchar solo en 127.0.0.1 y SHALL rechazar las peticiones cuyo encabezado `Host` no sea local.

#### Scenario: Página servida
- **WHEN** se pide `/` al servidor
- **THEN** responde con la página HTML y no hace referencia a ninguna dirección externa

#### Scenario: Encabezado Host ajeno
- **WHEN** llega una petición con `Host: ejemplo.com`
- **THEN** el servidor responde 403 y no ejecuta nada

### Requirement: Sections, corpus state and example questions
El panel SHALL organizarse por secciones (preguntar, ingerir, wiki, resultados y sistema), SHALL informar cuántos papers tiene el corpus, cuántos están ingeridos y cuál es el siguiente en el orden de ingesta, y SHALL ofrecer preguntas de ejemplo con una nota breve de qué muestra cada una.

#### Scenario: Siguiente paper
- **WHEN** el wiki tiene ingeridos los primeros 5 papers del manifest
- **THEN** el estado indica el total del corpus y que el siguiente es el paper del paso 6, con su identificador y título

#### Scenario: Preguntas de ejemplo
- **WHEN** se piden los ejemplos
- **THEN** cada uno trae una pregunta válida (no vacía, dentro del límite) y su nota

### Requirement: Real actions streamed as events
`POST /api/ejecutar` SHALL iniciar una acción del catálogo y devolver el identificador de su trabajo, y `GET /api/eventos/<id>` SHALL transmitir por SSE, en orden y desde el principio, los eventos del trabajo: las líneas de salida tal como las imprimiría la orden, las llamadas al modelo, los resultados estructurados y un evento final con el código de salida. Solo SHALL ejecutarse un trabajo a la vez.

#### Scenario: Líneas en orden
- **WHEN** una acción imprime tres líneas
- **THEN** el flujo trae tres eventos de línea en ese orden seguidos de un evento final con código 0

#### Scenario: Otro trabajo en curso
- **WHEN** se pide una acción mientras otra se está ejecutando
- **THEN** la petición se rechaza con 409 y un mensaje

#### Scenario: Acción desconocida
- **WHEN** se pide una acción que no está en el catálogo
- **THEN** la petición se rechaza con 400 y no se ejecuta nada

#### Scenario: Falla de la acción
- **WHEN** una acción lanza un error
- **THEN** el flujo trae un evento de error y un evento final con código 1, y el servidor sigue disponible

### Requirement: Observed model calls
Las acciones que usan el modelo SHALL emitir un evento al iniciar cada llamada y otro al terminarla con la etiqueta, los tokens de entrada, de caché y de salida, los segundos, los dólares y el texto devuelto, sin alterar la respuesta ni el registro del cliente del modelo.

#### Scenario: Eventos de una llamada
- **WHEN** el agente hace una llamada con la etiqueta `wiki`
- **THEN** el flujo trae un evento "llamando" y uno "llamada" con esos campos, y el texto de la respuesta es el que devolvió el modelo

### Requirement: Structured results of comparison and ingestion
Al terminar una comparación, el servidor SHALL emitir un evento de resultado con, por sistema, la respuesta, si se abstuvo, las citas con el comienzo de su fragmento, los tokens, las llamadas, los segundos, los dólares, la traza y los fragmentos recuperados. Al terminar una ingesta SHALL emitir las páginas creadas y actualizadas y los conteos de citas eliminadas, enlaces rotos y líneas sin cita que quedaron en el registro del wiki.

#### Scenario: Resultado de una comparación
- **WHEN** termina `comparar` con éxito
- **THEN** el flujo trae un resultado con un elemento por sistema y los fragmentos de las citas

#### Scenario: Resultado de una ingesta
- **WHEN** termina la ingesta del paper 6
- **THEN** el flujo trae el paso 6, las páginas creadas y actualizadas y los tres conteos

### Requirement: Whitelisted file viewer
`GET /api/archivo` SHALL devolver solo archivos que coincidan con la lista blanca declarada, con su tipo y su texto, y SHALL rechazar rutas absolutas, con `..`, de `.env`, de `.git` o que no estén en la lista, así como truncar los archivos mayores que el límite avisando de ello.

#### Scenario: Archivo permitido
- **WHEN** se pide `README.md`
- **THEN** se devuelve su texto con el tipo `markdown`

#### Scenario: Recorrido de directorios
- **WHEN** se pide `../.env` o `docs/../.env`
- **THEN** se rechaza con 403 y no se lee ningún archivo

#### Scenario: Archivo fuera de la lista
- **WHEN** se pide un archivo que existe pero no está en la lista blanca
- **THEN** se rechaza con 403

#### Scenario: Archivo grande
- **WHEN** el archivo supera el límite
- **THEN** se devuelve el comienzo y se indica que está truncado

### Requirement: Session cost and cap
El panel SHALL acumular los dólares de los eventos de llamada como gasto de la sesión, SHALL mostrar la estimación de cada acción de pago antes de ejecutarla y SHALL rechazar nuevas acciones de pago cuando el gasto alcance el tope de la sesión.

#### Scenario: Gasto acumulado
- **WHEN** terminan dos llamadas de 0,001 y 0,002 USD
- **THEN** el estado informa un gasto de sesión de 0,003 USD

#### Scenario: Tope alcanzado
- **WHEN** el gasto de la sesión alcanza el tope y se pide una acción de pago
- **THEN** se rechaza con un mensaje y las acciones sin costo siguen disponibles

### Requirement: Recording and replay
Cada trabajo SHALL guardar sus eventos con su tiempo relativo en `results/demo/grabaciones/`, y una reproducción SHALL reemitir los de la grabación más reciente de esa acción cuyo encabezado coincida con los parámetros pedidos (por ejemplo, la pregunta y el estado del wiki al grabarla), con esos tiempos, marcando cada evento como reproducido, sin crear ningún cliente del modelo ni modificar archivos.

#### Scenario: Grabación al terminar
- **WHEN** termina un trabajo
- **THEN** existe una grabación con sus eventos y un encabezado con la acción y la fecha

#### Scenario: Reproducción
- **WHEN** se pide reproducir una acción grabada
- **THEN** el flujo trae los eventos grabados, todos marcados como reproducidos, y ninguna llamada al modelo

#### Scenario: Sin grabación
- **WHEN** se pide reproducir una acción que nunca se grabó
- **THEN** se rechaza con un mensaje

### Requirement: Validated parameters and confirmation
El servidor SHALL validar los parámetros de cada acción (largo y tipo de la pregunta, paso entero dentro del corpus, carpeta del wiki confinada a `data/wiki/`), SHALL pasar la pregunta a las órdenes sin que pueda interpretarse como opción, y SHALL exigir una confirmación explícita en las acciones que gastan saldo o borran estado.

#### Scenario: Pregunta vacía o demasiado larga
- **WHEN** la pregunta está vacía o pasa del límite
- **THEN** se rechaza con 400

#### Scenario: Carpeta de wiki fuera de data/wiki
- **WHEN** el parámetro del wiki apunta fuera de `data/wiki/`
- **THEN** se rechaza con 400

#### Scenario: Acción destructiva sin confirmar
- **WHEN** se pide reiniciar el wiki de la demostración sin confirmación
- **THEN** se rechaza y el wiki no cambia

#### Scenario: Acción de pago sin confirmar
- **WHEN** se pide una comparación o una ingesta sin confirmación
- **THEN** se rechaza con 400 y no se llama al modelo

### Requirement: Pilot metrics view
`GET /api/metricas` SHALL devolver las métricas por sistema y paso y los veredictos por pregunta del piloto guardado, leyendo solo archivos de resultados, sin llamar al modelo.

#### Scenario: Métricas del piloto
- **WHEN** se piden las métricas
- **THEN** se devuelve una fila por sistema y paso y la lista de veredictos por pregunta
