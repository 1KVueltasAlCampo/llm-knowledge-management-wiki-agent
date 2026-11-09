# Proposal

## Why

Las operaciones del sistema (preguntar a los dos sistemas, ingerir un paper, explorar el wiki, ver métricas y costo) viven hoy en consolas distintas, con su salida en texto plano. La consola no distingue visualmente al RAG del WikiLLM, no muestra el recorrido del agente mientras ocurre y obliga a recordar comandos y a localizar archivos a mano.

Hace falta una interfaz local, usable como cualquier demo de un proyecto de código abierto, que ejecute las **mismas operaciones reales** y muestre en vivo lo que mostraría la consola, más lo que la consola no enseña bien: las llamadas al modelo, los pasos del agente, el costo acumulado y las citas con su fragmento, con cada sistema en su propia columna. Debe seguir siendo utilizable si falla la conexión con el proveedor.

## What Changes

- Nuevo paquete `wikillm.panel` y orden `python -m wikillm.panel`: un servidor **solo local** (127.0.0.1), sin dependencias nuevas ni recursos externos, que sirve una página única y transmite eventos al navegador por *Server-Sent Events*.
- **Secciones**: Preguntar (con preguntas de ejemplo), Ingerir (estado del corpus y siguiente paper), Wiki (índice y historial versionado), Resultados (métricas del piloto y estimación de costo) y Sistema (estado y herramientas).
- **Acciones reales**: reiniciar el wiki, verificar el entorno, comparar una pregunta en ambos sistemas, ingerir un paper, estimar el costo de la corrida, calcular métricas del piloto y validar el banco. Se ejecutan en el servidor (las que llaman al modelo, dentro del proceso, con el índice del RAG ya cargado) y su salida se transmite línea a línea.
- **Vista de comparación** con una columna por sistema (RAG en azul, WikiLLM en verde): estado en vivo, pasos del agente, fragmentos que recuperó el RAG, respuesta, citas con el texto que las respalda, y tokens, tiempo y costo.
- **Visor de archivos** con lista blanca (wiki de la demostración, evidencia, documentos, especificaciones y código clave) que renderiza Markdown, JSON y JSONL, y convierte las citas `[span_id]` y los enlaces `[[página]]` en enlaces que se abren.
- **Costo de la sesión** acumulado desde las llamadas, con un tope configurable que bloquea nuevas acciones de pago.
- **Grabación y reproducción**: cada ejecución se guarda con sus eventos y puede reproducirse sin llamar al proveedor; el panel marca la reproducción de forma inequívoca.
- Vista de **métricas del piloto** y tabla de las llamadas al modelo de cada ejecución.
- Se expone en el RAG el último resultado de recuperación (identificadores y distancias) para que `comparar` y el panel lo muestren.

## Capabilities

### New Capabilities
- `demo-panel`: panel local de demostración con ejecución en vivo, visor de archivos, grabación y reproducción.

### Modified Capabilities
- `harness`: la comparación puntual incluye los fragmentos que recuperó el RAG.
- `rag-arm`: el brazo expone su última recuperación.

## Impact

- Código nuevo en `src/wikillm/panel/` (servidor, trabajos, acciones, archivos, ejemplos y la página). Cambios pequeños en `rag/brazo.py` y `arnes/comparar.py`. Pruebas sin red ni saldo: el servidor se prueba con un servidor real en un puerto libre y acciones falsas.
- Sin dependencias nuevas.
- Gasto de saldo: una secuencia completa de demostración (dos comparaciones y una ingesta) cuesta alrededor de 0,011 USD (medido el 9-nov), y el doble en hora pico del proveedor. Cada botón de pago muestra su estimación antes de ejecutarse.
- Fuera de este cambio: conversación de varios turnos, autenticación (el servidor no sale de la máquina), edición de archivos desde el panel y acceso a cualquier archivo fuera de la lista blanca.
