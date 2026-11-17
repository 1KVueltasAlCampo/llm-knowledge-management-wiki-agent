# Proposal

## Why

Construir el wiki de 100 papers cuesta unos 3 USD. Las siguientes corridas (capas con grafo y con tgrep) solo
cambian cómo se consulta, así que deben poder reutilizar el conocimiento ya construido en cada paso. El wiki
guarda ya una copia `paso-N` por cada paper ingerido, pero el arnés no sabía usarlas. Ver decisión 0009.

## What Changes

- `Wiki.clonar_desde`, `Wiki.situar_en_paso`, `Wiki.ingeridos_en_paso` y `validar_prestamo` en `wiki/almacen.py`.
- `BrazoWikiPrestado` en `wiki/brazo.py`: el brazo `wiki` sin ingesta, sobre una copia del wiki construido.
- `arnes correr --wiki-de <corrida|carpeta>`: valida que el wiki tenga las copias y el mismo orden, no cuenta
  ingesta en la estimación y declara `reutiliza_wiki_de` en `corrida.json`.

## Impact

- No cambia ningún formato de resultados. El wiki original solo se lee; la corrida trabaja sobre su copia.
- Dueño del código: `src/wikillm/wiki/` (Juan David). Aviso en el PR.
