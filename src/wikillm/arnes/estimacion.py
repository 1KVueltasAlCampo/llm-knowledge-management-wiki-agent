"""Costo estimado de una corrida y la puerta de los 5 USD.

Las cifras son cotas altas, no promedios: salen de la primera corrida real del wiki (bitácora del
7-nov-2026) con margen, porque el costo de consultar e ingerir crece con el tamaño del wiki.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from wikillm.common.costo import es_hora_pico

LIMITE_SIN_CONFIRMAR_USD = 5.0
USD_POR_PREGUNTA = {"rag": 0.0008, "wiki": 0.004, "wiki_grafo": 0.004, "wiki_grafo_tgrep": 0.004}
USD_POR_PREGUNTA_DESCONOCIDA = 0.004
# los brazos con capas comparten el wiki del brazo "wiki": no ingieren
USD_INGESTA_POR_PAPER = {"rag": 0.0, "wiki": 0.03, "wiki_grafo": 0.0, "wiki_grafo_tgrep": 0.0}
USD_INGESTA_DESCONOCIDA = 0.03


class ExcesoDeCosto(RuntimeError):
    """La estimación pasa del límite y no se confirmó el gasto."""


@dataclass(frozen=True)
class Estimacion:
    preguntas: int
    pasos: int
    papers: int
    usd_ingesta: float
    usd_preguntas: float

    @property
    def llamadas_de_pregunta(self) -> int:
        return self.preguntas * self.pasos

    @property
    def total(self) -> float:
        return self.usd_ingesta + self.usd_preguntas


def estimar(brazos: list[str], *, preguntas: int, pasos: int, papers: int) -> Estimacion:
    """Costo máximo esperado: ``papers`` ingeridos y ``preguntas`` en cada uno de ``pasos``."""
    por_pregunta = sum(USD_POR_PREGUNTA.get(b, USD_POR_PREGUNTA_DESCONOCIDA) for b in brazos)
    por_paper = sum(USD_INGESTA_POR_PAPER.get(b, USD_INGESTA_DESCONOCIDA) for b in brazos)
    return Estimacion(
        preguntas=preguntas,
        pasos=pasos,
        papers=papers,
        usd_ingesta=papers * por_paper,
        usd_preguntas=preguntas * pasos * por_pregunta,
    )


def exigir_confirmacion(
    estimacion: Estimacion, confirmo_usd: float, limite: float = LIMITE_SIN_CONFIRMAR_USD
) -> None:
    if estimacion.total > limite and confirmo_usd < estimacion.total:
        raise ExcesoDeCosto(
            f"La estimación es de {estimacion.total:.2f} USD, más de {limite:.0f}. "
            f"Para correr, confirma con --confirmo-usd {estimacion.total:.2f} (o más)."
        )


def aviso_de_hora_pico(momento: datetime) -> str | None:
    if es_hora_pico(momento):
        return (
            "Ahora es hora pico de DeepSeek (lunes a viernes, 01–04 y 06–10 UTC): "
            "las llamadas cuestan el doble."
        )
    return None
