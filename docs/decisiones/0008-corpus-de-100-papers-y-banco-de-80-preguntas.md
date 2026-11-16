# 0008. Corpus de 100 papers en orden cronológico y banco de 80 preguntas

**Fecha:** 16 de noviembre de 2026. **Estado:** propuesta (Juan Diego), pendiente de revisión de
Juan David. **El orden y los pasos los cambia la decisión 0009; el banco pasa a tener 100 preguntas.** **Complementa:** la decisión 0001 (modelo único) y el plan de ampliación del 11-nov.

## Decisión

1. **Corpus de 100 papers**: los 50 actuales más los 50 de la ampliación (`data/ampliacion/hoja_verificacion.csv`,
   los que citan los 50 actuales). Vive en una carpeta aparte, `data/corpus100/` (lista de ids,
   manifest, Gold y fragmentos), de modo que el corpus de 50 y la corrida `oficial-1` quedan intactos.
2. **Orden cronológico** por fecha de la primera versión, con la misma regla de siempre (`ordenar`).
   Los 50 nuevos (de 2018 a 2025) entran antes que casi todos los de 2026, así que cambia la posición
   de cada paper y la `ingesta_minima` de 50 de las 60 preguntas acordadas. `wikillm.eval ampliar-banco`
   la recalcula con el nuevo manifest, sin tocar `banco.jsonl`.
3. **Banco de 80 preguntas** (`data/preguntas/banco_100.jsonl`): las 60 acordadas más las 20 de caso de
   borde que escogió Juan Diego (`data/ampliacion/preguntas_borde_JDi.json`), con evidencia anclada a
   `span_id` y huella. Quedan en `verificado_a` y sin revisión cruzada: son **preliminares** (regla 11).
   No se incluyen las de Juan David porque no marcó cuáles escoge.
4. **Corrida `ampliado-1`**: pasos 0, 10, …, 100, con los mismos parámetros que `oficial-1` (modelo,
   temperatura 0, razonamiento desactivado, `k=5`, 8 acciones del wiki, tope de salida de 32.000) y
   `--estado-minimo verificado_a`, así que el arnés la marca «no vale para el informe».

## Por qué

- El tutor pidió casos de borde con información antigua y reciente muy parecidas (reunión del 11-nov),
  y el orden cronológico con lo antiguo primero es el diseño que plantean los autores (README: el
  corpus se ingiere de forma cronológica).
- Una carpeta aparte conserva la reproducibilidad de `oficial-1` (la huella del banco y el manifest).
- Metadatos: 66 de los 100 salen de la API de arXiv; los otros 34 salen de las páginas `abs` ya
  descargadas, porque la API devolvía 429 y 503 (`wikillm.corpus metadatos-abs`).

## Límites que el informe debe declarar

- **Comparabilidad con `oficial-1`**: los pasos y el orden son distintos (0–50 frente a 0–100). Solo se
  compara el paso final de cada una y sobre las 60 preguntas comunes; el efecto de «añadir 50 papers» se
  mezcla con el del cambio de orden.
- **Las respuestas de las 60 pudieron cambiar** al añadir papers que reportan lo mismo con otro valor.
  Una comprobación automática de claves marca 18 preguntas con sus claves completas en algún paper
  nuevo; es una señal ruidosa (claves numéricas cortas) y no se revisó una por una.
- **Preguntas nuevas sin verificación cruzada**, y solo las de un autor.
- El wiki no es determinista y hay una sola corrida.

## Costo

Estimación del arnés: 7,22 USD como cota alta (3,00 de ingesta y 4,22 de preguntas) a tarifa normal.
Con `oficial-1` el gasto real fue el 54 % de la cota. Tope fijado en 9 USD para esta corrida, con
2,9 USD de reserva dentro del saldo disponible.
