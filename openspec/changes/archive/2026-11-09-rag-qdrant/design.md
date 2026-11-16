# Design

## Context

Hoy `IndiceRag` (`src/wikillm/rag/indice.py`) usa `chromadb.PersistentClient` y
`langchain_chroma.Chroma`. Lo que usa de Chroma es poco: crear o abrir la colección con distancia
coseno, `add_texts` en lotes con metadatos, `get`/`delete` filtrando por `arxiv_id` (para la
idempotencia por huella), `count` y `similarity_search_with_score` con un filtro
`arxiv_id ∈ ingeridos`. El resto del sistema (brazo RAG, arnés, panel) solo ve `IndiceRag`.

## Goals / Non-Goals

**Goals:**
- Cambiar Chroma por Qdrant sin cambiar el comportamiento observable del RAG: mismos fragmentos,
  mismo modelo de embeddings, coseno, top-5, filtro por papers ingeridos e idempotencia.
- Que la demostración (panel y verificación) funcione igual con el índice nuevo.
- Que una corrida empezada con Chroma no pueda mezclarse con Qdrant al reanudar.

**Non-Goals:**
- Qdrant como servidor (Docker o nube). El modo local alcanza para 5.430 fragmentos.
- Cambiar la fragmentación, el modelo de embeddings, `k` o el prompt del RAG.
- Búsqueda híbrida, re-ranking o cualquier cosa más allá de la búsqueda vectorial (regla 4).

## Decisions

1. **`langchain-qdrant` sobre un `QdrantClient(path=...)` local.** Se mantiene LangChain, como en el
   RAG original. `QdrantVectorStore` se crea sobre un cliente local. La colección se crea con
   `VectorParams(size=<dimensión de los embeddings>, distance=COSINE)` si no existe. La
   idempotencia, el borrado y el conteo usan el cliente directamente (`scroll`, `delete` con
   `FilterSelector`, `count(exact=True)`), igual que hoy se usa `_collection` de Chroma.
   *Alternativa descartada:* usar solo `qdrant-client` sin LangChain. Quedaría más corto, pero el
   brazo dejaría de ser el «RAG simple con LangChain» acordado con el tutor.
2. **Ids de punto con `uuid5`.** Qdrant acepta como id solo enteros o UUID. El id de cada fragmento
   (`<arxiv_id>#…`) se convierte con `uuid5(NAMESPACE_URL, id)`, que es determinista, y el id
   original se conserva en los metadatos.
3. **Filtro sobre `metadata.arxiv_id`.** LangChain guarda los metadatos bajo la clave `metadata` del
   payload. El filtro de recuperación es `FieldCondition(key="metadata.arxiv_id",
   match=MatchAny(any=ingeridos))`.
4. **Distancia = 1 − similitud.** Qdrant devuelve la similitud coseno (mayor es más cercano). Chroma
   devolvía una distancia. Se convierte para que `Recuperado.distancia`, las trazas
   (`{"span_ids", "distancia"}`) y la barra del panel (`1 − distancia`) mantengan su sentido.
5. **Búsqueda exacta.** El modo local de Qdrant compara contra todos los vectores (no usa HNSW).
   Con 5.430 fragmentos de 384 dimensiones es instantáneo y hace la recuperación determinista. Es
   la causa esperada de cualquier diferencia de top-5 frente a `piloto-1`.
6. **Carpetas.** `data/qdrant` para la demo y `data/qdrant/<corrida>` para el arnés. Se añade
   `qdrant/` a `.gitignore`. La opción `--chroma` pasa a `--indice` (`dest="indice"`), y `--chroma`
   se acepta como alias oculto para no romper órdenes guardadas.
7. **`base_vectorial` en los parámetros del brazo.** `brazos.rag` pasa de `{"k": 5}` a
   `{"k": 5, "base_vectorial": "qdrant"}`. `_comprobar_reanudacion` ya compara `brazos`, así que
   reanudar una corrida de Chroma aborta sin código nuevo de comprobación.
8. **Un solo proceso por carpeta.** Qdrant local bloquea la carpeta. El panel la tiene abierta
   mientras corre, y `scripts/verificar_demo.py` (que el panel lanza como subproceso) no podría
   abrirla. La verificación pregunta primero a `http://127.0.0.1:8765/api/estado`, que suma
   `rag_fragmentos`, y solo si el panel no responde abre la carpeta. Las corridas del arnés usan
   carpetas propias por corrida, así que no chocan con el panel.

## Risks / Trade-offs

- **[El top-5 cambia en algunas preguntas]** → Es esperable (búsqueda exacta frente a HNSW). Por
  eso se repite el piloto como `piloto-2` y se comparan cobertura y contexto con `piloto-1` en la
  bitácora.
- **[La API de `langchain-qdrant` cambia entre versiones]** → Se fija la versión en `pyproject.toml`
  y `uv.lock`, y las pruebas de `IndiceRag` corren contra Qdrant local real (sin red) con
  embeddings falsos.
- **[Dos procesos abren la misma carpeta]** → El error de Qdrant es claro («already accessed by
  another instance»). La verificación lo evita preguntando al panel, y la documentación dice que
  para usar `wikillm.rag` sobre `data/qdrant` hay que cerrar el panel.
- **[Quedan copias viejas en `data/chroma`]** → Están ignoradas por Git. La bitácora dice que se
  pueden borrar.

## Migration Plan

1. Instalar dependencias (`uv sync`) y reconstruir el índice:
   `uv run python -m wikillm.rag indexar` (unos 72 s en GPU, sin costo).
2. Reiniciar el panel para que abra `data/qdrant`.
3. Repetir el piloto como `piloto-2` y recalcular sus métricas.
4. Rollback: revertir el commit y reconstruir `data/chroma` con la orden anterior.
