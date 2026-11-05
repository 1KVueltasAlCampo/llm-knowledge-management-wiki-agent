"""Cálculo del costo de una llamada al modelo."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

# Horas pico de DeepSeek en UTC, de lunes a viernes: [inicio, fin).
VENTANAS_PICO_UTC = ((1, 4), (6, 10))
FACTOR_HORA_PICO = 2.0


@dataclass(frozen=True)
class Tarifas:
    """Dólares por millón de tokens, a tarifa normal (fuera de hora pico)."""

    entrada_sin_cache: float
    entrada_con_cache: float
    salida: float


def es_hora_pico(momento: datetime) -> bool:
    """Indica si el momento cae en hora pico. Una fecha sin zona horaria se toma como UTC.

    No distingue los festivos chinos (también tarifa baja), así que es una cota superior.
    """
    momento = momento.replace(tzinfo=UTC) if momento.tzinfo is None else momento.astimezone(UTC)
    if momento.weekday() >= 5:
        return False
    return any(inicio <= momento.hour < fin for inicio, fin in VENTANAS_PICO_UTC)


def calcular_costo(
    tokens_entrada_sin_cache: int,
    tokens_entrada_cache: int,
    tokens_salida: int,
    tarifas: Tarifas,
    hora_pico: bool = False,
) -> float:
    """Costo estimado en dólares. Los tokens de razonamiento ya están dentro de los de salida."""
    base = (
        tokens_entrada_sin_cache * tarifas.entrada_sin_cache
        + tokens_entrada_cache * tarifas.entrada_con_cache
        + tokens_salida * tarifas.salida
    ) / 1_000_000
    return base * (FACTOR_HORA_PICO if hora_pico else 1.0)
