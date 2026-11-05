# Proposal

## Why

Los dos brazos (RAG y wiki) y el arnés de comparación necesitan texto real en el formato del
Gold para poder construirse y probarse, y el corpus completo de 50 papers llegará después, de
parte de Juan Diego. Con un mini-corpus de 5 papers que ya cumpla el contrato
(`specs/formato-gold.md`) se puede avanzar sin esperar, y además se valida que el formato es
realista.

## What Changes

- Se añade un proceso que, dado un archivo con identificadores de arXiv, descarga el HTML de cada
  paper (capa Bronze), lo convierte en Markdown limpio (capa Silver) y escribe el archivo Gold con
  el encabezado de metadatos y el manifiesto `corpus.jsonl`.
- La descarga respeta `robots.txt`, incluido el `Crawl-delay` (15 segundos en arXiv), y se
  identifica con un nombre de cliente genérico.
- Es idempotente: volver a ejecutarlo no vuelve a descargar ni cambia los archivos.
- Se valida el resultado y se informa de cualquier archivo que incumpla el contrato.
- Se crea `data/corpus_ids.txt` con los 5 papers elegidos.
- Se ajusta `specs/formato-gold.md`: el ritmo de peticiones es el `Crawl-delay` del sitio, no
  1–2 segundos, y `estado_publicacion` pasa a tener `desconocido` como valor por defecto.

## Capabilities

### New Capabilities
- `corpus-gold`: construcción reproducible y respetuosa del corpus en capas Bronze, Silver y
  Gold a partir de identificadores de arXiv, conforme al contrato del Gold.

### Modified Capabilities

## Impact

- Código nuevo en `src/wikillm/ingest/` y pruebas con ejemplos sintéticos (sin texto real de
  papers).
- Dependencias nuevas: `requests`, `beautifulsoup4`, `lxml` y `pyyaml`.
- Archivos nuevos: `data/corpus_ids.txt` (versionado) y, en local e ignorados por Git,
  `data/raw/`, `data/processed/` y `data/gold/` (solo `corpus.jsonl` se versiona).
- Hace 10 peticiones a arXiv (5 páginas HTML y 5 páginas de resumen con los metadatos),
  separadas por el `Crawl-delay` de 15 segundos: unos 3 minutos en total.
- Este módulo es un sustituto temporal del scraper completo de Juan Diego: el contrato que
  comparten es el formato Gold.
