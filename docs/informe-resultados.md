# Resultados, discusión y conclusiones (borrador para el informe)

Borrador del 18 de noviembre de 2026 para pasar a `docs/entrega/informe.tex`, que hoy conserva la estructura
del anteproyecto («Resultados esperados»). Cada cifra sale de una corrida guardada en `results/` o de un
documento de evaluación citado entre paréntesis; no se usó ninguna que no esté en el repositorio. Los
números y las tablas son definitivos; la redacción es un punto de partida para los autores.

## 1. Qué se comparó

Un **RAG simple** (búsqueda vectorial con `bge-small`, Qdrant, `k = 5`, una llamada al modelo) frente a un
**WikiLLM** (un agente que mantiene un wiki de páginas Markdown, 461 páginas con 100 papers, y lo consulta con
búsqueda y lectura, hasta 8 acciones). Los dos usan el **mismo modelo** (`deepseek-flash`, temperatura 0), el
mismo corpus (100 preprints de arXiv sobre memoria para agentes de IA) y las mismas **100 preguntas**
verificadas por los dos autores: 60 originales y 40 de borde (T1 a T5: hecho puntual, síntesis entre papers,
comparación o contradicción, actualización y no respondible). Se pregunta en tres cargas del corpus (33, 66 y 100 papers). La
correctitud la decide primero una capa determinista y, solo en lo dudoso, un juez de otro proveedor (Gemini);
una cita solo vale si resuelve a un fragmento real del corpus (corrida `ampliado-fases-1`).

## 2. Resultados

### 2.1 Correctitud: el wiki acierta más, pero depende del contexto del RAG

Cobertura = fracción de preguntas respondibles que el sistema contesta bien.

| Paso | Respondibles | RAG | Wiki | Diferencia (IC 95 %) | Solo RAG / solo wiki | p (McNemar) |
|--:|--:|--:|--:|---|--:|--:|
| 33 | 19 | 0,53 | 0,68 | +0,16 [−0,05, +0,42] | 1 / 4 | 0,38 |
| 66 | 51 | 0,47 | 0,61 | +0,14 [−0,02, +0,31] | 6 / 13 | 0,17 |
| **100** | **84** | **0,48** | **0,70** | **+0,23 [+0,11, +0,35]** | **7 / 26** | **0,001** |

Con el corpus completo, por tipo: T1 0,64 / 0,79 (RAG / wiki), T2 0,40 / 0,80 (p = 0,03), T3 0,22 / 0,56 y T4
0 / 0 (4 preguntas). Los dos sistemas se abstienen bien cuando el corpus no responde: abstención correcta de
1,00 al paso 100. Todas las respuestas que citan, citan fragmentos reales (fundamentación 1,00 en ambos).

### 2.2 Sensibilidad al número de fragmentos del RAG

La ventaja se reduce de forma continua al darle más contexto al RAG (`docs/sensibilidad-rag-y-deriva-del-wiki.md`).

| `k` del RAG | Diferencia al paso 100 (IC 95 %) | p | Tokens de entrada (300 respuestas) |
|--:|---|--:|--:|
| 5 | +0,23 [+0,11, +0,35] | 0,001 | 0,43 M |
| 10 | +0,15 [+0,05, +0,26] | 0,015 | 0,82 M |
| 15 | +0,11 [+0,01, +0,21] | 0,078 | 1,22 M |
| 20 | +0,06 [−0,05, +0,17] | 0,38 | 1,61 M |

El wiki usa 4,30 M de tokens de entrada en la misma corrida base.

### 2.3 Por qué falla cada sistema

(`results/ampliado-fases-1/fallos/`.) De 172 respuestas no correctas en 600: el RAG falla sobre todo por
**abstenerse cuando sí había respuesta** (62 de 94) y el wiki por
**no abstenerse o dar una fuente parcial** (46 de 78). La deriva se midió leyendo las copias `paso-N` del wiki:
**no pierde lo ya aprendido** (85,9 % de las líneas del paso 33 siguen idénticas en el 100; 97 % de las
cifras se conservan), pero **solo capta el 63 % al 80 % de lo respondible** al ingerir, y **no retira el valor
viejo** cuando llega uno nuevo (A016-T4-03 y A039-T4-03). El cuello de botella del wiki es la captura al
ingerir, no el olvido.

### 2.4 Costo y tiempo

(`docs/eficiencia-calidad-costo.md`.) Construir el wiki de 100 papers costó **1,6 a 2,9 USD y 1,8 h**, con un
costo por paper que crece de 0,008 a 0,020 USD a medida que el wiki crece; el RAG no tiene costo de ingesta.
En el paso 100, una consulta del wiki cuesta **7,2 veces** la del RAG (0,00096 frente a 0,00014 USD), tarda
**4,1 veces** más (6,1 frente a 1,5 s) y acierta 19 respuestas más de cada 100 (75 frente a 56). **No hay
punto de equilibrio en costo**: con 10.000 consultas el costo por respuesta correcta del wiki sigue siendo unas
6 veces el del RAG. Un tope de 4 acciones en lugar de 8 recortó el costo un 29 % y perdió 3 respuestas (72
frente a 75, no significativo).

### 2.5 Confiabilidad de la evaluación

Un segundo juez independiente del principal (Claude, a ciegas) revisó 115 respuestas: **acuerdo del 94,8 %,
kappa 0,893**, con discrepancias en ambos sentidos (`docs/evaluacion-auxiliar-ampliado-fases-1.md`). Detectó
dos debilidades menores del método: la capa determinista puede acreditar un número por coincidencia con otro
del texto, y el juez principal tiende a ser indulgente con omisiones parciales en preguntas de lista.

### 2.6 Alternativas probadas que no mejoraron los aciertos

Se probaron Graphify (grafo de títulos y enlaces, entidades con PageRank personalizado, hechos por entidad,
grafo semántico con LLM, citas entre papers) y tgrep (búsqueda por trigramas sobre las páginas), siguiendo
la sugerencia del tutor: **ningún grafo recupera mejor que el texto completo** (cobertura de la evidencia con 5
páginas: 0,38 el grafo, 0,67 el `search` actual, 0,80 el texto completo) y tgrep reduce llamadas y latencia sin
mejorar de forma significativa los aciertos (`docs/evaluacion-grafo-100-papers.md`,
`docs/informe-graphify-independiente.md`). Gasto total de estas pruebas: ≈ 1 USD.

### 2.7 Preguntas de varios saltos y citas entre papers

Sin cambiar ninguna pregunta, las 34 que exigen combinar dos o más papers (30 de ellas encadenadas por
citas) son las difíciles: el RAG con `k = 5` acierta el 26 % y el wiki el 56 % (62 % y 80 % en las de un solo
paper). La ventaja del wiki ahí es +0,29 con `k = 5` (p = 0,013) y **0,00 con `k = 20`**. Una herramienta
que le deja al agente seguir las citas entre papers **no se usó ni una vez** en 34 preguntas y no mejoró los
aciertos (`docs/preguntas-de-varios-saltos.md`).

### 2.8 Seguridad frente a texto malicioso

Se sembraron órdenes con un canario (anulación directa, suplantación del sistema, secuestro del agente) en los
documentos que ven el RAG, la consulta del wiki y la ingesta: **0 ataques logrados en 72 respuestas y 2
ingestas envenenadas** (`docs/prueba-de-inyeccion.md`). Límites: 6 preguntas, ataques sencillos y la página
ajena del wiki casi no se expuso.

## 3. Discusión

**Respuesta a la pregunta.** Con el mismo modelo, un wiki mantenido por un LLM **contesta mejor que un RAG
simple** cuando el corpus está completo (+0,23 de cobertura con `k = 5`), sobre todo en las preguntas que combinan
papers (T2) o los comparan (T3), pero **cuesta unas 7 veces más por consulta, tarda unas 4 veces más y no se
amortiza en dólares**. La mejora es de calidad, no de ahorro.

**Qué no dicen los resultados.**
- La ventaja **depende del contexto del RAG**: con 20 fragmentos, un contexto del tamaño del que usa el wiki,
  la diferencia (+0,06) deja de ser significativa. El resultado es robusto a la configuración fijada (`k = 5`)
  solo en parte.
- **No se probó la hipótesis de actualización.** Las preguntas T4 son 4 y ningún sistema las contestó bien;
  el análisis de deriva muestra que el wiki no retira el valor viejo, así que esa ventaja prevista no apareció.
- Es una sola corrida con temperatura 0, un solo modelo y un solo dominio.

**Amenazas a la validez.**
- *Sesgo de selección del orden de ingesta:* diez papers se movieron de carga mirando las preguntas (decisión
  0009), lo que puede favorecer a cualquiera de los dos en los pasos intermedios.
- *Preguntas de borde:* 40 de las 100 partieron de borradores generados por un modelo y fueron verificadas por
  los dos autores, sin kappa entre ellos; el segundo juez no es independiente para ese grupo (acuerdo 95,3 %,
  como el de las originales).
- *Jueces:* el principal y el segundo coinciden en el 94,8 %; el 5 % restante no sesga hacia un brazo.
- *Costos en dólares:* la caché de prefijos de DeepSeek distorsiona el costo entre corridas; por eso se
  comparan tokens y tiempos.
- *Cola de la distribución:* con 84 pares respondibles, las diferencias por tipo (T3, T4) tienen intervalos
  anchos.

**Decisión de negocio.** Compilar por adelantado conviene cuando el corpus es estable, se harán muchas
consultas y el valor de una respuesta correcta en comparaciones entre documentos justifica pagar unas 6 a 7
veces más por consulta (y 1,6 a 2,9 USD de construcción por cada 100 papers). Recuperar sin compilar conviene
cuando el presupuesto o la latencia mandan, el corpus cambia con frecuencia o hay pocas consultas; y antes de
adoptar el wiki conviene probar un RAG con más contexto, que cierra buena parte de la brecha.

## 4. Conclusiones

1. **El wiki gana en calidad y pierde en costo.** +0,23 de cobertura con el corpus completo frente a un RAG
   de 5 fragmentos, a 7,2 veces el costo y 4,1 veces el tiempo por consulta.
2. **La ventaja se reduce con el contexto del RAG** y deja de ser significativa con `k = 20`; el RAG simple,
   bien configurado, es un competidor fuerte y barato.
3. **El límite del wiki es la captura, no el olvido:** conserva lo que aprende (97 % de las cifras) pero capta
   del 63 % al 80 % de lo respondible y no retira valores obsoletos. Mejorar la ingesta es el trabajo futuro
   con más recorrido.
4. **Más herramientas no ayudaron:** ningún grafo supera a la búsqueda de texto completo, tgrep solo ahorra
   llamadas y el agente no usó una herramienta de citas entre papers ni una vez en las 34 preguntas de varios
   saltos. Los recortes de costo por tope de acciones son baratos pero pierden respuestas.
5. **El método es confiable y el sistema resiste inyecciones sencillas:** acuerdo de 94,8 % entre jueces y 0
   ataques logrados en la prueba de inyección, con los límites declarados.

**Trabajo futuro.** Ingesta que capte más y retire lo obsoleto; preguntas nuevas de varios saltos que obliguen
a encadenar citas; RAG híbrido (BM25 más vectores) como línea base aparte; más repeticiones y otros modelos.

## 5. Estrategia de comunicación (criterio F3 de la rúbrica)

| Audiencia | Qué necesita | Medio |
|---|---|---|
| Tutor y jurado | El método, las cifras con su incertidumbre y las decisiones | Informe (`docs/entrega/informe.tex`) y exposición |
| Quien decide una adopción | Cuándo conviene compilar y cuándo recuperar, y a qué costo | Párrafo de decisión del informe y un one-pager (`docs/presentacion/one-pager.html`) |
| Quien quiera reproducir | Cómo repetir cada cifra | Repositorio público, `README.md`, `AGENTS.md` y los documentos de `docs/` |

Mensaje único: *compilar y mantener no es lo mismo que recuperar; la diferencia se mide y se paga, y depende
del contexto que se le da al RAG*. En la exposición, una sola cifra por diapositiva (cobertura, costo por
consulta, sensibilidad a `k`), la demostración de la pregunta antes y después de ingerir el paper, y las
limitaciones dichas por nosotros antes de que las pregunten.
