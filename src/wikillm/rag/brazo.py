"""Brazo RAG simple: recuperar los k fragmentos más cercanos y hacer una sola llamada al modelo."""

from __future__ import annotations

import time
from collections.abc import Callable, Collection, Sequence

from wikillm.common.modelo import ClienteModelo
from wikillm.common.responder import ResultadoBrazo, ResultadoIngesta
from wikillm.common.respuesta import REGLAS_DE_RESPUESTA, extraer_citas_leidas
from wikillm.rag.indice import K_POR_DEFECTO, IndiceRag, Recuperado

INTRODUCCION = (
    "You answer questions about a corpus of arXiv papers. Use ONLY the context passages given "
    "below. Every paragraph in them starts with its span id in square brackets, for example "
    "[2605.18490#s4.p3]. "
)
INSTRUCCIONES = INTRODUCCION + REGLAS_DE_RESPUESTA
SIN_PASAJES = "(no passages)"


def construir_contexto(recuperados: Sequence[Recuperado]) -> str:
    if not recuperados:
        return SIN_PASAJES
    return "\n\n".join(
        f"Passage {i}\n{r.fragmento.texto}" for i, r in enumerate(recuperados, start=1)
    )


def construir_mensajes(pregunta: str, contexto: str) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": INSTRUCCIONES},
        {"role": "user", "content": f"Context:\n\n{contexto}\n\nQuestion: {pregunta}"},
    ]


def extraer_citas(
    respuesta: str,
    recuperados: Sequence[Recuperado],
    spans_validos: Collection[str] | None = None,
) -> list[str]:
    """``span_id`` citados entre corchetes, recuperados y existentes en ``spans.jsonl``."""
    recuperados_ids = {span_id for r in recuperados for span_id in r.fragmento.span_ids}
    return extraer_citas_leidas(respuesta, recuperados_ids, spans_validos)


class BrazoRag:
    nombre = "rag"

    def __init__(
        self,
        modelo: ClienteModelo,
        indice: IndiceRag,
        *,
        k: int = K_POR_DEFECTO,
        spans_validos: Collection[str] | None = None,
        reloj: Callable[[], float] = time.perf_counter,
    ) -> None:
        self._modelo = modelo
        self._indice = indice
        self._k = k
        self._spans_validos = spans_validos
        self._reloj = reloj

    def ingerir(self, arxiv_id: str) -> ResultadoIngesta:
        return self._indice.ingerir(arxiv_id)

    def responder(self, pregunta: str) -> ResultadoBrazo:
        inicio = self._reloj()
        recuperados = self._indice.recuperar(pregunta, self._k)
        contexto = construir_contexto(recuperados)
        llamada = self._modelo.generar(construir_mensajes(pregunta, contexto), etiqueta=self.nombre)
        return ResultadoBrazo.desde_llamadas(
            llamada.texto,
            extraer_citas(llamada.texto, recuperados, self._spans_validos),
            [llamada],
            self._reloj() - inicio,
            contexto=contexto,
        )

    @property
    def ingeridos(self) -> list[str]:
        return list(self._indice.ingeridos)
