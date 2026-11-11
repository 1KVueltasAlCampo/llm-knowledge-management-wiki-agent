# Tasks

## 1. Capas
- [x] 1.1 `src/wikillm/wiki/capas.py`: `GrafoDelWiki`, `BusquedaTgrep`, lectura por secciones y `CapasDeConsulta`. Verificación: `tests/test_wiki_capas.py`.
- [x] 1.2 `ConsultaWiki(capas=...)` y `analizar_accion(extras=...)` sin cambiar el modo base. Verificación: `test_sin_capas_el_agente_conserva_su_protocolo` y los tests de `test_wiki_consulta.py`.
- [x] 1.3 `BrazoWikiCapas`: comparte el wiki, no ingiere. Verificación: `test_el_brazo_con_capas_no_ingiere_y_comparte_el_wiki`.

## 2. Arnés
- [x] 2.1 `--graphify`, `--tgrep`, `--capas-trabajo` en `arnes correr`; brazo declarado en `corrida.json` y contado en la estimación. Verificación: `test_con_graphify_se_declara_un_brazo_mas_que_no_suma_ingesta` y `arnes correr --estimar` (4,67 USD sin opciones, 7,31 con ellas).
- [x] 2.2 Prueba con los binarios reales, sin llamar al modelo: grafo de 15 papers (15 nodos para «HippoRAG knowledge graph»), tgrep sobre «4\.38» y lectura con un nombre del grafo.

## 3. Cierre
- [x] 3.1 `uv run ruff check . && uv run ruff format --check . && uv run pytest`.
- [ ] 3.2 Repetir la comparación sobre la corrida completa (brazo `wiki_grafo`) y reportarla.
