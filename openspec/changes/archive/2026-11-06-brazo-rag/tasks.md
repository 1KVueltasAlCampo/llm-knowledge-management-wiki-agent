# Tasks

## 1. Preparación

- [x] 1.1 Añadir `langchain-chroma`, `langchain-huggingface` y `langchain-text-splitters` con `uv add` y configurar en `pyproject.toml` el índice `cu126` de PyTorch para Windows y Linux. Verificación: `uv run python -c "import torch, chromadb, langchain_chroma, langchain_huggingface; print(torch.__version__, torch.cuda.is_available())"` imprime una versión `+cu126` y `True`.
- [x] 1.2 Confirmar que `data/chroma/` está ignorada por Git. Verificación: `git check-ignore data/chroma/x` la ignora.

## 2. Fragmentación

- [x] 2.1 Crear `rag/fragmentos.py` con el tipo `Fragmento` (texto, identificador, título, sección) y la división de un Gold: por `##`, luego por párrafos con el límite de tokens medido por una función de longitud inyectable. Verificación: pruebas con un Gold sintético y una medida falsa de tokens comprueban sección corta, sección larga subdividida, párrafo gigante partido, prefijo «Título — Sección» y metadatos.
- [x] 2.2 Leer todos los Gold de una carpeta con `leer_gold` y producir los fragmentos. Verificación: una prueba con dos Gold sintéticos devuelve los fragmentos de ambos con su identificador.

## 3. Índice vectorial

- [x] 3.1 Crear `rag/indice.py` que cree los embeddings con `EMBEDDING_MODEL` y `EMBEDDING_DEVICE`, con error claro si falta la GPU. Verificación: una prueba que simula `cuda` no disponible comprueba que el mensaje menciona `EMBEDDING_DEVICE=cpu`.
- [x] 3.2 Construir el índice Chroma persistente con huella del Gold: reutilizarlo si no cambió y reconstruirlo por completo si cambió. Verificación: pruebas con embeddings falsos (determinísticos, sin descargar nada) comprueban primera construcción, segunda ejecución sin recalcular y reconstrucción sin restos tras modificar un Gold.
- [x] 3.3 Recuperar los `k` fragmentos más cercanos con sus metadatos. Verificación: una prueba con embeddings falsos comprueba el límite `k`, el orden y los metadatos.

## 4. Brazo RAG

- [x] 4.1 Crear `rag/brazo.py` con el prompt, la llamada única al modelo con etiqueta `rag` y la extracción de fuentes citadas filtradas contra las recuperadas. Verificación: pruebas con un cliente del modelo falso comprueban el contenido del mensaje, una sola llamada, el orden de las fuentes, el descarte de un identificador no recuperado y las fuentes vacías cuando no hay citas.
- [x] 4.2 Devolver un `ResultadoBrazo` válido con segundos de recuperación y generación. Verificación: una prueba comprueba que `BrazoRag` cumple `Brazo`, `nombre == "rag"`, `llamadas == 1` y segundos mayores que cero.
- [x] 4.3 Añadir `python -m wikillm.rag` con subcomandos `indexar` y `preguntar "..."` que imprimen el índice construido o la respuesta con fuentes y métricas. Verificación: una prueba de la función principal con piezas falsas comprueba la salida.

## 5. Ejecución real

- [x] 5.1 Indexar los 5 Gold reales en el Terminal. Verificación: informe con el número de fragmentos, el dispositivo y el tiempo; la segunda ejecución no recalcula.
- [x] 5.2 Con el aviso previo al usuario, hacer **una** pregunta real (de coste cercano a 0,001 USD) sobre un paper del corpus. Verificación: la respuesta cita un paper recuperado, las fuentes salen no vacías, el registro `results/dev/llamadas.jsonl` contiene la llamada con su costo.

## 6. Cierre

- [x] 6.1 Ejecutar `uv run ruff check . && uv run ruff format --check . && uv run pytest` y `openspec validate brazo-rag`. Verificación: todo termina sin errores.
