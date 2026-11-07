# Design

## Context

**Qué dice el corpus sobre cómo debe ser un wiki** (lectura del 7-nov-2026 de los papers indicados):

| Pregunta | Evidencia | Lectura |
|---|---|---|
| ¿Importa que la consulta sea un agente? | LLM-Wiki (2605.25480), ablación en MuSiQue, HotpotQA y 2Wiki: sin *progressive traversal* (una búsqueda y leer una vez) el F1 baja de 11,7 a 13,8 puntos; sin estructura de wiki, de 6,1 a 7,0; sin Error Book, de 3,4 a 4,0. En MuSiQue la variante sin recorrido da 0,601, por debajo del RAG denso (0,611) | El recorrido agéntico es el componente que más pesa |
| ¿Es el agente o es la estructura? | ReFind (2608.12888): un bucle genérico de búsqueda por palabras clave sobre el historial sin estructura alguna supera a los sistemas de memoria con grafos o árboles. APDMem (2610.02472): el agente decide cuánto profundizar y con el 8 % de la conversación basta | Lo que aporta es el control del agente sobre qué y cuánto lee |
| ¿Qué herramientas? | LLM-Wiki: `wiki_search` (prioriza nombre, alias, etiquetas y descripción) y `wiki_read` por lotes con enlaces; tope de 15 llamadas, paciencia de 3 búsquedas vacías, al menos una lectura antes de responder. Cochran-2 (2607.04576): lo que redujo el costo fue una búsqueda por palabras clave que devuelve resúmenes de una línea por página (un tercio menos con un agente capaz; 58 % con el catálogo forzado); un agente capaz no carga el índice, infiere la página | Dos herramientas, resúmenes por página y un tope; el índice completo no es la vía principal |
| ¿Cuál es el costo? | Cochran-1 (2605.18490): el wiki navegado por un agente gasta unas 21 veces más tokens por consulta que un RAG de una ronda; una descomposición del RAG recupera casi toda su ventaja de síntesis con ~6 veces el costo, y el wiki parafrasea y pierde precisión en algunos casos | Hay que topar las acciones, medir el costo por respuesta y decirlo en el informe |
| ¿Debe ser agente también la ingesta? | LLM-Wiki compila seleccionando páginas, generando actualizaciones y validando con reglas deterministas; los enlaces rotos son entre el 29 y el 64 % de los errores que detectan y las referencias mal formadas entre el 19 y el 28 %. Filesystem-memory (2607.26637): la organización hecha por agentes libres se erosiona salvo con el agente más fuerte, y cambiar solo las herramientas reordena el almacén tanto como cambiar de modelo | Ingesta controlada, con validadores en código |
| ¿Qué pasa con los datos que se actualizan? | MERIT (2609.05441): las memorias que se reescriben al escribir (almacén de hechos y resumen del LLM) se mantienen entre 0,70 y 1,00 en hechos actualizados, mientras la recuperación por embeddings baja de forma impredecible | La ingesta debe resolver el valor vigente, no apilar versiones |

**Del proyecto.** El tutor pidió un RAG simple y habló de «wiki-LLM 1, 2…»; el anteproyecto describe un agente con ingesta, consulta y revisión. Los contratos de brazos y de resultados ya existen (`ingerir`, `responder`, citas por `span_id`, `abstained`, `context_tokens`), y el RAG v2 ya valida sus citas.

**Tamaños medidos.** Los 50 papers suman 1,08 M de tokens (media 21.659, máximo 112.449). `deepseek-flash` tiene 1 M de contexto y cuesta 0,15 USD por millón de entrada, 0,003 con caché y 0,60 de salida: un prefijo repetido es casi gratis, y de eso depende cómo se arman los mensajes de ingesta y del bucle.

## Goals / Non-Goals

**Goals:**
- Un wiki que se pueda leer y modificar pieza por pieza, y que cumpla el contrato sin traducciones.
- Que toda afirmación y todo enlace del wiki sean verificables por código, y que las actualizaciones queden escritas con ambas citas.
- Que el costo de ingerir y el de consultar queden medidos por separado y con honestidad (incluido el contexto leído).
- Que las reglas de respuesta sean idénticas a las del RAG: lo único que cambia es la arquitectura.

**Non-Goals:**
- *Lint* automático o Error Book, aprobación humana, ablaciones y Obsidian.
- La variante de navegación fija (sin recorrido), que sería la ablación «sin recorrido» de LLM-Wiki: es barata y queda para un cambio posterior.
- Afinar los prompts contra el banco: las instrucciones son generales y no mencionan papers ni cifras.
- Construir los 50 papers: lo hace el arnés.

## Decisions

1. **Carpeta con archivos y un repositorio Git propio.** `index.md`, `log.md` y `pages/*.md`; cada ingesta es un commit con la etiqueta `paso-N`: la «copia versionada tras cada ingesta» del diseño, que permite inspeccionar o evaluar cualquier paso sin reingerir. La carpeta es `data/wiki/<corrida>/`, ignorada por el repositorio principal (son textos derivados de arXiv, regla 8). Alternativa descartada: una base de datos, porque no se podría leer con un editor.
2. **Dos tipos de página y un resumen de una línea en cada una.** `paper`: una por paper, que asegura que sus hechos entran aunque no encajen en ningún tema. `concepto`: integra lo que dicen varios papers sobre un tema, donde viven las actualizaciones y contradicciones. El resumen es lo que devuelve la búsqueda, según Cochran-2.
3. **La consulta es un agente con `wiki_search` y `wiki_read`.** Protocolo de acciones JSON, una por turno, sobre el cliente único del modelo: no se usa la llamada nativa a herramientas porque `ClienteModelo` es el único punto de entrada y así se conservan registro, costo y tope de gasto de cada llamada. Tope de 8 acciones (LLM-Wiki usa 15 y Cochran 30, pero con papers y preguntas más largas); paciencia de 3 búsquedas vacías; al menos una lectura antes de responder; si se agota el tope, una respuesta final con lo leído. La lectura devuelve hasta 3 páginas por acción.
4. **La búsqueda es léxica y determinista.** Puntúa por palabras clave con más peso en el título y el resumen. Sin embeddings: así el wiki no depende de lo que se está comparando con el RAG, y la búsqueda se prueba sin red. ReFind muestra que la búsqueda léxica con un agente que reformula basta.
5. **Ingesta en dos pasos controlados con el paper primero.** El plan decide qué tocar (recibe paper e índice) y la escritura redacta (recibe paper, páginas a actualizar y plan). Con el paper antes de lo variable el prefijo es el mismo en las dos llamadas y la segunda lo lee desde la caché. Alternativa descartada: un agente libre que lee y escribe archivos, que Filesystem-memory muestra que se erosiona y que no permite validar de forma atómica.
6. **Las páginas se reescriben completas**, no con diffs, que serían más difíciles de validar. Las instrucciones piden mantener las de concepto bajo unas 600 palabras, condensando lo viejo, y un resumen de una línea de 25 palabras como máximo. La primera corrida real (5 papers) mostró páginas de 800–1.100 palabras con el tope de 1.200 y una escritura cortada en el tope de 16.000 tokens de salida, y resúmenes de 40–70 palabras.
7. **Índice y registro generados por el código.** El modelo solo escribe páginas. El índice siempre refleja el disco, y el registro es una fuente confiable de lo que pasó en cada paso.
8. **Validación al escribir, eliminando y contando.** Una cita que no resuelve a un fragmento de un paper ya ingerido se quita; un enlace `[[x]]` sin destino se deja como texto; las líneas con cifra sin cita se cuentan. No se rechaza la página: rechazar tiraría páginas buenas por un defecto menor. Los enlaces rotos son el error más frecuente en LLM-Wiki, y el código lo corrige sin llamar al modelo.
9. **El valor vigente y el superado.** Una regla general en las instrucciones: cuando un paper nuevo da otro valor para una magnitud que ya consta, la página deja el más reciente como vigente y el anterior como superado con su cita; los conflictos se escriben juntos. Es el principio del patrón y lo que MERIT premia en los hechos actualizados.
10. **Contexto y costo completos.** `tokens_contexto` cuenta lo que devolvieron las herramientas (búsquedas y páginas), sin repetirlo por turno, y `tokens_entrada` ya refleja el costo real de reenviar la conversación. El índice no se carga entero: se puede leer como la página `index`.
11. **Reglas de respuesta compartidas.** El texto de reglas (inglés, contexto como datos, citas por `span_id`, frase de abstención) y la extracción de citas pasan a `common/`, y el RAG y el wiki los importan. La regla 1 pide una sola variable.
12. **Atómico.** Si la escritura de una ingesta no es válida, se repite una vez con el error; si sigue mal, se lanza un error y no se toca ningún archivo.

## Risks / Trade-offs

- **El costo por consulta puede ser alto.** Cochran-1 mide 21 veces el de un RAG simple. Se mitiga con el tope, la búsqueda por resúmenes y la caché de prefijo, y el experimento lo mide; si fuera inabordable se evalúa el wiki en menos pasos.
- **La comparación no es simétrica: el wiki tiene un presupuesto de consulta mayor que el RAG de una ronda.** El tutor pidió el RAG simple. Es una diferencia de arquitectura (LLM-Wiki lo declara igual), y como el costo y la latencia por respuesta son métricas del experimento, la comparación es de sistemas completos. El informe debe decirlo, y la descomposición de RAG que recomienda Cochran-1 queda como control opcional.
- **El agente puede dar vueltas sin leer lo que importa.** El tope y la regla de leer antes de responder lo acotan; cuántas acciones usa se registra en el resultado.
- **El modelo puede condensar de más en las páginas de concepto.** Cada paper conserva su página, que no se condensa.
- **Los conceptos pueden multiplicarse sin orden.** Sin lint no se fusionan duplicados. Se mide el tamaño del índice por paso.
- **El JSON puede ser inválido en papers largos.** Una repetición y, si no, un error claro. En la consulta, una acción mal formada que se repite mal se toma como respuesta y se registra.
- **El estudio de LLM-Wiki es de sus propios autores**, con otros corpus y modelo. Se usa como evidencia de diseño, no como predicción del resultado aquí.
