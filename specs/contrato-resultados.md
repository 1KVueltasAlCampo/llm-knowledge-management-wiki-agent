# Contrato: resultados del arnés y banco de preguntas

**Autor:** Juan Diego. **Estado:** borrador v0 para revisión de Juan David (dueño del arnés).
Si se acepta, el arnés escribe este formato y el módulo `wikillm.eval` calcula las métricas
sobre él.

## 1. Archivo de resultados

`results/<corrida>/respuestas.jsonl`: una línea por (pregunta, sistema, paso de ingesta).

```json
{
  "run_id": "2026-11-13-a",
  "question_id": "A-T1-003",
  "system": "rag",
  "ingest_step": 12,
  "answer": "El wiki obtuvo 0,71 de exactitud frente a 0,64 del RAG.",
  "abstained": false,
  "citations": ["2605.18490#s4.p3"],
  "context_tokens": 5321,
  "input_tokens": 5410,
  "output_tokens": 87,
  "latency_s": 2.4,
  "cost_usd": 0.00086,
  "model": "deepseek-flash",
  "temperature": 0,
  "timestamp": "2026-11-13T15:02:11Z"
}
```

| Campo | Obligatorio | Qué es |
|---|---|---|
| `run_id` | Sí | Identificador de la corrida (regla 9 de la constitución). |
| `question_id` | Sí | `id` del banco de preguntas. |
| `system` | Sí | `rag` o `wiki`. |
| `ingest_step` | Sí | Cuántos papers se habían ingerido (1..N, según `orden_ingesta`). |
| `answer` | Sí | Texto de la respuesta tal como la dio el sistema. |
| `abstained` | Sí | `true` si el sistema dijo que no puede responder con lo ingerido. |
| `citations` | Sí | Lista de `span_id` (ver `specs/propuesta-gold-v1.md` §2). Puede ir vacía. |
| `context_tokens` | Sí | Tokens del contexto recuperado o leído (páginas del wiki, trozos del RAG). Es la base de la eficiencia de contexto. |
| `input_tokens`, `output_tokens`, `cost_usd`, `latency_s` | Sí | Los que ya registra `ClienteModelo`. |
| `model`, `temperature`, `timestamp` | Sí | Reproducibilidad. |

**Citas del wiki.** Las páginas del wiki son derivadas; para medir fundamentación, cada
afirmación debe poder llegar a un `span_id` del Gold. Si el agente del wiki guarda en cada
página las fuentes como `span_id`, basta con propagarlas a `citations`. Una cita a una página
del wiki sin `span_id` cuenta como no fundamentada.

## 2. Banco de preguntas

`data/preguntas/banco.jsonl` (versionado; sin texto de arXiv):

```json
{
  "id": "A-T3-002",
  "texto": "¿Qué sistema supera a HippoRAG 2 en ... y por cuánto?",
  "tipo": "T3",
  "respuesta_oraculo": "…",
  "respuesta_clave": ["0,71", "LLM-Wiki"],
  "evidencia": [{"span_id": "2605.25480#s5.p2", "sha256": "…"}],
  "fuentes_requeridas": ["2502.14802", "2605.25480"],
  "ingesta_minima": 13,
  "autor": "A",
  "redactado_por": "deepseek-v4-pro",
  "estado_verificacion": "borrador"
}
```

- Tipos: `T1` hecho puntual o numérico de una fuente; `T2` síntesis multi-fuente; `T3`
  contradicción o superación entre estudios; `T4` dato que una fuente posterior actualiza;
  `T5` no respondible con lo ingerido hasta ese paso.
- `ingesta_minima` = mayor `orden_ingesta` entre `fuentes_requeridas`. Para T4 la respuesta
  correcta **cambia** desde la ingesta de la fuente posterior: se usa
  `respuesta_por_paso: [{"desde": 7, "respuesta_oraculo": …}, {"desde": 19, …}]`.
- T5: `fuentes_requeridas` vacía o con un paper que entra más tarde; la respuesta correcta
  antes de ese paso es abstenerse.
- `estado_verificacion`: `borrador` → `verificado_a` → `verificado_b` → `acordado`. Solo una
  persona cambia el estado; el código nunca marca `verificado_*` ni `acordado`.
- `respuesta_clave`: cifras o entidades que la capa determinista busca en la respuesta.

## 3. Métricas que produce `wikillm.eval`

| Métrica | Cómo se calcula |
|---|---|
| Correctitud (capa 1) | Normaliza números (coma y punto decimal, %, separadores) y entidades; acierta si aparecen todas las `respuesta_clave`. Resultado: `correcta`, `incorrecta` o `indeterminada`. |
| Correctitud (capa 2) | Solo para las `indeterminada`: juez Gemini con rúbrica, temperatura 0. Se calibra contra etiquetas humanas en una submuestra y se reporta el acuerdo (kappa). |
| Fundamentación | Proporción de `citations` que resuelven a un fragmento del Gold con la misma huella y pertenecen a un paper ya ingerido en ese paso. (Que el fragmento **respalde** la afirmación lo decide el juez o una persona; se reporta aparte.) |
| Cobertura | Por sistema y paso: correctas / preguntas con `ingesta_minima ≤ paso`. |
| Abstención | Para T5: proporción de abstenciones correctas; las respuestas a T5 cuentan como alucinación. |
| Contexto y costo | Media y mediana de `context_tokens` y `cost_usd` por sistema y paso; tokens por respuesta correcta. |

## 4. Costo previsto

60 preguntas × N pasos evaluados × 2 sistemas. Con los 50 pasos son 6.000 respuestas;
evaluando cada 5 ingestas (10 pasos) son 1.200. El juez solo ve las `indeterminada`.
Decisión pendiente para ambos autores: qué pasos se evalúan.
