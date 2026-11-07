# Proposal

## Why

Las preguntas T4 miden si un sistema actualiza lo que sabe cuando entra un paper que corrige un dato. Los borradores de la mitad A mostraron tres defectos: 13 de 18 nombran al paper posterior en la pregunta (en pasos anteriores a su ingesta no se puede contestar), algunas tienen un «antes» que es otra magnitud, y las 18 tienen vacías las claves de la respuesta previa, así que ahí siempre decide el juez. Acordado con Juan Diego el 6-nov-2026: la pregunta es neutra, trata de un mismo dato y se repite en varios pasos; la respuesta correcta cambia con el paso, y se cuenta como «obsoleta» la que tras el cambio sigue dando el valor viejo.

## What Changes

- El redactor recibe una instrucción nueva para T4: un solo dato que ambos papers reportan, redacción neutra (sin «later», «earlier», «original»…) y claves para la respuesta previa (`answer_before_keys`).
- Un borrador T4 se descarta si menciona el orden de los papers o si no trae la respuesta previa con sus claves. Las claves previas pasan a ser `respuesta_clave` del tramo inicial, en vez de borrarse.
- `validar-banco` marca los T4 que mencionen el orden o no tengan claves previas.
- Las métricas marcan como `obsoleta` la respuesta T4 que, desde el paso del cambio, no es correcta y repite todas las claves previas; el agregado por paso cuenta cuántas hay y su tasa.

## Capabilities

### New Capabilities
- `banco-t4`: forma válida de una pregunta T4 y la medida de respuesta obsoleta.

### Modified Capabilities

## Impact

- Código de Juan Diego (`src/wikillm/eval/`: `redaccion.py`, `banco.py`, `metricas.py`) y sus pruebas. Se avisa en `docs/bitacora-datos.md`, como pide `AGENTS.md`.
- No toca ningún contrato de `specs/`: añade un campo opcional (`answer_before_keys`) a lo que el redactor devuelve.
- No gasta saldo. Los 102 borradores ya generados de la mitad A no se regeneran: los T4 con problema se corrigen a mano en la página de revisión, y `validar-banco` los señala.
