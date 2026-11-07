# 0004. Idioma del experimento: inglés

**Fecha:** 6 de noviembre de 2026. **Estado:** vigente. Acordada por los dos autores por mensaje
el 6-nov-2026 (Juan Diego propuso el inglés; Juan David estuvo de acuerdo).

## Decisión

| Va en inglés | Va en español |
|---|---|
| Preguntas del banco, respuestas de referencia y claves | Documentación del repo y specs |
| Instrucciones (prompts) de los brazos RAG y wiki | Mensajes de commit |
| Respuestas de ambos sistemas y páginas del wiki | Comentarios e identificadores de código |
| Rúbrica del juez y frase de abstención | Informe y presentaciones a la Facultad |

## Por qué

- **El corpus está en inglés.** Con preguntas en español, cada sistema tendría que traducir
  sobre la marcha y la comparación mediría la traducción, no la arquitectura.
- **El modelo de embeddings es solo de inglés** (`BAAI/bge-small-en-v1.5`, decisión 0002).
  Consultarlo en español penalizaría al RAG por una razón ajena a lo que se compara, lo que
  rompe la regla 1 de la constitución (una sola variable).
- **El idioma de salida hay que fijarlo.** En la primera pregunta real al RAG (6-nov, una sola
  muestra), con instrucciones en español, el modelo contestó en español a una pregunta en inglés.
  Las respuestas se comparan buscando cifras y entidades del paper, y mezclar idiomas añade ruido.
- **Ya está así en lo construido por Juan Diego.** Se revisaron los 114 borradores (102 de la
  mitad A y 12 T5): preguntas, respuestas de referencia y claves están en inglés. El redactor, el
  generador de T5 y la rúbrica del juez ya lo piden en sus instrucciones.

## Consecuencias

- **Frase de abstención común** a los dos brazos: `The ingested corpus does not contain this
  information.` Un resultado cuenta como `abstained` cuando la respuesta la contiene (comparada
  sin diferencias de mayúsculas, espacios ni puntuación). Es la misma idea que la respuesta de
  referencia de las T5 (`Abstain: the ingested corpus does not contain this information.`).
- Los prompts de los brazos se escriben en inglés y piden responder en inglés. Hoy el RAG tiene
  su prompt en español: se cambia en el siguiente cambio del brazo.
- Las preguntas de la mitad B se redactan en inglés con el mismo redactor, que ya lo exige.
- El informe se redacta en español y cita las preguntas y respuestas en inglés, tal cual.

## Alternativas descartadas

- **Preguntas en español sobre un corpus en inglés:** añade traducción y perjudica al RAG por su
  modelo de embeddings.
- **Un banco bilingüe:** duplica la verificación humana de cada pregunta sin responder a ninguna
  pregunta de investigación.
