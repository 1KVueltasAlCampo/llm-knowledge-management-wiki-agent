# Tasks

## 1. Traza con detalle

- [x] 1.1 Añadir `detalle` a `Traza` en `wiki/consulta.py` (acción, argumento y resumen del resultado por cada búsqueda, lectura y respuesta) y exponerlo en `BrazoWiki.traza()`. Verificación: pruebas de una consulta con búsqueda, lectura y respuesta; de una página inexistente; y de que el detalle se reinicia. Las pruebas existentes de la traza se ajustan al campo nuevo.

## 2. Comparación

- [x] 2.1 Crear `arnes/comparar.py`: ingerir hasta el paso en todos los brazos, comprobar el estado, preguntar a cada brazo, formatear la salida con las citas resueltas contra el Gold y registrar la línea de evidencia. Verificación con brazos falsos: misma pregunta a los dos, estado fuera de orden aborta sin preguntar, cita con su fragmento, abstención sin citas, traza con pasos, tabla final y línea de evidencia sin texto de arXiv.
- [x] 2.2 Añadir la orden `comparar` a `arnes/__main__.py` y ampliar `_crear_brazos_reales` para aceptar la carpeta del wiki y la del índice. Verificación con fábricas falsas: código 0 con salida y archivo, paso tomado del wiki, wiki vacío en el paso 0, wiki fuera de orden con código 1, fallo del modelo con código 1 y sin línea de evidencia, y que `correr` no cambia.

## 3. Uso

- [x] 3.1 Documentar la demostración (`docs/demo.md`) y añadir su sección al README. Verificación: los comandos del documento existen y las rutas que cita están en el repositorio.
- [x] 3.2 Con aviso previo del costo (≈0,002 USD por comparación), ejecutar `comparar` sobre el wiki de desarrollo con tres preguntas (un dato puntual, una actualización y una que debe abstenerse) y guardar la evidencia. Verificación: las citas muestran su fragmento, la traza lista los pasos del agente y el archivo de evidencia tiene una línea por pregunta.

## 4. Cierre

- [x] 4.1 Ejecutar `uv run ruff check . && uv run ruff format --check . && uv run pytest` y `openspec validate demo-comparacion`. Verificación: todo termina sin errores.
