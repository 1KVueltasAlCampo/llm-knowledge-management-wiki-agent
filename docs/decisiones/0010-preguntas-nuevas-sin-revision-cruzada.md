# 0010. Las 40 preguntas nuevas cuentan sin revisión cruzada

**Fecha:** 16 de noviembre de 2026. **Estado:** aceptada por los dos autores. Juan Diego lo propuso en un
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
