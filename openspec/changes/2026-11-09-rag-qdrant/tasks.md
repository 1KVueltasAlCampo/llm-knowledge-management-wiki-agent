# Tasks

## 1. Dependencias
- [x] 1.1 Quitar `langchain-chroma` y añadir `langchain-qdrant` en `pyproject.toml` (`uv remove` / `uv add`); añadir `qdrant/` a `.gitignore`. Verificación: `uv sync` termina sin errores y `uv run python -c "import langchain_qdrant, qdrant_client"` funciona.

## 2. Índice en Qdrant
- [x] 2.1 Escribir primero las pruebas nuevas de `tests/test_rag_indice.py` (índice persistente entre procesos; recuperación limitada a los ingeridos con distancia creciente en [0, 2]) y verlas fallar. Verificación: `uv run pytest tests/test_rag_indice.py` en rojo.
- [x] 2.2 Reescribir `IndiceRag` sobre `QdrantClient(path=...)` + `QdrantVectorStore` (decisiones 1–5) y `RUTA_INDICE_POR_DEFECTO = data/qdrant`. Verificación: `uv run pytest tests/test_rag_indice.py` en verde, también las pruebas que ya había (idempotencia, Gold modificado, otra corrida).

## 3. Rutas y opciones
- [x] 3.1 `--indice` (alias `--chroma`) en `wikillm.rag` y `wikillm.arnes comparar`; `data/qdrant/<corrida>` en `arnes correr` y en el mensaje de `corrida.py`; `data/qdrant` en `panel/acciones.py`. Verificación: `uv run pytest tests/test_panel_acciones.py tests/test_arnes*` en verde y `--help` muestra `--indice`.
- [x] 3.2 `brazos.rag` con `base_vectorial: "qdrant"` y prueba de que reanudar una corrida con `{"k": 5}` aborta. Verificación: prueba nueva en verde.

## 4. Herramienta de la demostración
- [x] 4.1 `/api/estado` añade `rag_fragmentos` (número o `null`). Verificación: prueba en `tests/test_panel_servidor.py`.
- [x] 4.2 `scripts/verificar_demo.py` pregunta al panel y solo si no responde abre `data/qdrant`. Verificación: con el panel corriendo, la revisión del índice sale `[OK]`; con el panel apagado, también.

## 5. Datos y prueba en vivo
- [x] 5.1 Reconstruir el índice: `uv run python -m wikillm.rag indexar`. Verificación: 50 papers y el mismo número de fragmentos que con Chroma (5.430).
- [x] 5.2 Reiniciar el panel y repetir la demo de BeliefShift antes y después de ingerir el paper 6 (con aviso de costo, unos 0,02 USD). Verificación: los dos se abstienen antes y los dos responden 68,160 con `2603.23848#s18.p3` después; el wiki se deja en el paso 5.
- [x] 5.3 Repetir el piloto como `piloto-2` (mismas 17 preguntas, pasos 0 y 5; imprimir antes `--estimar`) y calcular sus métricas. Verificación: `results/piloto-2/metricas_por_paso.json` existe y la bitácora compara cobertura, contexto y costo con `piloto-1`.

## 6. Documentación
- [x] 6.1 `docs/decisiones/0005-qdrant-como-base-vectorial.md`, README (tabla de estado y descripción del RAG), `docs/presentacion/guion-demo.md`, comentarios y docstrings que nombran Chroma, y entrada en `docs/bitacora-datos.md`. Verificación: `rg -i chroma src scripts README.md docs/presentacion` solo deja las menciones históricas que se quieren conservar.
- [x] 6.2 Traer el one-pager (`docs/presentacion/one-pager.html`, rama `docs/one-pager`, sin PR) y actualizar la arquitectura y los algoritmos a Qdrant. Verificación: se abre en el navegador sin errores y no menciona Chroma.

## 7. Cierre
- [x] 7.1 `uv run ruff check . && uv run ruff format --check . && uv run pytest`. Verificación: todo pasa.
