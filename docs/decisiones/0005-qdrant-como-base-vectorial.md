# 0005. Qdrant en modo local como base vectorial del RAG

**Fecha:** 9 de noviembre de 2026. **Estado:** vigente; reemplaza el uso de Chroma.

## Decisión
El índice del RAG usa **Qdrant en modo local embebido** (`QdrantClient(path="data/qdrant")`,
sin servidor), a través de `langchain-qdrant`, en lugar de Chroma. Todo lo demás sigue igual:
modelo de embeddings `BAAI/bge-small-en-v1.5`, fragmentos alineados con los `span_id`, distancia
coseno, top-5 y filtro por los papers ingeridos en cada paso.

## Por qué
- Lo recomendó el profesor, y Juan David (dueño de `src/wikillm/rag/`) estuvo de acuerdo.
- En modo local, Qdrant compara la pregunta con todos los vectores (búsqueda exacta). Con 5.430
  fragmentos es instantáneo y hace que la recuperación sea determinista, mientras que el HNSW de
  Chroma es aproximado. Para un experimento que compara arquitecturas, la búsqueda exacta quita una
  fuente de ruido.
- Sigue siendo búsqueda vectorial y nada más (regla 4 de la constitución): cambia el almacén, no
  la arquitectura del RAG.
- Se cambia antes de la corrida completa (23–27 de noviembre), así que no invalida ningún
  resultado final.

## Consecuencias
- El índice vive en `data/qdrant/` (y `data/qdrant/<corrida>` en el arnés). Hay que reconstruirlo
  con `uv run python -m wikillm.rag indexar`. `data/chroma/` queda sin uso.
- Qdrant local deja abrir la carpeta a **un solo proceso**. El panel la tiene abierta mientras
  corre, así que `scripts/verificar_demo.py` le pregunta al panel por el índice en lugar de
  abrirla. Para usar `wikillm.rag` sobre `data/qdrant` hay que cerrar el panel.
- `corrida.json` guarda `base_vectorial: "qdrant"` en los parámetros del brazo RAG. Una corrida
  empezada con Chroma no se puede reanudar con Qdrant.
- El piloto se repite como `piloto-2` para que todas las cifras salgan de la misma base vectorial.
- La opción `--chroma` pasa a llamarse `--indice`. `--chroma` se sigue aceptando como alias.
