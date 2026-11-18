# llm-knowledge-management-wiki-agent

[![CI](https://github.com/1KVueltasAlCampo/llm-knowledge-management-wiki-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/1KVueltasAlCampo/llm-knowledge-management-wiki-agent/actions/workflows/ci.yml)

Proyecto de maestría en Inteligencia Artificial Aplicada. Compara experimentalmente dos formas de poner conocimiento a disposición de un modelo de lenguaje: **recuperarlo en cada consulta (RAG)** o **compilarlo por adelantado en un wiki de páginas enlazadas que un agente mantiene de forma incremental (WikiLLM)**. La comparación se hace con el mismo modelo, el mismo corpus y las mismas preguntas; lo único que varía es la arquitectura.

## Problema

Las organizaciones y los equipos técnicos acumulan conocimiento fragmentado en documentos que cambian con el tiempo. Un sistema RAG resuelve cada consulta recuperando los fragmentos más cercanos a la pregunta en el espacio vectorial, sin distinguir entre una fuente reciente y otra superada, y repite el trabajo de síntesis en cada respuesta. Un wiki mantenido por un LLM traslada ese trabajo a la ingesta: integra cada fuente nueva en páginas existentes y responde consultando ese conocimiento ya organizado, a cambio de un costo de mantenimiento.

La literatura disponible no converge: los estudios que comparan ambos enfoques usan corpus, modelos y métricas distintos y llegan a conclusiones que no coinciden. No hay, por tanto, una respuesta establecida sobre en qué condiciones conviene cada enfoque, lo que justifica una comparación controlada y reproducible.

## Pregunta de investigación e hipótesis

> ¿Cómo se comparan un sistema RAG simple y un WikiLLM, con el mismo modelo, a medida que se ingiere un corpus de forma cronológica, en correctitud, fundamentación, costo y tiempo?

**Hipótesis de trabajo.** La recuperación por similitud tiende a devolver el fragmento más parecido al texto de la pregunta, aunque esté superado; un wiki mantenido incrementalmente puede reflejar la información más reciente. Esta diferencia debería hacerse visible en las preguntas cuya respuesta cambia al ingerirse un paper posterior. La contrapartida esperada es un costo de ingesta y de consulta mayor en el wiki.

La formulación es abierta: cualquier resultado, incluido uno desfavorable al WikiLLM, es válido y se reporta. Las conclusiones se expresan como un **conjunto de métricas ordenadas por importancia**, no como una cifra única.

## Estado (17 de noviembre de 2026)

La corrida base (RAG simple frente a WikiLLM) sobre 100 papers y 100 preguntas está hecha y analizada. Resta cerrar el informe y la sustentación (exposición el 20 de noviembre y cierre el 27).

| Componente | Estado |
|---|---|
| Corpus de 100 papers (Bronze → Silver → Gold, manifest, fragmentos citables y tres cargas) | Listo: los 50 iniciales más 50 que añaden los papers anteriores a los que citaban y casos de borde ([decisión 0008](docs/decisiones/0008-corpus-de-100-papers-y-banco-de-80-preguntas.md) y [0009](docs/decisiones/0009-cargas-por-fases-y-wiki-reutilizable.md)). El corpus inicial de 50 está en [docs/corpus.md](docs/corpus.md). |
| RAG simple (LangChain y Qdrant local) | Listo, con citas verificadas contra el corpus. |
| WikiLLM (ingesta controlada y consulta por agente) | Listo. El conocimiento de los 100 papers se construyó aparte (461 páginas, unos 1,60 USD) y la corrida lo reutiliza (`--wiki-de`). |
| Arnés de comparación | Listo: reanudable, con control de costo, wiki reutilizable (`--wiki-de`) y brazos seleccionables (`--brazos`). |
| Métricas (correctitud, fundamentación, cobertura, abstención, respuestas obsoletas, acuerdo) | Listas; un juez de otro modelo solo ve lo indeterminado. |
| Banco de 100 preguntas | Cerrado: las 60 originales (acuerdo inicial: A 69,2 % con kappa 0,40; B 60,0 % con kappa 0,15, antes de aplicar las correcciones cruzadas; ver [bitácora](docs/bitacora-datos.md)) y 40 casos de borde (20 por autor). Los dos autores verificaron las 100 contra los papers (las 40 de borde el 16 de noviembre; para ellas no se calculó kappa). |
| Corrida base `ampliado-fases-1` (pasos 33, 66 y 100) | Hecha. Cobertura del wiki frente al RAG con `k = 5`: 0,68 / 0,53, 0,61 / 0,47 y 0,70 / 0,48; al paso 100 la diferencia es +0,23 (IC 95 % [+0,11, +0,35], p = 0,001). Resultados en `results/ampliado-fases-1/`. |
| Corrida de 11 pasos `ampliado-1` (Juan Diego) | Hecha con 80 preguntas; ver la [bitácora](docs/bitacora-datos.md). |
| Análisis complementarios | RAG con `k` = 10, 15 y 20 (la ventaja del wiki baja a +0,06 y deja de ser significativa con `k = 20`), deriva del wiki entre cargas y wiki con acceso al texto original: [docs/sensibilidad-rag-y-deriva-del-wiki.md](docs/sensibilidad-rag-y-deriva-del-wiki.md). Graphify y tgrep: [docs/evaluacion-grafo-100-papers.md](docs/evaluacion-grafo-100-papers.md). |
| Informe final, diapositivas y demostración | En preparación con las cifras anteriores. |

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
        mismas preguntas en los pasos de ingesta 33, 66 y 100
                                        │
              respuestas + citas + tokens + tiempo + costo
                                        │
                         métricas comunes y ranking
```

**Corpus.** 100 preprints de arXiv sobre memoria de agentes, RAG y wikis de LLM, casi todos de 2026, es decir, posteriores al corte de entrenamiento del modelo, para que no responda de memoria. Los 50 iniciales se ampliaron con papers anteriores a los que ellos citan, para que la información antigua y la reciente compitan por similitud semántica (sugerencia del tutor). Las semillas anteriores (HippoRAG y HippoRAG 2) se marcan y se reportan aparte. Los textos se obtienen de la versión HTML de arXiv y se procesan en tres capas: *Bronze* (crudo, inmutable), *Silver* (texto útil) y *Gold* (Markdown con encabezado de metadatos y huella de contenido). Un único Gold alimenta a los dos sistemas.

**Fragmentos citables.** Cada párrafo, tabla, ecuación o pie de figura del Gold tiene un identificador (`span_id`, por ejemplo `2405.14831#s11.p1`) y su huella. Las citas de ambos sistemas solo valen si resuelven a un fragmento real del corpus.

**RAG simple.** Búsqueda vectorial y nada más, sin agentes ni delegación: fragmentos de hasta 400 tokens alineados con los fragmentos citables, embeddings `bge-small-en-v1.5` en GPU, almacén Qdrant en modo local (búsqueda exacta, [decisión 0005](docs/decisiones/0005-qdrant-como-base-vectorial.md)) y una sola llamada al modelo con los 5 fragmentos más cercanos.

**WikiLLM.** El wiki es una carpeta de páginas Markdown con índice y registro, versionada en un repositorio Git propio con una copia por paso de ingesta. La ingesta es un proceso controlado de dos llamadas por paper (plan y escritura) cuya salida valida el código: se descartan las citas que no resuelven a un fragmento de un paper ya ingerido, los enlaces entre páginas sin destino se dejan como texto y se cuentan las afirmaciones numéricas sin cita. La consulta es un agente con dos herramientas, búsqueda de páginas y lectura de páginas, con un tope de acciones, que responde con las mismas reglas que el RAG.

**Misma variable.** Ambos sistemas comparten el modelo (`deepseek-flash`), el corpus, las preguntas, el idioma de las respuestas, la frase de abstención y la extracción de citas. El wiki dispone de un presupuesto de consulta mayor que el RAG de una sola ronda; es una diferencia de arquitectura que el experimento mide a través de tokens, latencia y costo por respuesta.

**Evolución en el tiempo.** Los 100 papers se ingieren de uno en uno, en tres cargas de 33, 33 y 34 papers con la cronología como base y diez excepciones que ordenan los papers según las preguntas que dependen de ellos ([decisión 0009](docs/decisiones/0009-cargas-por-fases-y-wiki-reutilizable.md)). Tras los pasos 33, 66 y 100 se formulan las mismas preguntas a los dos sistemas, de modo que se observa cómo evoluciona cada uno al crecer el corpus; con ese orden se pueden contestar 19, 51 y 84 preguntas en cada corte.

## Banco de preguntas

El banco tiene **100 preguntas** (47 T1, 15 T2, 18 T3, 4 T4 y 16 T5), redactadas en inglés: las 60 originales (30 por autor) y 40 casos de borde (20 por autor) añadidos al ampliar el corpus. Las respuestas correctas salen **del corpus**, no del mundo: si un paper afirma algo, el sistema debe repetirlo con su fuente.

| Tipo | Qué pregunta | Qué mide | Ejemplo |
|---|---|---|---|
| **T1 · Hecho puntual** | Un dato de **un solo paper** | Si el sistema recupera y reporta bien un hecho | «What is the synonymy threshold tau used by default in HippoRAG?» → 0.8 |
| **T2 · Síntesis** | Algo que exige **combinar dos o más papers** | Si conecta información repartida entre fuentes | Cómo difiere el uso de un grafo de conocimiento en HippoRAG del de páginas enlazadas en TrajWiki |
| **T3 · Comparación o contradicción** | Qué estudio **supera o contradice** a otro, y por cuánto | Si compara fuentes en lugar de mezclarlas | Cómo se compara el Recall@5 de HippoRAG 2 con el reportado para HippoRAG |
| **T4 · Actualización** | Un dato, **sin decir qué paper es más reciente**; se repite en varios pasos y su respuesta correcta cambia al ingerirse el paper que lo actualiza | Si da el valor nuevo tras el cambio o sigue dando el anterior (respuesta *obsoleta*) | «What is the highest passage Recall@5 on MuSiQue that the corpus reports for HippoRAG?»: un valor hasta que entra el paper posterior y otro después |
| **T5 · No respondible** | Algo del tema que **no está en el corpus** | Si sabe abstenerse en lugar de inventar | «How many datasets were used in the experiments to evaluate HVM-GraphRAG?» |

Cualquier pregunta se comporta como T5 **antes de su `ingesta_minima`** (el primer paso en que todas sus fuentes ya están ingeridas): en esos pasos lo correcto es abstenerse, de modo que la abstención se mide durante todo el experimento.

**Respuestas fijadas por humanos.** El código genera borradores con la evidencia anclada a fragmentos reales; solo una persona cambia su estado (`borrador` → `verificado_a` / `verificado_b` → `acordado`). Una pregunta cuenta en el experimento cuando los dos autores la verificaron contra el paper, y se reporta su acuerdo (kappa de Cohen) en las 60 originales. Las 40 preguntas de borde partieron de borradores generados con ayuda de un modelo y las verificaron los dos autores contra los papers antes de contar para el informe (sin kappa para esas 40).

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
| Construcción del conocimiento (100 papers, 461 páginas) | ≈ 1,60 USD |
| Corrida base `ampliado-fases-1` (100 preguntas × 3 pasos × 2 brazos) | 0,36 USD: RAG 0,055 y wiki 0,30 |
| Contexto medio por respuesta (`k = 5`) | RAG ≈ 1.300 tokens; wiki ≈ 4.800 tokens |
| RAG con `k` = 10, 15 y 20 (300 respuestas cada uno) | 0,07, 0,02 y 0,13 USD (el caché de DeepSeek altera el costo entre ellos) |

El costo por respuesta del wiki es unas cinco veces el del RAG con `k = 5`, y además hay que pagar la construcción, así que compilar por adelantado no se compensa en dólares: lo que se mide es la mejora de calidad. Detalle en la [bitácora](docs/bitacora-datos.md) y en [docs/sensibilidad-rag-y-deriva-del-wiki.md](docs/sensibilidad-rag-y-deriva-del-wiki.md).


## Alcance y límites

- Se evalúa **una variante de wiki** sobre **un corpus**. Quedan fuera la revisión automática periódica del wiki (*lint*), la aprobación humana de los cambios, las ablaciones sobre ambas y el uso de Obsidian como visor.
- Graphify y tgrep se evaluaron como capas de consulta y no mejoran los aciertos (ver [docs/evaluacion-grafo-100-papers.md](docs/evaluacion-grafo-100-papers.md)); quedan como capa opcional apagada.
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
| [tgrep y graphify](docs/evaluacion-tgrep-graphify.md), [a 100 papers](docs/evaluacion-grafo-100-papers.md) y [revisión independiente](docs/informe-graphify-independiente.md) | Evaluación de las dos herramientas: con 15 papers y con 100, con el binario real de tgrep y con ocho formas de usar Graphify. Están integradas como capa opcional (`src/wikillm/wiki/capas.py`, brazo `wiki_grafo`), apagada por defecto. |
| [Segundo juez](docs/evaluacion-auxiliar-ampliado-fases-1.md) | Evaluación auxiliar a ciegas de 115 respuestas de la corrida base: acuerdo de 94,8 % con el juez principal (kappa 0,893). |
| [Sensibilidad del RAG y deriva del wiki](docs/sensibilidad-rag-y-deriva-del-wiki.md) | El RAG con distintos `k`, qué conserva el wiki al ingerir más papers y el wiki con acceso al texto original. |
| [Estado del arte](docs/estado-del-arte.md) | Revisión de literatura, implementaciones existentes, vacíos y encuadre. |
| [Selección del corpus](docs/corpus.md) | Criterios, fuentes de candidatos y resultado de la selección de los 50 papers iniciales; la ampliación a 100 está en las decisiones 0008 y 0009. |
| [Bitácora](docs/bitacora-datos.md) | Qué se hizo, qué se decidió y qué falta, con las mediciones de cada etapa. |
| [Nota de traspaso](docs/traspaso-datos.md) | Cómo leer el Gold, el manifest y los fragmentos. |
| [Decisiones](docs/decisiones/) | Registro de decisiones de diseño. |
| [Contratos](specs/) | Formato Gold, interfaz de los brazos y contrato de resultados. |
| [Definición del problema](definicion_problema.md), [cronograma](cronograma.md), [cumplimiento de la rúbrica](cumplimiento_rubrica.md) | Documentos de planeación; la definición del problema y el cumplimiento de la rúbrica están alineados con el diseño final (17 de noviembre). |
| [Entrega final](docs/entrega/) | Informe y anteproyecto en LaTeX, con el cronograma como diagrama de Gantt. |

## Hitos

| Fecha | Hito |
|---|---|
| 16–17 de noviembre | Corrida base y análisis complementarios (hechos) |
| 20 de noviembre | Exposición |
| 27 de noviembre | Cierre: informe final y documentación de reproducción |


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
uv run python -m wikillm.corpus seleccionar   # elige los 50 papers iniciales → data/corpus_ids.txt
uv run python -m wikillm.ingest               # Bronze → Silver → Gold (respeta el ritmo de arXiv)
uv run python -m wikillm.corpus manifest      # data/manifest_corpus.jsonl
uv run python -m wikillm.corpus spans         # data/gold/spans.jsonl
uv run python -m wikillm.eval validar-banco   # valida el banco de preguntas
uv run python -m wikillm.rag indexar          # índice vectorial del RAG
uv run python -m wikillm.wiki ingerir --paso 5 --estimar   # costo esperado de ingerir 5 papers
uv run python -m wikillm.arnes comparar "<pregunta>" --wiki data/wiki/demo   # una pregunta a ambos sistemas
uv run python -m wikillm.arnes correr --corrida <nombre> --estimar   # costo de la corrida
uv run python -m wikillm.arnes correr --corrida <nombre>             # ejecuta ambos sistemas por pasos
uv run python -m wikillm.arnes correr --corrida <nombre> --graphify <graphify> [--tgrep <tgrep>]   # añade el brazo wiki_grafo (mismo wiki, consulta con grafo)
uv run python -m wikillm.arnes correr --corrida <nueva> --wiki-de <corrida construida> ...          # reutiliza un wiki ya construido (sin ingesta)
uv run python -m wikillm.corpus fases --manifest data/corpus100/manifest.jsonl --fases data/corpus100/fases.json   # orden de las tres cargas (0009)
uv run python -m wikillm.eval metricas --respuestas results/<nombre>/respuestas.jsonl
uv run ruff check . && uv run ruff format --check . && uv run pytest
```

Para el corpus de 100 papers y el banco de 100 preguntas (`data/corpus100/`, `data/preguntas/banco_100.jsonl`):

```bash
uv run python -m wikillm.corpus fases --manifest data/corpus100/manifest.jsonl --fases data/corpus100/fases.json
uv run python -m wikillm.wiki ingerir --wiki data/wiki/construccion-1 --gold data/corpus100/gold \
    --spans data/corpus100/gold/spans.jsonl --manifest data/corpus100/manifest.jsonl --paso 100   # construye el conocimiento (≈ 1,6 USD)
uv run python -m wikillm.arnes correr --corrida ampliado-fases-1 --pasos 33,66,100 \
    --banco data/preguntas/banco_100.jsonl --manifest data/corpus100/manifest.jsonl \
    --gold data/corpus100/gold --spans data/corpus100/gold/spans.jsonl --wiki-de construccion-1
uv run python -m wikillm.eval metricas --respuestas results/ampliado-fases-1/respuestas.jsonl --juez \
    --banco data/preguntas/banco_100.jsonl --manifest data/corpus100/manifest.jsonl \
    --spans data/corpus100/gold/spans.jsonl
```


Los textos de arXiv no se versionan (regla 8 de la [constitución](CONSTITUTION.md)); se regeneran con estos comandos.

## Licencia

Licencia **MIT** (ver [LICENSE](LICENSE)). El texto de los papers de arXiv no se redistribuye (regla 8) y conserva la licencia de sus autores.

## Equipo

Juan David Cruz · Juan Diego Ramírez
