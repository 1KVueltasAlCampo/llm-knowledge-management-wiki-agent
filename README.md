# llm-knowledge-management-wiki-agent

Proyecto de maestría en Inteligencia Artificial Aplicada sobre **WikiLLMs**: bases de conocimiento en markdown que un agente LLM construye y mantiene de forma incremental, como alternativa a recuperar y sintetizar en cada consulta.

El proyecto no se limita a construir uno. Su objeto es **medir si el mantenimiento incremental preserva la calidad** del conocimiento acumulado, y en qué condiciones compilar por adelantado resulta mejor que recuperar en el momento.

## El problema

Programar hoy con herramientas de IA exige consultar literatura abierta de forma constante. Esos repositorios publican sin revisión por pares y acumulan *slop*: textos generados por modelos de lenguaje, bien redactados, sin código ni evidencia verificable detrás. El volumen hace inviable filtrarlo a mano, y las reglas existentes son sustitutos y no filtros.

RAG agrava el problema en lugar de mitigarlo: al recuperar por similitud semántica trata todos los fragmentos como equivalentes, y otorga la misma autoridad a un experimento validado que a una afirmación sin sustento. El juicio recae entero en el lector, que no dispone de metadato alguno para ejercerlo.

## Pregunta de investigación

> ¿Cómo evoluciona la calidad de un WikiLLM a medida que se le van ingiriendo fuentes, y en qué condiciones supera a un sistema RAG tradicional?

La formulación es abierta a propósito: se busca delimitar **bajo qué condiciones** compilar conviene, no demostrar que siempre conviene. Se pone a prueba además una hipótesis de riesgo contra el propio diseño: que compilar **blanquee el ruido**, convirtiendo una afirmación débil en prosa segura y permanente. Si ocurre, el WikiLLM sería peor que RAG en este escenario, y el proyecto lo reportará.

Corresponde a la RQ1 de §11 del estado del arte. Las otras dos candidatas —*lint* como tarea evaluable, y la frontera económica compilar vs. recuperar— quedaron descartadas para un semestre; la comparación contra RAG se conserva como línea base, no como objeto principal.

## Estado

Fase de fundamentación. **No hay implementación todavía.** El plan de trabajo fue entregado y sustentado; el alcance definitivo queda sujeto a la delimitación con el tutor.

## Documentos

| Documento | Contenido |
|---|---|
| [Definición del problema](definicion_problema.md) | Necesidad de negocio, límites del RAG convencional, solución propuesta, pregunta de investigación y contribución esperada. |
| [Cronograma](cronograma.md) | Fases, fechas, entregables y reparto del trabajo. **Borrador**, sujeto a ajuste. |
| [Cumplimiento de la rúbrica](cumplimiento_rubrica.md) | Trazabilidad criterio por criterio con la evidencia que el proyecto entrega. |
| [Estado del arte](docs/estado-del-arte.md) | Revisión de literatura, panorama de implementaciones, vacíos de investigación y encuadre. |
| `Plan de trabajo del curso.docx` | Versión condensada a dos páginas de los tres documentos anteriores, entregada al curso. |

## Diseño experimental

Las fuentes se ordenan por fecha, se ingieren de a una, y tras cada ingesta se guarda una copia versionada del wiki. Sobre cada copia se responde el mismo conjunto de preguntas de control, con respuesta correcta fijada de antemano por los dos autores. Se miden cinco variables:

| Métrica | Qué responde |
|---|---|
| Cobertura | ¿El wiki contiene lo que debería? |
| Fundamentación | ¿Cada afirmación se rastrea hasta su fuente, con su nivel de respaldo? |
| Resolución de contradicciones | ¿El wiki se corrige cuando un trabajo nuevo supera una cifra anterior? |
| Supervivencia del error | ¿Cuántas ingestas sobrevive un error introducido a propósito? |
| Costo | Tokens y tiempo por ingesta y por consulta, frente a RAG. |

Las ablaciones varían la frecuencia de la revisión automática (*lint*) y la profundidad de la intervención humana. Ambas variables están enunciadas en la literatura y ninguna ha sido medida.

## Decisiones de alcance

- **Corpus:** una subárea de IA con *leaderboards* activos, entre 30 y 50 fuentes, restringida a una ventana temporal posterior al corte de entrenamiento del modelo evaluado, para que las afirmaciones sean numéricas y fechadas y el modelo no responda de memoria.
- **Procedencia como metadato de primera clase:** cada afirmación conserva su fuente y sus señales de respaldo.
- **Human-in-the-loop verificable:** el agente no escribe en producción; propone los cambios como *Pull Request* y un humano los aprueba. Cada aprobación queda registrada, y por tanto es medible.
- **Implementación fuera de un runtime de agente cerrado**, en Python con `litellm`, para conservar el control sobre semillas, temperatura y contabilidad de tokens que exige la reproducibilidad.

## Licencia

Se propone publicar bajo licencia **MIT**. Pendiente de añadir el archivo `LICENSE` al repositorio.

## Equipo

Juan David Cardona · Juan Diego Ramírez
