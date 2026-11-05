# corpus-gold Specification

## Purpose
Define cómo se construye el corpus en capas Bronze, Silver y Gold a partir de identificadores de arXiv, de forma reproducible y respetuosa con el sitio, cumpliendo el contrato de `specs/formato-gold.md`.

## Requirements

### Requirement: Identifier list input
El sistema SHALL tomar los papers de un archivo de texto con un identificador de arXiv por línea, ignorando líneas vacías y comentarios que empiecen con `#`.

#### Scenario: Lista con comentarios
- **WHEN** el archivo contiene identificadores, líneas vacías y comentarios
- **THEN** solo se procesan los identificadores, sin duplicados

### Requirement: Polite download
El sistema SHALL consultar `robots.txt` antes de descargar, SHALL NOT descargar rutas con `Disallow`, SHALL esperar al menos el `Crawl-delay` declarado (15 segundos por omisión si no se puede leer) entre peticiones al mismo sitio, SHALL usar un tiempo de espera máximo por petición y SHALL identificarse con un nombre de cliente que no incluya datos personales.

#### Scenario: Espera entre peticiones
- **WHEN** se descargan dos papers seguidos
- **THEN** transcurre al menos el `Crawl-delay` entre las dos peticiones

#### Scenario: Ruta prohibida
- **WHEN** `robots.txt` prohíbe la ruta de un documento
- **THEN** el documento no se descarga y se registra el motivo

### Requirement: Bronze layer
El sistema SHALL guardar el HTML tal como se recibió en `data/raw/<arxiv_id>/page.html`, y la página de resumen en `abs.html`, y añadir una línea a `capture.jsonl` con URL, fecha, estado HTTP y huella del contenido, incluidos los fallos. Los archivos Bronze SHALL NOT modificarse después de escritos.

#### Scenario: Descarga correcta
- **WHEN** se descarga un paper
- **THEN** existe `page.html` y una línea de captura con estado 200 y la huella

#### Scenario: Descarga fallida
- **WHEN** el servidor responde 404
- **THEN** se registra la línea de captura con ese estado y el paper no continúa a Silver

### Requirement: Silver layer
El sistema SHALL convertir el HTML a Markdown limpio en `data/processed/<arxiv_id>.md`: título como `#`, resumen, secciones y subsecciones como `##` y `###`, párrafos, listas, tablas como tablas de Markdown, ecuaciones como LaTeX entre `$…$` y pies de figura conservados. SHALL eliminar navegación, pie de página y bibliografía, y SHALL NOT dejar etiquetas HTML en el resultado.

#### Scenario: Estructura conservada
- **WHEN** un paper tiene secciones, tablas y ecuaciones
- **THEN** el Markdown conserva los encabezados en el mismo orden, las tablas como tablas y las ecuaciones entre `$`

#### Scenario: Sin ruido
- **WHEN** se convierte el HTML
- **THEN** el resultado no contiene menús, bibliografía ni etiquetas HTML

### Requirement: Gold layer
El sistema SHALL escribir `data/gold/<arxiv_id>.md` con el encabezado YAML definido en `specs/formato-gold.md` seguido del cuerpo de Silver, con los metadatos bibliográficos tomados de la página de resumen del paper en arXiv. El campo `estado_publicacion` SHALL ser `desconocido` mientras no se indique otro valor, porque arXiv no lo informa de forma fiable. El campo `tokens` SHALL ser una aproximación declarada como tal en la documentación.

#### Scenario: Encabezado completo
- **WHEN** se genera un archivo Gold
- **THEN** contiene todos los campos obligatorios, con `fecha_publicacion` de la primera versión y `version` la capturada

#### Scenario: Referencias dentro del corpus
- **WHEN** la bibliografía de un paper cita a otro paper del corpus
- **THEN** `referencias_en_corpus` incluye el identificador de este último

### Requirement: Manifest
El sistema SHALL generar `data/gold/corpus.jsonl` con una línea por paper, con los mismos campos del encabezado más la ruta del archivo.

#### Scenario: Una línea por paper
- **WHEN** termina la construcción de 5 papers
- **THEN** el manifiesto tiene 5 líneas, una por identificador

### Requirement: Idempotence
Ejecutar el proceso otra vez con la misma lista SHALL NOT volver a descargar páginas ya presentes en Bronze y SHALL producir archivos idénticos, salvo que se pida refrescar de forma explícita.

#### Scenario: Segunda ejecución
- **WHEN** se ejecuta de nuevo sin pedir refresco
- **THEN** no se hacen peticiones de páginas y los archivos Silver y Gold no cambian

### Requirement: Validation report
El sistema SHALL validar cada archivo Gold y reportar los que incumplan el contrato: campos obligatorios ausentes, identificadores repetidos, cuerpo vacío, etiquetas HTML residuales o `tokens` que no corresponda al cuerpo.

#### Scenario: Archivo inválido
- **WHEN** un archivo Gold no tiene el campo `sources`
- **THEN** el informe lo señala con el motivo y el proceso termina con código de error
