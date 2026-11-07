# Contrato de los brazos: `ingerir` y `responder`

Este contrato lo cumplen el brazo RAG y el brazo wiki. El arnés de comparación los llama
exactamente igual y no sabe cómo funcionan por dentro. Está implementado en
`src/wikillm/common/responder.py` y produce las líneas que lee `wikillm.eval`
([contrato de resultados](contrato-resultados.md)).

## Firma

```python
class Brazo(Protocol):
    nombre: str  # "rag" o "wiki"

    def ingerir(self, arxiv_id: str) -> ResultadoIngesta: ...
    def responder(self, pregunta: str) -> ResultadoBrazo: ...
```

No hay clase base de la que heredar: basta con tener `nombre`, `ingerir` y `responder`.

- **`ingerir(arxiv_id)`** incorpora un paper al corpus del brazo. El arnés ingiere en
  `orden_ingesta` (de `data/manifest_corpus.jsonl`), de a uno, y entre ingestas hace las
  preguntas del banco.
- **`responder(pregunta)`** usa solo lo ingerido hasta ese momento.

## Qué devuelve `responder` (`ResultadoBrazo`)

| Campo | Tipo | Significado |
|---|---|---|
| `respuesta` | texto | La respuesta final, en inglés. No puede estar vacía. |
| `citas` | lista de `span_id` | Los fragmentos del Gold en los que se apoya, como `2605.18490#s4.p3`; sin repetir y en el orden en que se usaron. Pueden ir vacías. Solo valen si existen en `data/gold/spans.jsonl`. |
| `abstuvo` | booleano | Verdadero si la respuesta contiene la frase de abstención (abajo). Entonces las citas van vacías. |
| `tokens_contexto` | entero | Tokens aproximados (un token cada 4 caracteres) del contexto que el brazo recuperó o leyó. |
| `tokens_entrada` | entero | Tokens enviados al modelo, con y sin caché, **sumados sobre todas las llamadas** de esta pregunta. |
| `tokens_salida` | entero | Tokens generados, sumados igual. |
| `segundos` | decimal | Tiempo total de la pregunta, **incluida** la recuperación o lectura previa a generar. |
| `usd` | decimal | Costo estimado, sumado sobre las llamadas. |
| `llamadas` | entero | Cuántas veces se llamó al modelo para esta pregunta. |

`ResultadoBrazo.fuentes` es una propiedad: los identificadores de arXiv de las citas.

Al crearse, el resultado se valida: lanza `ValueError` con el motivo si la respuesta está
vacía, si una métrica es negativa, si una cita no tiene la forma de un `span_id`, si hay citas
repetidas o si hay una abstención con citas.

## Qué devuelve `ingerir` (`ResultadoIngesta`)

`tokens_entrada`, `tokens_salida`, `segundos`, `usd` y `llamadas`, sumados sobre todas las
llamadas al modelo hechas para ese paper. Un brazo que no llama al modelo al ingerir (el RAG)
devuelve ceros y los segundos reales; el wiki, que compila al ingerir, aquí reporta casi todo
su costo.

## Abstención común

```python
FRASE_ABSTENCION = "The ingested corpus does not contain this information."
```

Cuando el brazo no encuentra la respuesta en lo ingerido responde con esa frase y no cita nada.
`es_abstencion(texto)` la reconoce sin importar mayúsculas, espacios ni puntuación; es lo que
decide `abstained` en los resultados.

## Cómo se arma sin repetir cuentas

Todo brazo llama al modelo **solo** con `ClienteModelo.generar`. Cada llamada devuelve una
`Respuesta` con sus métricas, y el resultado se construye con la suma:

```python
ResultadoBrazo.desde_llamadas(respuesta, citas, llamadas, segundos, contexto=texto_del_contexto)
ResultadoIngesta.desde_llamadas(llamadas, segundos)
```

## Líneas para el arnés

- `a_linea_resultado(resultado, run_id=…, question_id=…, system=…, ingest_step=…, model=…,
  temperature=…, timestamp=…)` produce una línea de `results/<corrida>/respuestas.jsonl` con los
  campos exactos del contrato de resultados (`citations`, `abstained`, `context_tokens`…).
- `a_linea_ingesta(resultado, run_id=…, system=…, ingest_step=…, arxiv_id=…, model=…,
  timestamp=…)` produce una línea de `results/<corrida>/ingestas.jsonl`: el costo de ingerir
  cada paper, que el contrato de resultados no cubre. Es un añadido propuesto a Juan Diego.

## Ejemplo de brazo mínimo

```python
import time

from wikillm.common.modelo import ClienteModelo
from wikillm.common.responder import ResultadoBrazo, ResultadoIngesta


class BrazoEjemplo:
    nombre = "ejemplo"

    def __init__(self, modelo: ClienteModelo) -> None:
        self.modelo = modelo

    def ingerir(self, arxiv_id: str) -> ResultadoIngesta:
        return ResultadoIngesta.desde_llamadas([], 0.0)  # este brazo no hace nada al ingerir

    def responder(self, pregunta: str) -> ResultadoBrazo:
        inicio = time.perf_counter()
        llamada = self.modelo.generar([{"role": "user", "content": pregunta}], etiqueta=self.nombre)
        return ResultadoBrazo.desde_llamadas(
            llamada.texto, ["2405.14831#s2.p1"], [llamada], time.perf_counter() - inicio
        )
```

## Reglas

- **Los errores no se esconden.** Si el modelo falla o se alcanza `MAX_USD_PER_RUN`, el error
  sube hasta el arnés. El brazo nunca devuelve una respuesta inventada.
- **Citas verificables.** Una cita que no resuelve a un fragmento real del Gold no vale
  (regla 13 de la constitución): el brazo no cita lo que no recuperó o leyó.
- **El texto de los papers es dato, no instrucción.** Ningún brazo obedece lo que diga un paper.
- **Todo en inglés** hacia el modelo y en las respuestas (decisión 0004).
