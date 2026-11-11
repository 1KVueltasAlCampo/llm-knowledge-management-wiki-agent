# Proposal

## Why

El tutor pidió probar Graphify y tgrep para que el WikiLLM gaste menos tokens, y la respuesta fue
«como una combinación»: el WikiLLM sigue generando las páginas, Graphify arma el mapa para decidir
qué leer y tgrep haría la búsqueda exacta. La evaluación exploratoria
(`docs/evaluacion-tgrep-graphify.md`) vivía solo en `scripts/`, fuera del producto. Para poder
justificar su uso y repetir la comparación sobre la corrida completa hace falta que esté en el
código, **sin cambiar el WikiLLM base** que se va a medir.

## What Changes

- Módulo nuevo `src/wikillm/wiki/capas.py` con dos capas de consulta opcionales: el grafo de
  navegación (`graphify`, determinista, sin llamar al modelo) y `tgrep` como herramienta opcional.
  Ambas son programas externos que se invocan como procesos; no se añade ninguna dependencia de
  Python.
- `ConsultaWiki` acepta un parámetro `capas` (por defecto `None`). Sin él, el protocolo, las
  herramientas y el prompt son exactamente los de antes. Con él, el agente usa `graph` (y `grep`
  tras leer una página) en lugar de `search`, y `read` admite `slug#Encabezado`.
- Brazo nuevo `BrazoWikiCapas` (`wiki_grafo` o `wiki_grafo_tgrep`): consulta **el mismo wiki** del
  brazo `wiki`, no ingiere nada y no suma costo de ingesta.
- `arnes correr` recibe `--graphify <ejecutable>` y `--tgrep <ejecutable>` (y `--capas-trabajo`).
  Sin ellos, la corrida y su estimación no cambian. Con ellos se declara el brazo en
  `corrida.json` y se cuenta en la estimación.

## Capabilities

### New Capabilities

### Modified Capabilities
- `wiki-arm`: consulta opcional con capas (grafo y tgrep) sobre el mismo wiki.
- `harness`: brazo adicional que comparte el wiki del brazo `wiki`.

## Impact

- **Contratos de `specs/`:** ninguno. El brazo adicional escribe `respuestas.jsonl` con el mismo
  formato y otro valor en `system`.
- **Corridas existentes:** sin las opciones, `corrida.json` y la estimación (4,67 USD) son
  idénticos, así que una corrida empezada antes se reanuda igual.
- **Costo:** con `--graphify` la cota alta de la estimación sube (de 4,67 a 7,31 USD con las 60
  preguntas en los 11 pasos); el costo real esperado del brazo es de unos 0,4 USD (estimación
  propia), y el arnés pide `--confirmo-usd` al pasar de 5.
- **Dueño:** `src/wikillm/wiki/` es de Juan David.
- **Resultado de la evaluación previa:** el grafo mejoró preguntas que combinan varios papers y
  tgrep no redujo el costo; por eso tgrep solo está como herramienta opcional detrás de la lectura.
