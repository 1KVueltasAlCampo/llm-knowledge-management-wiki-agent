# Design

## Context

Las operaciones de la demostración ya existen como órdenes de consola (`arnes comparar`, `arnes correr --estimar`, `wiki ingerir`, `eval metricas`, `eval validar-banco`, scripts de verificación) y sus funciones `principal` aceptan inyectar la salida (`salida`), el cliente del modelo (`crear_modelo`) y el constructor de brazos (`crear_brazos`). Eso permite ejecutarlas dentro de otro proceso sin cambiar su comportamiento y capturar exactamente lo que imprimirían.

**Formato de la interfaz (búsqueda del 9-nov-2026, fuentes secundarias).** Chainlit es el favorito para mostrar pasos y llamadas a herramientas de un agente, pero encaja peor con paneles múltiples; Streamlit y Gradio tienen más dificultad para actualizar pasos intermedios mientras algo corre; y para transmitir del servidor al navegador, SSE es el estándar (un solo sentido, sobre HTTP, con reconexión automática en `EventSource`). Los paneles de observabilidad (Langfuse, Phoenix) coinciden en dos vistas: una línea de tiempo por pasos y una transcripción de lo que dijo y pidió el agente.

## Goals / Non-Goals

**Goals:**
- Que todas las operaciones del sistema se puedan usar desde una sola interfaz, sin recordar comandos ni cambiar de ventana.
- Mostrar en vivo lo que haría la consola y lo que la consola no enseña bien (pasos del agente, llamadas, costo, citas con su fragmento).
- Distinguir sin ambigüedad al RAG del WikiLLM.
- Funcionar sin internet para todo lo que no es la llamada al modelo, y seguir siendo presentable si esa llamada falla.

**Non-Goals:**
- Un producto de usuario final, autenticación o varios usuarios: es una herramienta local de una persona.
- Editar archivos, ejecutar comandos arbitrarios o servir rutas fuera de la lista blanca.
- Sustituir la consola ni el arnés: la corrida completa sigue siendo `arnes correr`.

## Decisions

1. **Servidor con la biblioteca estándar y una página única.** `ThreadingHTTPServer` + SSE + HTML/CSS/JS sin dependencias ni CDN. Evita instalar un framework de interfaz con su propio modelo de sesión y garantiza que cargue sin red; el control total del diseño permite las dos columnas por sistema. Alternativas descartadas: Chainlit (formato de chat, difícil de dividir en dos columnas), Streamlit y Gradio (actualización de pasos intermedios y reejecución de la página).
2. **Un solo trabajo a la vez, en un único hilo.** Los clientes de Chroma y del modelo de embeddings se crean y se usan en ese hilo, y dos operaciones no pueden pisarse el estado (el wiki cambia al ingerir). Un nuevo pedido con otro trabajo en curso se rechaza con un mensaje.
3. **Las operaciones corren dentro del proceso.** Se llama a las funciones `principal` de las órdenes con `salida` capturada, así el texto de la consola es idéntico al de la orden. El RAG tarda unos segundos en cargar el modelo de embeddings; un primer trabajo de calentamiento lo hace al arrancar y el constructor de brazos reutiliza ese índice. Las órdenes que no usan modelo ni GPU (métricas, validación, Git, verificación) corren como subprocesos y se transmiten línea a línea.
4. **Cliente del modelo observado.** Un subtipo de `ClienteModelo` emite un evento antes y otro después de cada llamada (etiqueta, tokens, segundos, dólares y el texto devuelto). Así los pasos del agente (la acción JSON que devuelve en cada turno) y el costo aparecen en vivo sin tocar el cliente real ni leer archivos.
5. **El resultado estructurado se lee al terminar.** `comparar` deja una línea en `comparaciones.jsonl` y la ingesta una entrada en `log.md`; el servidor las lee y emite un evento de resultado con la traza completa (con lo que devolvió cada herramienta), que reemplaza la vista provisional de los pasos.
6. **Lista blanca de archivos.** El visor no acepta rutas libres: solo las que coinciden con patrones declarados (wiki de la demostración, evidencia, documentos, especificaciones, código clave). Nunca `.env`, `.git`, datos crudos ni nada fuera de la raíz. Es la única entrada de rutas del servidor.
7. **Grabación y reproducción.** Cada trabajo termina guardando sus eventos con su tiempo relativo en `results/demo/grabaciones/`. La reproducción los reemite con esos tiempos (con un tope por espera) y marca cada evento como reproducido; el panel muestra un aviso permanente. Es el plan B ante una falla de conexión y no se presenta nunca como ejecución en vivo.
8. **Navegación por secciones, sin guion.** La interfaz se organiza por lo que se hace (preguntar, ingerir, explorar el wiki, ver resultados, revisar el sistema) y ofrece preguntas de ejemplo; no impone un orden ni un tiempo.
9. **Costo visible y con tope.** Cada acción de pago muestra su estimación antes de ejecutarse y la sesión acumula el gasto real de las llamadas; al llegar al tope (0,25 USD por defecto) se bloquean las nuevas acciones de pago. El tope por corrida del cliente del modelo sigue vigente.
10. **La pregunta nunca llega como opción de una orden.** Los parámetros se validan (largo, tipo, carpeta del wiki dentro de `data/wiki/`) y la pregunta se pasa tras `--`.

## Risks / Trade-offs

- **El servidor ejecuta operaciones que gastan saldo:** solo escucha en 127.0.0.1, comprueba el encabezado `Host`, acepta un conjunto fijo de acciones con parámetros validados y limita el gasto de la sesión.
- **Capturar `stderr` es global al proceso:** solo hay un trabajo a la vez y el servidor no escribe en `stderr` mientras corre.
- **La página es un archivo grande sin pruebas automáticas de interfaz:** se comprueba su sintaxis con Node y se verifica a mano en el navegador integrado; la lógica con riesgo (rutas, eventos, grabación, costo, acciones) vive en el servidor y sí tiene pruebas.
- **El wiki mostrado durante una reproducción es el del disco**, que puede no coincidir con el estado grabado: el aviso de reproducción lo dice.
