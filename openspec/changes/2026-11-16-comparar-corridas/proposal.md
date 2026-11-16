# Proposal

## Why

La pregunta de la ampliación es qué pasa con cada brazo cuando el corpus pasa de 50 a 100 papers con
más casos de borde. `informe` compara los brazos dentro de una corrida; falta comparar **cada brazo
consigo mismo entre corridas**, sobre las mismas preguntas y de forma pareada, y mostrar aparte las
preguntas nuevas (que son preliminares).

## What Changes

- `uv run python -m wikillm.eval comparar-corridas --base results/<a> --ampliada results/<b>
  --paso-base N --paso-ampliada M --salida <carpeta>` lee los `evaluados.jsonl` de las dos corridas y
  escribe `comparacion.md` y `comparacion.csv`:
  - por sistema, sobre las preguntas respondibles en ambos pasos que están en las dos corridas:
    cobertura en cada una, diferencia (ampliada − base), IC95 bootstrap sobre las preguntas y McNemar
    exacto sobre los pares discordantes;
  - lo mismo por tipo de pregunta;
  - las preguntas que solo están en la ampliada (preliminares) con la comparación pareada wiki frente
    a RAG en el paso final;
  - contexto medio y costo por respuesta en esos pasos, y el costo de ingesta y de preguntas de cada
    corrida.
- Reutiliza `estadistica` (bootstrap y McNemar); no cambia ninguna métrica.

## Impact

- Código nuevo en `eval/`. Sin llamadas a API.
- Las dos corridas difieren en orden y en tamaño del corpus: el efecto de «más papers» se mezcla con
  el del orden. La salida lo declara.
