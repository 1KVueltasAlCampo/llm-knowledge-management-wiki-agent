# Design

## Context

Ya existen todas las piezas: `BrazoRag` y `BrazoWiki` cumplen el contrato `Brazo`, `ResultadoBrazo` trae citas, tokens, segundos y dólares, el wiki expone `traza()` y `ingeridos`, y el arnés sabe poner los brazos en el paso N y comprobar que su estado coincide (`_comprobar_estado`). Falta una orden que las junte para **una** pregunta y presente el resultado de forma legible.

El wiki ya construido (carpeta con su Git y sus copias por paso) y el índice vectorial de los 50 papers (que el RAG filtra por los papers ingeridos) son costosos de recrear: la orden debe reutilizarlos, no reconstruirlos.

## Goals / Non-Goals

**Goals:**
- Una orden, una pregunta, los dos sistemas, el mismo modelo y el mismo estado del corpus.
- Que quien mira vea por qué una respuesta es fiable: el fragmento citado y, en el wiki, qué buscó y qué leyó el agente.
- Dejar evidencia en un archivo, sin texto de arXiv.

**Non-Goals:**
- Conversar (varios turnos) o recordar preguntas anteriores: el agente responde preguntas independientes, igual que en el experimento.
- Ingerir papers desde esta orden: la ingesta tiene su propia orden y su propia estimación de costo.
- Reemplazar la corrida del arnés ni sus archivos de resultados.

## Decisions

1. **El paso lo fija el wiki.** El wiki es el estado caro y versionado; el RAG se pone al día en segundos (los embeddings ya están y se comprueba la huella). Así no hay un `--paso` que pueda contradecir al wiki.
2. **Misma comprobación de estado que la corrida.** Se reutiliza `_comprobar_estado`: si los papers ingeridos de algún brazo no son exactamente los N primeros del manifest, se aborta antes de preguntar. Una comparación sobre estados distintos no es una comparación.
3. **Las citas se muestran con su fragmento.** Se resuelve cada `span_id` contra el Gold (con la huella) y se imprime el comienzo del fragmento. Es lo que hace visible que la cita es real y no decorativa. El texto solo se imprime en pantalla; no se guarda.
4. **La traza lleva el detalle de las acciones.** Una lista ordenada con la acción, su argumento y un resumen de lo que devolvió la herramienta (cuántas páginas, cuáles, cuáles no existían). Se añade a la traza existente sin cambiar los contadores.
5. **El archivo de evidencia es append-only** (`results/demo/comparaciones.jsonl`), una línea por comparación. Guarda identificadores de citas, no su texto. El registro de llamadas del cliente del modelo va a `results/demo/llamadas.jsonl`, que ya está ignorado por Git.
6. **Un solo constructor de brazos.** La orden `comparar` usa el mismo constructor que `correr`, ampliado para aceptar la carpeta del wiki y la del índice; si no se indican, `correr` conserva su comportamiento (carpetas por corrida).
7. **Un fallo del modelo termina la orden con código 1** y no escribe nada, como en la corrida: no se muestra ni se guarda una respuesta a medias.

## Risks / Trade-offs

- **Cada ejecución gasta saldo** (≈0,002 USD). Es poco y queda registrado; el tope por ejecución sigue vigente.
- **La respuesta del modelo no es determinista** aunque la temperatura sea 0: dos ejecuciones pueden diferir. Es una limitación del proveedor; el archivo de evidencia guarda lo que pasó en cada una.
- **El fragmento citado puede ser largo** (tablas). Se recorta al imprimir.
