# Proposal

## Why

`arnes correr` siempre arma los brazos `rag` y `wiki` (y `wiki_grafo` con `--graphify`). Para medir la
sensibilidad del RAG al número de fragmentos (`--k`) o para correr solo un brazo nuevo sobre el wiki ya
construido hay que pagar de nuevo los otros brazos, que ya se midieron en otra corrida. Con
temperatura 0, repetirlos no aporta nada.

## What Changes

- `arnes correr --brazos rag,wiki,wiki_grafo` elige qué brazos responden. Sin la opción, todo queda
  como antes (`rag`, `wiki` y, con `--graphify`, el brazo con grafo).
- `corrida.json` declara solo los brazos elegidos; la estimación y el índice vectorial (Qdrant) se
  arman solo para ellos.
- Validaciones antes de gastar: nombres desconocidos, `--graphify` sin el brazo con grafo en la lista,
  brazo con grafo sin `wiki` (consulta el wiki que ese brazo sitúa en cada paso) y `--wiki-de` sin `wiki`.

## Capabilities

### Modified Capabilities
- `harness`: selección de brazos por corrida.

## Impact

- Sin `--brazos` no cambia ninguna salida ni `corrida.json`, así que las corridas empezadas siguen
  reanudándose.
- Una corrida con otros brazos se reanuda solo con los mismos (`brazos` va en la comprobación).
- Dueño: `src/wikillm/arnes/` (Juan David). Se necesita para las pruebas de sensibilidad del RAG.
