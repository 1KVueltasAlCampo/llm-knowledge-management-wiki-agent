## ADDED Requirements

### Requirement: Verified metadata
El sistema SHALL tomar título, autores, fechas, versión, categoría, `journal_ref` y DOI de la API de arXiv, nunca del `.bib` ni de memoria.

#### Scenario: Identificador del .bib
- **WHEN** se reúnen candidatos a partir de `referencias.bib`
- **THEN** cada candidato tiene los metadatos devueltos por la API y su origen (`bib` o `busqueda:<consulta>`)

### Requirement: Ingest order and author half
El manifest SHALL ordenar los papers por `fecha_publicacion` (empate por `arxiv_id`) y asignar `mitad` A a las posiciones impares y B a las pares.

#### Scenario: Prefijo de 30
- **WHEN** se toman las primeras 30 ingestas
- **THEN** cada autor tiene 15 papers de ese prefijo

### Requirement: HTML availability
El manifest SHALL registrar `html_available` según la última captura HTML de Bronze; un paper sin HTML no entra al corpus y se reemplaza por el siguiente candidato.

#### Scenario: Paper sin HTML
- **WHEN** la última captura HTML de un paper tiene estado distinto de 200
- **THEN** `html_available` es `false` y la orden `manifest` termina con código de error

### Requirement: Citable spans without text
El sistema SHALL calcular para cada bloque del cuerpo Gold un `span_id`, su sección, tipo, posición `[inicio, fin)` y la huella SHA-256 de su texto, sin guardar el texto.

#### Scenario: Cita que cambió
- **WHEN** se resuelve un `span_id` contra un Gold cuyo texto cambió
- **THEN** la resolución falla por huella distinta
