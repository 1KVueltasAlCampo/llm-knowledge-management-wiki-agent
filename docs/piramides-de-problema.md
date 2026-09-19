# Cinco pirámides de problema, puestas a prueba

Cinco formulaciones de problema, cada una construida en cuatro niveles —contexto
macro, soluciones actuales y sus fallas, el punto ciego específico, y la brecha a
resolver—. Cada nivel se somete a la misma prueba: un lector estricto y difícil de
convencer objeta que el punto ya está resuelto con algo que ya existe, y se responde
por qué esa solución existente no cierra el problema. Si una idea no sobrevive esta
prueba en los cuatro niveles, no está lista para presentarse como problema de
investigación.

---

## 1. Memoria institucional de una biblioteca de posgrado en IA

### Nivel 1 — Contexto global

Los programas de maestría en inteligencia artificial generan, cada semestre, decenas
de tesis y trabajos de grado que citan cientos de artículos de arXiv. Ese conocimiento
—qué se ha investigado ya, qué preguntas quedaron abiertas, qué cohorte trabajó qué
tema y con qué resultado— no se acumula institucionalmente: vive disperso en PDFs
entregados a una plataforma de gestión académica, en carpetas de cada estudiante, y en
la memoria de los profesores que dirigieron esos trabajos. Cuando llega una cohorte
nueva, empieza casi desde cero, sin visibilidad de lo que ya se intentó ni de qué
papers de referencia ya están agotados dentro del programa.

> **Objeción:** "Eso ya lo resuelve un gestor bibliográfico como Zotero o Mendeley con
> etiquetas compartidas, o un repositorio institucional tipo DSpace. Las universidades
> llevan veinte años indexando tesis; no hay problema aquí, solo falta que usen la
> herramienta que ya existe."

**Por qué sigue en pie:** un gestor bibliográfico resuelve el almacenamiento y la
búsqueda por metadatos —autor, año, palabra clave—, no la síntesis. Zotero no le dice a
un estudiante nuevo que tres trabajos de cohortes anteriores atacaron el mismo problema
desde ángulos distintos, y que el segundo contradijo la conclusión del primero. Esa
conexión exige leer y sintetizar, no catalogar; es exactamente la operación que ningún
sistema de indexación resuelve, porque no fue diseñado para eso, sino para encontrar un
documento, no para acumular conocimiento sobre las relaciones entre documentos.

### Nivel 2 — Soluciones actuales y sus fallas

Las respuestas actuales son dos: catálogos y repositorios que indexan por metadatos, y
sistemas RAG genéricos montados sobre el conjunto de PDFs de la biblioteca, que
responden preguntas recuperando fragmentos por similitud semántica. La primera no
sintetiza nada: devuelve una lista de documentos, y leer, comparar y concluir sigue
siendo enteramente humano. La segunda falla de forma más sutil: recupera fragmentos
parecidos a la pregunta sin distinguir si vienen de un trabajo de cinco cohortes atrás,
cuyo enfoque ya fue superado, o de la tesis del semestre pasado que lo corrigió — la
similitud por coseno no sabe de vigencia.

> **Objeción:** "Eso se arregla con un filtro de fecha en el RAG, o agregando el año de
> publicación al prompt de recuperación. Es trivial, cualquier ingeniero lo resuelve en
> una tarde."

**Por qué sigue en pie:** filtrar por fecha asume que lo más reciente es lo más
correcto, lo cual no siempre es cierto —una tesis reciente puede repetir un error que
otra ya corrigió antes—, y, más importante, un filtro de fecha no captura que el
documento B superó al documento A: solo sabe que B es más nuevo, no que ambos tratan la
misma pregunta y llegan a conclusiones distintas. Detectar esa relación exige comparar
contenido, no fecha, y eso ningún filtro de metadatos lo hace.

### Nivel 3 — El punto ciego

Ni los sistemas de vinculación de entidades ni los WikiLLM aplicados hasta ahora se han
probado sobre un corpus institucional cerrado, curado y de producción propia y
verificable como el de una maestría: los sistemas que anclan sus respuestas a una base
de conocimiento ya estructurada lo hacen sobre Wikidata y Wikipedia, bases públicas de
escala masiva mantenidas por miles de editores anónimos. Ningún trabajo revisado
aplica el patrón a un corpus pequeño —decenas o cientos de documentos, no millones—, de
producción propia, donde la verdad sobre qué trabajo superó a cuál puede confirmarse
preguntándole al profesor que dirigió ambos. Es un régimen de datos distinto —pequeño,
cerrado, con procedencia total y verificable— que ningún trabajo caracteriza.

> **Objeción:** "Un corpus pequeño no necesita nada sofisticado. Con cien documentos,
> cualquier persona los lee en un fin de semana. El problema desaparece con la escala."

**Por qué sigue en pie:** el problema no es de escala de lectura sino de escala de
mantenimiento continuo: no son cien documentos estáticos, son cien documentos que
crecen en veinte o treinta cada semestre, indefinidamente. La pregunta no es si alguien
puede leerlos todos una vez, sino si alguien va a releer los doscientos anteriores cada
vez que llega uno nuevo, para actualizar las conexiones — eso es exactamente lo que
ningún humano hace en la práctica, y es la razón de ser original del patrón: no es el
volumen lo que agota a quien mantiene una wiki, es la contabilidad repetida.

### Nivel 4 — La brecha

Falta una base de conocimiento mantenida por un LLM, anclada al corpus cerrado de una
maestría, que compile cada tesis y cada paper de referencia como una página enlazada,
marcando explícitamente cuándo un trabajo nuevo confirma, extiende o contradice a uno
anterior, con procedencia trazable a la cohorte y al director que lo respaldó — de
forma que un estudiante nuevo, o un profesor evaluando una propuesta, pueda consultar
en minutos qué ya se intentó y con qué resultado.

> **Objeción:** "Eso sigue siendo, en el fondo, un RAG con mejor metadata. No es un
> problema de investigación, es ingeniería de datos aplicada."

**Por qué sigue en pie:** la distinción no está en el nombre, sino en qué se mide: la
pregunta no es "constrúyanlo", es "¿el conocimiento compilado así se mantiene fiel a
sus fuentes y sigue siendo útil después de veinte actualizaciones sucesivas, o se
degrada como cualquier documentación humana abandonada?" — esa pregunta sobre la
trayectoria en el tiempo de un corpus mantenido, con una institución real como banco de
pruebas, es exactamente lo que la literatura revisada no mide en ningún caso.

---

## 2. Documentación técnica de un equipo de ingeniería de software

### Nivel 1 — Contexto global

En equipos de ingeniería que ya delegan buena parte de la escritura de código a
agentes basados en modelos de lenguaje, el cuello de botella se desplaza de "escribir
código" a "escribir y mantener la documentación que le permite a ese agente entender el
sistema" — decisiones de arquitectura, convenciones, por qué se descartó tal enfoque.
Esa documentación se acumula en herramientas como Confluence o Notion, wikis internas
que crecen sin que nadie tenga la responsabilidad explícita de retirar lo que dejó de
ser cierto.

> **Objeción:** "Eso ya lo resuelve cualquier wiki corporativa con control de
> versiones, o simplemente archivando las páginas viejas. Confluence tiene historial de
> cambios desde hace quince años."

**Por qué sigue en pie:** tener historial de versiones no es lo mismo que saber cuál
versión es la vigente sin leerlas todas. Un historial registra que una página cambió,
pero no le dice a un agente que consulta la wiki cuál de las cinco versiones anteriores
sigue siendo relevante, ni marca activamente una página como obsoleta cuando una
decisión posterior la contradice en otro lugar — eso exige que alguien, humano o
automático, revise activamente las conexiones entre páginas, que es justo lo que ningún
historial de versiones hace por sí solo.

### Nivel 2 — Soluciones actuales y sus fallas

La respuesta habitual —un sistema RAG apuntado al repositorio completo de
documentación de la empresa— falla de una manera concreta y ya documentada: recupera
fragmentos por similitud semántica sin ningún criterio de vigencia. Una decisión de
arquitectura de hace varios años, ya superada, puede tener una redacción más clara o
más extensa que la nota reciente que la reemplazó, y termina siendo la que el sistema
recupera y presenta con la misma confianza que si estuviera vigente.

> **Objeción:** "Basta con pedirle al modelo que priorice los documentos más recientes
> en el prompt, o con reindexar solo los últimos seis meses. Es una línea de
> configuración, no un problema de investigación."

**Por qué sigue en pie:** restringir la ventana temporal descarta decisiones antiguas
que pueden seguir siendo válidas —no todo lo viejo está superado— y no resuelve el caso
más dañino: dos documentos vigentes y recientes que se contradicen entre sí porque dos
personas documentaron el mismo sistema desde ángulos distintos sin coordinarse. Un
filtro de fecha no detecta eso, porque ambos documentos lo pasan igual.

### Nivel 3 — El punto ciego

La literatura sobre procedencia y confiabilidad de la información —formatos abiertos
de representación de conocimiento, principios de gestión de datos científicos, sistemas
de memoria que reconcilian hechos automáticamente— define con precisión los campos de
metadata que harían esto posible: quién escribió, cuándo, si fue verificado, si sigue
vigente. Pero ninguno de esos trabajos se ha aplicado ni evaluado sobre documentación
técnica real de un equipo de ingeniería: todos se prueban sobre datos científicos
públicos, conversaciones sintéticas o texto narrativo, nunca sobre el tipo de documento
—decisiones de arquitectura, runbooks, especificaciones— que motivó ese vocabulario de
metadatos en primer lugar.

> **Objeción:** "Si el vocabulario de campos ya existe, aplicarlo a documentación de
> ingeniería es trivial. Es copiar y pegar un esquema, no investigación."

**Por qué sigue en pie:** que el vocabulario exista no significa que se sepa qué
política de mantenimiento logra que esos campos se llenen correctamente con el tiempo.
La pregunta abierta no es si un campo de "verificado" o "vigente hasta" es válido como
esquema; es si un agente que ingiere documentación técnica real —con su jerga, sus
referencias cruzadas entre sistemas, sus decisiones que se revierten y se vuelven a
tomar— logra poblar esos campos de forma consistente y útil. Esa es una pregunta
empírica sin respuesta en la literatura, no una decisión de esquema.

### Nivel 4 — La brecha

Falta un WikiLLM que mantenga la documentación técnica de un equipo real, con marcado
explícito de vigencia y procedencia por afirmación, y una medición concreta de cuánta
información obsoleta deja de recuperarse frente a un RAG estándar apuntado al mismo
conjunto de documentos — no solo construir el sistema, sino cuantificar si de verdad
reduce el problema que motivó construirlo.

> **Objeción:** "Eso sigue siendo comparar dos sistemas de recuperación con distinta
> cantidad de metadata. No hay pregunta de investigación nueva, solo una evaluación de
> ingeniería."

**Por qué sigue en pie:** la pregunta de investigación no es cuál sistema recupera
mejor en un instante dado —eso sí sería solo ingeniería—, sino qué política de
mantenimiento (con qué frecuencia se revisa la wiki, cuánta intervención humana hace
falta, cómo se detecta que algo quedó obsoleto) logra que esa ventaja se sostenga a
medida que la documentación crece durante meses. Esa dimensión temporal es la que
ninguna comparación de una sola vez captura, y es el vacío exacto que ni los sistemas de
recuperación basados en grafos ni los de memoria de agentes evaluados hasta ahora
miden.

---

## 3. Perfiles de comprador acumulados para el sector inmobiliario

### Nivel 1 — Contexto global

Las plataformas y agencias inmobiliarias registran, en cada búsqueda, señales sobre lo
que un comprador realmente quiere —zona, presupuesto, tipo de propiedad, qué descarta
después de ver las primeras opciones— pero ese conocimiento se pierde consulta a
consulta: cada búsqueda nueva se procesa de forma aislada, sin acumular un entendimiento
cada vez más fino de qué distingue a un tipo de comprador de otro.

> **Objeción:** "Eso lo resuelve cualquier CRM con segmentación de clientes, o un
> modelo de *clustering* sobre las búsquedas. Es un problema de analítica de datos
> estándar, resuelto hace veinte años."

**Por qué sigue en pie:** un *clustering* agrupa números —rangos de presupuesto, zonas,
metros cuadrados— en segmentos estadísticos, pero no explica en lenguaje natural por
qué ese segmento se comporta así, ni lo conecta con el contexto que lo originó —una
nueva línea de transporte público que cambió la demanda de una zona, por ejemplo—.
Produce una etiqueta, no una página de conocimiento legible y conectada con las demás
observaciones, que es lo que un agente de ventas necesita para entender al comprador,
no solo para clasificarlo.

### Nivel 2 — Soluciones actuales y sus fallas

Los *dashboards* de analítica y los CRM con segmentación automática son la respuesta
estándar de la industria: agregan volumen de búsquedas por variable y generan reportes
numéricos, pero no producen conocimiento consultable en lenguaje natural que se
actualice explicando qué cambió y por qué desde el último reporte.

> **Objeción:** "Basta con pedirle a un modelo de lenguaje que redacte el reporte del
> CRM en prosa. El dato ya existe, solo falta un paso de generación de texto encima."

**Por qué sigue en pie:** redactar un reporte en prosa a partir de los mismos números
agregados no resuelve el problema de fondo: la información sigue sin acumularse entre
reportes, cada redacción parte otra vez de los datos crudos del período, sin memoria de
qué se dijo el mes anterior ni de si ese patrón se confirmó, se revirtió o fue una
anomalía pasajera. Generar texto no es lo mismo que compilar conocimiento que se
corrige y se actualiza con el tiempo.

### Nivel 3 — El punto ciego

Ningún trabajo revisado sobre bases de conocimiento mantenidas por modelos de lenguaje
se ha aplicado a un dominio de comportamiento de mercado en evolución continua, donde
la "entidad" no es una persona ni un concepto fijo sino un perfil estadístico que
cambia de forma con el tiempo. Los precedentes de anclaje a una base estructurada o de
recuperación por preguntas generadas se han probado sobre conocimiento enciclopédico
relativamente estable, no sobre un dominio donde la verdad de ayer puede dejar de serlo
la semana siguiente por una razón externa al corpus mismo.

> **Objeción:** "Eso es simplemente un modelo de series de tiempo con más pasos. La
> literatura de detección de tendencias ya resuelve la volatilidad de los datos."

**Por qué sigue en pie:** un modelo de series de tiempo predice un número; no produce
una entidad explicable —"el comprador tipo X"— que se pueda enlazar con otras entidades
del corpus (una zona, una campaña, un evento) y consultar en lenguaje natural, que es
justamente lo que distingue a un WikiLLM de un modelo predictivo: no se trata de
anticipar el próximo valor, sino de mantener una descripción legible y conectada de qué
está pasando y por qué, algo que ningún modelo de series de tiempo produce como
subproducto.

### Nivel 4 — La brecha

Falta una base de conocimiento mantenida por un LLM que compile perfiles de comprador
como páginas enlazadas —a zonas, a rangos de precio, a temporadas—, actualizándolas
cuando llegan señales nuevas de búsqueda, con procedencia explícita de qué observación
sustenta cada rasgo del perfil y cuándo se confirmó por última vez, de forma que un
vendedor pueda preguntar qué tipo de comprador busca en una zona ahora y recibir una
respuesta que reconoce cuándo el patrón cambió y por qué.

> **Objeción:** "Eso vuelve a ser, en el fondo, un sistema de recomendación con una
> capa de texto encima. La industria ya lo tiene resuelto con motores de
> recomendación."

**Por qué sigue en pie:** un motor de recomendación responde "a este comprador
probablemente le interesa esta propiedad"; no responde "el tipo de comprador que busca
en esta zona cambió en los últimos tres meses, y esto buscaba antes y esto busca ahora."
La primera es una predicción puntual sin memoria explicable; la segunda es conocimiento
acumulado y trazable en el tiempo — y es esa capacidad la que ningún motor de
recomendación estándar produce, porque no fue diseñado para explicar su propio cambio,
solo para predecir el siguiente clic.

---

## 4. Vinculación de literatura científica dispersa

### Nivel 1 — Contexto global

La investigación en inteligencia artificial se publica a un ritmo que hace casi
imposible que un investigador tenga visión completa de qué métodos ya se propusieron
bajo otro nombre, qué resultados de un área se replican silenciosamente en otra sin que
los autores se citen entre sí, y qué líneas de trabajo aparentemente distintas están,
en realidad, resolviendo la misma pregunta desde ángulos distintos.

> **Objeción:** "Eso ya lo resuelven los motores de citación como Google Scholar o
> Semantic Scholar, que muestran quién cita a quién. Es un problema de bibliometría
> resuelto desde hace años."

**Por qué sigue en pie:** los motores de citación solo muestran las conexiones que los
propios autores declararon explícitamente al citar; no detectan la conexión entre dos
trabajos que resuelven el mismo problema con métodos equivalentes pero nombres
distintos y sin citarse entre sí — que es precisamente el caso más común y más valioso
de encontrar, porque revela redundancia o una oportunidad de síntesis que ningún autor
señaló. Ese tipo de relación implícita es estructuralmente invisible para un grafo de
citas.

### Nivel 2 — Soluciones actuales y sus fallas

Herramientas que indexan implementaciones por tarea y por conjunto de datos de
referencia, y buscadores académicos que indexan por palabra clave y resumen, son la
respuesta actual: permiten encontrar trabajos relacionados con una tarea específica,
pero organizan la información por la etiqueta que el propio autor eligió, no por la
relación conceptual real entre los métodos.

> **Objeción:** "Con que la etiqueta de tarea esté bien puesta, el problema
> desaparece: cualquier investigador filtra por tarea y ya tiene todos los trabajos
> relacionados juntos."

**Por qué sigue en pie:** dos trabajos pueden compartir la etiqueta de tarea y no
compartir el mecanismo de fondo, o pueden no compartir la etiqueta —porque uno se
presenta como "detección de alucinaciones" y otro como "verificación factual"— y sin
embargo resolver esencialmente el mismo problema. Filtrar por etiqueta encuentra lo que
los autores decidieron nombrar igual, no lo que es conceptualmente equivalente, que es
la relación que de verdad importa para no reinventar lo ya hecho.

### Nivel 3 — El punto ciego

Los trabajos que usan un grafo de entidades con un algoritmo de ranking del tipo
*Personalized PageRank* para encontrar, sobre un corpus de texto, el nodo que conecta
información dispersa sin pista léxica directa entre las partes, están validados sobre
corpus narrativos —transcripciones, artículos periodísticos, ficción— y sobre preguntas
de referencia con respuesta conocida. Ninguno se ha aplicado a un corpus de literatura
científica, donde las entidades no son personas o lugares sino métodos, conjuntos de
datos y resultados numéricos, y donde la relación buscada no es "quién conoce a quién"
sino "qué método es, en el fondo, una variación de cuál otro."

> **Objeción:** "Cambiar el tipo de entidad de personas a métodos es un detalle de
> implementación menor, basta con ajustar el *prompt* de extracción. El mecanismo de
> fondo ya está probado, no hay nada nuevo que investigar."

**Por qué sigue en pie:** el mecanismo de extracción y de ranking puede ser el mismo,
pero la pregunta de si detecta relaciones útiles cambia por completo con el tipo de
corpus. En texto narrativo, dos menciones de la misma persona comparten casi siempre el
nombre; en literatura científica, dos métodos equivalentes casi nunca comparten
terminología — es exactamente el caso más difícil de resolución de entidades, y el que
ningún trabajo revisado prueba, precisamente porque los corpus evaluados hasta ahora no
lo exigen.

### Nivel 4 — La brecha

Falta un *wiki*-grafo que vincule papers, métodos y conjuntos de datos de un área de
investigación activa, construido para exponer relaciones que ningún autor declaró
explícitamente —qué trabajo es, en sustancia, la misma idea con otro nombre, o qué
método de un área resuelve, sin saberlo, un problema ya resuelto en otra—, con una
medición de cuántas de esas conexiones resultan, tras revisión humana, genuinamente
nuevas y no ya conocidas por los expertos del área.

> **Objeción:** "Sin verdad de referencia sobre qué conexiones son genuinamente
> nuevas, esa evaluación es completamente subjetiva. No hay forma de medir esto de
> forma rigurosa; es curiosidad intelectual disfrazada de investigación."

**Por qué sigue en pie:** la subjetividad se controla exactamente como se controla en
cualquier evaluación con jueces expertos: pidiendo a más de un experto del área que, sin
ver el resultado del sistema, liste de memoria las conexiones que ya conoce, y midiendo
qué proporción de las conexiones que el sistema encontró no estaba en esa lista. Es la
misma lógica de control que ya usan los bancos de pruebas de síntesis de investigación
existentes, adaptada a un objetivo distinto — no un método nuevo por inventar.

---

## 5. Degradación de calidad bajo mantenimiento incremental

### Nivel 1 — Contexto global

Cualquier base de conocimiento que se construye y se sigue actualizando con el
tiempo —a diferencia de un documento que se escribe una vez y se publica— puede
degradarse de formas que nadie está observando: un error introducido en una
actualización temprana puede sobrevivir intacto veinte actualizaciones después, una
afirmación puede quedar contradicha por una fuente nueva sin que nadie la corrija, y la
cobertura del conocimiento acumulado puede alejarse en silencio de lo que las fuentes
originales realmente dicen.

> **Objeción:** "Eso ya lo resuelve el control de versiones de Git: cualquier cambio
> queda registrado, y basta con revisar el historial de *commits* para ver qué se
> introdujo y cuándo."

**Por qué sigue en pie:** Git registra que algo cambió, no si ese cambio es correcto ni
si sigue siendo correcto después de que otros cambios posteriores lo rodean. El
historial de versiones responde "¿qué se modificó?", no "¿la página, en su estado
actual, sigue siendo fiel a las fuentes que la originaron, después de que otras diez
páginas relacionadas cambiaron a su alrededor?" — es una pregunta sobre la salud del
contenido acumulado, no sobre el registro de cambios, y Git no tiene ninguna noción de
fidelidad a una fuente ni de coherencia entre páginas.

### Nivel 2 — Soluciones actuales y sus fallas

Los bancos de pruebas disponibles para evaluar sistemas de generación de conocimiento
tipo wiki —los que miden calidad de artículos generados desde cero, o los que miden
memoria conversacional entre sesiones— evalúan siempre un artefacto producido en un solo
momento: se genera, se mide su calidad una vez, y ahí termina la evaluación. Ninguno
vuelve a medir ese mismo artefacto después de muchas rondas sucesivas de actualización.

> **Objeción:** "Basta con correr esos mismos bancos de pruebas varias veces, en
> distintos momentos, y comparar los resultados. No hace falta inventar una
> metodología nueva, solo repetir la medición existente."

**Por qué sigue en pie:** repetir una medición de calidad puntual en distintos
momentos no captura si el sistema sigue siendo fiel a sus fuentes originales o si ha
ido derivando hacia afirmaciones que ya nadie puede rastrear a un documento concreto.
La calidad medida de forma independiente en cada punto puede mantenerse estable
mientras la fundamentación se erosiona por debajo — exactamente el tipo de degradación
silenciosa que una medición puntual repetida, sin comparar contra las fuentes
originales, no puede detectar.

### Nivel 3 — El punto ciego

De todos los trabajos revisados sobre generación automática de resúmenes o
mantenimiento de documentación, solo uno mide algo parecido a esto —la generación
automática de resúmenes de cambios en una enciclopedia colaborativa—, y lo hace sobre
un subproducto acotado: qué tan bien se describe un cambio individual, no si la
acumulación de muchos cambios preserva la fidelidad del conocimiento resultante a sus
fuentes originales. Ningún trabajo mide la trayectoria completa de un corpus mantenido
por LLM a través de decenas de actualizaciones sucesivas, contra las fuentes que lo
originaron.

> **Objeción:** "Si nadie lo ha medido es porque probablemente no hay ninguna
> degradación real que valga la pena medir. La ausencia de evidencia en la literatura
> es evidencia de ausencia del problema."

**Por qué sigue en pie:** la ausencia de evidencia se explica mejor por la juventud del
patrón —tiene apenas meses de existir públicamente— que por la ausencia del problema.
Los sistemas de memoria de agentes evaluados sobre conversaciones de larga duración sí
muestran degradación medible con el tiempo, y no hay ninguna razón conceptual para
esperar que una base de conocimiento en prosa, mantenida por el mismo tipo de
mecanismo, esté exenta de un fenómeno que sí aparece en el pariente más cercano que sí
se ha medido.

### Nivel 4 — La brecha

Falta medir, sobre un corpus real ingerido en orden cronológico con una copia
congelada tras cada actualización, cómo evolucionan la cobertura, la fundamentación en
las fuentes originales y la tasa de resolución de contradicciones de una base de
conocimiento mantenida por un LLM a lo largo de docenas de actualizaciones sucesivas, y
qué políticas de mantenimiento —revisión automática con qué frecuencia, cuánta
intervención humana— preservan mejor esa calidad.

> **Objeción:** "Esto sigue siendo, al final, solo correr el mismo *pipeline* muchas
> veces y anotar números en una tabla. No hay una pregunta teórica de fondo, es trabajo
> de laboratorio repetitivo."

**Por qué sigue en pie:** el trabajo repetitivo es el método, no la pregunta. La
pregunta de fondo es si existe una arquitectura de mantenimiento —con qué frecuencia
revisar, cuánta intervención humana, qué tan agresivamente resumir— que haga que una
base de este tipo sea sostenible a largo plazo sin degradarse, y esa pregunta no tiene
respuesta conocida en ningún trabajo revisado. Que el método para responderla sea correr
el sistema muchas veces y medir no la vuelve menos una pregunta de investigación, de la
misma manera que un experimento clínico no deja de ser investigación por repetirse en
muchos pacientes.
