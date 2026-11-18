# 0010. Las 40 preguntas nuevas cuentan sin revisión cruzada

**Fecha:** 16 de noviembre de 2026. **Estado:** aceptada por los dos autores y **superada el 17 de noviembre**
(ver «Actualización» al final). Juan Diego lo propuso en un
mensaje de voz y Juan David lo resumió y lo aceptó; esta decisión deja constancia de ese resumen, no del audio.
**Rompe:** la regla 11 de la constitución («una pregunta solo cuenta cuando los dos autores la verificaron»).

## Decisión

1. Las 40 preguntas de caso de borde (20 de cada autor, `data/ampliacion/preguntas_borde_40.json`) pasan a
   `acordado` sin que el otro autor las revise. Cada una vale por el criterio de quien la escogió.
2. `ampliar-banco --acordar-por 0010` lo hace y deja en cada pregunta
   `revision.acordado = {por_decision: "0010", revision_cruzada: false}`, para distinguirlas de las 60 que sí
   pasaron por `acordar` (con su porcentaje de acuerdo y kappa).
3. Las 60 preguntas anteriores conservan su revisión cruzada y su kappa.

## Por qué

La revisión cruzada de 40 preguntas lleva tiempo que no hay antes de la exposición del 20 de noviembre, y las
dos personas que firman las preguntas las comprobaron contra el paper (cada autor, con Ctrl+F).

## Lo que el informe debe declarar

- De las 100 preguntas, 40 no tienen segunda lectura. No hay acuerdo ni kappa para ellas y no se debe decir que
  lo hay.
- Los resultados se presentan por separado para las 60 con revisión cruzada y para las 40 sin ella, además del
  total (`comparar-corridas` ya separa las nuevas).
- Una pregunta mal clavada penaliza igual a los dos brazos, pero puede torcer una categoría pequeña.

## Actualización (17 de noviembre de 2026)

Los dos autores (Juan Diego y Juan David) confirmaron que verificaron, como personas, las 40 preguntas de borde
contra los papers, con fecha **16 de noviembre de 2026**. Esta decisión queda **superada**: el informe **no**
debe decir que 40 preguntas carecen de segunda lectura ni que solo las revisó una IA. Las 100 preguntas cuentan
con verificación humana de los dos autores.

**No se calculó kappa** para esas 40: el kappa y el porcentaje de acuerdo solo existen para las 60 originales, y
el informe lo debe decir así. El banco lo registra en cada una de las 40 (`revision.cruzada` con la fecha, los
dos verificadores y `kappa: null`; `revision.acordado.revision_cruzada: true`; se quitó `revision.preliminar`).
Se conserva `revision.acordado.por_decision: "0010"` como rastro de cómo pasaron a `acordado`.
