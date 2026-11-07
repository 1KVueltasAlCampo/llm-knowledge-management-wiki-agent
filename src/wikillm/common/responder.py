"""Contrato común de los dos brazos (RAG y wiki) frente al arnés de comparación.

El arnés solo conoce esta interfaz: ingiere papers con ``ingerir`` y hace preguntas con
``responder``. Lo que pasa dentro de cada brazo (recuperación, lectura del wiki, número de
llamadas al modelo) queda oculto, pero su costo se suma en el resultado para que las métricas
sean comparables. Las funciones ``a_linea_*`` traducen el resultado a los campos en inglés de
``specs/contrato-resultados.md``.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

from wikillm.common.modelo import Respuesta
from wikillm.ingest.gold import aproximar_tokens

PATRON_SPAN = re.compile(r"^(\d{4}\.\d{4,5})#s\d+\.p\d+$")
FRASE_ABSTENCION = "The ingested corpus does not contain this information."


def _normalizar(texto: str) -> str:
    return re.sub(r"[\W_]+", " ", texto.casefold()).strip()


def es_abstencion(texto: str) -> bool:
    """Si el texto contiene la frase de abstención, sin importar mayúsculas ni puntuación."""
    return _normalizar(FRASE_ABSTENCION) in _normalizar(texto)


def _sin_negativos(objeto: Any, nombres: Sequence[str]) -> None:
    for nombre in nombres:
        if getattr(objeto, nombre) < 0:
            raise ValueError(f"La métrica {nombre} no puede ser negativa")


@dataclass(frozen=True)
class ResultadoBrazo:
    respuesta: str
    citas: tuple[str, ...]  # span_id, sin repetir y en orden de uso
    abstuvo: bool
    tokens_contexto: int
    tokens_entrada: int
    tokens_salida: int
    segundos: float
    usd: float
    llamadas: int

    def __post_init__(self) -> None:
        if not self.respuesta.strip():
            raise ValueError("La respuesta del brazo está vacía")
        object.__setattr__(self, "citas", tuple(self.citas))
        for cita in self.citas:
            if not PATRON_SPAN.match(cita):
                raise ValueError(f"La cita {cita!r} no es un span_id (<arxiv_id>#s<N>.p<M>)")
        repetidas = {c for c in self.citas if self.citas.count(c) > 1}
        if repetidas:
            raise ValueError(f"Citas repetidas: {sorted(repetidas)}")
        if self.abstuvo and self.citas:
            raise ValueError("Una abstención no puede llevar citas")
        _sin_negativos(
            self,
            ("tokens_contexto", "tokens_entrada", "tokens_salida", "segundos", "usd", "llamadas"),
        )

    @property
    def fuentes(self) -> tuple[str, ...]:
        """Identificadores de arXiv de las citas, sin repetir y en el orden en que aparecen."""
        return tuple(dict.fromkeys(c.split("#", 1)[0] for c in self.citas))

    @classmethod
    def desde_llamadas(
        cls,
        respuesta: str,
        citas: Sequence[str],
        llamadas: Sequence[Respuesta],
        segundos: float,
        contexto: str = "",
    ) -> ResultadoBrazo:
        """Suma las métricas de todas las llamadas al modelo hechas para una pregunta.

        ``contexto`` es el texto que el brazo recuperó o leyó. Si la respuesta es una abstención
        se descartan las citas: no hay nada que citar.
        """
        abstuvo = es_abstencion(respuesta)
        return cls(
            respuesta=respuesta,
            citas=() if abstuvo else tuple(citas),
            abstuvo=abstuvo,
            tokens_contexto=aproximar_tokens(contexto) if contexto else 0,
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
            "citas": list(self.citas),
            "abstuvo": self.abstuvo,
            "tokens_contexto": self.tokens_contexto,
            "tokens_entrada": self.tokens_entrada,
            "tokens_salida": self.tokens_salida,
            "segundos": self.segundos,
            "usd": self.usd,
            "llamadas": self.llamadas,
        }


@dataclass(frozen=True)
class ResultadoIngesta:
    tokens_entrada: int
    tokens_salida: int
    segundos: float
    usd: float
    llamadas: int

    def __post_init__(self) -> None:
        _sin_negativos(self, ("tokens_entrada", "tokens_salida", "segundos", "usd", "llamadas"))

    @classmethod
    def desde_llamadas(cls, llamadas: Sequence[Respuesta], segundos: float) -> ResultadoIngesta:
        return cls(
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
            "tokens_entrada": self.tokens_entrada,
            "tokens_salida": self.tokens_salida,
            "segundos": self.segundos,
            "usd": self.usd,
            "llamadas": self.llamadas,
        }


def a_linea_resultado(
    resultado: ResultadoBrazo,
    *,
    run_id: str,
    question_id: str,
    system: str,
    ingest_step: int,
    model: str,
    temperature: float,
    timestamp: str,
) -> dict[str, object]:
    """Línea de ``results/<corrida>/respuestas.jsonl`` (``specs/contrato-resultados.md`` §1)."""
    return {
        "run_id": run_id,
        "question_id": question_id,
        "system": system,
        "ingest_step": ingest_step,
        "answer": resultado.respuesta,
        "abstained": resultado.abstuvo,
        "citations": list(resultado.citas),
        "context_tokens": resultado.tokens_contexto,
        "input_tokens": resultado.tokens_entrada,
        "output_tokens": resultado.tokens_salida,
        "latency_s": resultado.segundos,
        "cost_usd": resultado.usd,
        "model": model,
        "temperature": temperature,
        "timestamp": timestamp,
    }


def a_linea_ingesta(
    resultado: ResultadoIngesta,
    *,
    run_id: str,
    system: str,
    ingest_step: int,
    arxiv_id: str,
    model: str,
    timestamp: str,
) -> dict[str, object]:
    """Línea de ``results/<corrida>/ingestas.jsonl``: el costo de ingerir cada paper."""
    return {
        "run_id": run_id,
        "system": system,
        "ingest_step": ingest_step,
        "arxiv_id": arxiv_id,
        "input_tokens": resultado.tokens_entrada,
        "output_tokens": resultado.tokens_salida,
        "calls": resultado.llamadas,
        "latency_s": resultado.segundos,
        "cost_usd": resultado.usd,
        "model": model,
        "timestamp": timestamp,
    }


@runtime_checkable
class Brazo(Protocol):
    nombre: str

    def ingerir(self, arxiv_id: str) -> ResultadoIngesta: ...

    def responder(self, pregunta: str) -> ResultadoBrazo: ...
