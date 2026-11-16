"""Acuerdo entre autores sobre una mitad del banco: medida del acuerdo y paso a «acordado».

Cada mitad la revisan los dos autores con la página de revisión (aceptar, corregir o descartar).
El código mide cuánto coinciden sobre las preguntas que ambos decidieron y, cuando una persona lo
ordena, pasa las preguntas al estado «acordado». No decide nada por su cuenta: las discrepancias
se resuelven antes (regla 11), y las preguntas que algún autor aún no ha leído se dejan fuera con
``pendientes`` y conservan su estado.
"""

from __future__ import annotations

import copy
from collections.abc import Collection
from typing import Any

from wikillm.eval.acuerdo import Acuerdo, kappa_cohen

ACORDADO = "acordado"


def _etiqueta(decision: str) -> str:
    return "aceptar" if decision == "aceptar" else "ajustar"


def decisiones(revision: list[dict[str, Any]]) -> dict[str, str]:
    """Decisión de cada pregunta que el revisor decidió (las demás se ignoran)."""
    return {
        r["question_id"]: r["decision"]
        for r in revision
        if r.get("decision") in ("aceptar", "corregir", "descartar")
    }


def medir_acuerdo(
    revision_a: list[dict[str, Any]], revision_b: list[dict[str, Any]], ids: Collection[str]
) -> tuple[Acuerdo, list[str]]:
    """Acuerdo en «aceptar o ajustar» sobre las preguntas de ``ids`` que ambos decidieron.

    Devuelve el acuerdo y los identificadores en los que no coinciden.
    """
    por_a, por_b = decisiones(revision_a), decisiones(revision_b)
    comunes = sorted(set(ids) & set(por_a) & set(por_b))
    etiquetas_a = [_etiqueta(por_a[i]) for i in comunes]
    etiquetas_b = [_etiqueta(por_b[i]) for i in comunes]
    discrepan = [i for i, a, b in zip(comunes, etiquetas_a, etiquetas_b, strict=True) if a != b]
    return kappa_cohen(etiquetas_a, etiquetas_b), discrepan


def acordar(
    banco: list[dict[str, Any]],
    *,
    pendientes: Collection[str],
    fecha: str,
    acuerdo: Acuerdo,
) -> list[dict[str, Any]]:
    """Copia del banco con las preguntas no pendientes en estado «acordado»."""
    desconocidas = sorted(set(pendientes) - {p["id"] for p in banco})
    if desconocidas:
        raise ValueError(f"Pendientes que no están en el banco: {', '.join(desconocidas)}")
    resultado = []
    for p in banco:
        nueva = copy.deepcopy(p)
        if p["id"] not in pendientes:
            nueva["estado_verificacion"] = ACORDADO
            nueva.setdefault("revision", {})["acordado"] = {
                "fecha": fecha,
                "porcentaje_acuerdo": round(acuerdo.porcentaje, 4),
                "kappa": None if acuerdo.kappa is None else round(acuerdo.kappa, 4),
            }
        resultado.append(nueva)
    return resultado
