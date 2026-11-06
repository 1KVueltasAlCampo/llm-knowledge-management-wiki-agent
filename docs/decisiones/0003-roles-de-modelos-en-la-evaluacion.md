# 0003. Roles de los modelos en la evaluación: quién responde, quién redacta y quién juzga

**Fecha:** 6 de noviembre de 2026. **Estado:** propuesta (Juan Diego), pendiente de revisión de
Juan David. **Modifica:** la decisión 0001 solo en el rol de juez.

## Decisión

| Rol | Modelo | Proveedor |
|---|---|---|
| Responder (RAG y wiki) | `deepseek-flash` (DeepSeek-V4.1-Flash-1017) | DeepSeek |
| Redactar borradores de preguntas | `deepseek-v4-pro` | DeepSeek |
| Juez de correctitud (capa 2) | `gemini-3.8-flash` | Google |

La regla 1 de la constitución no cambia: RAG y wiki usan el mismo modelo.

## Por qué

- **El juez no puede ser el modelo que responde.** Con la decisión 0001 el juez evaluaría sus
  propias respuestas: el sesgo de autopreferencia infla la métrica.
- **El redactor no puede ser el juez.** Si el juez escribió las respuestas oráculo, tiende a
  aceptar respuestas con su misma redacción.
- El juez es de otro proveedor que el que responde, que es la independencia que más importa.
  El redactor comparte proveedor con el que responde, pero sus borradores los verifica un
  humano contra el paper antes de usarse, así que ese sesgo queda acotado.
- `gemini-3.8-flash` en lugar de `gemini-4-argon`: el juez se llama cientos o miles de veces y
  Flash cuesta 0,75 / 3,75 USD por millón (entrada / salida) frente a 2,00 / 10,00 de Argon
  (tarifas hasta el 30-nov y el 31-dic-2026; suben después). La calibración contra etiquetas
  humanas dirá si basta; si no, se sube a Argon.

## Fuentes (consultadas el 6-nov-2026)

- `deepseek-flash` lo sirve DeepSeek-V4.1-Flash-1017:
  https://api-docs.deepseek.com/quick_start/pricing y https://api-docs.deepseek.com/news/news261017
- Modelos estables y tarifas de Gemini: https://aistudio.google.com/docs/models y
  https://aistudio.google.com/docs/pricing
- **El corte de entrenamiento de DeepSeek-V4.1-Flash no está publicado** en la tarjeta del
  modelo (https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash) ni en la documentación de la
  API. Un agregador de terceros indica mayo de 2025 (no verificado). Ver `docs/corpus.md` para
  cómo se maneja.

## Consecuencias

- `.env.example` gana `GEMINI_API_KEY`, `JUDGE_MODEL` y `DRAFT_MODEL`.
- El cliente de modelo necesita un segundo proveedor (Gemini) para el juez. Se propone como
  cambio aparte, sin tocar el camino de `deepseek-flash`.
- Los identificadores se confirman listando modelos con la API (`GET /models`) antes de la
  primera corrida real.
