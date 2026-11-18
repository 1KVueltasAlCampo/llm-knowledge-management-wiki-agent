# Entregable 3: Cumplimiento de la rúbrica

Estado al 17 de noviembre de 2026. Cada criterio dice lo que pide, lo que el proyecto **ya tiene** (con el
archivo donde se comprueba), lo que **falta** y lo que **quedó fuera del alcance**. Reemplaza a la versión del
10 de noviembre, que se escribió antes de ampliar el corpus a 100 papers y de correr el experimento. El
alcance real está en el [README](README.md#alcance-y-límites).

Leyenda: **Hecho** = existe y se puede comprobar hoy · **Falta** = trabajo pendiente · **Fuera de alcance** =
decidido y declarado.

## R.6.1: Modelos de IA generativa para nuevos productos

### Cr1: Formulación del problema

**Pide:** traducir el entorno empresarial en un problema abordable con IA generativa.

**Hecho.** El problema parte de una necesidad organizacional medida: el conocimiento está fragmentado, envejece
rápido y buscarlo consume jornada (Nakash y Bouhnik, 2024, en [definicion_problema.md](definicion_problema.md),
alineada con el diseño final el 17 de noviembre). El RAG que se usa para mitigarlo repite la síntesis en cada
consulta, mezcla documentos obsoletos con vigentes y no acumula nada. El proyecto lo estudia sobre literatura
abierta de IA porque es la versión más difícil del mismo problema y la única que se puede evaluar en público. La
pregunta de investigación y la hipótesis están en el [README](README.md#pregunta-de-investigación-e-hipótesis).

- **Decisión de negocio (18-nov).** Redactada en la discusión del borrador
  [docs/informe-resultados.md](docs/informe-resultados.md) (cuándo compilar y cuándo recuperar, con el costo
  y la sensibilidad al contexto del RAG). **Falta** pasarla al informe en LaTeX.

### Cr2: Elección del modelo

**Pide:** justificar la elección comparando alternativas, no solo nombrar un modelo.

**Hecho.** Se usa un modelo único, `deepseek-flash`, en los dos sistemas, porque el tutor pidió el mismo modelo
en ambos y recomendó este (y pidió no usar el Pro). La [decisión 0001](docs/decisiones/0001-modelo-unico-deepseek-flash.md)
compara las alternativas (DeepSeek Pro, Gemini, modelos comerciales grandes, modelo local) con criterios
explícitos: contexto, formato de salida, costo con caché y saldo. La
[decisión 0003](docs/decisiones/0003-roles-de-modelos-en-la-evaluacion.md) separa los roles (responde, redacta,
juzga) para que ningún modelo se evalúe a sí mismo.

**Límite declarado.** El experimento mide arquitecturas con un modelo, no modelos.

### Cr3: Integración del modelo

**Pide:** adaptar el modelo al caso, de forma funcional y escalable.

**Hecho.** El modelo es el motor de dos sistemas que comparten cliente, reglas de respuesta y citas. En el
WikiLLM, la ingesta son dos llamadas por paper (plan y escritura) cuya salida valida el código: descarta las
citas que no resuelven a un fragmento de un paper ya ingerido, deja como texto los enlaces sin destino y cuenta
las afirmaciones numéricas sin cita (`src/wikillm/wiki/ingesta.py`). El conocimiento de los 100 papers se
construyó aparte (461 páginas, 11.662 citas válidas, unos 1,60 USD) y las corridas lo reutilizan (`--wiki-de`);
el arnés puede correr solo los brazos que se pidan (`--brazos`). La consulta es un agente con herramientas de
búsqueda y lectura y un tope de acciones.

**Hecho (opcional).** Graphify y tgrep se integraron como capa opcional (`src/wikillm/wiki/capas.py`, brazo
`wiki_grafo`) y se evaluaron a fondo: no mejoran los aciertos
([docs/evaluacion-grafo-100-papers.md](docs/evaluacion-grafo-100-papers.md)). La capa queda apagada. Las
citas entre papers como aristas (idea del tutor) se probaron también en las 34 preguntas de varios papers: el
agente no usó la herramienta ni una vez ([docs/preguntas-de-varios-saltos.md](docs/preguntas-de-varios-saltos.md)).

**Fuera de alcance.** La aprobación humana de los cambios del wiki antes de escribirlos.

### Cr4: Interpretar la evaluación del desempeño

**Pide:** aplicar métricas adecuadas e interpretarlas frente a los objetivos.

**Hecho.** Las métricas están implementadas y probadas (`src/wikillm/eval/`): correctitud (capa determinista y,
solo para lo indeterminado, un juez de otro proveedor), fundamentación de las citas, cobertura, abstención,
respuestas obsoletas, contexto, costo y tiempo, con comparación pareada (intervalos y prueba de McNemar) y
análisis de fallos. Se evalúan contra un banco de **100 preguntas** fijadas por los dos autores y verificadas
por ambos contra los papers (el kappa solo existe para las 60 originales; para las 40 de borde no se calculó). La corrida base `ampliado-fases-1` ya está hecha: con `k = 5`, el wiki acierta el
0,70 frente al 0,48 del RAG al paso 100 (diferencia +0,23, IC 95 % [+0,11, +0,35], p = 0,001). El análisis de
sensibilidad muestra que con `k = 20` la diferencia baja a +0,06 y deja de ser significativa
([docs/sensibilidad-rag-y-deriva-del-wiki.md](docs/sensibilidad-rag-y-deriva-del-wiki.md)).

**Hecho (segundo juez).** La evaluación auxiliar sobre `ampliado-fases-1` ya está hecha: 115 respuestas a ciegas,
acuerdo de 94,8 % con el juez principal (kappa 0,893), con las discrepancias y los límites declarados
([docs/evaluacion-auxiliar-ampliado-fases-1.md](docs/evaluacion-auxiliar-ampliado-fases-1.md)).

**Falta.** Escribir la interpretación crítica en el informe (qué dicen los resultados, qué no, y los límites:
una corrida por celda, orden de ingesta diseñado con las preguntas a la vista).

## R.6.2: Automatizar tareas con IA generativa

### Cr5: Selección de tareas automatizables

**Pide:** identificar procesos donde la automatización aporta valor real.

**Hecho.** Se automatiza la síntesis y la reconciliación documental, que es repetitiva y costosa: el WikiLLM
integra cada fuente nueva en páginas existentes en lugar de rehacer la síntesis en cada consulta
([definición del problema](definicion_problema.md)).

**Fuera de alcance.** La revisión humana periódica del wiki (*lint*) y la aprobación de cambios.

### Cr6: Eficiencia lograda

**Pide:** demostrar que la solución mejora el proceso, con cifras.

**Hecho.** Todo costo se registra (regla 6). Construir el conocimiento cuesta unos 1,60 USD; con `k = 5`, una
respuesta del wiki cuesta unas cinco veces la del RAG (≈ 0,0010 frente a ≈ 0,00018 USD) y usa unos 4.800
tokens de contexto frente a 1.300. **No existe un punto de equilibrio en dólares**: compilar por adelantado no
se compensa en costo. Lo que el experimento muestra es una mejora de **calidad** (+0,23 de cobertura con
`k = 5`), que se reduce cuando el RAG recibe un contexto como el del wiki. También se midió que el wiki casi no
olvida lo aprendido (97 % a 99 % de las cifras se conservan entre cargas) pero no capta todo al ingerir.

- **Calidad frente a costo (18-nov).** [docs/eficiencia-calidad-costo.md](docs/eficiencia-calidad-costo.md)
  une la construcción (1,6 a 2,9 USD y 1,8 h), el costo y el tiempo por consulta y por respuesta correcta, y
  escenarios de 100 a 10.000 consultas: en el paso 100 el wiki acierta 19 respuestas más de cada 100 a 7,2 veces
  el costo por consulta (unas 6 veces por respuesta correcta con 10.000 consultas). Un experimento de 0,068 USD
  con tope de 4 acciones recortó el costo un 29 % y perdió 3 respuestas (no significativo).

**Falta.** Solo llevarlo al informe sin sugerir un ahorro que no existe.

### Cr7: Mitigación de riesgos éticos

**Pide:** estrategias para sesgos algorítmicos, privacidad y seguridad.

**Hecho.**
- **Seguridad.** El texto de un paper es dato, nunca instrucción (regla 13): los prompts lo tratan así y
  ninguna cita vale si no resuelve a un fragmento real del corpus. Las claves viven en `.env` y fuera de Git
  (regla 5).
- **Sesgo.** El criterio de inclusión del corpus está declarado ([docs/corpus.md](docs/corpus.md)). La
  respuesta correcta sale del corpus, no del mundo (regla 3), y el juez es de otro proveedor que el
  respondedor (decisión 0003). Las 100 preguntas fueron verificadas por los dos autores como personas; las 40
  de borde partieron de borradores generados con ayuda de un modelo.
- **Privacidad y uso responsable.** El corpus es público y sin datos personales. Se respetan `robots.txt`, los
  términos de uso y el ritmo de peticiones (regla 8), y no se versionan textos de arXiv.

- **Inyección de instrucciones (18-nov).** Se sembraron tres ataques con canario (anulación directa,
  suplantación del sistema, secuestro del agente) en el RAG, en la consulta del wiki y en la ingesta de dos
  papers envenenados: 0 ataques logrados en 72 respuestas y 2 ingestas, por 0,03 USD
  ([docs/prueba-de-inyeccion.md](docs/prueba-de-inyeccion.md)). Límites declarados allí: 6 preguntas, ataques
  sencillos y el wiki «en otra página» casi no se expuso.

**Falta.** En el informe hay que declarar el sesgo de selección del orden de ingesta (diez papers
se movieron de carga mirando las preguntas, decisión 0009).

**Fuera de alcance.** El brazo con modelo local y la medición de eficacia de la revisión humana.

### Cr8: Documentación de la solución

**Pide:** que la solución esté documentada y pueda replicarse.

**Hecho.** [README](README.md) con el diseño, el estado y cómo reproducir de principio a fin (incluido el flujo
de 100 papers); [AGENTS.md](AGENTS.md) y [CONSTITUTION.md](CONSTITUTION.md); diez
[decisiones de diseño](docs/decisiones/); contratos en [specs/](specs/); cambios guiados por OpenSpec con
propuesta, tareas y verificación; bitácora y nota de traspaso de datos; tres documentos de evaluación de las
herramientas y de sensibilidad; scripts de análisis reproducibles; licencia MIT ([LICENSE](LICENSE)); y el
historial de commits semánticos como evidencia del trabajo.

**Hecho.** El repositorio es público (confirmado el 17 de noviembre).

## R.7.1: Gestión y preparación de datos para el despliegue

### Cr1: Preprocesamiento

**Pide:** limpieza, transformación y validación dentro del flujo.

**Hecho.** Los 100 papers pasan por tres capas: *Bronze* (HTML crudo e inmutable, con huella SHA-256), *Silver*
(texto útil) y *Gold* (Markdown con metadatos, versión del preprint y huella). Cada párrafo, tabla, ecuación o
pie de figura recibe un identificador citable (`span_id`) con su huella ([docs/corpus.md](docs/corpus.md),
[specs/formato-gold.md](specs/formato-gold.md)). Se corrigió el conversor, que perdía 14 tablas de 4 papers que
LaTeXML dibuja con `<span>`, con prueba. El banco se valida con `wikillm.eval validar-banco` (100 preguntas, 138
evidencias que resuelven a un fragmento con la misma huella). Todo ocurre **antes** de cualquier llamada de pago.

### Cr2: Selección y dominio técnico

**Pide:** herramientas pertinentes, usadas correctamente.

**Hecho.** Python 3.12 con uv; ruff y pytest para calidad y regresiones (la suite no llama a la API real,
regla 7); LangChain con embeddings `bge-small-en-v1.5` en GPU y Qdrant local para el RAG
([decisión 0005](docs/decisiones/0005-qdrant-como-base-vectorial.md)); la API de arXiv para metadatos; Git con
una copia versionada del wiki por paso de ingesta; OpenSpec para especificar antes de codificar; y un panel
web local para observar los dos sistemas. Graphify y tgrep se evaluaron con criterio y se dejaron como capa
opcional.

### Cr3: Automatización e integración del pipeline

**Pide:** un pipeline que automatice la entrada de datos y se integre con el modelo.

**Hecho.** El pipeline es modular y cada paso es un comando que se puede repetir por separado:

```
wikillm.corpus candidatos → seleccionar → manifest → fases → spans   (qué papers, en qué cargas y qué fragmentos)
wikillm.ingest                                                       (Bronze → Silver → Gold)
wikillm.eval ampliar-banco                                           (banco de 100 con evidencia anclada)
wikillm.wiki ingerir                                                 (plan + escritura + validación)
wikillm.arnes correr [--wiki-de] [--brazos]                          (preguntas por pasos con costo controlado)
wikillm.eval metricas → informe → fallos → comparar-corridas         (correctitud, citas, costo, comparación)
```

Los dos sistemas leen el mismo Gold y el mismo manifiesto (`orden_ingesta`), lo que mantiene una sola variable
entre ellos.

## R.7.2: Automatización del despliegue (MLOps)

### Cr4: Automatización del despliegue

**Pide:** scripts, orquestación y monitorización.

**Hecho.** Todo se ejecuta con scripts reproducibles. El arnés imprime antes su estimación de costo, respeta un
tope de gasto por corrida y avisa de la hora pico del proveedor. El panel local muestra en vivo las llamadas,
los costos y las citas.

**Hecho.** Flujo de integración continua en `.github/workflows/ci.yml`: en cada push a `main` y en cada Pull
Request ejecuta `ruff check`, `ruff format --check` y `pytest`, sin claves ni PyTorch (las pruebas no los
usan). Se comprobó que la suite pasa en una copia solo con los archivos versionados, sin red ni caché de
modelos. Queda pendiente su primera ejecución en GitHub.

**Fuera de alcance.** Ejecución por calendario y avisos automáticos cuando una métrica se degrada: el
[cronograma](cronograma.md) preveía disparo manual y documentarlo como limitación.

### Cr5: Escalabilidad y robustez

**Pide:** soportar crecimiento y resistir fallos.

**Hecho.** `ClienteModelo` reintenta con espera creciente ante errores transitorios y falla con un error claro
al llegar al tope de gasto. El arnés es **reanudable**: repetir el comando con el mismo nombre salta lo que ya
consta y comprueba que el wiki contenga exactamente los N primeros papers. Se ejerció en las corridas reales,
con cortes de red que se reanudaron sin perder datos. El corpus creció de 50 a 100 papers sin cambiar el
código.

- **Costo y tiempo por paso (18-nov).** Las curvas de ingesta de 0 a 100 papers están en
  `results/costo-calidad/` (`ingesta_usd_acumulado.svg`, `ingesta_minutos_acumulados.svg`) y se explican en
  [docs/eficiencia-calidad-costo.md](docs/eficiencia-calidad-costo.md).

### Cr6: Prácticas MLOps

**Pide:** versionado, logging, actualización y reentrenamiento.

**Hecho.** Versionado: el wiki vive en un repositorio Git propio con una etiqueta `paso-N` por paso, y cada
corrida guarda en `corrida.json` el commit, el modelo, la temperatura, los precios y la huella del banco
(regla 9). Logging: cada llamada al modelo deja una línea con tokens, tiempo y dólares (`llamadas.jsonl`).
Regresión: pytest. Equivalente del reentrenamiento: como el sistema no entrena pesos, lo equivalente es la
**actualización** del wiki cuando entra un paper que cambia un dato; las preguntas T4 y el análisis de deriva
miden si cada sistema da el valor nuevo: el wiki conserva lo aprendido, pero no retira el valor viejo cuando
llega el nuevo.

## RA1: Comunicación escrita

**Hecho.** Informe y anteproyecto en LaTeX ([docs/entrega](docs/entrega/)), estado del arte con referencias
verificadas, cronograma como diagrama de Gantt, y los documentos de evaluación con tablas.

**Borrador hecho (18-nov).** [docs/informe-resultados.md](docs/informe-resultados.md) trae Resultados,
Discusión, Conclusiones y la estrategia de comunicación, con las cifras de las corridas guardadas y el
mensaje: *compilar y mantener no es lo mismo que recuperar, y la diferencia se mide, pero depende del
contexto que se da al RAG*.

**Falta (es el mayor pendiente).**
- **F1, F2, F3 y F4:** pasar ese borrador a `docs/entrega/informe.tex` (que sigue con «Resultados
  esperados»), recompilar el PDF (no hay LaTeX en el equipo de desarrollo) y revisar la redacción de los
  autores.
- **F5, gramática y referencias:** revisión de redacción, tablas y figuras con el estilo pedido por el curso.

## RA2: Comunicación oral (exposición el 20 de noviembre)

**Hecho.** Guion y diapositivas de la demostración ([docs/presentacion](docs/presentacion/),
[docs/demo.md](docs/demo.md)): la misma pregunta a los dos sistemas antes y después de ingerir el paper que la
responde.

**Falta.**
- Actualizar el guion y las diapositivas con las cifras finales (hoy citan 5 de 50 papers y 60 preguntas).
- Ensayar con tiempos y cuidar muletillas, voz y recursos de apoyo (F4 a F6).
- Preparar la defensa (F7) con las preguntas previsibles: por qué `k = 5` y qué pasa con `k = 20`; por qué
  Graphify y tgrep no mejoran los aciertos; qué implica que el orden de ingesta se diseñó mirando las
  preguntas; por qué el wiki cuesta más y qué se gana; por qué confiar en un sistema que usa IA para
  sintetizar literatura posiblemente contaminada por IA (trazabilidad de citas verificadas).

## Resumen de lo que falta

| Pendiente | Criterio | Fecha límite |
|---|---|---|
| Actualizar guion y diapositivas con las cifras finales y ensayar | RA2 | 20 de nov |
| Pasar el borrador de resultados, discusión y conclusiones al informe en LaTeX y recompilarlo | RA1, R.6.1 Cr4 | 27 de nov |
| Primera ejecución de la integración continua en GitHub (el flujo ya está escrito) | R.7.2 Cr4 | al subir |
