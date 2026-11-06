"""Banco de preguntas: lectura, validación y respuesta esperada por paso de ingesta.

Contrato en `specs/contrato-resultados.md` §2.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

TIPOS = {"T1", "T2", "T3", "T4", "T5"}
ESTADOS = ("borrador", "verificado_a", "verificado_b", "acordado")
AUTORES = {"A", "B"}
OBLIGATORIOS = (
    "id",
    "texto",
    "tipo",
    "respuesta_oraculo",
    "evidencia",
    "fuentes_requeridas",
    "ingesta_minima",
    "autor",
    "estado_verificacion",
)


@dataclass
class Esperado:
    """Qué cuenta como correcto para una pregunta en un paso dado."""

    respondible: bool
    respuesta_oraculo: str | None
    respuesta_clave: list[str]


def leer_banco(ruta: Path) -> list[dict[str, Any]]:
    return [
        json.loads(linea)
        for linea in ruta.read_text(encoding="utf-8").splitlines()
        if linea.strip()
    ]


def calcular_ingesta_minima(fuentes: list[str], orden: dict[str, int]) -> int | None:
    """Primer paso en que todas las fuentes requeridas ya se ingirieron."""
    if not fuentes:
        return None
    return max(orden[f] for f in fuentes)


def validar_banco(preguntas: list[dict[str, Any]], orden: dict[str, int]) -> list[str]:
    """Problemas del banco frente al contrato y al manifest. Lista vacía = válido."""
    problemas: list[str] = []
    vistos: set[str] = set()
    for p in preguntas:
        pid = p.get("id", "<sin id>")
        for campo in OBLIGATORIOS:
            if campo not in p:
                problemas.append(f"{pid}: falta '{campo}'")
        if pid in vistos:
            problemas.append(f"{pid}: id repetido")
        vistos.add(pid)
        if p.get("tipo") not in TIPOS:
            problemas.append(f"{pid}: tipo inválido {p.get('tipo')!r}")
        if p.get("autor") not in AUTORES:
            problemas.append(f"{pid}: autor inválido {p.get('autor')!r}")
        if p.get("estado_verificacion") not in ESTADOS:
            problemas.append(f"{pid}: estado inválido {p.get('estado_verificacion')!r}")
        fuentes = p.get("fuentes_requeridas") or []
        desconocidas = [f for f in fuentes if f not in orden]
        if desconocidas:
            problemas.append(f"{pid}: fuentes fuera del corpus {desconocidas}")
            continue
        for evidencia in p.get("evidencia") or []:
            fuente = str(evidencia.get("span_id", "")).split("#")[0]
            if fuente not in fuentes:
                problemas.append(f"{pid}: evidencia de {fuente} no está en fuentes_requeridas")
        if p.get("tipo") != "T5":
            esperado = calcular_ingesta_minima(fuentes, orden)
            if esperado is None:
                problemas.append(f"{pid}: una pregunta {p.get('tipo')} necesita fuentes")
            elif p.get("ingesta_minima") != esperado:
                problemas.append(
                    f"{pid}: ingesta_minima {p.get('ingesta_minima')} y debería ser {esperado}"
                )
        if p.get("tipo") == "T2" and len(fuentes) < 2:
            problemas.append(f"{pid}: una pregunta T2 necesita al menos dos fuentes")
    return problemas


def esperado_en_paso(pregunta: dict[str, Any], paso: int) -> Esperado:
    """Respuesta esperada tras `paso` ingestas.

    Antes de `ingesta_minima` (o siempre, si es T5 sin fuentes) lo correcto es abstenerse.
    Una T4 puede declarar `respuesta_por_paso` para que la respuesta cambie con el corpus.
    """
    minima = pregunta.get("ingesta_minima")
    if minima is None or paso < int(minima):
        return Esperado(respondible=False, respuesta_oraculo=None, respuesta_clave=[])
    oraculo = pregunta["respuesta_oraculo"]
    clave = list(pregunta.get("respuesta_clave") or [])
    for tramo in sorted(pregunta.get("respuesta_por_paso") or [], key=lambda t: t["desde"]):
        if paso >= int(tramo["desde"]):
            oraculo = tramo["respuesta_oraculo"]
            clave = list(tramo.get("respuesta_clave") or [])
    return Esperado(respondible=True, respuesta_oraculo=oraculo, respuesta_clave=clave)
