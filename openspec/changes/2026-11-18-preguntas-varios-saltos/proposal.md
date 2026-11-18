# Proposal

## Why

El tutor planteó usar las citas entre papers como aristas para alcanzar un segundo paper (varios saltos).
Hasta ahora las pruebas con citas (Graphify, precarga por citas) usaron un subconjunto de preguntas elegido
mirando resultados. Falta medir, sin cambiar ninguna pregunta, qué tan bien contesta cada sistema las
preguntas que ya exigen combinar varios papers y si una herramienta de citas ayuda de punta a punta.

## What Changes

- `scripts/varios_saltos.py` (sin gasto): reparte los resultados ya guardados del paso 100 entre
  preguntas de un paper, de varios papers y de varios papers **encadenados por citas** (alguno cita a otro
  de los exigidos, según `referencias_en_corpus`), para RAG con `k` = 5, 10, 15, 20 y wiki con 8 y 4
  acciones.
- Herramienta `cites` y variante `citas` en `scripts/comparar_herramientas.py`: el agente puede pedir los
  papers que cita un paper y los que lo citan, con su página del wiki. Se prueba sobre las 34 preguntas
  de varios papers contra el mismo agente sin la herramienta (`generico`).
- `docs/preguntas-de-varios-saltos.md` con los resultados y sus límites.

## Capabilities

### Added Capabilities
- `evaluation`: análisis de preguntas de varios saltos y prueba de la herramienta de citas.

## Impact

- No cambia el banco, los prompts ni el brazo del wiki; la herramienta vive solo en el script exploratorio.
- Gasto estimado: 0,08 USD (68 respuestas). Dueño: Juan David (`scripts/`, `docs/`).
