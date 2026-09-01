# Entregable 3: Cumplimiento de la rúbrica

Cada criterio, en orden, con lo que pide y lo que el proyecto entrega.

## R.6.1 — Modelos de IA generativa para nuevos productos

### Cr1 — Formulación del problema

**Pide:** traducir el entorno empresarial en un problema abordable con IA generativa.

**Entrega:** el problema parte de una ineficiencia empresarial medida —hasta un 30 % de la jornada buscando información en el caso más severo (Nakash y Bouhnik, 2024)— y nombra tres límites concretos del RAG que hoy se usa para resolverla: repite el trabajo de síntesis en cada consulta, mezcla documentos obsoletos con vigentes, y no acumula nada. El proyecto lo estudia sobre literatura abierta de IA porque es la versión más difícil del mismo problema (más de 20.500 preprints de computación al mes, obsolescencia en semanas, y slop que ninguna regla filtra) y la única que se puede evaluar en público.

### Cr2 — Elección del modelo

**Pide:** justificar la elección comparando alternativas, no solo nombrar un modelo.

**Entrega:** la ingesta debe leer una fuente nueva y revisar entre 10 y 15 páginas ya escritas. Eso fija cuatro requisitos: contexto amplio, obediencia estricta al formato de salida, costo por token predecible (el costo es una de las variables que el experimento mide) y una opción que corra en local. Las implementaciones existentes del patrón llegan a los mismos dos primeros requisitos por vía empírica —recomiendan ventanas de 200K tokens en adelante y advierten que, para extraer, obedecer el formato importa más que la capacidad bruta del modelo—, lo que respalda derivarlos aquí desde el diseño.

| Alternativa | Contexto | Sigue el formato | Costo | Corre local | Para qué se usa |
|---|---|---|---|---|---|
| Modelo comercial grande (Claude, GPT, Gemini) | ≥200K | Alta | Alto | No | Ingesta y revisión |
| Modelo comercial económico (Haiku, mini) | ≥200K | Media-alta | Bajo | No | Consultas y evaluación masiva |
| Modelo abierto local (Qwen, Llama con Ollama) | 32–128K | Media | Cómputo propio | Sí | Privacidad y control de contaminación |
| Embeddings + reordenador | — | — | Muy bajo | Sí | Solo la línea base RAG |

No se elige un modelo: se elige **qué modelo va en cada etapa**. Se usa `litellm` para que cambiar de modelo sea cambiar una línea de configuración, no reescribir código. Así el modelo es una variable del experimento y se puede reportar la relación costo/calidad en vez de un solo número. La restricción del corpus a fechas posteriores al corte de entrenamiento es parte de esta justificación: sin ella el modelo responde de memoria y se estaría midiendo lo que ya sabía, no la arquitectura.

### Cr3 — Integración del modelo

**Pide:** adaptar el modelo al caso, de forma innovadora y escalable.

**Entrega:** el modelo no es un chat. Es el motor de un ciclo documental gobernado por Git: lee una fuente, propone cambios en varias páginas a la vez, y los entrega como *Pull Request* para que un humano los apruebe. La diferencia con las implementaciones existentes está en dónde se ubica el control humano: hoy se protege una página marcándola a mano para que no sea sobrescrita, es decir, después de que el agente ya escribió. Aquí ninguna escritura llega al wiki sin aprobación previa, y cada aprobación queda registrada, que es lo que permite medir la revisión humana en lugar de solo confiar en ella. La misma arquitectura sirve para cualquier organización que ya use Git y markdown, sin infraestructura adicional.

### Cr4 — Evaluación del desempeño

**Pide:** aplicar métricas adecuadas e interpretarlas frente a los objetivos.

**Entrega:** cinco métricas medidas sobre cada copia versionada del wiki (cobertura, fundamentación, resolución de contradicciones, supervivencia del error y costo), contra un conjunto de preguntas de control con respuesta fijada de antemano por los dos autores, reportando el acuerdo entre ambos. Las métricas 3 y 4 no son estándar de exactitud: miden si el sistema se corrige a sí mismo con el tiempo, que es el objetivo real del producto.

## R.6.2 — Automatización de tareas

### Cr5 — Selección de tareas automatizables

**Pide:** identificar procesos donde la automatización aporta valor real.

**Entrega:** se automatiza la reconciliación documental —repetitiva, costosa en tiempo y con criterio estable— y se deja al humano el juicio de validez, que es donde automatizar aporta poco y arriesga mucho. El reparto es explícito, no accidental.

### Cr6 — Eficiencia lograda

**Pide:** demostrar que la solución mejora el proceso, con cifras.

**Entrega:** compilar por adelantado es *más* caro que RAG hasta cierto número de consultas. El proyecto reporta esa curva y el punto donde se cruza, en función de cuántas consultas se hacen por cada fuente ingerida. Una mejora afirmada sin punto de equilibrio no sería demostrable, y por eso se mide en lugar de declararse.

### Cr7 — Mitigación de riesgos éticos

**Pide:** estrategias frente a sesgos, privacidad y seguridad.

**Seguridad.** Un documento fuente puede traer instrucciones ocultas dirigidas al agente. En RAG el daño dura una respuesta; aquí quedaría escrito en el wiki de forma permanente. Mitigación: las fuentes se tratan siempre como datos y nunca como órdenes, toda escritura pasa por *Pull Request* revisado, y se prueba el sistema con documentos preparados para atacarlo, reportando cuántos se detienen.

**Sesgo.** Tres frentes: qué fuentes entran (criterio de inclusión declarado), la tendencia a que lo más reciente sobrescriba lo anterior sin evidencia suficiente, y el riesgo mayor en este dominio —que la compilación **convierta literatura débil en prosa autoritativa**. Ese último no se declara: se mide, inyectando fuentes de baja calidad y observando con cuánta seguridad el wiki termina afirmándolas.

**Privacidad.** El corpus es público y sin datos personales. Todo texto enviado a un proveedor externo queda registrado, y el brazo con modelo local permite correr el pipeline completo sin que los datos salgan del equipo, midiendo cuánta calidad cuesta esa opción.

La revisión humana es el control que atraviesa los tres, y su eficacia se reporta como dato: errores detectados sobre errores introducidos, y minutos de revisión por error detectado.

### Cr8 — Documentación

**Pide:** que la solución esté documentada y se pueda replicar.

**Entrega:** repositorio público con licencia MIT, instrucciones de reproducción de principio a fin, las instrucciones del agente versionadas como archivo, y un registro de las decisiones de arquitectura con su justificación.

## R.7.1 — Gestión y preparación de datos

### Cr1 — Preprocesamiento

**Pide:** limpieza, transformación y validación dentro del flujo.

**Entrega:** extracción de texto de PDF y LaTeX conservando la estructura, normalización de codificación y de notación de cifras, eliminación de duplicados por huella de contenido y por versión del preprint, unificación de nombres de métodos y benchmarks, y validación de formato que descarta documentos malformados **antes** de gastar una llamada al modelo.

### Cr2 — Selección y dominio de herramientas

**Pide:** herramientas pertinentes, usadas correctamente.

**Entrega:** Python con `litellm` (cambiar de proveedor sin tocar código), `pydantic` (verificar que la salida del modelo tenga la forma esperada), `pytest` (detectar regresiones), la API de arXiv (traer fuentes y metadatos), y Git más Obsidian como capa de revisión humana sobre los mismos archivos markdown, sin quedar atados a ninguna plataforma.

### Cr3 — Automatización e integración

**Pide:** un pipeline que automatice la entrada de datos y se integre con el modelo.

**Entrega:** un flujo modular de seis pasos —traer la fuente, extraer afirmaciones con su origen, unificar entidades, actualizar páginas, revisar el wiki, guardar copia versionada— donde cada paso se puede volver a ejecutar por separado sin rehacer los anteriores.

## R.7.2 — Automatización del despliegue (MLOps)

### Cr4 — Automatización del despliegue

**Pide:** ejecución de scripts, orquestación y monitorización en producción.

**Entrega:** un orquestador que corre el flujo por calendario o a demanda, con seguimiento de costo y tiempo en cada paso y aviso automático cuando una métrica se degrada.

### Cr5 — Escalabilidad y robustez

**Pide:** soportar crecimiento y resistir fallos.

**Entrega:** la ingesta es idempotente —procesar dos veces la misma fuente no la duplica—, reintenta con espera creciente cuando el proveedor falla, y guarda avance por fuente para reanudar sin reprocesar todo. Se reporta además cómo se degrada el tiempo de respuesta a medida que el wiki crece.

### Cr6 — Prácticas MLOps

**Pide:** versionado, logging, actualización y reentrenamiento.

**Entrega:** las instrucciones del agente se versionan como código, cada operación deja registro estructurado, y el conjunto de preguntas de control funciona como prueba de regresión: si un cambio en el agente empeora la calidad, se detecta antes de desplegarlo. Sobre el reentrenamiento: el sistema no entrena pesos, así que su equivalente real es la **recompilación**. Cuando llega una fuente que supera lo anterior, el pipeline vuelve a generar las páginas afectadas y deja registrada la sustitución con su fecha. Ese ciclo es justamente lo que el experimento mide.

## RA1 y RA2 — Comunicación escrita y oral

El documento tiene las tres secciones pedidas —problema, cronograma y cumplimiento—, usa tablas donde la comparación es el contenido, y cita en norma APA con cada referencia verificada en su fuente original. La sustentación se organiza sobre una sola idea: *compilar y mantener no es lo mismo que recuperar, y la diferencia se puede medir*. Se prepara la defensa de las tres preguntas previsibles: por qué no basta con GraphRAG, qué pasa si el resultado favorece a RAG, y por qué confiar en un sistema que usa IA para sintetizar literatura contaminada por IA. La segunda ya está resuelta en el diseño, porque delimitar en qué condiciones gana cada arquitectura también es un resultado. La tercera se responde con la trazabilidad de fuentes y la revisión humana, cuya eficacia el proyecto mide en vez de afirmar.
