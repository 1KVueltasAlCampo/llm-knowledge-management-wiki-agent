# Tasks

## 1. Base común

- [x] 1.1 Crear `common/respuesta.py` con las reglas de respuesta y la extracción de citas que hoy están en `rag/brazo.py`, y hacer que el RAG las importe. Verificación: las pruebas del RAG siguen en verde, y una prueba comprueba que las reglas del RAG y las del wiki contienen el mismo texto.

## 2. El wiki en disco

- [x] 2.1 Crear `wiki/almacen.py`: crear la carpeta, leer y escribir páginas con su encabezado (incluido el resumen), regenerar `index.md`, añadir entradas a `log.md` y guardar copias (commit y etiqueta `paso-N`) en un repositorio Git propio. Verificación: pruebas con una carpeta temporal: wiki nuevo, ida y vuelta de una página, índice con todas las páginas, entrada del registro, commit con su etiqueta.
- [x] 2.2 Crear `wiki/lectura.py` con el paper rotulado con sus `span_id`. Verificación: una prueba con un Gold sintético comprueba que los rótulos coinciden con `calcular_spans`, que los encabezados quedan sin rótulo y que el texto no cambia.

## 3. Herramientas de consulta

- [x] 3.1 Crear `wiki/herramientas.py` con `wiki_search` (puntuación léxica con más peso en el título y el resumen, máximo 8 resultados, determinista) y `wiki_read` (hasta 3 páginas, nombres inexistentes informados). Verificación: pruebas con coincidencia en el título frente al cuerpo, sin coincidencias, orden determinista, páginas existentes e inexistentes y más de tres páginas.

## 4. Ingesta

- [x] 4.1 Escribir los prompts de plan y de escritura (inglés, paper primero, paper como dato, regla del valor vigente y el superado, formato JSON, tope de tamaño de página) y el análisis de sus salidas. Verificación: pruebas del orden del mensaje, de la regla del valor vigente, de la ausencia de identificadores de paper y cifras, y de que un plan con un nombre inexistente lo ignora.
- [x] 4.2 Aplicar las páginas escritas con validación: citas solo de papers ya ingeridos que existan en `spans.jsonl`, enlaces `[[slug]]` solo con destino tras el lote, y conteo de citas eliminadas, enlaces rotos y líneas con cifra sin cita. Verificación: pruebas con una cita inventada, una de un paper no ingerido, un enlace sin destino, uno a una página del mismo lote y una línea con cifra sin cita.
- [x] 4.3 Implementar `ingerir` con las dos llamadas, la repetición ante un JSON inválido, la atomicidad, el registro, la copia versionada y la no repetición de un paper ya ingerido. Verificación: pruebas con un cliente falso: dos llamadas con el paper primero, suma del resultado, JSON inválido recuperado, JSON inválido dos veces sin tocar archivos, commit con etiqueta y reingesta sin llamadas.

## 5. Consulta agéntica

- [x] 5.1 Implementar el bucle del agente en `wiki/consulta.py`: acciones JSON, tope de acciones, paciencia de búsquedas vacías, lectura obligatoria antes de responder, respuesta final forzada, repetición ante una acción mal formada, wiki vacío con una sola llamada, citas válidas solo si están en lo leído y `tokens_contexto` con lo que devolvieron las herramientas. Verificación: pruebas con un cliente falso guionado: búsqueda, lectura y respuesta; tope agotado; tres búsquedas vacías; responder sin leer; acción mal formada recuperada y no recuperada; wiki vacío; cita ajena a lo leído; abstención con citas vacías.

## 6. Brazo y consola

- [x] 6.1 Crear `BrazoWiki`, cumplir el contrato `Brazo` y añadir `python -m wikillm.wiki` con `ingerir` (con `--paso N`) y `preguntar`; añadir `data/wiki/` a `.gitignore`. Verificación: una prueba de que cumple `Brazo`, una de la función principal con piezas falsas y `git check-ignore data/wiki/x`.

## 7. Ejecución real

- [x] 7.1 Con aviso previo al usuario y su estimación, ingerir los 5 primeros papers con el modelo real y revisar el wiki que sale: páginas, citas eliminadas, enlaces rotos, líneas sin cita y tamaño. Verificación: informe de costo y segundos por ingesta, y proyección a los 50 papers.
- [x] 7.2 Con aviso previo, hacer tres preguntas reales (una de un solo paper, una de dos y una que deba abstenerse), registrando cuántas acciones usó el agente. Verificación: las citas resuelven a spans de `spans.jsonl`, la línea de resultado pasa `leer_resultados`, la abstención se reconoce y se informa el costo por pregunta.
- [x] 7.3 Anotar en `docs/bitacora-datos.md` el costo medido, la proyección y lo observado. Verificación: la entrada tiene cifras de la corrida y no estimaciones.

## 8. Cierre

- [x] 8.1 Ejecutar `uv run ruff check . && uv run ruff format --check . && uv run pytest` y `openspec validate agente-wiki-v1`. Verificación: todo termina sin errores.
