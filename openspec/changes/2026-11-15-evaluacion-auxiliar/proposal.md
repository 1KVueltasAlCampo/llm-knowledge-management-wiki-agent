# Proposal

## Why

La capa 2 de correctitud depende de un solo juez (Gemini flash-lite) que, según la decisión 0003,
todavía no está calibrado. Para la pre-sustentación conviene medir cuánto coincide con un segundo
juez independiente, usando la cuota de Claude Code (sin gasto de API). La decisión 0006 fija los
límites: es evaluación **auxiliar**, nunca reemplaza veredictos ni estados del banco.

## What Changes

- `wikillm.eval auxiliar exportar --corrida results/<c>`: escribe `auxiliar/items.jsonl`, ciego
  (pregunta, respuesta de referencia, respuesta a calificar), con todas las respuestas
  indeterminadas en la capa determinista más una muestra aleatoria con semilla de las demás
  respondibles.
- `wikillm.eval auxiliar importar --corrida results/<c>`: lee `auxiliar/veredictos_claude.jsonl`
  y calcula acuerdo y kappa con el veredicto principal, en total y por origen del veredicto y por
  sistema. Escribe `auxiliar/acuerdo.json` y `auxiliar/acuerdo.md`.
- ADR 0006. No cambia métricas, contrato de resultados ni el arnés.

## Impact

- Código nuevo: `src/wikillm/eval/auxiliar.py` y subcomando `auxiliar`.
- Spec nueva: `evaluacion-auxiliar`. No llama a ninguna API (constitución #7).
