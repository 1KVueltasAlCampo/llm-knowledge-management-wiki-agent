# llm-knowledge-management-wiki-agent

Proyecto de maestría en Inteligencia Artificial Aplicada. Compara experimentalmente dos formas de poner conocimiento a disposición de un modelo de lenguaje: **recuperarlo en cada consulta (RAG)** o **compilarlo por adelantado en un wiki de páginas enlazadas que un agente mantiene de forma incremental (WikiLLM)**. La comparación se hace con el mismo modelo, el mismo corpus y las mismas preguntas; lo único que varía es la arquitectura.

## Problema

Las organizaciones y los equipos técnicos acumulan conocimiento fragmentado en documentos que cambian con el tiempo. Un sistema RAG resuelve cada consulta recuperando los fragmentos más cercanos a la pregunta en el espacio vectorial, sin distinguir entre una fuente reciente y otra superada, y repite el trabajo de síntesis en cada respuesta. Un wiki mantenido por un LLM traslada ese trabajo a la ingesta: integra cada fuente nueva en páginas existentes y responde consultando ese conocimiento ya organizado, a cambio de un costo de mantenimiento.

La literatura disponible no converge: los estudios que comparan ambos enfoques usan corpus, modelos y métricas distintos y llegan a conclusiones que no coinciden. No hay, por tanto, una respuesta establecida sobre en qué condiciones conviene cada enfoque, lo que justifica una comparación controlada y reproducible.

## Pregunta de investigación e hipótesis

> ¿Cómo se comparan un sistema RAG simple y un WikiLLM, con el mismo modelo, a medida que se ingiere un corpus de forma cronológica, en correctitud, fundamentación, costo y tiempo?

**Hipótesis de trabajo.** La recuperación por similitud tiende a devolver el fragmento más parecido al texto de la pregunta, aunque esté superado; un wiki mantenido incrementalmente puede reflejar la información más reciente. Esta diferencia debería hacerse visible en las preguntas cuya respuesta cambia al ingerirse un paper posterior. La contrapartida esperada es un costo de ingesta y de consulta mayor en el wiki.

La formulación es abierta: cualquier resultado, incluido uno desfavorable al WikiLLM, es válido y se reporta. Las conclusiones se expresan como un **conjunto de métricas ordenadas por importancia**, no como una cifra única.

## Estado (7 de noviembre de 2026)

Fase de preparación del experimento: los dos sistemas y el arnés de comparación están construidos y probados; resta cerrar el banco de preguntas y ejecutar la corrida completa.

| Componente | Estado |
|---|---|
| Corpus de 50 papers (Bronze → Silver → Gold, manifest y fragmentos citables) | Listo. Ver [docs/corpus.md](docs/corpus.md). |
| RAG simple (LangChain y Chroma) | Listo, con citas verificadas contra el corpus. |
| WikiLLM (ingesta controlada y consulta por agente) | Listo. |
| Arnés de comparación (reanudable, con control de costo) y comparación puntual de una pregunta | Listo; ejecutado en un piloto que no se usa en el informe. |
| Métricas (correctitud, fundamentación, cobertura, abstención, respuestas obsoletas, acuerdo) | Listas y probadas con resultados sintéticos. |
| Banco de 60 preguntas | 30 de la mitad A verificadas por un autor; 30 de la mitad B seleccionadas y en espera de verificación. Falta el acuerdo entre autores. |
| Corrida completa, análisis, informe y demostración | Pendientes. |

## Diseño experimental

```
 arXiv (HTML) ─► Bronze ─► Silver ─► GOLD (Markdown + metadatos, fragmentos citables)
                                        │
                     ┌──────────────────┴──────────────────┐
                     ▼                                     ▼
            RAG simple                              WikiLLM
   (fragmentos → vectores → top-k)      (ingesta: plan + escritura de páginas;
                                         consulta: búsqueda y lectura por agente)
                     │                                     │
                     └──────────► MISMO MODELO ◄───────────┘
                                        │
        mismas preguntas en los pasos de ingesta 0, 5, 10, …, 50
                                        │
              respuestas + citas + tokens + tiempo + costo
                                        │
                         métricas comunes y ranking
```

**Corpus.** 50 preprints de arXiv sobre memoria de agentes, RAG y wikis de LLM, casi todos de 2026, es decir, posteriores al corte de entrenamiento del modelo, para que no responda de memoria. Las dos semillas anteriores (HippoRAG y HippoRAG 2) se marcan y se reportan aparte. Los textos se obtienen de la versión HTML de arXiv y se procesan en tres capas: *Bronze* (crudo, inmutable), *Silver* (texto útil) y *Gold* (Markdown con encabezado de metadatos y huella de contenido). Un único Gold alimenta a los dos sistemas.

**Fragmentos citables.** Cada párrafo, tabla, ecuación o pie de figura del Gold tiene un identificador (`span_id`, por ejemplo `2405.14831#s11.p1`) y su huella. Las citas de ambos sistemas solo valen si resuelven a un fragmento real del corpus.

**RAG simple.** Búsqueda vectorial y nada más, sin agentes ni delegación: fragmentos de hasta 400 tokens alineados con los fragmentos citables, embeddings `bge-small-en-v1.5` en GPU, almacén Chroma y una sola llamada al modelo con los 5 fragmentos más cercanos.

**WikiLLM.** El wiki es una carpeta de páginas Markdown con índice y registro, versionada en un repositorio Git propio con una copia por paso de ingesta. La ingesta es un proceso controlado de dos llamadas por paper (plan y escritura) cuya salida valida el código: se descartan las citas que no resuelven a un fragmento de un paper ya ingerido, los enlaces entre páginas sin destino se dejan como texto y se cuentan las afirmaciones numéricas sin cita. La consulta es un agente con dos herramientas, búsqueda de páginas y lectura de páginas, con un tope de acciones, que responde con las mismas reglas que el RAG.

**Misma variable.** Ambos sistemas comparten el modelo (`deepseek-flash`), el corpus, las preguntas, el idioma de las respuestas, la frase de abstención y la extracción de citas. El wiki dispone de un presupuesto de consulta mayor que el RAG de una sola ronda; es una diferencia de arquitectura que el experimento mide a través de tokens, latencia y costo por respuesta.

**Evolución en el tiempo.** Los papers se ingieren de uno en uno en orden de publicación. Tras los pasos 0, 5, 10, …, 50 se formulan las mismas preguntas a los dos sistemas, de modo que se observa cómo evoluciona cada uno al crecer el corpus.

## Banco de preguntas

El banco tiene **60 preguntas** (30 por autor), redactadas en inglés. Las respuestas correctas salen **del corpus**, no del mundo: si un paper afirma algo, el sistema debe repetirlo con su fuente.

| Tipo | Qué pregunta | Qué mide | Ejemplo |
|---|---|---|---|
| **T1 · Hecho puntual** | Un dato de **un solo paper** | Si el sistema recupera y reporta bien un hecho | «What is the synonymy threshold tau used by default in HippoRAG?» → 0.8 |
| **T2 · Síntesis** | Algo que exige **combinar dos o más papers** | Si conecta información repartida entre fuentes | Cómo difiere el uso de un grafo de conocimiento en HippoRAG del de páginas enlazadas en TrajWiki |
| **T3 · Comparación o contradicción** | Qué estudio **supera o contradice** a otro, y por cuánto | Si compara fuentes en lugar de mezclarlas | Cómo se compara el Recall@5 de HippoRAG 2 con el reportado para HippoRAG |
| **T4 · Actualización** | Un dato, **sin decir qué paper es más reciente**; se repite en varios pasos y su respuesta correcta cambia al ingerirse el paper que lo actualiza | Si da el valor nuevo tras el cambio o sigue dando el anterior (respuesta *obsoleta*) | «What is the highest passage Recall@5 on MuSiQue that the corpus reports for HippoRAG?»: un valor hasta que entra el paper posterior y otro después |
| **T5 · No respondible** | Algo del tema que **no está en el corpus** | Si sabe abstenerse en lugar de inventar | «How many datasets were used in the experiments to evaluate HVM-GraphRAG?» |

Cualquier pregunta se comporta como T5 **antes de su `ingesta_minima`** (el primer paso en que todas sus fuentes ya están ingeridas): en esos pasos lo correcto es abstenerse, de modo que la abstención se mide durante todo el experimento.

**Respuestas fijadas por humanos.** El código genera borradores con la evidencia anclada a fragmentos reales; solo una persona cambia su estado (`borrador` → `verificado_a` / `verificado_b` → `acordado`). Una pregunta cuenta en el experimento cuando los dos autores la verificaron por separado contra el paper, y se reporta su acuerdo (kappa de Cohen). Por diseño, al menos 20 de las 30 preguntas de cada autor son respondibles en las primeras 30 ingestas.

## Métricas

Se usan únicamente métricas aplicables a los dos sistemas.

| Métrica | Qué responde |
|---|---|
| Correctitud | ¿La respuesta coincide con la fijada de antemano? Primero una capa determinista (claves normalizadas) y, solo para lo indeterminado, un juez de otro modelo (su calibración contra etiquetas humanas está prevista). |
| Fundamentación | ¿Las citas resuelven a fragmentos reales de papers ya ingeridos en ese paso? |
| Cobertura | De las preguntas respondibles en un paso, ¿cuántas se contestan bien? |
| Abstención | En T5 y antes de la `ingesta_minima`, ¿se abstiene o inventa? |
| Respuestas obsoletas | En T4, tras el cambio, ¿sigue dando el valor anterior? |
| Contexto, costo y tiempo | Tokens de contexto, tokens, dólares y segundos por respuesta, más el costo de ingesta del wiki. |

Las métricas se combinan en un ranking ponderado cuyos pesos se fijan antes de ver los resultados, con un análisis de sensibilidad que comprueba si el orden cambia al modificarlos.

## Decisiones de diseño

Cada una está registrada en [docs/decisiones](docs/decisiones/) o en una especificación de [openspec/specs](openspec/specs/).

- **Un solo modelo para responder** (`deepseek-flash`), por API y a través de un único cliente (`wikillm.common.modelo.ClienteModelo`) que registra tokens, tiempo y dólares de cada llamada y respeta un tope de gasto por corrida.
- **Ningún modelo se evalúa a sí mismo.** El juez de correctitud es de otro proveedor (`gemini-3.1-flash-lite`) y los borradores de preguntas los redactan modelos distintos del que responde (decisión 0003).
- **Experimento en inglés:** preguntas, respuestas, instrucciones y páginas del wiki (decisión 0004).
- **El corpus es dato, no instrucción.** Ningún texto de un paper cambia lo que hace el agente, y las citas se validan contra el corpus.
- **Embeddings en GPU por defecto** (decisión 0002).

## Mediciones de desarrollo

No son resultados del experimento; sirven para dimensionar su costo. Detalle en la [bitácora](docs/bitacora-datos.md).

| Medición | Valor |
|---|---|
| Indexación del RAG con los 50 papers (5.430 fragmentos, GPU) | 159 s |
| Ingesta del wiki con 5 papers | 0,028 USD y 198 s |
| Costo por pregunta con 5 papers ingeridos | RAG ≈ 0,0003–0,0004 USD; wiki ≈ 0,0008 USD |
| Piloto del arnés (17 preguntas, pasos 0 y 5, 68 respuestas) | 0,056 USD |

La corrida completa se estima entre 1 y 2,5 USD.

## Alcance y límites

- Se evalúa **una variante de wiki** sobre **un corpus**. Quedan fuera la revisión automática periódica del wiki (*lint*), la aprobación humana de los cambios, las ablaciones sobre ambas y el uso de Obsidian como visor.
- El wiki dispone de un presupuesto de consulta mayor que el del RAG de una ronda.
- El corpus procede de un único dominio (memoria de agentes y wikis de LLM) y el modelo es uno solo; la extrapolación a otros dominios o modelos queda como trabajo futuro.
- Con temperatura 0 el proveedor no garantiza respuestas idénticas entre ejecuciones: una sola corrida por pregunta contiene ruido, y los resultados deben reportarse con esa salvedad.

## Metodología de desarrollo

Desarrollo guiado por especificaciones con [OpenSpec](https://github.com/Fission-AI/OpenSpec): cada cambio pasa por propuesta, especificación, tareas y verificación antes de archivarse. Las reglas permanentes están en la [constitución](CONSTITUTION.md) y la guía de trabajo en [AGENTS.md](AGENTS.md). El historial de commits semánticos y la documentación incremental constituyen la evidencia del trabajo. Las pruebas automáticas nunca llaman a la API real.

## Estructura

| Ruta | Contenido |
|---|---|
| `src/wikillm/ingest/`, `src/wikillm/corpus/` | Pipeline Bronze → Silver → Gold, selección del corpus, manifest y fragmentos citables |
| `src/wikillm/rag/` | RAG simple |
| `src/wikillm/wiki/` | WikiLLM: almacén, ingesta, herramientas y consulta |
| `src/wikillm/arnes/` | Arnés de comparación |
| `src/wikillm/eval/` | Banco de preguntas, métricas, juez y acuerdo entre autores |
| `src/wikillm/common/` | Cliente del modelo, costo y reglas de respuesta compartidas |
| `specs/`, `openspec/` | Contratos compartidos y especificaciones vivas |
| `docs/` | Corpus, decisiones, bitácora, estado del arte y documentos de entrega |
| `data/` | Identificadores, metadatos, preguntas y huellas; los textos de arXiv se regeneran |
| `results/` | Resultados de las corridas |

## Documentos

| Documento | Contenido |
|---|---|
| [Demostración](docs/demo.md) | Recorrido de punta a punta con la evidencia que produce. |
| [Estado del arte](docs/estado-del-arte.md) | Revisión de literatura, implementaciones existentes, vacíos y encuadre. |
| [Selección del corpus](docs/corpus.md) | Criterios, fuentes de candidatos y resultado de la selección de los 50 papers. |
| [Bitácora](docs/bitacora-datos.md) | Qué se hizo, qué se decidió y qué falta, con las mediciones de cada etapa. |
| [Nota de traspaso](docs/traspaso-datos.md) | Cómo leer el Gold, el manifest y los fragmentos. |
| [Decisiones](docs/decisiones/) | Registro de decisiones de diseño. |
| [Contratos](specs/) | Formato Gold, interfaz de los brazos y contrato de resultados. |
| [Definición del problema](definicion_problema.md), [cronograma](cronograma.md), [cumplimiento de la rúbrica](cumplimiento_rubrica.md) | Documentos de planeación correspondientes a la formulación inicial; se actualizan con el diseño descrito en este archivo. |
| [Entrega final](docs/entrega/) | Informe y anteproyecto en LaTeX, con el cronograma como diagrama de Gantt. |

## Hitos

| Fecha | Hito |
|---|---|
| 23–27 de noviembre | Corrida completa sobre el banco acordado |
| 30 de noviembre – 4 de diciembre | Análisis, ranking con sensibilidad, informe y guion de demostración; congelamiento el 4 de diciembre |
| 7–11 de diciembre | Entrega y sustentación |

## Demostración

[docs/demo.md](docs/demo.md) describe un recorrido de punta a punta sobre el corpus real: la misma pregunta al RAG y al wiki antes de ingerir el paper que la responde, la ingesta de ese paper en vivo, la pregunta repetida y la evidencia que queda (citas con su fragmento, pasos del agente, costo y copias versionadas del wiki).

```bash
uv run python -m wikillm.arnes comparar "<pregunta>" --wiki data/wiki/demo
uv run python -m wikillm.panel        # interfaz web local (http://127.0.0.1:8765)
```

El panel local ejecuta las mismas órdenes y muestra en vivo, con una columna por sistema, el recorrido del agente, las llamadas al modelo, las citas con su fragmento y el costo. Tiene cinco secciones (preguntar, ingerir, wiki, resultados y sistema), un visor de archivos de solo lectura y un tope de gasto por sesión; cada ejecución real queda guardada y puede reproducirse sin llamar al modelo.

## Cómo reproducir

Requiere [uv](https://docs.astral.sh/uv/) y un archivo `.env` creado a partir de `.env.example`. Los comandos que llaman al modelo gastan saldo y muestran antes su estimación.

```bash
uv sync
uv run python -m wikillm.corpus candidatos    # metadatos verificados con la API de arXiv
uv run python -m wikillm.corpus seleccionar   # elige los 50 papers → data/corpus_ids.txt
uv run python -m wikillm.ingest               # Bronze → Silver → Gold (respeta el ritmo de arXiv)
uv run python -m wikillm.corpus manifest      # data/manifest_corpus.jsonl
uv run python -m wikillm.corpus spans         # data/gold/spans.jsonl
uv run python -m wikillm.eval validar-banco   # valida el banco de preguntas
uv run python -m wikillm.rag indexar          # índice vectorial del RAG
uv run python -m wikillm.wiki ingerir --paso 5 --estimar   # costo esperado de ingerir 5 papers
uv run python -m wikillm.arnes comparar "<pregunta>" --wiki data/wiki/demo   # una pregunta a ambos sistemas
uv run python -m wikillm.arnes correr --corrida <nombre> --estimar   # costo de la corrida
uv run python -m wikillm.arnes correr --corrida <nombre>             # ejecuta ambos sistemas por pasos
uv run python -m wikillm.eval metricas --respuestas results/<nombre>/respuestas.jsonl
uv run ruff check . && uv run ruff format --check . && uv run pytest
```

Los textos de arXiv no se versionan (regla 8 de la [constitución](CONSTITUTION.md)); se regeneran con estos comandos.

## Licencia

Se propone publicar bajo licencia **MIT**. Pendiente de añadir el archivo `LICENSE` al repositorio.

## Equipo

Juan David Cruz · Juan Diego Ramírez
