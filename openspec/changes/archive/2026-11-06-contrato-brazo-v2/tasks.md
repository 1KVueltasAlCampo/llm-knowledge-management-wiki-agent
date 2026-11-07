# Tasks

## 1. Contrato de los brazos

- [x] 1.1 En `common/responder.py`, cambiar `ResultadoBrazo` a `citas`, `abstuvo` y `tokens_contexto`, con `fuentes` derivada, validación (forma de `span_id`, citas repetidas, abstención con citas) y `a_dict`. Verificación: pruebas con un resultado válido, uno por cada incumplimiento y la derivación de `fuentes`.
- [x] 1.2 Añadir `FRASE_ABSTENCION` y `es_abstencion`, y `desde_llamadas` con `tokens_contexto` calculado con `aproximar_tokens`. Verificación: pruebas con la frase tal cual, con otra puntuación, con una cifra, y con 4.000 caracteres de contexto (1.000 tokens).
- [x] 1.3 Añadir `ResultadoIngesta` (con su suma de llamadas y sus validaciones) y el método `ingerir` al protocolo `Brazo`. Verificación: pruebas de un brazo falso que lo cumple y de objetos a los que les falta `nombre`, `ingerir` o `responder`.
- [x] 1.4 Añadir `a_linea_resultado` y `a_linea_ingesta`. Verificación: una prueba escribe una línea de resultado y `leer_resultados` de `wikillm.eval` la acepta con `citations`, `abstained` y `context_tokens`; otra comprueba la línea de ingesta y su serialización.
- [x] 1.5 Actualizar `specs/interfaz-responder.md`. Verificación: describe cada campo nuevo y su ejemplo de brazo mínimo ejecuta sin error.

## 2. RAG v2

- [x] 2.1 En `rag/fragmentos.py`, construir fragmentos a partir de los spans (`calcular_spans`): agrupar por sección hasta el máximo, partir spans largos conservando su `span_id` y rotular cada span. Verificación: pruebas con spans cortos, sección larga, tabla gigante y que ningún fragmento pasa el máximo con una medida falsa de tokens.
- [x] 2.2 En `rag/indice.py`, ingesta por paper con huella del Gold, reemplazo si cambió y recuperación restringida a los papers ingeridos. Verificación: pruebas con embeddings falsos de primera ingesta, reingesta sin recalcular, Gold modificado, paper no ingerido que no aparece y corpus vacío.
- [x] 2.3 Comprobar al ingerir que el `hash` del Gold coincide con `data/gold/corpus.jsonl`. Verificación: una prueba con hash distinto lanza un error que nombra el paper.
- [x] 2.4 En `rag/brazo.py`, prompt en inglés con contexto rotulado, `ingerir`, citas validadas contra lo recuperado y `spans.jsonl`, `abstuvo` y `tokens_contexto`. Verificación: pruebas con un cliente del modelo falso: mensaje en inglés con los `span_id`, una sola llamada, citas en orden, descarte de una cita no recuperada y de una inventada, abstención con citas vacías, contexto vacío.
- [x] 2.5 Actualizar `python -m wikillm.rag`: `indexar` ingiere los papers en `orden_ingesta` (con `--paso N` para los primeros N) y `preguntar` responde con lo ingerido. Verificación: una prueba de la función principal con piezas falsas.

## 3. Ejecución real

- [x] 3.1 Ingerir los 50 papers en orden con embeddings reales. Verificación: informe con fragmentos, segundos por ingesta y total; una segunda ejecución no recalcula; sin errores de hash.
- [x] 3.2 Con aviso previo al usuario, hacer **una** pregunta real (~0,0003 USD) con los 50 ingeridos. Verificación: las citas resuelven a spans de `spans.jsonl`, la línea de resultado pasa `leer_resultados` y el registro de llamadas contiene el costo.
- [x] 3.3 Repetir la prueba gratuita de recuperación sobre los borradores y anotar el resultado en `docs/bitacora-datos.md`. Verificación: comparable con la medición del 6-nov (78 % y 48 % en T1).

## 4. Cierre

- [x] 4.1 Ejecutar `uv run ruff check . && uv run ruff format --check . && uv run pytest` y `openspec validate contrato-brazo-v2`. Verificación: todo termina sin errores.
