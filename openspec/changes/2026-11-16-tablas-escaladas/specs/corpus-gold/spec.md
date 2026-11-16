## MODIFIED Requirements

### Requirement: Silver layer
El sistema SHALL convertir el HTML a Markdown limpio en `data/processed/<arxiv_id>.md`: título como `#`, resumen, secciones y subsecciones como `##` y `###`, párrafos, listas, tablas como tablas de Markdown, ecuaciones como LaTeX entre `$…$` y pies de figura conservados. SHALL convertir una tabla de LaTeXML tanto si usa `<table class="ltx_tabular">` como si, por estar escalada, usa `<span class="ltx_tabular">`. SHALL eliminar navegación, pie de página y bibliografía, y SHALL NOT dejar etiquetas HTML en el resultado.

#### Scenario: Tabla escalada
- **WHEN** una tabla está dibujada con `span.ltx_tabular`, `span.ltx_tr` y `span.ltx_td`
- **THEN** el Markdown la contiene como tabla con sus filas y celdas y `tablas` la cuenta
