"""Qué preguntas del banco se hacen, según su estado de verificación (regla 11)."""

from __future__ import annotations

from collections import Counter
from collections.abc import Collection
from typing import Any

from wikillm.eval.banco import ESTADOS, TIPOS

ESTADO_PARA_INFORME = "acordado"


class ErrorDeSeleccion(ValueError):
    """El filtro de preguntas no es válido o no deja ninguna."""


def seleccionar(
    banco: list[dict[str, Any]],
    *,
    estado_minimo: str = ESTADO_PARA_INFORME,
    tipos: Collection[str] | None = None,
    ids: Collection[str] | None = None,
) -> list[dict[str, Any]]:
    """Preguntas con estado igual o posterior al mínimo, acotadas por tipo e id, por id."""
    if estado_minimo not in ESTADOS:
        raise ErrorDeSeleccion(f"Estado mínimo desconocido: {estado_minimo!r} (usa {ESTADOS})")
    for tipo in tipos or ():
        if tipo not in TIPOS:
            raise ErrorDeSeleccion(f"Tipo desconocido: {tipo!r} (usa {sorted(TIPOS)})")
    existentes = {p["id"] for p in banco}
    faltan = sorted(set(ids or ()) - existentes)
    if faltan:
        raise ErrorDeSeleccion(f"No están en el banco: {', '.join(faltan)}")
    minimo = ESTADOS.index(estado_minimo)
    elegidas = [
        p
        for p in banco
        if ESTADOS.index(p["estado_verificacion"]) >= minimo
        and (not tipos or p["tipo"] in tipos)
        and (not ids or p["id"] in ids)
    ]
    if not elegidas:
        raise ErrorDeSeleccion(
            f"Ninguna pregunta cumple el filtro (estado mínimo {estado_minimo}, "
            f"tipos {sorted(tipos or [])}, ids {sorted(ids or [])})"
        )
    return sorted(elegidas, key=lambda p: p["id"])


def valida_para_informe(preguntas: list[dict[str, Any]]) -> bool:
    """Solo vale para el informe si todas las preguntas hechas están acordadas por los autores."""
    return bool(preguntas) and all(
        p["estado_verificacion"] == ESTADO_PARA_INFORME for p in preguntas
    )


def conteo_por_estado(preguntas: list[dict[str, Any]]) -> dict[str, int]:
    return dict(Counter(p["estado_verificacion"] for p in preguntas))
