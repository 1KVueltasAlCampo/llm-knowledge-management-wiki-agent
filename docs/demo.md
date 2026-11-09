# Demostración del sistema

Recorrido de punta a punta del sistema sobre el corpus real: un wiki mantenido por un agente y un RAG simple responden la misma pregunta con el mismo modelo; se ingiere un paper nuevo en vivo; se repite la pregunta y se inspecciona la evidencia que queda. Cada comando se ejecuta desde la raíz del repositorio.

## Interfaz web

```powershell
uv run python -m wikillm.panel          # abre http://127.0.0.1:8765 (opciones: --puerto, --tope-usd, --no-abrir)
```

Solo escucha en la máquina local. Al arrancar carga el índice del RAG (unos 15 s en GPU). Secciones:

| Sección | Qué hace |
|---|---|
| Preguntar | Una pregunta (o un ejemplo) a los dos sistemas: columna azul para el RAG y verde para el WikiLLM, con pasos del agente, fragmentos recuperados, respuesta, citas con su fragmento, costo y tabla comparativa |
| Ingerir | Estado del corpus, siguiente paper del orden de ingesta y su ingesta con plan, escritura, validación del código y copia versionada |
| Wiki | Índice, páginas y historial versionado |
| Resultados | Métricas del piloto y estimación del costo de una corrida |
| Sistema | Estado (clave, índice, wiki), verificaciones y reinicio del wiki en el paso 5 |

La consola de cada ejecución muestra la misma salida que la orden equivalente (con un botón para copiarla), y la pestaña de llamadas lista tokens, tiempo y dólares de cada llamada al modelo. «Archivos» abre un visor de solo lectura (wiki, evidencia, documentos, especificaciones y código clave; nunca `.env`). Las acciones que llaman al modelo piden confirmación con su estimación, y la sesión se bloquea al llegar al tope de gasto (0,25 USD por defecto). Cada ejecución queda en `results/demo/grabaciones/` (no se versiona: incluye fragmentos de papers) y «Ejecuciones guardadas» la reproduce sin llamar al modelo, con un aviso permanente de que es una reproducción.

## Qué muestra

| Paso | Qué se ve | Qué demuestra |
|---|---|---|
| 1 | El wiki en disco: índice, páginas con citas, registro y copias versionadas | La memoria del sistema es un artefacto legible y versionado |
| 2 | La misma pregunta a los dos sistemas **antes** de ingerir el paper que la responde | Ambos se abstienen en lugar de inventar |
| 3 | Ingesta en vivo de un paper | El mantenimiento incremental: páginas creadas y actualizadas, citas validadas, copia versionada |
| 4 | La misma pregunta **después** de la ingesta | Ambos responden con la cita del mismo fragmento; se ve qué hizo el agente |
| 5 | Archivos de evidencia | Trazas, costos por llamada y reproducibilidad de la corrida |
| 6 | Estimación de la corrida completa y métricas del piloto | Control de costo y cadena de evaluación |

## Preparación

Requiere el entorno instalado (`uv sync`), el archivo `.env` con la clave del proveedor, el Gold local de los 50 papers, el índice vectorial del RAG y el wiki de desarrollo con 5 papers (`data/wiki/dev2`). En una máquina nueva todo eso se reconstruye con los comandos de la sección «Cómo reproducir» del [README](../README.md).

```powershell
.\scripts\preparar_demo.ps1                 # copia limpia del wiki en el paso 5 (data/wiki/demo)
uv run python scripts/verificar_demo.py     # comprueba datos, índice, GPU, wiki y repositorio
uv run python scripts/probar_modelo.py      # una llamada mínima: confirma la conexión y muestra el saldo
```

## Secuencia

**1. El wiki en el paso 5.** Se abren `data/wiki/demo/index.md` (20 páginas, cada una con un resumen de una línea), una página de paper (por ejemplo `pages/hipporag-neurobiologically-inspired-long-term-memory-for-lar.md`, con `[span_id]` tras cada afirmación) y `log.md` (una entrada por ingesta, con las citas eliminadas, los enlaces rotos y las afirmaciones sin cita). Las copias versionadas:

```powershell
git -C data/wiki/demo log --oneline --decorate
```

**2. Pregunta antes de la ingesta.** El paper de BeliefShift es el sexto en el orden de ingesta; con 5 papers ingeridos no hay respuesta en el corpus.

```powershell
uv run python -m wikillm.arnes comparar "What is the total number of sessions in the BeliefShift dataset?" --wiki data/wiki/demo
```

Resultado esperado: ambos sistemas responden la frase de abstención. En el bloque del wiki se ven las búsquedas que hizo el agente con distintas palabras clave y la lectura del índice antes de abstenerse.

**3. Ingesta en vivo.** Dos llamadas al modelo (plan y escritura), unos 40 s y menos de 0,01 USD:

```powershell
uv run python -m wikillm.wiki ingerir --paso 6 --wiki data/wiki/demo
```

Imprime las páginas creadas y actualizadas, las citas eliminadas por no resolver a un fragmento real, los enlaces rotos y las afirmaciones numéricas sin cita. Quedan una entrada nueva en `log.md` y la etiqueta `paso-6` en el repositorio del wiki.

**4. La misma pregunta después de la ingesta.**

```powershell
uv run python -m wikillm.arnes comparar "What is the total number of sessions in the BeliefShift dataset?" --wiki data/wiki/demo
```

Resultado esperado: ambos responden 68,160 y citan `2603.23848#s18.p3`, con el comienzo del fragmento del corpus que lo respalda. El agente del wiki muestra su recorrido (una búsqueda, la lectura de la página del paper y la respuesta). Como el proveedor no garantiza respuestas idénticas entre ejecuciones, la redacción y el número de pasos del agente pueden variar.

**5. Evidencia.**

| Archivo | Contenido |
|---|---|
| `results/demo/comparaciones.jsonl` | Una línea por comparación: respuestas, citas, abstención, costo y traza del agente |
| `results/demo/llamadas.jsonl` | Cada llamada al modelo con sus tokens, segundos y dólares (no se versiona: contiene texto de los papers) |
| `data/wiki/demo/log.md` | Registro de cada ingesta |
| `results/piloto-1/` | Piloto del arnés: `corrida.json` (modelo, pasos, huella del banco), `respuestas.jsonl`, `ingestas.jsonl`, `trazas.jsonl` |

**6. Corrida completa y métricas.**

```powershell
uv run python -m wikillm.arnes correr --corrida demo-estimar --pasos 0,5 --estado-minimo borrador --tipos T1,T4,T5 --estimar
uv run python -m wikillm.eval metricas --respuestas results/piloto-1/respuestas.jsonl
uv run python -m wikillm.eval validar-banco
```

La primera orden solo estima el costo (no llama al modelo); la segunda calcula cobertura y contexto por sistema y paso sobre el piloto; la tercera valida el banco de 60 preguntas.

## Costo de la demostración

| Acción | Costo aproximado |
|---|---|
| Una comparación (RAG y wiki) | 0,0006–0,0012 USD |
| Ingesta de un paper | 0,006–0,009 USD |
| Secuencia completa de arriba | menos de 0,02 USD |

## Si falla la conexión

En la interfaz web, «Ejecuciones guardadas» reproduce una ejecución anterior sin llamar al proveedor. Los pasos 1, 5 y 6 no usan el proveedor. Para los pasos 2 a 4 se reproducen las respuestas guardadas en `results/demo/ensayos/` y en `results/piloto-1/trazas.jsonl`.
