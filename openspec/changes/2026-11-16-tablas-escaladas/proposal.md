# Proposal

## Why

LaTeXML dibuja una tabla escalada con `\resizebox` como `<span class="ltx_tabular">` y no como
`<table class="ltx_tabular">`. El conversor Silver solo buscaba `table.ltx_tabular`, así que esas
tablas desaparecían del Gold sin avisar. Al reconvertir el Bronze guardado y el de la ampliación se
perdían 13 tablas en cuatro papers: Hindsight (2512.12818, sus 4 tablas), BEAM (2510.27246, 7),
GAM (2511.18423, 2) y una tabla de ablación de 2608.12888. Hindsight sale con 0 tablas.

## What Changes

- `src/wikillm/ingest/markdown.py` reconoce filas y celdas de LaTeXML tanto en `<table>` como en `<span>`
  (`ltx_tr`, `ltx_td`, `ltx_th`, `ltx_colspan_N`).
- Una prueba con una tabla escalada.
- El Gold del corpus de 100 papers se construye con el conversor corregido (`data/corpus100/`).
  El Gold de 50 y la corrida `oficial-1` no se tocan.

## Impact

- Cambia el texto (y la huella) de los cuatro papers; los otros 96 no cambian de byte.
- Las preguntas con evidencia en esos papers se reanclan con `ampliar-banco` o por huella.
- Dueño del código: `src/wikillm/ingest/` (Juan David, Juan Diego). Aviso en el PR.
