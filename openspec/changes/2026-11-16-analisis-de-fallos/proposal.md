# Proposal

## Why

Las métricas dicen cuánto acierta cada brazo, pero no por qué falla. Para interpretar los resultados
(no solo reportarlos) hace falta separar los fallos: abstenerse cuando había respuesta, responder sin
citar la fuente que hacía falta, citar solo parte de las fuentes de una pregunta de varios papers, o
citarlas todas y aun así equivocarse. Cada causa apunta a una parte distinta del sistema.

## What Changes

- Nuevo comando `uv run python -m wikillm.eval fallos --corrida results/<corrida>` que lee
  `evaluados.jsonl` y el banco, y escribe en `results/<corrida>/fallos/`:
  - `detalle.csv`: una fila por respuesta no correcta con su categoría;
  - `resumen.md`: conteos por sistema y categoría, y por sistema y tipo de pregunta.
- La categoría sale de datos guardados: si abstuvo, qué papers citó (por el `span_id`) frente a las
  `fuentes_requeridas` de la pregunta, y la marca de respuesta obsoleta. No llama a ningún modelo.

## Impact

- Código nuevo en `eval/`. Es un análisis descriptivo: no cambia veredictos ni métricas.
- Las categorías son una pista, no un diagnóstico: citar todas las fuentes no prueba que el modelo las
  haya leído bien. El resumen lo dice y `detalle.csv` permite revisar casos a mano.
