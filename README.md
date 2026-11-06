# llm-knowledge-management-wiki-agent

Proyecto de maestría en Inteligencia Artificial Aplicada sobre **WikiLLMs**: bases de conocimiento en markdown que un agente LLM construye y mantiene de forma incremental, como alternativa a recuperar y sintetizar en cada consulta.

El proyecto no se limita a construir uno. Su objeto es **medir si el mantenimiento incremental preserva la calidad** del conocimiento acumulado, y en qué condiciones compilar por adelantado resulta mejor que recuperar en el momento.

## El problema

Programar hoy con herramientas de IA exige consultar literatura abierta de forma constante. Esos repositorios publican sin revisión por pares y acumulan *slop*: textos generados por modelos de lenguaje, bien redactados, sin código ni evidencia verificable detrás. El volumen hace inviable filtrarlo a mano, y las reglas existentes son sustitutos y no filtros.

RAG no parece ser la solución más óptima: al recuperar por similitud semántica trata todos los fragmentos como equivalentes, y otorga la misma autoridad a un experimento validado que a una afirmación sin sustento. 

## Pregunta de investigación

> ¿Cómo evoluciona la calidad de un WikiLLM a medida que se le van ingiriendo fuentes, y en qué condiciones supera a un sistema RAG tradicional?

La formulación es abierta: se busca delimitar **bajo qué condiciones** compilar conviene, no demostrar que siempre conviene. Un resultado desfavorable al WikiLLM también es válido, y el proyecto lo reportará.

Corresponde a la RQ1 de §11 del estado del arte. Las otras dos candidatas —*lint* como tarea evaluable, y la frontera económica compilar vs. recuperar— quedaron descartadas para un semestre; la comparación contra RAG se conserva como línea base, no como objeto principal.

## Estado (6 de noviembre de 2026)

Fase de implementación. Hito: el viernes 13 de noviembre de 2026 el corpus y los prototipos deben estar listos para empezar la comparación.

| Parte | Responsable | Estado |
|---|---|---|
| Corpus de 50 papers (Bronze → Silver → Gold, manifest y fragmentos citables) | Juan Diego (pipeline base: Juan David) | Listo. Ver [docs/corpus.md](docs/corpus.md). |
| Métricas de calidad (correctitud, fundamentación, cobertura, acuerdo) | Juan Diego | Listo y probado con resultados sintéticos. |
| Banco de 60 preguntas | Ambos (30 cada uno) | Borradores de la mitad A en curso; falta la verificación humana. |
| RAG, agente de la wiki y arnés de comparación | Juan David | En construcción. |

## Documentos

| Documento | Contenido |
|---|---|
| [Definición del problema](definicion_problema.md) | Necesidad de negocio, límites del RAG convencional, solución propuesta, pregunta de investigación y contribución esperada. |
| [Cronograma](cronograma.md) | Fases, fechas, entregables y reparto del trabajo. **Borrador**, sujeto a ajuste. |
| [Cumplimiento de la rúbrica](cumplimiento_rubrica.md) | Trazabilidad criterio por criterio con la evidencia que el proyecto entrega. |
| [Estado del arte](docs/estado-del-arte.md) | Revisión de literatura, panorama de implementaciones, vacíos de investigación y encuadre. |
| [Entrega final](docs/entrega/) | Documento en LaTeX y su PDF, en el formato de la Facultad Barberi. Compone los cuatro documentos anteriores y lleva el cronograma como diagrama de Gantt. |
| [Anteproyecto](docs/entrega/anteproyecto.tex) | Versión de 4 páginas en LaTeX para revisión del tutor, centrada en la optimización del contexto para modelos y personas. |
| [Selección del corpus](docs/corpus.md) | Criterios, fuentes de candidatos y resultado de la selección de los 50 papers. |
| [Bitácora de datos](docs/bitacora-datos.md) | Qué se hizo, qué se decidió y qué falta en la parte de datos y evaluación. |
| [Nota de traspaso](docs/traspaso-datos.md) | Cómo leer el Gold, el manifest y los fragmentos; qué contrato de resultados se propone. |
| [Decisiones](docs/decisiones/) | Decisiones registradas (modelo único, embeddings, roles de los modelos en la evaluación). |
| [Contratos](specs/) | Formato Gold, propuesta Gold v1 y contrato de resultados del arnés. |
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

### Preguntas de control: cinco tipos

El banco tiene **60 preguntas** (30 por autor). Cada tipo mide una capacidad distinta, y juntos responden la pregunta de investigación:

| Tipo | Qué pregunta | Qué mide | Ejemplo |
|---|---|---|---|
| **T1 · Hecho puntual** | Un dato concreto de **un solo paper** | Si el sistema recupera y reporta bien un hecho | "¿Qué umbral de sinonimia τ usa HippoRAG por defecto?" → 0,8 |
| **T2 · Síntesis** | Algo que exige **combinar dos o más papers** | Si conecta información repartida entre fuentes | "¿En qué difieren STALE y TEPA en su manejo de memorias obsoletas?" |
| **T3 · Contradicción o superación** | Qué estudio **supera o contradice** a otro, y por cuánto | Si detecta conflictos en vez de mezclar las fuentes | "¿Qué framework rinde mejor en QA multi-salto, HippoRAG o SSGM?" |
| **T4 · Actualización** | Un dato que **cambia** cuando llega un paper posterior | Si actualiza lo que sabe: la respuesta correcta cambia en ese paso | Una cifra que un trabajo posterior mejora |
| **T5 · No respondible** | Algo del tema que **no está en el corpus** | Si sabe abstenerse en lugar de inventar | "¿Qué puntaje logra EdgeMem en LoCoMo?" (EdgeMem no está en el corpus) |

- **T1 y T2** miden **cobertura**: si el sistema tiene y encuentra la información.
- **T3 y T4** son donde se espera la ventaja del WikiLLM: al mantenerse de forma incremental debería resolver contradicciones y actualizar cifras, mientras que RAG puede recuperar el fragmento desactualizado.
- **T5** mide **alucinación**. Además, cualquier pregunta se comporta como T5 **antes de su `ingesta_minima`** (el primer paso en que ya es respondible): en esos pasos lo correcto es abstenerse, así que la abstención se mide en todo el experimento.

**Respuestas fijadas por humanos.** Los borradores los redacta un LLM con la evidencia anclada a fragmentos reales del corpus. Solo entran al experimento cuando los dos autores los verificaron por separado contra el paper. Se reporta su acuerdo con kappa de Cohen y los desacuerdos se resuelven en conjunto. La revisión comprueba que la respuesta salga de la cita, que tenga una sola respuesta correcta, que se responda solo con sus fuentes, que el tipo sea el correcto y que las claves de corrección sean justas. Por diseño, al menos 20 de las 30 preguntas de cada autor son respondibles en las primeras 30 ingestas, para que el experimento sea válido también con 30 fuentes.

Las ablaciones varían la frecuencia de la revisión automática (*lint*) y la profundidad de la intervención humana. Ambas variables están enunciadas en la literatura y ninguna ha sido medida.

## Decisiones de alcance

- **Corpus:** 50 preprints de arXiv sobre memoria de agentes, RAG y wikis de LLM, casi todos de 2026, es decir, posteriores al corte de entrenamiento del modelo evaluado, para que no responda de memoria. Las dos semillas anteriores (HippoRAG y HippoRAG 2) se marcan y se reportan aparte. El diseño también es válido con las primeras 30 ingestas.
- **Procedencia como metadato de primera clase:** cada afirmación conserva su fuente y sus señales de respaldo.
- **Human-in-the-loop verificable:** el agente no escribe en producción; propone los cambios como *Pull Request* y un humano los aprueba. Cada aprobación queda registrada, y por tanto es medible.
- **Implementación fuera de un runtime de agente cerrado**, en Python con el SDK de OpenAI contra la API de DeepSeek (`wikillm.common.modelo.ClienteModelo`), para conservar el control sobre semillas, temperatura y contabilidad de tokens que exige la reproducibilidad.
- **Mismo modelo en ambos sistemas:** RAG y wiki usan `deepseek-flash`. El juez de correctitud es Gemini (`gemini-3.1-flash-lite`) y los borradores de preguntas los redacta `deepseek-v4-pro`, para que ningún modelo se evalúe a sí mismo (decisión 0003).

## Cómo reproducir

Requiere [uv](https://docs.astral.sh/uv/) y un archivo `.env` creado a partir de `.env.example`.

```bash
uv sync
uv run python -m wikillm.corpus candidatos    # metadatos verificados con la API de arXiv
uv run python -m wikillm.corpus seleccionar   # elige los 50 papers → data/corpus_ids.txt
uv run python -m wikillm.ingest               # Bronze → Silver → Gold (15 s entre peticiones)
uv run python -m wikillm.corpus manifest      # data/manifest_corpus.jsonl
uv run python -m wikillm.corpus spans         # data/gold/spans.jsonl
uv run python -m wikillm.eval borradores --autor A   # plan y costo; --ejecutar redacta
uv run python -m wikillm.eval metricas --respuestas results/<corrida>/respuestas.jsonl
uv run ruff check . && uv run ruff format --check . && uv run pytest
```

Los textos de arXiv no se versionan (regla 8 de la [constitución](CONSTITUTION.md)); se regeneran con estos comandos.

## Licencia

Se propone publicar bajo licencia **MIT**. Pendiente de añadir el archivo `LICENSE` al repositorio.

## Equipo

Juan David Cruz · Juan Diego Ramírez
