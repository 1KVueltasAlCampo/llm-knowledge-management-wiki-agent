# Tasks

## 1. Preparación

- [x] 1.1 Añadir `requests`, `beautifulsoup4`, `lxml` y `pyyaml` con `uv add`. Verificación: `uv run python -c "import requests, bs4, lxml, yaml"` termina sin error.
- [x] 1.2 Crear `data/corpus_ids.txt` con los 5 identificadores (2405.14831, 2502.14802, 2605.25480, 2605.18490, 2607.04576) y un comentario con el título de cada uno. Verificación: una prueba lo lee y obtiene 5 identificadores únicos; `git check-ignore data/corpus_ids.txt` no lo ignora.
- [x] 1.3 Ajustar `specs/formato-gold.md`: ritmo de peticiones igual al `Crawl-delay` del sitio y `estado_publicacion` con `desconocido` por defecto. Verificación: el texto refleja ambos cambios y no queda la regla de "1–2 segundos".

## 2. Descarga cortés (Bronze)

- [x] 2.1 Crear `ingest/arxiv.py` con la lectura de la lista de identificadores, la consulta de `robots.txt` (`Disallow` y `Crawl-delay`) y la descarga con espera, tiempo máximo y nombre de cliente genérico. Verificación: pruebas con una sesión HTTP y un reloj falsos comprueban la espera mínima entre peticiones, el rechazo de una ruta prohibida y que el nombre de cliente no contiene correo.
- [x] 2.2 Guardar Bronze (`page.html`, `abs.html` y `capture.jsonl` con URL, fecha, estado y huella, incluidos fallos) y no volver a descargar lo existente. Verificación: pruebas comprueban los archivos creados, el registro de un 404 y que una segunda ejecución no hace peticiones.

## 3. Conversión (Silver)

- [x] 3.1 Crear `ingest/markdown.py` que convierta el HTML de LaTeXML en Markdown: título, resumen, secciones y subsecciones, párrafos, listas, tablas, ecuaciones en `$…$`, pies de figura, sin navegación ni bibliografía. Verificación: pruebas con un HTML sintético en `tests/fixtures/` comprueban cada elemento y que no quedan etiquetas HTML.
- [x] 3.2 Extraer de la bibliografía los identificadores de arXiv citados antes de eliminarla. Verificación: una prueba con una bibliografía sintética devuelve los identificadores esperados.

## 4. Metadatos y Gold

- [x] 4.1 Analizar la página de resumen (etiquetas `citation_*` y categoría principal) y la versión que aparece dentro del HTML. Verificación: pruebas con páginas sintéticas comprueban título, autores, fechas, categoría y versión.
- [x] 4.2 Crear `ingest/gold.py` que arme el encabezado YAML según `specs/formato-gold.md`, aproxime `tokens`, calcule `referencias_en_corpus` en segunda pasada y escriba el archivo Gold y `corpus.jsonl`. Verificación: pruebas comprueban los campos obligatorios, el cruce de referencias entre dos papers sintéticos y una línea de manifiesto por paper.
- [x] 4.3 Crear la validación del contrato (campos obligatorios, duplicados, cuerpo vacío, etiquetas HTML, `tokens`). Verificación: pruebas con un archivo válido y uno por cada tipo de incumplimiento, con código de error en el último caso.

## 5. Ejecución

- [x] 5.1 Crear la orden `uv run python -m wikillm.ingest` que encadene todo y escriba un resumen por paper (secciones, tablas, ecuaciones, tokens). Verificación: una prueba de punta a punta con red falsa produce Gold válido y una segunda ejecución no cambia ningún archivo.
- [x] 5.2 Ejecutar sobre los 5 papers reales (unos 3 minutos por la espera de 15 s entre las 10 peticiones). Verificación: 5 archivos Gold válidos, 5 líneas en `corpus.jsonl`, el informe de validación sin errores, y la comparación manual de las secciones de un paper con las del HTML original.

## 6. Cierre

- [x] 6.1 Ejecutar `uv run ruff check . && uv run ruff format --check . && uv run pytest`. Verificación: sin errores y con todas las pruebas en verde.
