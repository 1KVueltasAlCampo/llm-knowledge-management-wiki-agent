# Design

## Context

Observado el 4 de noviembre de 2026 sobre los 5 papers elegidos:

- Las cinco páginas de `arxiv.org/html/<id>` abren y comparten la misma estructura (LaTeXML):
  `article.ltx_document`, títulos de sección `h2.ltx_title_section`, resumen `.ltx_abstract`,
  tablas `table.ltx_tabular` (de 6 a 59 por paper), ecuaciones `<math alttext="…">` (de 42 a
  865), figuras con `figcaption`, notas `.ltx_note` y bibliografía en `section.ltx_bibliography`.
- `robots.txt` de arXiv permite `/abs`, `/html` y `/pdf`, prohíbe `/api` y declara
  **`Crawl-delay: 15`**. El de `export.arxiv.org` (donde vive la API) es `Disallow: /`; la API
  se rige por sus propios términos de uso (una petición cada 3 s y una sola conexión).
- La página de resumen `arxiv.org/abs/<id>` trae los metadatos en etiquetas `citation_title`,
  `citation_author`, `citation_date` (primera versión), `citation_online_date` (versión más
  reciente) y `citation_arxiv_id`, más la categoría principal. La URL de `/html/<id>` no se
  redirige a una con versión; la versión aparece dentro del HTML, en los enlaces al propio
  identificador (por ejemplo `2605.18490v3`).
- El contrato del Gold ya está en `specs/formato-gold.md`. Juan Diego construirá el scraper
  completo; este módulo es un sustituto temporal con el mismo resultado.

## Goals / Non-Goals

**Goals:**
- Producir 5 archivos Gold válidos que sirvan para construir RAG, wiki y arnés.
- Que el proceso sea reproducible, idempotente y respetuoso con arXiv.
- Poder probar toda la lógica sin red ni texto real de papers.

**Non-Goals:**
- No se implementa el plan B de PDF: un paper sin HTML se registra como fallo.
- No se calcula `estado_publicacion` ni se resuelven referencias fuera del corpus.
- No se optimiza para 50 papers ni se paraleliza (la espera de 15 s lo impide por diseño).

## Decisions

**1. Conversor propio sobre la estructura de LaTeXML, con `beautifulsoup4` y `lxml`.**
Es el stack que recomendó el tutor y la estructura es predecible. Alternativas descartadas:
`markdownify` y `trafilatura` (tratan mal las ecuaciones, que aquí deben salir como `$alttext$`)
y Scrapling (innecesario para HTML ya semántico).

**2. Metadatos de la página `/abs`, cuerpo del HTML.**
Las etiquetas `citation_*` de la página de resumen dan título, autores y fechas de forma estable,
y la versión sale de los enlaces al propio identificador dentro del HTML (la mayor). Se evita la API porque el `robots.txt` de su host
prohíbe todo y su uso se rige por otros términos; así todo lo que se descarga es `/abs` y
`/html`, rutas permitidas con el mismo `Crawl-delay`. La página de resumen se guarda en Bronze
junto al HTML para regenerar el Gold sin volver a pedirla.

**3. Ritmo de peticiones tomado de `robots.txt`.**
Se lee con `urllib.robotparser` y se respeta `Crawl-delay` y `Disallow`. Si no se puede leer, se
usan 15 s. El reloj y la espera se inyectan para probarlo sin esperar. Esto corrige la regla de
"1–2 segundos" que el curso da para sitios genéricos.

**4. Identificación del cliente genérica.**
`wikillm-tesis-icesi/0.1 (proyecto academico)`, sin correo ni nombres.

**5. Idempotencia por existencia de Bronze.**
Si `page.html` existe, no se descarga. Un parámetro de refresco fuerza la descarga y compara la
huella. Silver y Gold se regeneran siempre desde Bronze, de forma determinista.

**6. `tokens` aproximado como caracteres entre 4, y `referencias_en_corpus` en segunda pasada.**
Es una estimación declarada, suficiente para comparar tamaños. La bibliografía se analiza antes
de eliminarla del cuerpo, buscando identificadores de arXiv en sus enlaces y textos, y se cruza
con la lista del corpus cuando todos están procesados.

**7. YAML con `pyyaml` y ejemplos sintéticos en las pruebas.**
Las pruebas usan un HTML en miniatura escrito a mano que imita LaTeXML, así no se versiona
texto de papers.

## Risks / Trade-offs

- [Tablas con celdas combinadas o anidadas salen imperfectas] → Se aplanan las celdas y el
  informe cuenta tablas y ecuaciones por paper para detectar pérdidas; revisión manual de uno de
  los cinco.
- [Ecuaciones muy largas inflan el texto] → Se conserva el LaTeX original; se mide en tokens y
  se decide después si recortar.
- [La estructura de LaTeXML cambia] → Las pruebas fijan lo esperado y el informe de validación
  avisa si un paper no tiene secciones.
- [Cinco papers tardan unos 2 minutos por la espera] → Es el costo de respetar el sitio.
- [El corpus completo de Juan Diego usará otro conversor] → Lo único compartido es el contrato
  del Gold; las pruebas de validación sirven para comprobar también su salida.
