# 0009. Tres cargas por fases y wiki reutilizable

**Fecha:** 16 de noviembre de 2026. **Estado:** propuesta (Claude, a pedido de Juan David), pendiente de
revisión de Juan Diego. **Cambia:** el orden y los pasos de la decisión 0008. **Complementa:** 0001, 0007.

## Decisión

1. **Cuatro puntos de consulta, tres cargas.** La corrida `ampliado-fases-1` pregunta en los pasos 0, 33, 66 y
   100, y no en 11 pasos. Los pasos de 10 en 10 de la 0008 contienen estos mismos cortes, pero cuestan
   más respuestas sin aportar otra comparación (800 respuestas en vez de 2.200; unos 4,9 USD de cota
   y no 8,3).
2. **Qué papers entran en cada carga.** `data/corpus100/fases.json` fija la fase de cada paper
   (33, 33 y 34 papers). Dentro de una fase el orden es cronológico, y `orden_ingesta` se calcula con
   `wikillm.corpus fases`. La regla: cronológico por fecha de la primera versión, con 10 excepciones
   (tabla de abajo) elegidas mirando las 100 preguntas.
3. **El wiki construido se puede reutilizar.** `arnes correr --wiki-de <corrida>` copia el wiki de
   otra corrida y lo sitúa en cada paso con sus copias `paso-N`: el brazo `wiki` no ingiere (costo de
   ingesta 0) y las capas con grafo o tgrep se consultan sobre el mismo conocimiento. El original no se toca.

## Por qué estas cargas

Preguntas que nos hicimos y lo que contestan los datos del banco (100 preguntas: 47 T1, 15 T2, 18 T3, 4 T4,
16 T5):

- **¿Primero todos los papers viejos?** La carga 1 reúne casi todos los más antiguos (de 2018 a
  octubre de 2025, más WiCER, de mayo de 2026) porque el «viejo primero» es lo que da sentido a las T4 y a
  las T3: la cifra original llega antes y la re-medición después. MemOS y LightMem, que por fecha serían
  de la carga 2, entran en la 1 para que Mem0, Zep y MemOS lleguen juntos y sus re-mediciones (LiCoMemory,
  el reanálisis de Mem0) lleguen después.
- **¿Que los primeros 33 respondan todo?** No, y es a propósito. Con la carga 1 se pueden contestar 19 de
  las 84 preguntas que tienen respuesta; el resto debe abstenerse con papers parecidos ya en el wiki.
  Si la carga 1 respondiera todo no habría nada que medir en las cargas 2 y 3, y la abstención no se
  pondría a prueba con un señuelo cercano.
- **¿Un tema entero primero?** No. Cada carga mezcla temas (memoria de agentes, RAG con grafos, conflicto,
  seguridad), de modo que una pregunta cuya fuente llega después tiene vecinos semánticos ya ingeridos. Un tema
  entero en la carga 1 dejaría las demás cargas sin vecinos y volvería trivial la abstención.
- **¿Qué hay en la carga 2?** Las fuentes nuevas de ese lote más las re-mediciones de sistemas que ya
  están (LiCoMemory re-mide Mem0, Zep y A-MEM; HippoRAG 2 re-mide HippoRAG). Es la carga que crea el
  conflicto entre lo antiguo y lo nuevo: 51 preguntas se pueden responder al cierre (11 de ellas T3) y la
  respuesta de dos T4 cambia entre las cargas 1 y 2.
- **¿Y la carga 3?** Llegan los papers de 2026 que re-reportan o reanalizan (por ejemplo 2603.02473 y
  2609.18182, que da otra cifra de HippoRAG 2). Es el único corte donde las 84 preguntas ya tienen todas sus fuentes, y es donde cambia
  la respuesta de A039-T4-03 y A016-T4-03. 12 de las 15 T2 solo se completan en ella.
- **¿Dejar información vieja para el final?** No en el diseño base: una fuente antigua que llegue después de
  la nueva rompe la clave de las T4 (la respuesta correcta depende de la fecha, no de la llegada) y mezcla
  dos efectos, el orden de llegada y la antigüedad. Es un experimento aparte (orden inverso) y exige un
  wiki nuevo, porque el construido aquí no sirve para otro orden.

Resultado: de las 34 preguntas con varias fuentes, 32 tienen sus fuentes en dos cargas o más (4 en las tres), y
los cortes dejan responder 19 (paso 33), 51 (paso 66) y 84 (paso 100) preguntas.

## Excepciones a la cronología

| Paper | Título | Fase | Por qué |
|---|---|---|---|
| 2404.06654 | RULER: What's the Real Context Size of Your Long | 1 → 2 | RULER sale de la fase 1 para dejar sitio a los papers que entran y mantener 33 papers por fase. |
| 2409.05591 | MemoRAG: Boosting Long Context Processing with G | 1 → 2 | MemoRAG sale de la fase 1 por la misma razón. |
| 2502.14802 | From RAG to Memory: Non-Parametric Continual Lea | 1 → 2 | Cadena de HippoRAG: el original (fase 1), HippoRAG 2 (fase 2) y el reanálisis (fase 3). Las T4 A039-T4-03, A016-T4-03, B001-T4-05, B001-T4-06 y la T3 B002-T3-02 cambian de respuesta en cada fase. |
| 2507.03724 | MemOS: A Memory OS for AI System | 2 → 1 | MemOS largo a la fase 1, junto a Mem0 y Zep: en JD-02, JD-22, JD-27, JDi-20 y JDi-21 las cifras de los sistemas llegan en la fase 1 y la re-medición de LiCoMemory o el reanálisis llegan en la fase 2. |
| 2510.18866 | LightMem: Lightweight and Efficient Memory-Augme | 2 → 1 | LightMem a la fase 1 por la misma razón (JD-22, JD-29) y para repartir las respuestas de una sola fuente entre las tres fases. |
| 2603.02473 | Diagnosing Retrieval vs. Utilization Bottlenecks | 2 → 3 | Cierra la familia de LoCoMo: LoCoMo (fase 1), LiCoMemory (fase 2) y este paper (fase 3). JD-19, JD-31, JDi-19 y B013-T3-05 ven tres versiones del conjunto. |
| 2605.07068 | WiCER: Wiki-memory Compile, Evaluate, Refine Ite | 2 → 1 | WiCER pasa a la fase 1 para que A013-T3-02 (fases 1 y 2) y A018-T2-01 (fases 1 y 3) se contesten con fuentes que llegan en fases distintas. |
| 2605.25480 | Retrieval as Reasoning: Self-Evolving Agent-Nati | 2 → 3 | Completa la cadena anterior (A016-T4-03 y A026-T3-02): la cifra de HippoRAG 2 se reporta otra vez en la fase 3. |
| 2609.16073 | The Immutable Past: Formalizing State Mutability | 3 → 2 | Reparte el conjunto de B034-T2-01: sus miembros llegan en las fases 1 y 2. |
| 2610.30755 | Is Complex Agentic Memory Always Needed? Naive R | 3 → 2 | Reanálisis de Mem0 en la fase 2 (JDi-25, JD-02) y miembro de los conjuntos A053-T2-01 y A054-T2-01. |

## Límites que el informe debe declarar

- **El orden se diseñó con las preguntas a la vista.** Es el mismo para los dos brazos, pero no es el
  orden natural de aparición: 10 de 100 papers cambian de fase. Como robustez se puede repetir la corrida
  con el orden cronológico puro (otros ~3 USD de ingesta).
- **Una T2 con las fuentes en cargas distintas** solo tiene respuesta completa al final. Antes, la clave
  correcta es abstenerse y un conjunto parcial cuenta como «no se abstuvo». Falta una clave por paso
  para las T2 (solo las T4 la tienen).
- **El wiki reutilizado** reproduce exactamente lo que vio la corrida que lo construyó: sirve para comparar
  formas de consulta, no para medir otra ingesta ni otro orden.

## Cómo se usa

```bash
uv run python -m wikillm.corpus fases --manifest data/corpus100/manifest.jsonl --fases data/corpus100/fases.json
uv run python -m wikillm.arnes correr --corrida ampliado-fases-1 --pasos 0,33,66,100 --banco data/preguntas/banco_100.jsonl --manifest data/corpus100/manifest.jsonl --gold data/corpus100/gold --spans data/corpus100/gold/spans.jsonl --confirmo-usd 5
uv run python -m wikillm.arnes correr --corrida grafo-1 --wiki-de ampliado-fases-1 --graphify <graphify> --pasos 0,33,66,100 ...
```

`data/wiki/ampliado-fases-1` es el conocimiento construido: no se borra ni se edita a mano.

**Nota del 17 de noviembre.** El nombre `ampliado-1` ya lo usaba la corrida de 11 pasos de la decisión 0008 (Juan Diego, 80 preguntas), así que esta corrida se guardó como `ampliado-fases-1`. En la práctica el conocimiento se construyó aparte en `data/wiki/construccion-1` (≈ 1,60 USD) y la corrida pregunta en los pasos 33, 66 y 100, sin el paso 0.
