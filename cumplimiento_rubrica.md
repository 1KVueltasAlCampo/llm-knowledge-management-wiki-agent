# Entregable 3: Cumplimiento de la rúbrica

Estado al 10 de noviembre de 2026. Cada criterio dice lo que pide, lo que el proyecto **ya
tiene** (con el archivo donde se comprueba), lo que **falta** y lo que **quedó fuera del
alcance**. Este documento reemplaza al de la formulación inicial, que prometía cosas que el
diseño final no construye (aprobación humana por Pull Request, Obsidian, `litellm`, un
orquestador con avisos, pruebas de inyección y un brazo con modelo local). El alcance real
está en el [README](README.md#alcance-y-límites).

Leyenda: **Hecho** = existe y se puede comprobar hoy · **Con la corrida** = lo produce la
corrida completa · **Falta** = trabajo pendiente · **Fuera de alcance** = decidido y declarado.

## R.6.1 — Modelos de IA generativa para nuevos productos

### Cr1 — Formulación del problema

**Pide:** traducir el entorno empresarial en un problema abordable con IA generativa.

**Hecho.** El problema parte de una necesidad organizacional medida: el conocimiento está
fragmentado, envejece rápido y buscarlo consume jornada (Nakash y Bouhnik, 2024, en
[definicion_problema.md](definicion_problema.md)). El RAG que hoy se usa para mitigarlo tiene tres
límites: repite la síntesis en cada consulta, mezcla documentos obsoletos con vigentes y no
acumula nada. El proyecto lo estudia sobre literatura abierta de IA porque es la versión más
difícil del mismo problema y la única que se puede evaluar en público. La pregunta de
investigación y la hipótesis están en el [README](README.md#pregunta-de-investigación-e-hipótesis)
y la literatura en [docs/estado-del-arte.md](docs/estado-del-arte.md).

**Falta.** Alinear `definicion_problema.md` con el diseño final: todavía describe la aprobación por
Pull Request y la revisión en Obsidian, que están fuera de alcance.

### Cr2 — Elección del modelo

**Pide:** justificar la elección comparando alternativas, no solo nombrar un modelo.

**Hecho.** Se usa un modelo único, `deepseek-flash`, en los dos sistemas, porque el tutor pidió el
mismo modelo en ambos y recomendó este. La
[decisión 0001](docs/decisiones/0001-modelo-unico-deepseek-flash.md) compara las alternativas
disponibles (DeepSeek Pro, Gemini, modelos comerciales grandes, modelo local) con criterios
explícitos: contexto, formato de salida, costo con caché y saldo. La
[decisión 0003](docs/decisiones/0003-roles-de-modelos-en-la-evaluacion.md) separa los roles
(responde, redacta, juzga) para que ningún modelo se evalúe a sí mismo.

**Límite declarado.** El experimento mide arquitecturas con un modelo, no modelos. No se comparó la
calidad de otros respondedores.

### Cr3 — Integración del modelo

**Pide:** adaptar el modelo al caso, de forma funcional y escalable.

**Hecho.** El modelo no es un chat: es el motor de dos sistemas que comparten cliente, reglas de
respuesta y citas. En el WikiLLM, la ingesta es un proceso de dos llamadas por paper (plan y
escritura) cuya salida valida el código: descarta las citas que no resuelven a un fragmento de un
paper ya ingerido, deja como texto los enlaces sin destino y cuenta las afirmaciones numéricas sin
cita (`src/wikillm/wiki/ingesta.py`). La consulta es un agente con herramientas de búsqueda y
lectura y un tope de acciones. Cada llamada pasa por `ClienteModelo`, que registra tokens, tiempo y
dólares y respeta el tope de gasto.

**Hecho (opcional).** La evaluación de [graphify y tgrep](docs/evaluacion-tgrep-graphify.md) llevó a
una capa de consulta con grafo sobre el mismo wiki, integrada como brazo adicional `wiki_grafo`
(`src/wikillm/wiki/capas.py`, opciones `--graphify` y `--tgrep` de `arnes correr`). Está apagada por
defecto y no cambia el WikiLLM base.

**Fuera de alcance.** La aprobación humana de los cambios del wiki antes de escribirlos.

### Cr4 — Interpretar la evaluación del desempeño

**Pide:** aplicar métricas adecuadas e interpretarlas frente a los objetivos.

**Hecho.** Las métricas están implementadas y probadas con resultados sintéticos
(`src/wikillm/eval/`): correctitud (capa determinista y, solo para lo indeterminado, un juez de
otro modelo), fundamentación de las citas, cobertura, abstención, respuestas obsoletas y
contexto, costo y tiempo. Se evalúan contra un banco de 60 preguntas con respuesta fijada de
antemano por los dos autores, con el acuerdo entre ambos reportado (kappa de 0,40 en A y de 0,15 en
B antes de aplicar las correcciones cruzadas; [bitácora](docs/bitacora-datos.md)).

**Con la corrida.** Los resultados y su interpretación (ranking con análisis de sensibilidad) salen
de la corrida completa y se escriben en el informe.

**Falta.** Calibrar el juez contra etiquetas humanas (prevista) y ejecutarlo sobre el piloto antes
de la corrida.

## R.6.2 — Automatizar tareas con IA generativa

### Cr5 — Selección de tareas automatizables

**Pide:** identificar procesos donde la automatización aporta valor real.

**Hecho.** Se automatiza la síntesis y la reconciliación documental, que es repetitiva y costosa:
el WikiLLM integra cada fuente nueva en páginas existentes en lugar de rehacer la síntesis en cada
consulta. La [definición del problema](definicion_problema.md) explica por qué esa es la tarea con
valor.

**Fuera de alcance.** La revisión humana periódica del wiki (*lint*) y la aprobación de cambios.

### Cr6 — Eficiencia lograda

**Pide:** demostrar que la solución mejora el proceso, con cifras.

**Hecho.** Todo costo se registra (regla 6) y hay mediciones de desarrollo: ingerir un paper
cuesta del orden de 0,016 USD y una consulta entre 0,0003 y 0,001 USD
([README](README.md#mediciones-de-desarrollo)). La evaluación de [graphify y
tgrep](docs/evaluacion-tgrep-graphify.md) cuantifica tokens y dólares por consulta.

**Con la corrida.** Costo de ingesta, de consulta y tiempo por paso para los dos sistemas, con los
que se calcula el **punto de equilibrio**: cuántas consultas por paper ingerido hacen falta para que
compilar por adelantado salga más barato que recuperar (`scripts/punto_de_equilibrio.py`).

**Falta.** Escribir esa curva en el informe con los datos de la corrida.

### Cr7 — Mitigación de riesgos éticos

**Pide:** estrategias para sesgos algorítmicos, privacidad y seguridad.

**Hecho.**
- **Seguridad.** El texto de un paper es dato, nunca instrucción (regla 13): los prompts lo tratan
  así y ninguna cita vale si no resuelve a un fragmento real del corpus. Las claves viven en `.env`
  y fuera de Git (regla 5).
- **Sesgo.** El criterio de inclusión del corpus está declarado en [docs/corpus.md](docs/corpus.md).
  La respuesta correcta sale del corpus, no del mundo (regla 3), y el juez es de otro proveedor que
  el respondedor para evitar la autopreferencia (decisión 0003).
- **Privacidad y uso responsable.** El corpus es público y sin datos personales. Se respetan
  `robots.txt`, los términos de uso y el ritmo de peticiones (regla 8), y no se versionan textos de
  arXiv.

**Falta.** No hay una prueba con documentos hechos para atacar al agente ni con fuentes de baja
calidad. Opción acotada: probar con 2 o 3 frases de inyección sembradas en un paper de desarrollo y
reportar si el agente las ignora (costo estimado de centavos). Si no se hace, se declara como
limitación.

**Fuera de alcance.** El brazo con modelo local y la medición de eficacia de la revisión humana.

### Cr8 — Documentación de la solución

**Pide:** que la solución esté documentada y pueda replicarse.

**Hecho.** [README](README.md) con el diseño, las decisiones y cómo reproducir de principio a fin;
[AGENTS.md](AGENTS.md) y [CONSTITUTION.md](CONSTITUTION.md); cinco [decisiones de
diseño](docs/decisiones/) con su justificación; contratos en [specs/](specs/); cambios guiados por
OpenSpec con propuesta, tareas y verificación; bitácora y nota de traspaso de datos; licencia MIT
([LICENSE](LICENSE)); y el historial de commits semánticos como evidencia del trabajo. Los textos
de arXiv se regeneran con los comandos del README.

**Falta.** Confirmar que el repositorio es público antes de la entrega.

## R.7.1 — Gestión y preparación de datos para el despliegue

### Cr1 — Preprocesamiento

**Pide:** limpieza, transformación y validación dentro del flujo.

**Hecho.** El corpus de 50 papers pasa por tres capas: *Bronze* (HTML crudo e inmutable, con huella
SHA-256 de la descarga), *Silver* (texto útil) y *Gold* (Markdown con encabezado de metadatos, versión
del preprint y huella de contenido). Cada párrafo, tabla, ecuación o pie de figura recibe un
identificador citable (`span_id`) con su huella ([docs/corpus.md](docs/corpus.md),
[specs/formato-gold.md](specs/formato-gold.md)). El banco de preguntas se valida con
`wikillm.eval validar-banco` (60 preguntas, 0 problemas). Todo esto ocurre **antes** de cualquier
llamada de pago al modelo.

### Cr2 — Selección y dominio técnico

**Pide:** herramientas pertinentes, usadas correctamente.

**Hecho.** Python 3.12 con uv; ruff y pytest para calidad y regresiones (215 archivos formateados y
la suite de pruebas pasa sin llamar a la API real, regla 7); LangChain con embeddings
`bge-small-en-v1.5` en GPU y Qdrant en modo local para el RAG
([decisión 0005](docs/decisiones/0005-qdrant-como-base-vectorial.md)); la API de arXiv para metadatos;
Git con una copia versionada del wiki por paso de ingesta; OpenSpec para especificar antes de
codificar; y un panel web local para observar los dos sistemas.

### Cr3 — Automatización e integración del pipeline

**Pide:** un pipeline que automatice la entrada de datos y se integre con el modelo.

**Hecho.** El pipeline es modular y cada paso es un comando que se puede repetir por separado:

```
wikillm.corpus candidatos → seleccionar → manifest → spans   (qué papers y qué fragmentos)
wikillm.ingest                                               (Bronze → Silver → Gold)
wikillm.rag indexar                                          (fragmentos → vectores → Qdrant)
wikillm.wiki ingerir                                         (plan + escritura + validación)
wikillm.arnes correr                                         (ingesta por pasos + preguntas)
wikillm.eval metricas                                        (correctitud, citas, costo)
```

Los dos sistemas leen el mismo Gold y el mismo manifiesto (`orden_ingesta`), lo que mantiene una
sola variable entre ellos.

## R.7.2 — Automatización del despliegue (MLOps)

### Cr4 — Automatización del despliegue

**Pide:** scripts, orquestación y monitorización.

**Hecho.** Todo se ejecuta con scripts reproducibles. El arnés (`wikillm.arnes correr`) orquesta la
ingesta por pasos y las preguntas, imprime antes su estimación de costo y respeta un tope de gasto
por corrida. El panel local muestra en vivo las llamadas, los costos y las citas.

**Fuera de alcance.** Ejecución por calendario y avisos automáticos cuando una métrica se degrada;
el [cronograma](cronograma.md) ya preveía ejecutar con disparo manual y documentarlo como limitación.

**Falta (opcional).** Un flujo de integración continua que ejecute ruff y pytest en cada cambio; hoy
esas comprobaciones se ejecutan a mano antes de cerrar un cambio.

### Cr5 — Escalabilidad y robustez

**Pide:** soportar crecimiento y resistir fallos.

**Hecho.** `ClienteModelo` reintenta con espera creciente ante errores transitorios y falla con un
error claro al llegar al tope de gasto. El arnés es **reanudable**: repetir el comando con el mismo
nombre salta lo que ya consta, y comprueba que el wiki contenga exactamente los N primeros papers
antes de preguntar en el paso N.

**Con la corrida.** El tiempo y el costo por paso a medida que el corpus crece de 0 a 50 papers, para
los dos sistemas.

### Cr6 — Prácticas MLOps

**Pide:** versionado, logging, actualización y reentrenamiento.

**Hecho.** Versionado: el wiki vive en un repositorio Git propio con una etiqueta `paso-N` por paso, y
cada corrida guarda en `corrida.json` el commit, el modelo, la temperatura, los precios y la huella
del banco (regla 9). Logging: cada llamada al modelo deja una línea con tokens, tiempo y dólares
(`llamadas.jsonl`). Regresión: pytest. Equivalente del reentrenamiento: como el sistema no entrena
pesos, lo equivalente es la **recompilación** del wiki cuando entra un paper que actualiza a otro, y
las preguntas T4 miden justamente si cada sistema da el valor nuevo o se queda con el obsoleto.

## RA1 y RA2 — Comunicación escrita y oral

**Hecho.** Informe y anteproyecto en LaTeX ([docs/entrega](docs/entrega/)), estado del arte con
referencias verificadas, cronograma como diagrama de Gantt, guion y diapositivas de la demostración
([docs/presentacion](docs/presentacion/), [docs/demo.md](docs/demo.md)). La sustentación se organiza
sobre una idea: *compilar y mantener no es lo mismo que recuperar, y la diferencia se puede medir*.
La demostración muestra la misma pregunta a los dos sistemas antes y después de ingerir el paper que
la responde.

**Falta.** El capítulo de resultados, las cifras finales y la curva de equilibrio, que dependen de la
corrida. Para la defensa conviene tener preparadas tres preguntas previsibles: por qué no basta con
GraphRAG, qué pasa si el resultado favorece al RAG (cualquier resultado es válido y se reporta, como
dice la hipótesis) y por qué confiar en un sistema que usa IA para sintetizar literatura que puede
estar contaminada por IA (trazabilidad de citas verificadas contra el corpus).

## Resumen de lo que falta

| Pendiente | Criterio | Depende de |
|---|---|---|
| Alinear `definicion_problema.md` con el diseño final | R.6.1 Cr1 | Nada |
| Probar el juez sobre el piloto y calibrarlo | R.6.1 Cr4 | Clave de Gemini |
| Curva de punto de equilibrio en el informe | R.6.2 Cr6 | Corrida completa |
| Prueba de inyección o declararlo como limitación | R.6.2 Cr7 | Decisión del equipo |
| Confirmar que el repositorio es público | R.6.2 Cr8 | Equipo |
| Flujo de integración continua (opcional) | R.7.2 Cr4 | Nada |
| Capítulo de resultados y cifras finales | RA1, R.6.1 Cr4 | Corrida completa |
