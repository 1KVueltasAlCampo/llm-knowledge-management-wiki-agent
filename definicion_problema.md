# Entregable 1: Definición del problema

## 1. La necesidad de negocio

En las organizaciones, el conocimiento —procesos, decisiones técnicas, manuales, políticas— está fragmentado y envejece rápido, y buscarlo consume tiempo de trabajo. Un estudio con 716 empleados de cuatro entidades públicas, presentado en iConference 2024, encontró que el **22,3 % dedica cerca de media jornada semanal** a buscar la información que necesita para trabajar, y que un **10,5 % dedica jornada y media**, cerca del 30 % de su semana (Nakash y Bouhnik, 2024). La cifra más citada en la industria —alrededor del 20 % de la semana laboral— proviene de un informe de McKinsey de 2012 (Chui et al., 2012) y conviene leerla como orden de magnitud; ambas apuntan a lo mismo: la ineficiencia es transversal y anterior a la IA.

Para mitigarlo, las organizaciones están adoptando asistentes basados en **Recuperación Aumentada por Generación (RAG)**. La evaluación sistemática de Han et al. (2025) muestra que ni RAG vectorial ni los enfoques basados en grafos dominan de forma absoluta: cada uno gana en tareas distintas según la naturaleza de la consulta. Frente al problema de conocimiento corporativo, el RAG convencional presenta tres límites de negocio:

1. **Costo operativo por consulta.** El modelo debe recuperar, leer y sintetizar fragmentos de texto crudo *cada vez* que alguien pregunta. El trabajo de síntesis se repite íntegro en cada consulta, aunque la pregunta sea parecida a la de ayer (Karpathy, 2026).
2. **Degradación de la coherencia.** El sistema recupera documentos obsoletos o en conflicto con políticas recientes, e intenta reconciliarlos en el momento de responder. Eso propaga errores y deriva en respuestas institucionales inconsistentes —el fenómeno que Myakala et al. (2026) formalizan como *drift coherence*— y en alucinaciones que la literatura ataca anclando la generación en fuentes verificadas (Semnani et al., 2023).
3. **Incapacidad de consolidación.** El conocimiento sintetizado no persiste. La empresa no construye un activo que crezca, sino un buscador que vuelve a empezar de cero (Karpathy, 2026).

## 2. Dónde se estudia el problema: la literatura abierta en IA

El proyecto instancia ese problema general sobre un corpus concreto: **la literatura abierta de inteligencia artificial publicada en arXiv**. La elección no es temática sino metodológica. Es la versión más exigente del mismo problema, y la única que puede evaluarse de forma reproducible y pública.

Programar hoy con herramientas de IA exige consultar literatura abierta de forma constante, y en este campo el intervalo entre publicar y construir se comprimió a semanas: una cifra de referencia puede quedar superada en un trimestre. Pero estos repositorios publican sin revisión por pares y acumulan **slop**: textos generados por modelos de lenguaje, bien redactados, sin código ni evidencia verificable detrás.

El volumen hace inviable filtrarlo a mano —solo en febrero de 2026 arXiv recibió más de **20.500 preprints de computación** (arXiv, 2026a)— y las reglas existentes no cierran el hueco, porque son sustitutos y no filtros: la de octubre de 2025 restringe un formato en lugar de detectar IA (arXiv, 2025), y la sanción de mayo de 2026 solo castiga el descuido visible, como referencias inventadas o el *prompt* olvidado dentro del texto (arXiv, 2026b). Elazar y Antoniak (2026) confirman dónde queda el vacío: **el texto generado por LLM es casi seis veces más frecuente en artículos que no son revisiones**, justo la categoría que ninguna regla alcanza.

Lejos de mitigarlo, RAG agrava el problema: al recuperar por similitud semántica **trata todos los fragmentos como equivalentes**, y otorga la misma autoridad a un experimento rigurosamente validado que a una afirmación sin sustento. En un corpus donde ya no puede presumirse que lo publicado fue verificado por alguien, esa indiferencia deja de ser un detalle técnico y pasa a ser el problema central: el juicio recae entero en el lector, que no dispone de ningún metadato para ejercerlo.

Además, el corpus es de acceso libre, sin permisos ni costos de licencia, lo que permite publicar datos y código y que un tercero replique el experimento. Un corpus corporativo real haría imposible esa verificación.

## 3. Solución propuesta

El proyecto diseña e implementa un **pipeline MLOps que construye y mantiene una base de conocimiento en markdown interenlazado (patrón WikiLLM)**, y mide si el mantenimiento incremental preserva la calidad de lo acumulado. La arquitectura mueve el costo de síntesis desde la consulta hacia la ingesta: el agente compila una vez y después responde sobre páginas ya redactadas, enlazadas y fechadas.

| | RAG (línea base) | WikiLLM (propuesta) |
|---|---|---|
| Momento de la síntesis | En cada consulta | Una vez, al ingerir |
| Qué persiste | Fragmentos + embeddings | Páginas redactadas y enlazadas |
| Manejo de la contradicción | Implícito, al responder | Explícito, marcado y fechado en la página |
| Falla característica | Recuperar el fragmento equivocado | Propagar un error de síntesis anterior |

Cuatro decisiones delimitan el alcance:

**Corpus acotado y con verdad verificable.** Una subárea de IA con *leaderboards* activos, entre 30 y 50 fuentes, y una ventana temporal **posterior al corte de entrenamiento del modelo evaluado**. Las afirmaciones sobre resultados en benchmarks son numéricas, fechadas y objetivamente superables, lo que da un criterio de verdad sin juicio subjetivo; la ventana posterior al corte impide que el modelo responda de memoria en lugar de leer el wiki.

**La procedencia es un metadato de primera clase.** Cada afirmación conserva su fuente y sus señales de respaldo: código disponible, experimentos propios, estado de publicación y versión del preprint. La calidad de la evidencia no se disuelve en la prosa.

**Human-in-the-loop verificable.** El agente no escribe sobre la base en producción: propone los cambios como *Pull Request* en Git. Un revisor humano los evalúa en Obsidian —donde el grafo de enlaces muestra qué páginas toca cada cambio— y aprueba o corrige. La revisión queda versionada, lo que convierte la gobernanza en un dato medible: cuántos errores intercepta el humano y a qué costo en tiempo.

**Código y datos abiertos.** Repositorio público bajo licencia MIT, sobre fuentes libres, en coherencia con los principios de Ciencia Abierta que el proyecto estudia.

## 4. Pregunta de investigación y evaluación

> **¿Cómo evoluciona la calidad de un WikiLLM a medida que se le van ingiriendo fuentes, y en qué condiciones supera a un sistema RAG tradicional?**

La pregunta es deliberadamente abierta. Se busca establecer *bajo qué condiciones* compilar por adelantado conviene, no demostrar que siempre conviene: Han et al. (2025) ya mostraron que ninguna arquitectura gana en todo. Hay además una hipótesis de riesgo que el proyecto se obliga a probar contra sí mismo: **una base compilada puede blanquear el ruido**, convirtiendo una afirmación débil en prosa segura y permanente. Si eso ocurre, el WikiLLM sería peor que RAG aquí, y el proyecto lo reportará.

El método es simple: se ordenan las fuentes por fecha, se ingieren de a una, y tras cada ingesta se guarda una copia versionada del wiki. Sobre cada copia se responde el mismo conjunto de preguntas de control, cuyas respuestas correctas los dos autores fijaron de antemano. Se miden cinco cosas:

| Qué se mide | Pregunta que responde |
|---|---|
| Cobertura | ¿El wiki sabe lo que debería saber? |
| Fundamentación | ¿Cada afirmación se puede rastrear a su fuente, con su nivel de respaldo? |
| Resolución de contradicciones | Cuando un trabajo nuevo supera una cifra anterior, ¿el wiki se actualiza? |
| Supervivencia del error | Si se introduce un error a propósito, ¿cuántas ingestas después sigue ahí? |
| Costo | ¿Cuántos tokens y cuánto tiempo por ingesta y por consulta, frente a RAG? |

Comparando esas mediciones al variar la frecuencia de la revisión automática (*lint*) y el grado de intervención humana, se identifica qué política de mantenimiento conserva mejor la calidad. Esas dos variables están enunciadas en la literatura pero nadie las ha medido.

## 5. Contribución esperada

Los trabajos de referencia —STORM (Shao et al., 2024), WikiChat (Semnani et al., 2023) y el conjunto de evaluación FreshWiki— miden artefactos **generados una sola vez**. Ninguno evalúa lo que define al patrón WikiLLM: qué le ocurre a una base de conocimiento **mantenida en el tiempo**.

El patrón, en cambio, sí tiene implementaciones maduras. La más completa es un plugin de Obsidian que ya ofrece detección de contradicciones, fusión de duplicados y páginas protegidas contra sobrescritura (green-dalii, 2026). Eso confirma que el problema de ingeniería está resuelto y desplaza la pregunta abierta hacia la evaluación: la única cifra de desempeño publicada en este espacio es un 27,1 % frente a un 24,1 % de la línea base, autorreportada por el propio proyecto, sobre su propio corpus, y **midiendo recuperación en un wiki ya construido, no su conservación a lo largo del mantenimiento**. Una ventaja de tres puntos, sin protocolo independiente, no establece que el patrón funcione: establece que todavía no se ha medido lo que importa.

Ninguna evaluación disponible mide, tampoco, si la base conserva o destruye la trazabilidad de la calidad de la evidencia mientras crece, que es lo que está en juego cuando la fuente de entrada tiene una relación señal-ruido decreciente. El proyecto aporta el protocolo de evaluación de mantenimiento incremental, su primer conjunto de mediciones, y la implementación abierta que lo hace reproducible.

---

## Referencias

arXiv. (2025, 31 de octubre). *Attention authors: Updated practice for review articles and position papers in arXiv CS category*. arXiv Blog. https://blog.arxiv.org/2025/10/31/attention-authors-updated-practice-for-review-articles-and-position-papers-in-arxiv-cs-category/

arXiv. (2026a). *Monthly submissions*. https://arxiv.org/stats/monthly_submissions

arXiv. (2026b, mayo). *Política de sanción por uso no verificado de modelos de lenguaje en envíos a la sección de Ciencias de la Computación*. arXiv. [verificar en el anuncio oficial]

Chui, M., Manyika, J., Bughin, J., Dobbs, R., Roxburgh, C., Sarrazin, H., Sands, G., & Westergren, M. (2012). *The social economy: Unlocking value and productivity through social technologies*. McKinsey Global Institute. https://www.mckinsey.com/industries/technology-media-and-telecommunications/our-insights/the-social-economy

Elazar, Y., & Antoniak, M. (2026). *LLM-generated or human-written? Comparing review and non-review papers on arXiv* (arXiv:2601.17036). arXiv. https://arxiv.org/abs/2601.17036

green-dalii. (2026). *Karpathy LLM Wiki: Obsidian plugin* [Software]. GitHub. https://github.com/green-dalii/obsidian-llm-wiki

Han, H., Ma, L., Wang, Y., Shomer, H., Lei, Y., Qi, Z., Guo, K., Hua, Z., Long, B., Liu, H., Aggarwal, C. C., & Tang, J. (2025). *RAG vs. GraphRAG: A systematic evaluation and key insights* (arXiv:2502.11371). arXiv. https://arxiv.org/abs/2502.11371

Karpathy, A. (2026, 4 de abril). *LLM wiki: A pattern for building personal knowledge bases using LLMs* [Gist]. GitHub. https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f

Myakala, P. K., Agrawal, M., & Manche, R. (2026). *BeliefShift: Benchmarking temporal belief consistency and opinion drift in LLM agents* (arXiv:2603.23848). arXiv. https://arxiv.org/abs/2603.23848

Nakash, M., & Bouhnik, D. (2024). How much time does the workforce spend searching for information in the "new normal"? En *iConference 2024 Proceedings*. https://www.ideals.illinois.edu/items/129980

Semnani, S. J., Yao, V. Z., Zhang, H. C., & Lam, M. S. (2023). WikiChat: Stopping the hallucination of large language model chatbots by few-shot grounding on Wikipedia. En *Findings of the Association for Computational Linguistics: EMNLP 2023* (pp. 2387–2413). https://arxiv.org/abs/2305.14292

Shao, Y., Jiang, Y., Kanell, T. A., Xu, P., Khattab, O., & Lam, M. S. (2024). Assisting in writing Wikipedia-like articles from scratch with large language models. En *Proceedings of NAACL 2024*. https://arxiv.org/abs/2402.14207
