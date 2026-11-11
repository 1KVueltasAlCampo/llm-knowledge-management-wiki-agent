## ADDED Requirements

### Requirement: Optional query layers on the wiki
La consulta del wiki SHALL poder usar, de forma opcional y apagada por defecto, un grafo de navegación (graphify) y tgrep. Sin capas, el protocolo, las herramientas y el prompt del agente SHALL ser idénticos a los del WikiLLM base. Con capas, el agente SHALL disponer de `graph` en lugar de `search`, de `read` con secciones (`slug#Encabezado`, también con los nombres `pages/<slug>.md` del grafo) y, si se indicó tgrep, de `grep`. `grep` SHALL NOT contar como lectura, SHALL devolver como máximo 3 líneas recortadas y SHALL rechazarse hasta que el agente haya leído una página. El grafo SHALL construirse a partir de los `.md` del wiki sin llamar a ningún modelo y SHALL reconstruirse cuando cambia el número de papers ingeridos.

#### Scenario: Sin capas
- **WHEN** se consulta el wiki sin indicar capas
- **THEN** el prompt del sistema es `INSTRUCCIONES_AGENTE` y la acción `search` sigue disponible

#### Scenario: Con capas
- **WHEN** se consulta el wiki con capas
- **THEN** el prompt describe `graph` y `read` por secciones, la acción `search` se rechaza como no válida y `grep` responde que se lea primero si aún no se leyó ninguna página

#### Scenario: Wiki que crece
- **WHEN** entra un paper nuevo al wiki entre dos consultas
- **THEN** la siguiente consulta al grafo lo reconstruye antes de responder

#### Scenario: Herramienta externa ausente
- **WHEN** no se puede ejecutar graphify o tgrep, o fallan al construir
- **THEN** la consulta se detiene con un `ErrorDeCapa` que dice qué herramienta falló
