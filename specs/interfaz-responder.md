# Contrato de los brazos: `responder(pregunta)`

Este contrato lo cumplen el brazo RAG y el brazo wiki. El arnés de comparación llama a los dos
exactamente igual y no sabe cómo funcionan por dentro. Está implementado en
`src/wikillm/common/responder.py`.

## Firma

```python
class Brazo(Protocol):
    nombre: str  # "rag" o "wiki"

    def responder(self, pregunta: str) -> ResultadoBrazo: ...
```

No hay clase base de la que heredar: basta con tener `nombre` y `responder`.

## Qué devuelve (`ResultadoBrazo`)

| Campo | Tipo | Significado |
|---|---|---|
| `respuesta` | texto | La respuesta final. No puede estar vacía. |
| `fuentes` | lista de ids de arXiv | Los papers en los que se apoyó la respuesta, sin repetir y en el orden en que se usaron (por ejemplo `"2405.14831"`, sin versión). Puede ir vacía si el brazo dice que el corpus no tiene la información. |
| `tokens_entrada` | entero | Tokens enviados al modelo, con y sin caché, **sumados sobre todas las llamadas** de esta pregunta. |
| `tokens_salida` | entero | Tokens generados, sumados igual. |
| `segundos` | decimal | Tiempo total de la pregunta, **incluida** la recuperación o lectura previa a generar. |
| `usd` | decimal | Costo estimado, sumado sobre las llamadas. |
| `llamadas` | entero | Cuántas veces se llamó al modelo para esta pregunta. |

Al crearse, el resultado se valida: lanza `ValueError` con el motivo si la respuesta está
vacía, si una métrica es negativa o si una fuente no es un identificador de arXiv o está
repetida.

## Cómo se arma sin repetir cuentas

Todo brazo debe llamar al modelo **solo** con `ClienteModelo.generar`. Cada llamada devuelve una
`Respuesta` con sus métricas; el resultado se construye con la suma:

```python
ResultadoBrazo.desde_llamadas(respuesta, fuentes, llamadas, segundos)
```

## Ejemplo de brazo mínimo

```python
import time

from wikillm.common.modelo import ClienteModelo
from wikillm.common.responder import ResultadoBrazo


class BrazoEjemplo:
    nombre = "ejemplo"

    def __init__(self, modelo: ClienteModelo) -> None:
        self.modelo = modelo

    def responder(self, pregunta: str) -> ResultadoBrazo:
        inicio = time.perf_counter()
        llamada = self.modelo.generar([{"role": "user", "content": pregunta}], etiqueta=self.nombre)
        return ResultadoBrazo.desde_llamadas(
            llamada.texto, ["2405.14831"], [llamada], time.perf_counter() - inicio
        )
```

## Reglas

- **Los errores no se esconden.** Si el modelo falla o se alcanza `MAX_USD_PER_RUN`, el error
  sube hasta el arnés. El brazo nunca devuelve una respuesta inventada.
- **Un brazo, una pregunta, un resultado.** El estado entre preguntas (el índice vectorial o el
  wiki) puede existir, pero el costo de construirlo no se mezcla con el de responder.
- **Sin versión en las fuentes.** El corpus identifica cada paper por su id; la versión está
  en el encabezado del Gold.
- **Lo que no cubre este contrato:** el formato completo del JSONL de resultados (pregunta,
  juez, métricas de calidad). Eso lo define el arnés; aquí solo se fija la parte del brazo.
