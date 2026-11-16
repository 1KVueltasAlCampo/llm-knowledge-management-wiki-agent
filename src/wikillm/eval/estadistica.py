"""Comparación pareada de los dos brazos: bootstrap sobre preguntas y prueba de McNemar exacta.

Python puro y con semilla fija: repetir el cálculo sobre los mismos datos da lo mismo.
"""

from __future__ import annotations

import math
import random
from collections import defaultdict
from typing import Any

from wikillm.eval.correctitud import CORRECTA

REMUESTREOS = 2_000
SEMILLA = 1


def mcnemar_exacto(solo_rag: int, solo_wiki: int) -> float:
    """Valor p bilateral exacto (binomial con p=0,5) sobre los pares discordantes."""
    n = solo_rag + solo_wiki
    if n == 0:
        return 1.0
    cola = sum(math.comb(n, i) for i in range(min(solo_rag, solo_wiki) + 1))
    return min(1.0, 2 * cola / 2**n)


def bootstrap_diferencia(
    rag: list[int], wiki: list[int], remuestreos: int = REMUESTREOS, semilla: int = SEMILLA
) -> tuple[float, float]:
    """Intervalo del 95 % (percentiles 2,5 y 97,5) de wiki − RAG, remuestreando preguntas."""
    n = len(rag)
    azar = random.Random(semilla)
    diferencias = []
    for _ in range(remuestreos):
        indices = [azar.randrange(n) for _ in range(n)]
        diferencias.append((sum(wiki[i] for i in indices) - sum(rag[i] for i in indices)) / n)
    diferencias.sort()
    return (
        diferencias[round(0.025 * (remuestreos - 1))],
        diferencias[round(0.975 * (remuestreos - 1))],
    )


def _fila(paso: int, tipo: str, pares: list[tuple[int, int]]) -> dict[str, Any]:
    rag = [r for r, _ in pares]
    wiki = [w for _, w in pares]
    n = len(pares)
    solo_rag = sum(1 for r, w in pares if r and not w)
    solo_wiki = sum(1 for r, w in pares if w and not r)
    inf, sup = bootstrap_diferencia(rag, wiki)
    return {
        "ingest_step": paso,
        "tipo": tipo,
        "n": n,
        "cobertura_rag": sum(rag) / n,
        "cobertura_wiki": sum(wiki) / n,
        "diferencia": (sum(wiki) - sum(rag)) / n,
        "ic95_inf": inf,
        "ic95_sup": sup,
        "solo_rag": solo_rag,
        "solo_wiki": solo_wiki,
        "p_mcnemar": mcnemar_exacto(solo_rag, solo_wiki),
    }


def comparar_pareado(evaluados: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Una fila por paso (`tipo` vacío) y por (tipo, paso) con las respondibles de ambos brazos."""
    por_pregunta: dict[tuple[int, str], dict[str, tuple[str, int]]] = defaultdict(dict)
    for e in evaluados:
        if not e["respondible"]:
            continue
        clave = (int(e["ingest_step"]), e["question_id"])
        por_pregunta[clave][e["system"]] = (e["tipo"], int(e["veredicto"] == CORRECTA))

    grupos: dict[tuple[int, str], list[tuple[int, int]]] = defaultdict(list)
    for (paso, _), sistemas in sorted(por_pregunta.items()):
        if "rag" not in sistemas or "wiki" not in sistemas:
            continue
        tipo = sistemas["rag"][0]
        par = (sistemas["rag"][1], sistemas["wiki"][1])
        grupos[(paso, "")].append(par)
        grupos[(paso, tipo)].append(par)
    return [_fila(paso, tipo, pares) for (paso, tipo), pares in sorted(grupos.items())]
