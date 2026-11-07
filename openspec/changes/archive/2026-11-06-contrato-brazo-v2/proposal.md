# Proposal

## Why

Juan Diego fijó en `specs/contrato-resultados.md` cómo se mide el experimento: se ingiere un paper a la vez, en `orden_ingesta`; tras ciertos pasos se responde el banco; cada respuesta lleva `citations` como `span_id`, `abstained` y `context_tokens`; y la fundamentación solo cuenta citas que resuelven a un fragmento real del Gold. El contrato de brazos que ya tenemos (`responder(pregunta)` con `fuentes` como ids de arXiv) no lo cumple, y el RAG v1 tampoco: cita papers y no fragmentos, no sabe de pasos de ingesta y su prompt está en español (decisión 0004). Hay que alinear la interfaz antes de construir el wiki, para no hacerlo dos veces.

## What Changes

- **Interfaz `Brazo`:** además de `responder(pregunta)`, un método `ingerir(arxiv_id)` que incorpora un paper al corpus del brazo y devuelve un `ResultadoIngesta` (tokens, segundos, dólares y llamadas). `responder` usa solo lo ya ingerido.
- **`ResultadoBrazo`:** `fuentes` pasa a `citas` (lista de `span_id`) y se añaden `abstuvo` y `tokens_contexto`. `fuentes` queda como propiedad derivada de las citas.
- **Abstención común:** una frase fija en inglés y una función que decide si una respuesta se abstiene.
- **Líneas de resultados:** funciones que convierten un resultado del brazo en una línea con los campos exactos de `specs/contrato-resultados.md` (y que pasa `leer_resultados` de `wikillm.eval`), y una línea de `ingestas.jsonl` para el costo por ingesta, que el contrato no tenía.
- **RAG v2:** fragmentos construidos a partir de los fragmentos citables (`spans`), de modo que cada uno sabe qué `span_id` contiene; ingesta incremental en el orden del manifest; recuperación restringida a lo ingerido; prompt en inglés con el contexto rotulado por `span_id`; citas válidas solo si se recuperaron y existen en `data/gold/spans.jsonl`; comprobación de que el Gold local es el que versionó Juan Diego.
- Se actualiza `specs/interfaz-responder.md`.

## Capabilities

### New Capabilities

### Modified Capabilities
- `arm-interface`: `ingerir`, citas por `span_id`, abstención, métricas de contexto y líneas de resultados.
- `rag-arm`: fragmentos por `span_id`, ingesta incremental, prompt en inglés y citas validadas.

## Impact

- Código en `src/wikillm/common/responder.py` y `src/wikillm/rag/`, con sus pruebas. Contrato que toca: `specs/interfaz-responder.md` (mío) y `specs/contrato-resultados.md` (de Juan Diego, solo se lee; se propone `ingestas.jsonl` como añadido).
- Es un cambio incompatible con el `ResultadoBrazo` actual, pero nadie más lo usa todavía.
- Gasto de saldo: una pregunta real al final (~0,0003 USD), con aviso previo. El resto, local y gratis.
- El índice de 50 papers se vuelve a construir (~100 s en la GPU).
