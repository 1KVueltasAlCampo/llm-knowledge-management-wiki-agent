# Entregable 2: Cronograma de trabajo

> **Borrador.** Este cronograma es una propuesta de trabajo, no un compromiso cerrado. Las fases y fechas se ajustarán tras la delimitación del alcance con el tutor (F0) y según el calendario académico oficial.

Semestre 2026-2. Equipo de dos personas. Los hitos internos son los que gobiernan el plan.

| # | Fase | Fechas | Entregable verificable | Responsable |
|---|---|---|---|---|
| F0 | Delimitación y aprobación | 1 – 7 sep | Acta de alcance validada con el tutor: subárea de IA, ventana temporal y criterio de inclusión del corpus. Repositorio público con licencia MIT. | Ambos |
| F1 | Corpus e ingeniería de datos | 8 – 21 sep | Corpus versionado de 30 a 50 preprints con extracción de texto y estructura. Base de metadatos y señales de calidad por fuente. Reporte de calidad de datos. | J. D. Ramírez |
| F2 | Protocolo de evaluación | 22 sep – 5 oct | 60 preguntas de control con respuesta verificable en las fuentes, respondidas por separado por los dos autores y con el nivel de acuerdo entre ambos reportado. Script de evaluación automática. | Ambos |
| F3 | Agente WikiLLM v1 | 6 – 19 oct | Operaciones `ingest` y `lint` funcionando. Wiki compilado sobre el corpus con procedencia por afirmación. Flujo *human-in-the-loop* vía Pull Request. | J. D. Cardona |
| F4 | Línea base y orquestación | 20 oct – 2 nov | Línea base RAG reproducible sobre el mismo corpus. Pipeline orquestado con ejecución programada, reintentos, *logging* estructurado y monitoreo de costo. | Ambos |
| F5 | Experimento | 3 – 16 nov | N ingestas incrementales con *snapshot* por ingesta, tres ablaciones de *lint*, inyección controlada de errores y de fuentes de baja calidad. Resultados y notebooks. | Ambos |
| F6 | Cierre | 17 – 27 nov | Informe final, documentación de reproducción, artículo comparativo y sustentación oral. | Ambos |

## Hitos de control y contingencia

El riesgo dominante del plan es que F3 se desplace y comprima el experimento, que es donde reside la contribución. Se fijan dos puntos de corte:

- **5 de octubre — F2 cerrada.** Si las preguntas de control no están listas en esa fecha, se reducen de 60 a 30 antes que retrasar F5. Sin preguntas de control no hay nada que medir, de modo que esta fase no es negociable en existencia, solo en tamaño.
- **2 de noviembre — F4 cerrada.** Si el pipeline orquestado no está estable, el experimento se ejecuta con disparo manual y la orquestación se documenta como limitación. Se protege el experimento, no la infraestructura.

Alcance recortable en orden, si se pierde tiempo: primero las ablaciones de intervención humana, después las de frecuencia de *lint*, y por último el número de fuentes. La línea base RAG y la inyección controlada **no son recortables**: sin ellas el resultado no es interpretable.

## Distribución del trabajo

**J. D. Ramírez** — curaduría y flujo de datos del corpus, y diseño de la **base de metadatos y señales de calidad** por fuente (disponibilidad de código, experimentos propios, estado de publicación, historial de versiones, cifras reportadas en benchmarks). Esa base es la que hace medible la métrica de discriminación de evidencia; sin ella, la hipótesis de riesgo del proyecto no se puede evaluar. Actúa además como la segunda persona que responde las preguntas de control y opera el punto de revisión humana del experimento.

**J. D. Cardona** — agente LLM, operaciones de ingesta y *lint*, orquestación del pipeline, arnés de evaluación y ejecución del experimento.
