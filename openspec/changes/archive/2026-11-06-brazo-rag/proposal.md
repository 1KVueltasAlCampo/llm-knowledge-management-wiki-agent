# Proposal

## Why

El RAG es la línea base de toda la comparación: sin él no hay contra qué medir al wiki. El tutor
pidió que sea simple (LangChain, una base de datos vectorial, «lo más sencillo posible, eso sale
en un día») y que use el mismo modelo que el wiki. Con el contrato `Brazo` ya fijado y los 5
papers en Gold, se puede construir ahora y dejarlo listo para que Juan Diego lo itere.

## What Changes

- Se añade un proceso que lee los archivos Gold, los divide en fragmentos (primero por los
  encabezados `##`, que el contrato del Gold declara como fronteras, y luego por párrafos si un
  fragmento excede lo que el modelo de embeddings puede leer), calcula sus embeddings en local y
  los guarda en un índice vectorial persistente.
- El índice es idempotente: si el Gold no cambió, no se recalcula.
- Se añade el brazo RAG: dada una pregunta, recupera los fragmentos más cercanos, hace **una**
  llamada al modelo con ellos como contexto y devuelve un `ResultadoBrazo`. Las fuentes son los
  papers que la respuesta cita y que estaban entre los fragmentos recuperados.
- Los embeddings usan la GPU por defecto (decisión 0002) y, si no está disponible, el error
  indica cambiar `EMBEDDING_DEVICE` a `cpu`.
- Se configura PyTorch con CUDA en `pyproject.toml`.

## Capabilities

### New Capabilities
- `rag-arm`: línea base RAG simple (fragmentación, índice vectorial, recuperación y generación
  con el modelo único) que cumple el contrato `Brazo`.

### Modified Capabilities

## Impact

- Código nuevo en `src/wikillm/rag/` y pruebas con embeddings falsos (sin descargar modelos ni
  usar GPU).
- Dependencias nuevas: `langchain-chroma`, `langchain-huggingface`, `langchain-text-splitters`
  (y con ellas `chromadb`, `sentence-transformers` y `torch`). Instalar PyTorch con CUDA descarga
  unos 3 GB. El índice vive en `data/chroma/`, ignorado por Git.
- La primera ejecución real descarga el modelo `BAAI/bge-small-en-v1.5` (unos 130 MB) de Hugging
  Face.
- La verificación real hace **una pregunta** al modelo (del orden de 0,001 USD). Se avisará antes.
- No se implementan reordenamiento, búsqueda híbrida ni reescritura de preguntas: eso es lo que
  Juan Diego podrá probar al iterar.
