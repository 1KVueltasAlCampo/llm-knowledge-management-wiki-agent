# Proposal

## Why

El profesor recomendó usar Qdrant en lugar de Chroma como base vectorial del RAG, y Juan David
(dueño de `src/wikillm/rag/`) está de acuerdo. Conviene hacerlo ahora: la corrida completa está
planeada para el 23–27 de noviembre, así que el cambio no invalida ningún resultado final. Solo el
piloto, hecho con Chroma, se repite para que todas las cifras salgan de la misma base vectorial.

## What Changes

- `IndiceRag` (`src/wikillm/rag/indice.py`) guarda y busca los fragmentos en **Qdrant en modo
  local embebido** (`QdrantClient(path=...)`, sin servidor). El resto se mantiene igual: mismo
  modelo de embeddings (`BAAI/bge-small-en-v1.5`), mismos fragmentos, distancia coseno, top-5,
  filtro por los papers ingeridos e ingesta idempotente por la huella del Gold.
- En modo local Qdrant hace búsqueda **exacta** (no aproximada como el HNSW de Chroma), así que la
  recuperación es determinista.
- El índice pasa de `data/chroma/` a `data/qdrant/` (y `data/qdrant/<corrida>` en el arnés). La
  opción `--chroma` de `wikillm.rag` y `wikillm.arnes comparar` pasa a llamarse `--indice`;
  `--chroma` se sigue aceptando como alias para no romper órdenes guardadas.
- Los parámetros del brazo RAG en `corrida.json` incluyen `base_vectorial: "qdrant"`, así que una
  corrida empezada con Chroma no se puede reanudar con Qdrant sin que la reanudación aborte.
- Herramienta de la demo: el panel y `scripts/verificar_demo.py` usan el índice de Qdrant. Como
  Qdrant local bloquea la carpeta para un solo proceso, la verificación de la preparación pregunta
  al panel cuando el panel tiene el índice abierto, en vez de fallar.
- Se registra la decisión `docs/decisiones/0005-qdrant-como-base-vectorial.md`.

## Capabilities

### New Capabilities

### Modified Capabilities
- `rag-arm`: el índice persistente es Qdrant local con búsqueda exacta y queda declarado en los
  parámetros del brazo.
- `harness`: el estado aislado de cada corrida usa `data/qdrant/<corrida>`.
- `demo-panel`: la verificación de la preparación funciona con el índice abierto por el panel.

## Impact

- **Contratos de `specs/`:** ninguno. `formato-gold.md` y `contrato-resultados.md` no cambian: las
  respuestas siguen citando `span_id` y el formato de `respuestas.jsonl` es el mismo.
- **Dueños:** `src/wikillm/rag/` y `src/wikillm/panel/` son de Juan David, que aprobó el cambio. Se
  avisa en el PR y en `docs/bitacora-datos.md`.
- **Dependencias:** se quita `langchain-chroma` (y con ella `chromadb`) y se añade
  `langchain-qdrant` (que trae `qdrant-client`).
- **Datos:** hay que reconstruir el índice: unos 72 s en GPU, sin costo de API. `data/chroma/`
  queda sin uso y se puede borrar.
- **Gasto de API:** la implementación y las pruebas no gastan saldo. El piloto se repite como
  `results/piloto-2`, con las mismas 17 preguntas y los mismos pasos (0 y 5) que `piloto-1`. El
  arnés no permite correr un solo brazo, así que se repiten los dos aunque solo cambie el RAG:
  `piloto-1` costó 0,016 USD en preguntas, más unos 0,04 USD de ingesta del wiki. En total son
  **unos 0,06 USD**, el doble en hora pico. Antes de correrlo se imprime la cota de `--estimar`.
