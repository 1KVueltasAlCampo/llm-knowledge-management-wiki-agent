# Nota de traspaso: corpus, preguntas y métricas (de Juan Diego para Juan David)

Rama: `data/corpus` (sin push hasta que lo acordemos). Tu pipeline de `ingest/` no cambió:
todo lo nuevo está en `src/wikillm/corpus/` y `src/wikillm/eval/`.

## Qué hay en Gold

- `data/corpus_ids.txt`: los 50 identificadores (antes 5). Mismo formato.
- `uv run python -m wikillm.ingest` produce `data/gold/<id>.md` exactamente con tu contrato
  (`specs/formato-gold.md`). Para ti no cambia nada: el RAG y la wiki leen lo mismo.
- **Nuevo y versionado:**
  - `data/manifest_corpus.jsonl`: una fila por paper con `orden_ingesta` (1..50 por fecha de
    primera versión), `mitad` (A/B), `html_available`, `pre_corte`, `senal_codigo`,
    `estado_publicacion`, `referencias_en_corpus` y `citado_por_en_corpus`. **El arnés debe
    ingerir en `orden_ingesta`.**
  - `data/gold/spans.jsonl`: fragmentos citables (`span_id` como `2605.18490#s4.p3`, sección,
    tipo, offsets en el cuerpo devuelto por `leer_gold`, huella). Sin texto.

## Qué te pido revisar

1. `specs/propuesta-gold-v1.md`: `sources` con versión, `spans.jsonl` y los campos del manifest.
   Todo es aditivo.
2. `specs/contrato-resultados.md`: el JSONL que propongo que escriba el arnés. Lo crítico:
   `ingest_step`, `abstained`, `citations` como `span_id` y `context_tokens`.
3. `docs/decisiones/0003-…`: el juez pasa a Gemini (`gemini-3.8-flash`) y los borradores a
   `deepseek-v4-pro`. RAG y wiki siguen con `deepseek-flash` (la regla 1 no cambia).
4. Qué pasos evaluamos: con 60 preguntas × 50 pasos × 2 sistemas son 6.000 respuestas;
   propongo cada 5 ingestas (1.200) y el paso 0 sin corpus.

## Cómo citar para que la fundamentación funcione

Si la wiki guarda en cada página los `span_id` de donde salió cada afirmación y el RAG trocea
por fragmentos de `spans.jsonl` (o mapea sus trozos a los `span_id` que contienen), basta con
devolverlos en `citations`. Una cita a una página de wiki sin `span_id` cuenta como no
fundamentada.

## Cómo probar las métricas ya

```bash
uv run python -m wikillm.eval sinteticos            # resultados falsos con el contrato
uv run python -m wikillm.eval metricas --respuestas results/sintetico/respuestas.jsonl
```

## Preguntas

Cada uno escribe las de su mitad (impar → A, par → B; las multi-fuente son del autor del paper
que entra más tarde). `uv run python -m wikillm.eval borradores --autor B` muestra el plan y el
costo sin llamar a nada; con `--ejecutar` genera borradores anclados a fragmentos reales y una
hoja CSV local para verificar. Nada pasa de `borrador` sin que lo marque una persona.
