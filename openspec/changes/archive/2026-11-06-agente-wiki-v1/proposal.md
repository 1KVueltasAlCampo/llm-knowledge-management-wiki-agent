# Proposal

## Why

El experimento compara un RAG simple con un wiki mantenido por un LLM, y el RAG ya cumple el contrato de los brazos (`ingerir` y `responder`). Falta el otro brazo, que es el que tiene más decisiones abiertas. Para tomarlas se leyó el corpus (ver `design.md`), y la lectura apunta a un diseño con dos mitades distintas:

- **La consulta debe ser un agente.** En LLM-Wiki, la ablación que quita el recorrido progresivo (una sola búsqueda y leer una vez) pierde de 11,7 a 13,8 puntos de F1, más que quitar la estructura del wiki o el *Error Book*. ReFind, APDMem y el estudio de progressive disclosure de Cochran coinciden en que lo que aporta es que el agente controle cuánto y qué lee.
- **La ingesta debe ser un proceso controlado, no un agente libre.** Los wikis que funcionan seleccionan las páginas afectadas, generan las actualizaciones y las validan con reglas deterministas; y el estudio de memoria en sistema de archivos encuentra que la organización hecha por agentes libres se erosiona.

El costo es el riesgo principal: el wiki agéntico de Cochran gasta unas 21 veces más tokens por consulta. Por eso la consulta tiene un tope de acciones, una búsqueda que devuelve resúmenes de una línea y el costo se mide en cada respuesta.

## What Changes

- Se añade el brazo `BrazoWiki` (`nombre = "wiki"`), que cumple el contrato `Brazo` con el mismo modelo que el RAG (`deepseek-flash`).
- **El wiki vive en disco:** `index.md`, `log.md` y páginas en `pages/`. Cada paper ingerido tiene su página (para no perder hechos) y hay páginas de concepto que integran lo que dicen varios papers, donde viven las actualizaciones y las contradicciones. Cada página lleva un resumen de una línea.
- **Ingesta en dos pasos controlados** por paper: un plan (qué páginas actualizar o crear) y la escritura. El paper se lee con cada fragmento rotulado con su `span_id`. El código descarta las citas que no resuelven a un fragmento real de un paper ya ingerido y desenlaza los enlaces `[[página]]` que no tienen destino, y cuenta ambas cosas. El índice y el registro los escribe el código, y cada ingesta deja una copia versionada (commit y etiqueta `paso-N`).
- **Consulta como agente con dos herramientas**, como en LLM-Wiki: `wiki_search(consulta)`, que devuelve resúmenes de página, y `wiki_read(páginas)`, que devuelve páginas completas con sus enlaces. El agente decide cuántas acciones usa, con un tope, y responde con el mismo prompt que el RAG: en inglés, el contexto como datos, citas por `span_id` y la misma frase de abstención.
- Se factorizan a `common/` las reglas de respuesta y la extracción de citas, para que los dos brazos las compartan (regla 1: una sola variable).
- Orden de consola `python -m wikillm.wiki` con `ingerir` y `preguntar`.

## Capabilities

### New Capabilities
- `wiki-arm`: wiki mantenido por un LLM con ingesta controlada, procedencia por fragmento y consulta agéntica con herramientas, que cumple el contrato `Brazo`.

### Modified Capabilities

## Impact

- Código nuevo en `src/wikillm/wiki/` y en `src/wikillm/common/`, con pruebas que usan un cliente de modelo falso. El RAG solo cambia de dónde importa las reglas de respuesta y las citas.
- `.gitignore` ignora `data/wiki/`: son textos derivados de arXiv, y llevan su propio repositorio de copias.
- Contratos: cumple `specs/interfaz-responder.md` y `specs/contrato-resultados.md` sin cambiarlos.
- Gasto de saldo, siempre con aviso previo y estimación: la verificación real ingiere los 5 primeros papers y hace tres preguntas, unos 0,05 a 0,15 USD. Construir los 50 papers costaría del orden de 0,5 a 1 USD, y cada pregunta de 0,003 a 0,02 USD según cuántas acciones use el agente (por medir).
- Para el informe: el wiki tiene un presupuesto de consulta mayor que el RAG de una sola ronda. Es una diferencia de arquitectura que el experimento mide (tokens, costo y latencia por respuesta), y debe decirse.
- Quedan fuera la revisión automática (*lint*), la aprobación humana, las ablaciones y Obsidian. La variante de navegación fija (sin recorrido) es una ablación barata para un cambio posterior.
