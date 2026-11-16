# Proposal

## Why

Los autores decidieron (decisión 0010) que las 40 preguntas nuevas cuenten sin revisión cruzada. Hoy
`ampliar-banco` solo las deja en `verificado_a` o `verificado_b`, y con eso la corrida «no vale para el informe».

## What Changes

- `ampliar-banco --acordar-por <decisión>` pasa las preguntas nuevas a `acordado` y anota en
  `revision.acordado` la decisión y que no hubo revisión cruzada.
- ADR 0010.

## Impact

- Solo una persona decide; el código lo registra. Las 60 preguntas anteriores no cambian.
