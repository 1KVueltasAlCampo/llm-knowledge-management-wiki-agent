"""Contrato común de los dos brazos (RAG y wiki) frente al arnés de comparación.

El arnés solo conoce esta interfaz: llama a ``responder(pregunta)`` y recibe un ``ResultadoBrazo``.
Lo que pasa dentro de cada brazo (recuperación, lectura del wiki, número de llamadas al modelo)
queda oculto, pero su costo se suma en el resultado para que las métricas sean comparables.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from wikillm.common.modelo import Respuesta

PATRON_ID_ARXIV = re.compile(r"^\d{4}\.\d{4,5}$")


@dataclass(frozen=True)
class ResultadoBrazo:
    respuesta: str
    fuentes: tuple[str, ...]
    tokens_entrada: int
    tokens_salida: int
    segundos: float
    usd: float
    llamadas: int

    def __post_init__(self) -> None:
        if not self.respuesta.strip():
            raise ValueError("La respuesta del brazo está vacía")
        object.__setattr__(self, "fuentes", tuple(self.fuentes))
        for fuente in self.fuentes:
            if not PATRON_ID_ARXIV.match(fuente):
                raise ValueError(f"La fuente {fuente!r} no es un identificador de arXiv")
        repetidas = {f for f in self.fuentes if self.fuentes.count(f) > 1}
        if repetidas:
            raise ValueError(f"Fuentes repetidas: {sorted(repetidas)}")
        for nombre in ("tokens_entrada", "tokens_salida", "segundos", "usd", "llamadas"):
            if getattr(self, nombre) < 0:
                raise ValueError(f"La métrica {nombre} no puede ser negativa")

    @classmethod
    def desde_llamadas(
        cls,
        respuesta: str,
        fuentes: Sequence[str],
        llamadas: Sequence[Respuesta],
        segundos: float,
    ) -> ResultadoBrazo:
        """Suma las métricas de todas las llamadas al modelo hechas para una pregunta."""
        return cls(
            respuesta=respuesta,
            fuentes=tuple(fuentes),
            tokens_entrada=sum(
                r.tokens_entrada_sin_cache + r.tokens_entrada_cache for r in llamadas
            ),
            tokens_salida=sum(r.tokens_salida for r in llamadas),
            segundos=segundos,
            usd=sum(r.usd for r in llamadas),
            llamadas=len(llamadas),
        )

    def a_dict(self) -> dict[str, object]:
        return {
            "respuesta": self.respuesta,
            "fuentes": list(self.fuentes),
            "tokens_entrada": self.tokens_entrada,
            "tokens_salida": self.tokens_salida,
            "segundos": self.segundos,
            "usd": self.usd,
            "llamadas": self.llamadas,
        }


@runtime_checkable
class Brazo(Protocol):
    nombre: str

    def responder(self, pregunta: str) -> ResultadoBrazo: ...
