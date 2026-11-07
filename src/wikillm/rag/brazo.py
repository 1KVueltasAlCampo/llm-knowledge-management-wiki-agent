"""Brazo RAG simple: recuperar los k fragmentos más cercanos y hacer una sola llamada al modelo."""

from __future__ import annotations

import re
import time
from collections.abc import Callable, Sequence
from typing import Any

from wikillm.common.modelo import ClienteModelo
from wikillm.common.responder import ResultadoBrazo
from wikillm.rag.indice import K_POR_DEFECTO, Recuperado, recuperar

INSTRUCCIONES = (
    "Eres un asistente que responde preguntas sobre un corpus de papers de arXiv. "
    "Responde únicamente con la información de los fragmentos del contexto; no uses "
    "conocimiento propio. Cita cada afirmación con el identificador del paper entre corchetes, "
    "por ejemplo [2405.14831]. Si el contexto no contiene la información, responde exactamente "
    "«El corpus no contiene esta información.» y no cites ningún paper. "
    "Responde en el idioma de la pregunta."
)
PATRON_GRUPO = re.compile(r"\[([^\[\]]+)\]")
PATRON_ID = re.compile(r"\d{4}\.\d{4,5}")


def construir_mensajes(pregunta: str, recuperados: Sequence[Recuperado]) -> list[dict[str, str]]:
    contexto = "\n\n".join(
        f"Fragmento {i} (paper [{r.fragmento.arxiv_id}])\n{r.fragmento.texto}"
        for i, r in enumerate(recuperados, start=1)
    )
    return [
        {"role": "system", "content": INSTRUCCIONES},
        {"role": "user", "content": f"Contexto:\n\n{contexto}\n\nPregunta: {pregunta}"},
    ]


def extraer_fuentes(respuesta: str, recuperados: Sequence[Recuperado]) -> list[str]:
    """Identificadores citados entre corchetes que estaban entre los recuperados.

    Acepta ``[id]`` y también ``[id1, id2]``. Un identificador citado que no se recuperó (el
    modelo lo inventó o lo recordó) se ignora. Sin repetir y en orden de primera cita.
    """
    disponibles = {r.fragmento.arxiv_id for r in recuperados}
    fuentes: list[str] = []
    for grupo in PATRON_GRUPO.finditer(respuesta):
        for identificador in PATRON_ID.findall(grupo.group(1)):
            if identificador in disponibles and identificador not in fuentes:
                fuentes.append(identificador)
    return fuentes


class BrazoRag:
    nombre = "rag"

    def __init__(
        self,
        modelo: ClienteModelo,
        almacen: Any,
        *,
        k: int = K_POR_DEFECTO,
        reloj: Callable[[], float] = time.perf_counter,
    ) -> None:
        self._modelo = modelo
        self._almacen = almacen
        self._k = k
        self._reloj = reloj

    def responder(self, pregunta: str) -> ResultadoBrazo:
        inicio = self._reloj()
        recuperados = recuperar(self._almacen, pregunta, self._k)
        llamada = self._modelo.generar(
            construir_mensajes(pregunta, recuperados), etiqueta=self.nombre
        )
        return ResultadoBrazo.desde_llamadas(
            llamada.texto,
            extraer_fuentes(llamada.texto, recuperados),
            [llamada],
            self._reloj() - inicio,
        )
