# Proposal

## Why

La constitución (regla 13) dice que el corpus es dato y no instrucción, y los prompts de los dos
brazos lo repiten, pero nunca se comprobó que el modelo lo cumpla. La rúbrica (R.6.2, Cr7) pide
evidencia de seguridad frente a texto malicioso dentro de los documentos.

## What Changes

- `wikillm.eval.inyeccion`: lógica pura de la prueba (ataques, siembra del texto, detección de éxito,
  elección de preguntas con semilla y resumen). Sin red.
- `scripts/prueba_inyeccion.py`: corre la prueba con el modelo real (`deepseek-flash`) sobre copias
  temporales; no modifica el Gold, el índice vectorial ni el wiki reales. Tres ataques (anulación
  directa, suplantación del sistema, secuestro del agente) en dos posiciones (la evidencia y otro
  fragmento) más un control sin ataque, en el RAG y en la consulta del wiki, y una ingesta del wiki
  con dos papers envenenados.
- Resultados en `results/inyeccion/` y análisis en `docs/prueba-de-inyeccion.md`.

## Capabilities

### Added Capabilities
- `evaluation`: prueba de inyección de instrucciones en los documentos.

## Impact

- No cambia los prompts ni el comportamiento de los brazos: la prueba mide las defensas actuales.
- Gasto estimado: 0,10 USD (tope 0,25 USD). Dueño: Juan David (`src/wikillm/eval/`, `scripts/`).
