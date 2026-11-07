# Design

## Context

**Lo que ya existe y el arnés debe usar tal cual:**

| Pieza | Dónde | Qué aporta |
|---|---|---|
| Interfaz `Brazo` | `common/responder.py` | `ingerir(arxiv_id)` y `responder(pregunta)`; `a_linea_resultado` y `a_linea_ingesta` ya generan las líneas del contrato |
| Banco | `eval/banco.py` | `leer_banco`, estados (`borrador` → `verificado_a` → `verificado_b` → `acordado`), `esperado_en_paso` (qué es correcto en cada paso) |
| Métricas | `eval/metricas.py` | `leer_resultados` valida los campos obligatorios; `evaluar_resultados` ya trata los pasos en que una pregunta aún no es respondible |
| Manifest | `data/manifest_corpus.jsonl` | `orden_ingesta` de los 50 papers |
| Costo | `common/costo.py` | `es_hora_pico` (lunes a viernes, 01–04 y 06–10 UTC, el doble de precio) |

**Medidas de la corrida de desarrollo del wiki (5 papers, bitácora del 7-nov-2026):** ingerir un paper cuesta 0,006–0,007 USD de media y tarda unos 40 s; una pregunta cuesta 0,0008 USD con 5 papers. El RAG costó 0,0003–0,0004 USD por pregunta y sus ingestas no llaman al modelo (384 dimensiones en GPU, 159 s para los 50). La literatura (Cochran) avisa de hasta 21 veces más tokens por consulta con un wiki grande: por eso la estimación usa una cota alta para el wiki y se re-mide con el piloto.

**Tamaño:** con 60 preguntas, 11 pasos (0, 5, …, 50) y dos brazos son 1.320 respuestas. Con 0,0005 USD por pregunta del RAG y hasta 0,003 del wiki, las preguntas suman del orden de 2,5 USD; la ingesta del wiki, 0,3–0,8 USD.

## Goals / Non-Goals

**Goals:**
- Una sola orden que produce los archivos del contrato, con la misma ejecución para los dos brazos.
- Que una corrida cortada se pueda continuar sin gastar dos veces y sin líneas duplicadas.
- Que cada corrida diga qué modelo, qué preguntas, qué pasos y qué estados de verificación usó, y si vale para el informe.
- Que el gasto se vea antes de empezar y no pueda pasar del tope.

**Non-Goals:**
- Calcular métricas o llamar al juez: ya existe en `eval`, con su propio gasto y su propio aviso.
- Decidir qué pasos se evalúan ni qué preguntas entran: son entradas de la orden.
- Ejecutar los brazos en paralelo: complica el tope de gasto y la comparación de latencias sin ganar nada que importe.
- Ablaciones del wiki o variaciones de `k`.

## Decisions

1. **Los brazos se alternan dentro de cada paso, no se corre uno entero y luego el otro.** En cada paso ambos ingieren lo nuevo y luego, para cada pregunta, primero responde el RAG y después el wiki. Así los dos ven la misma hora del día, la misma carga de la API y la misma tarifa (la hora pico duplica el precio), y la latencia es comparable. Alternativa descartada: un brazo después del otro, que haría que uno corra de madrugada y el otro en hora pico.
2. **Un solo `ClienteModelo` para los dos brazos.** El tope `MAX_USD_PER_RUN` y el registro de llamadas cubren la corrida entera. El costo de cada brazo sale de sus resultados, que ya lo suman por llamada.
3. **Las preguntas se hacen en todos los pasos**, también en los que la fuente aún no se ha ingerido: ahí la respuesta correcta es abstenerse y es lo que mide la alucinación. Lo decide `esperado_en_paso`, no el arnés. Se puede acotar con `--tipos` o `--preguntas`.
4. **Reanudación por clave.** Una respuesta se identifica por (`question_id`, `system`, `ingest_step`) y una ingesta por (`system`, `arxiv_id`); al empezar se leen las ya escritas y se saltan. Los archivos se escriben línea a línea y con vaciado inmediato, así que un corte pierde como mucho la pregunta en curso. Los brazos son idempotentes al ingerir (el wiki no llama al modelo con un paper ya ingerido y el RAG no recalcula embeddings con la misma huella), por lo que la reanudación los vuelve a poner al día sin gasto. Al reingerir no se escribe de nuevo la línea de `ingestas.jsonl`.
5. **El wiki debe estar exactamente en el paso.** Antes de preguntar en el paso N se comprueba que el brazo tiene ingeridos los N primeros papers del orden; si el wiki ya está más adelante (una carpeta anterior) o no coincide con el orden, se aborta con un mensaje en lugar de responder con un estado equivocado.
6. **Cada corrida tiene sus carpetas:** `data/wiki/<corrida>/` y `data/chroma/<corrida>/`. Una corrida nueva nunca reutiliza un wiki o un índice de otra. Reanudar sí, con el mismo nombre.
7. **El estado de verificación manda.** Por defecto se preguntan solo las `acordado` (regla 11). `--estado-minimo borrador` permite pilotos, y entonces `corrida.json` marca `valida_para_informe: false` y la orden lo avisa al empezar y al terminar. Así un piloto con borradores no puede acabar en el informe por descuido.
8. **La puerta de costo copia el patrón de `eval borradores`:** se imprime la estimación; si pasa de 5 USD se exige `--confirmo-usd` con un valor mayor o igual; `--estimar` no llama al modelo. La estimación usa cotas, no promedios: 0,0008 USD por pregunta del RAG, 0,004 por pregunta del wiki y 0,03 por paper ingerido en el wiki. Se avisa si la hora actual es de pico, pero no se bloquea (una corrida larga cruza horas).
9. **Un fallo del modelo detiene la corrida** (`ErrorDeModelo` tras los reintentos del cliente, o tope de gasto). No se inventa ni se omite una respuesta: se conserva todo lo escrito y se sale con código 1 indicando cómo reanudar. Es mejor una corrida cortada y reanudable que un hueco silencioso que sesga una comparación.
10. **`corrida.json` registra la reproducibilidad (regla 9):** el nombre y la fecha de la corrida, el commit y si el árbol estaba limpio, el modelo y la temperatura, los precios, los pasos, los brazos con sus parámetros (`k`, `max_acciones`), el banco con su huella y los estados de las preguntas, y si vale para el informe. Se escribe al empezar y se completa al terminar.
11. **La traza del wiki va a un archivo aparte.** El contrato de resultados no tiene lugar para «acciones del agente», y meterlo en `respuestas.jsonl` rompería a quien lo lea. `trazas.jsonl` lo guarda con las mismas claves (`question_id`, `system`, `ingest_step`) para poder unirlo. El arnés lo pide a los brazos que lo tengan (`traza()`), sin depender de ninguno.

## Risks / Trade-offs

- **La corrida completa tarda horas** (los 50 papers del wiki son unos 35–60 min de ingesta, más ≈1.320 respuestas). Se mitiga con la reanudación y un progreso por paso.
- **La estimación puede quedarse corta si el wiki crece mucho.** Se usan cotas altas y se re-mide con el piloto; el tope de gasto es la última defensa.
- **Preguntar todo en todos los pasos cuesta más que preguntar solo lo respondible.** El sobrecosto es pequeño (las preguntas aún no respondibles son baratas: el wiki casi no encuentra nada y el RAG recupera igual) y lo que se mide, la abstención, es una de las métricas del experimento.
- **El cliente compartido serializa las llamadas** y no habrá paralelismo. Es deliberado (decisión 1 y Non-Goals).
- **Un piloto con borradores puede confundirse con una corrida válida.** Se marca en `corrida.json` y se avisa en pantalla.
