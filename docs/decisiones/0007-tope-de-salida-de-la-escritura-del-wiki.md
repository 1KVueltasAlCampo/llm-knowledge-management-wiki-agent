# 0007. Tope de salida de la escritura del wiki: de 16.000 a 32.000 tokens

**Fecha:** 16 de noviembre de 2026. **Estado:** propuesta (Juan Diego), pendiente de revisión de
Juan David, dueño de `src/wikillm/wiki/`. **Complementa:** la decisión 0001 (modelo único).

## Qué pasó

En la corrida oficial `oficial-1` (60 preguntas, 11 pasos), la ingesta del wiki falló en el paso 20,
al escribir las páginas de `2606.06240` (≈60.000 tokens de entrada). La respuesta del modelo llegó
al tope de 16.000 tokens de salida (`MAX_TOKENS_ESCRITURA`), el JSON quedó cortado
(`Expecting ',' delimiter`, columna 57.300) y los dos intentos fallaron. El arnés paró, como
indica la especificación (los fallos detienen la corrida). Antes de ese paso, la escritura ya había
llegado a 16.268 tokens de salida entre dos llamadas, y la bitácora del 10-nov avisaba de que el
tope se volvería a alcanzar al crecer el wiki. Quedan por ingerir papers aún más grandes (por
ejemplo `2610.04794`, ≈112.000 tokens).

## Decisión

`MAX_TOKENS_ESCRITURA` pasa de 16.000 a **32.000** tokens. Es un tope, no un objetivo: solo cambia
el resultado de las llamadas que antes se cortaban.

## Por qué es seguro para la comparación

- El modelo admite hasta 393.216 tokens de salida (decisión 0001), así que el nuevo tope está dentro
  de su límite.
- Los pasos 0, 5, 10 y 15 ya guardados no se repiten. Una sola escritura de esos pasos llegó al
  tope: la del paper 13 (`2605.18490`), que se cortó en 16.000 tokens y se reintentó una vez (3
  llamadas, 30.542 tokens de salida en total); sus páginas son las de la segunda respuesta, válida.
  Con 32.000 esa escritura habría salido en una sola llamada y, por tanto, algo distinta. Las
  demás ingestas (papers 14, 16 y 17, de 15.377 a 16.268 tokens) sumaron plan y escritura en dos
  llamadas, cada una por debajo del tope. Si se quiere una corrida sin esa asimetría, se repite
  entera con otro nombre (unos 1–2 USD más).
- RAG no cambia, y el wiki conserva el mismo modelo, la misma temperatura y las mismas instrucciones.
  Es un cambio de la capacidad de escritura del wiki, no de su estrategia.
- Las corridas de reanudación comparan `k` y `max_acciones`, no este tope; el cambio queda escrito
  aquí y en `results/oficial-1/` (se anota el commit que reanuda).

## Costo

La salida cuesta 0,60 USD por millón (el doble en hora pico). Una llamada de 32.000 tokens cuesta
como máximo 0,038 USD en pico, así que el efecto sobre el gasto total es de centavos.

## Riesgos

- Una escritura más larga puede dejar páginas más largas en el wiki y más contexto en las consultas
  posteriores. Es el comportamiento que el wiki habría tenido sin el tope, y se mide con
  `context_tokens` en los resultados.
- Si una llamada llegara también a 32.000, el arnés vuelve a parar con el mismo error y se decide de
  nuevo.
