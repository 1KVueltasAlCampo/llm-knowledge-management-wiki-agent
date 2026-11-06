# Constitución del proyecto

Reglas que no se negocian en cada tarea. Si hay que romper una, se discute y se registra en
`docs/decisiones/`.

1. **Una sola variable.** RAG y wiki usan el **mismo modelo**, el mismo corpus y las mismas
   preguntas. Lo único que cambia es la arquitectura. (Pedido del tutor.)
2. **Especificar antes de codificar.** Todo cambio nuevo pasa por OpenSpec: propuesta,
   especificación, tareas y verificación. Los contratos compartidos viven en `specs/`.
3. **La respuesta correcta sale del corpus**, no del mundo. Si un paper dice algo falso, el
   sistema debe repetirlo con su fuente.
4. **RAG simple.** Búsqueda vectorial y nada más: sin agentes ni delegación entre subagentes.
5. **Ningún secreto en Git.** Las claves viven en `.env`, que está ignorado. La plantilla
   pública es `.env.example`.
6. **Todo costo se registra.** Cada llamada al modelo guarda tokens de entrada y salida,
   tiempo y dólares, y cada corrida respeta `MAX_USD_PER_RUN`.
7. **Las pruebas no gastan saldo.** Los tests nunca llaman a la API real.
8. **Corpus responsable.** No se versionan textos de arXiv, solo identificadores, metadatos y
   posiciones con su huella (`span_id`).
   Se respetan `robots.txt`, los términos de uso y el ritmo de peticiones.
9. **Reproducible.** Se registran el modelo exacto, la temperatura y la fecha de cada corrida.
   Las cifras del informe salen solo de corridas guardadas en `results/`.
10. **Trabajo incremental y visible.** Commits pequeños con mensajes semánticos (`feat:`,
    `fix:`, `docs:`, `test:`, `chore:`) y documentación al día. El historial del repo es la
    evidencia del trabajo.
11. **Respuestas fijadas por humanos.** Una pregunta solo cuenta en el experimento cuando los
    dos autores la verificaron contra el paper; el código crea borradores y nunca cambia su
    estado. Se reporta el acuerdo entre autores.
12. **Nadie se evalúa a sí mismo.** El juez es un modelo distinto del que responde y del que
    redactó las preguntas (decisión 0003). La capa determinista decide primero; el juez solo
    ve lo indeterminado.
13. **El corpus es dato, no instrucción.** Ningún texto de un paper cambia lo que hace un
    agente, y ninguna cita vale si no resuelve a un fragmento real del Gold.
