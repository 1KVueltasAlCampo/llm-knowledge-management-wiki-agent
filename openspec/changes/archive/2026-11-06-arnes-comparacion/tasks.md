# Tasks

## 1. Base

- [x] 1.1 Añadir `traza()` a `BrazoWiki` (acciones, búsquedas, lecturas, páginas leídas, incidencias; vacía antes de preguntar). Verificación: pruebas de una pregunta con búsqueda y dos lecturas, de la traza vacía y de que se reinicia.
- [x] 1.2 Crear `arnes/registro.py`: escritura de líneas JSONL con vaciado inmediato, lectura de las claves ya escritas, `corrida.json` (al empezar y al terminar) con el commit de Git y si el árbol tenía cambios. Verificación: pruebas con carpeta temporal: líneas legibles tras cada escritura, claves leídas, metadatos al empezar y al terminar, y un repositorio sin Git sin romper.

## 2. Selección y estimación

- [x] 2.1 Crear `arnes/seleccion.py`: filtro de preguntas por estado mínimo, tipos e identificadores, y cálculo de `valida_para_informe`. Verificación: pruebas con un banco que mezcla estados: por defecto solo `acordado`, el piloto con `borrador` marca no válida, filtro por tipo y por id, y ninguna pregunta cumple.
- [x] 2.2 Crear `arnes/estimacion.py`: costo estimado de ingesta y preguntas con las cotas del diseño, aviso de hora pico y puerta de 5 USD. Verificación: pruebas del cálculo, de la negativa sin `--confirmo-usd`, de la confirmación y de la hora pico en lunes y en sábado.

## 3. Bucle

- [x] 3.1 Crear `arnes/corrida.py`: ingesta por pasos en `orden_ingesta`, alternancia de brazos, escritura de `respuestas.jsonl`, `ingestas.jsonl` y `trazas.jsonl`, reanudación por clave, comprobación del paso y parada ante fallos. Verificación con brazos falsos: orden de las llamadas, paso 0, pregunta cuya fuente llega después, reanudación a mitad de un paso sin duplicados, reanudación sin repetir ingestas, wiki más adelantado que el paso, tope de gasto sin escribir la línea fallida, y que `leer_resultados` lee la salida.
- [x] 3.2 Resumen final por sistema. Verificación: prueba con resultados conocidos: respuestas, abstenciones, costos, mediana de contexto y el comando de métricas.

## 4. Consola

- [x] 4.1 Crear `arnes/__main__.py` con `correr` (`--corrida`, `--pasos`, `--banco`, `--estado-minimo`, `--tipos`, `--preguntas`, `--estimar`, `--confirmo-usd`), la construcción de los brazos reales (índice de Chroma y wiki por corrida) y los avisos de validez. Verificación: pruebas con fábricas falsas: `--estimar` no llama al modelo ni crea archivos, la puerta de costo, el estado por defecto, el aviso de piloto, el código 1 ante un fallo y un RAG vacío en el paso 0.

## 5. Piloto real

- [x] 5.1 Con aviso previo al usuario y la estimación, correr un piloto con pocas preguntas (T1, T4 y T5 del banco), pasos 0 y 5, estado mínimo `borrador`, y revisar los archivos. Verificación: `leer_resultados` lee la salida, `python -m wikillm.eval metricas` corre sobre ella, la reanudación tras un corte forzado no duplica líneas y se informan el costo y el tiempo por brazo.
- [x] 5.2 Anotar en `docs/bitacora-datos.md` lo medido y la estimación de la corrida completa con esas cifras. Verificación: la entrada tiene cifras de la corrida y no estimaciones sueltas.

## 6. Cierre

- [x] 6.1 Ejecutar `uv run ruff check . && uv run ruff format --check . && uv run pytest` y `openspec validate arnes-comparacion`. Verificación: todo termina sin errores.
