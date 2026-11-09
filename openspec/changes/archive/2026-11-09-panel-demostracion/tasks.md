# Tasks

## 1. Base del RAG y de la comparación

- [x] 1.1 Exponer `ultimos_recuperados` en `BrazoRag` y mostrarlos en `comparar` (salida y línea de evidencia, solo identificadores y distancias). Verificación: pruebas del brazo (antes de preguntar, después, reemplazo) y de la comparación (se listan con la marca de citado; el sistema sin recuperación no los muestra; la evidencia no lleva texto).

## 2. Servidor del panel

- [x] 2.1 Crear `panel/archivos.py` con la lista blanca y la lectura segura. Verificación: archivo permitido, `..`, ruta absoluta, `.env`, archivo fuera de la lista, archivo grande truncado y tipos por extensión.
- [x] 2.2 Crear `panel/trabajos.py`: un trabajo a la vez en un hilo, eventos con orden y tiempo, grabación y reproducción. Verificación: orden de eventos, rechazo de un segundo trabajo, error de la acción con código 1, grabación escrita, reproducción marcada y sin ejecutar la acción, y ausencia de grabación.
- [x] 2.3 Crear `panel/observado.py` (cliente del modelo observado). Verificación con un cliente HTTP falso: eventos antes y después de cada llamada, y la respuesta intacta.
- [x] 2.4 Crear `panel/acciones.py` con el catálogo, la validación de parámetros, las acciones en proceso y las de subproceso, los resultados estructurados y el costo de la sesión. Verificación: parámetros inválidos, confinamiento del wiki, confirmación, tope de gasto, línea de comparación y entrada de ingesta convertidas en resultados.
- [x] 2.5 Crear `panel/ejemplos.py` y la lectura del estado del corpus (`datos.corpus`). Verificación: ejemplos con pregunta y nota válidas; siguiente paper según lo ingerido.
- [x] 2.6 Crear `panel/servidor.py` y `panel/__main__.py`. Verificación con un servidor real en un puerto libre: página, Host ajeno, archivo permitido y rechazado, ejecución con flujo SSE, 409, 400, estado y métricas.

## 3. Página

- [x] 3.1 Escribir `panel/static/index.html`: navegación por secciones, columnas RAG y WikiLLM, línea de tiempo del agente, consola y llamadas, visor de archivos, costo, ejecuciones guardadas y reproducción. Verificación: sintaxis del JavaScript con Node y revisión en el navegador integrado en cada sección.

## 4. Uso

- [x] 4.1 Con aviso previo del costo (≈0,011 USD por secuencia completa), ejecutar la secuencia desde el panel para grabarla y comprobar el recorrido. Verificación: las grabaciones existen para las acciones de pago y la reproducción las repite sin llamar al modelo.
- [x] 4.2 Documentar el panel en `docs/demo.md` y en el README. Verificación: los comandos y rutas citados existen.

## 5. Cierre

- [x] 5.1 Ejecutar `uv run ruff check . && uv run ruff format --check . && uv run pytest` y `openspec validate panel-demostracion`. Verificación: todo termina sin errores.
