# Proposal

## Why

Al ampliar el corpus de 50 a 100 papers en orden cronológico, los 50 papers nuevos (de 2023 a 2025)
entran antes que los de 2026 y cambian la posición de todos. La `ingesta_minima` de las 60 preguntas
acordadas depende de esa posición, así que hay que recalcularla; y las preguntas de caso de borde
verificadas por Juan Diego (en el Excel de la ampliación) deben convertirse al formato del banco con
su evidencia anclada a fragmentos reales (`span_id` y huella), no copiada a mano.

## What Changes

- `uv run python -m wikillm.eval ampliar-banco` lee el banco acordado, las definiciones de las
  preguntas nuevas, el manifest del corpus de 100 papers y sus fragmentos, y escribe un banco nuevo
  (el original no se toca):
  - recalcula `ingesta_minima` y, en T4, el paso del cambio con el orden del nuevo manifest;
  - convierte cada definición en una pregunta con `evidencia` resuelta desde citas literales del
    paper (el fragmento cuyo texto contiene la cita) y estado `verificado_a`;
  - el banco resultante debe pasar `validar-banco` contra el nuevo manifest.
- Las preguntas nuevas llevan `revision.cruzada` ausente: son **preliminares** hasta que el otro autor
  las revise (regla 11), y el banco lo declara.

## Impact

- Código nuevo en `eval/`. No cambia `banco.jsonl`, que sigue siendo la base de `oficial-1`.
- Una cita que no se encuentra en ningún fragmento, o que cae en fragmentos de un paper que no es una
  fuente de la pregunta, detiene el comando sin escribir nada.
