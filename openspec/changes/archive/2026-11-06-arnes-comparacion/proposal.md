# Proposal

## Why

Los dos brazos ya existen y cumplen el mismo contrato (`ingerir` y `responder`), y el módulo `eval` ya sabe calcular métricas sobre `results/<corrida>/respuestas.jsonl`. Falta lo que los une: el programa que **ingiere los papers de uno en uno, hace las preguntas del banco en cada paso de evaluación a los dos brazos y guarda los resultados** en el formato del contrato. Sin él no hay experimento, y todo lo que mide la tesis (correctitud, abstención, obsolescencia, costo y contexto por paso) sale de sus archivos.

Lo que hace difícil este programa no es el bucle, sino que sea **justo, reanudable y honesto con el gasto**:

- Los dos brazos deben correr en las mismas condiciones (mismo modelo, mismas preguntas, mismo orden de papers, mismo momento del día) para que la única variable sea la arquitectura (regla 1).
- Una corrida de 11 pasos × 2 brazos × decenas de preguntas dura horas y llama a una API de pago: si se corta a la mitad no puede repetirse desde cero ni dejar líneas duplicadas.
- El informe solo puede citar cifras de corridas guardadas (regla 9) y de preguntas que los dos autores verificaron (regla 11): la corrida debe dejar escrito con qué se hizo y si vale para el informe.

## What Changes

- Orden de consola `python -m wikillm.arnes correr`, que para cada paso de evaluación: ingiere los papers pendientes en `orden_ingesta` en los dos brazos y, a continuación, hace cada pregunta del banco a cada brazo, alternando los brazos pregunta a pregunta.
- **Tres archivos de resultados por corrida** en `results/<corrida>/`: `respuestas.jsonl` (el contrato de Juan Diego, una línea por pregunta, sistema y paso), `ingestas.jsonl` (el costo de ingerir cada paper, propuesto en el contrato de brazos) y `trazas.jsonl` (qué hizo el agente del wiki en cada pregunta: acciones, búsquedas, páginas leídas, incidencias). Además `corrida.json` con todo lo necesario para reproducirla.
- **Puerta de costo:** antes de gastar se imprime la estimación (ingesta, preguntas y hora pico); si supera 5 USD no corre sin `--confirmo-usd`. `--estimar` solo imprime. Un único `ClienteModelo` compartido aplica el tope `MAX_USD_PER_RUN` al total.
- **Reanudable:** si la corrida se corta, volver a lanzarla con el mismo `--corrida` continúa donde quedó, sin repetir llamadas ni duplicar líneas.
- **Estado de verificación:** solo se preguntan las preguntas con el estado mínimo pedido (por defecto `acordado`, el que exige la regla 11), y `corrida.json` indica si la corrida **vale para el informe**.
- Cada corrida usa su propia carpeta del wiki y su propio índice vectorial, para que ninguna corrida herede estado de otra.
- `BrazoWiki` expone `traza()` con lo que hizo el agente en la última pregunta.

## Capabilities

### New Capabilities
- `harness`: el arnés que ejecuta los dos brazos sobre el banco por pasos de ingesta y guarda resultados reproducibles, reanudables y con el gasto controlado.

### Modified Capabilities
- `wiki-arm`: el brazo expone la traza de la última pregunta.

## Impact

- Código nuevo en `src/wikillm/arnes/` (bucle, registro, estimación, orden de consola) y un método en `src/wikillm/wiki/brazo.py`. Pruebas con brazos y cliente de modelo falsos: ninguna llama a la API.
- No cambia `specs/contrato-resultados.md`: el arnés escribe el formato tal cual. `ingestas.jsonl` y `trazas.jsonl` son archivos aparte que el contrato no prohíbe.
- Ni las métricas ni el juez se tocan: se siguen ejecutando con `python -m wikillm.eval metricas --respuestas results/<corrida>/respuestas.jsonl`.
- Gasto de saldo, con aviso previo y estimación: la verificación real es un piloto de pocas preguntas y 2 pasos (unos 0,05–0,2 USD). La corrida completa (50 papers, 11 pasos, ≈60 preguntas, dos brazos) se estima en 1–4 USD y **no forma parte de este cambio**: se lanza cuando las preguntas estén acordadas.
- **Decisión que sigue pendiente entre los dos autores**: qué pasos se evalúan (el contrato §4 propone cada 5 ingestas: 0, 5, …, 50). El arnés recibe los pasos por argumento, así que no la bloquea.
- Fuera de este cambio: el juez, las métricas, la elección de preguntas y las ablaciones del wiki.
