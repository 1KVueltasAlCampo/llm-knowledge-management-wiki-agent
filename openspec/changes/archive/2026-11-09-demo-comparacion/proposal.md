# Proposal

## Why

El arnés ejecuta corridas completas sobre el banco de preguntas, pero no hay forma de **hacer una sola pregunta a los dos sistemas y ver juntos lo que cada uno hace**: la respuesta, las citas con el fragmento que las respalda, los pasos del agente del wiki, y el costo y el tiempo. Hoy hay que lanzar el RAG y el wiki por separado, en dos consolas, y las respuestas salen sin la traza del agente.

Ese comando sirve para tres cosas: inspeccionar un caso concreto antes o después de una corrida (por qué un sistema acertó y el otro no), depurar el agente, y **demostrar el sistema funcionando de punta a punta** con la evidencia que produce.

## What Changes

- Orden de consola `python -m wikillm.arnes comparar "<pregunta>"`: hace la misma pregunta al RAG y al wiki, con el mismo modelo, sobre el mismo estado del corpus, y muestra por cada sistema la respuesta, las citas con el fragmento literal que las respalda, los pasos del agente (solo el wiki), los tokens, el tiempo y el costo, y al final una tabla comparativa.
- **El paso de ingesta lo fija el wiki.** El comando lee cuántos papers tiene ingeridos el wiki indicado y pone el RAG en el mismo estado; si el wiki no sigue el orden del manifest, aborta con un mensaje.
- Cada comparación se añade a `results/demo/comparaciones.jsonl` (pregunta, paso, y por sistema: respuesta, citas, abstención, costo y traza), sin texto de arXiv.
- La traza del agente del wiki guarda ahora el **detalle ordenado de sus acciones** (búsqueda con su consulta, lectura con sus páginas, respuesta), además de los contadores.
- La construcción de los dos brazos reales pasa a aceptar las carpetas del wiki y del índice, para reutilizar el wiki y el índice ya construidos.

## Capabilities

### New Capabilities

### Modified Capabilities
- `harness`: el arnés ofrece la comparación puntual de una pregunta.
- `wiki-arm`: la traza incluye el detalle ordenado de las acciones del agente.

## Impact

- Código en `src/wikillm/arnes/` (módulo `comparar` y la orden de consola) y en `src/wikillm/wiki/consulta.py` y `brazo.py` (detalle de la traza). Pruebas con brazos falsos: ninguna llama a la API.
- El detalle de la traza se añade a las líneas de `trazas.jsonl` de las corridas; los campos existentes no cambian.
- Gasto de saldo: una comparación cuesta del orden de 0,002 USD (una consulta del RAG y otra del wiki). El tope `MAX_USD_PER_RUN` aplica igual.
- Fuera de este cambio: conversación de varios turnos, ingesta desde este comando y cualquier cambio en el banco o en las métricas.
