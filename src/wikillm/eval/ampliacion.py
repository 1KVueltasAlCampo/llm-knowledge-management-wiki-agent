"""Ampliar el banco al corpus de 100 papers: reordenar las preguntas y sumar las de caso de borde.

El orden cronológico del corpus ampliado cambia la posición de cada paper, y con ella la
`ingesta_minima` de las preguntas. Las preguntas nuevas se definen con citas literales del paper y
aquí se anclan a fragmentos reales (`span_id` y huella): nunca se copia texto de arXiv.
"""

from __future__ import annotations

import copy
import re
from pathlib import Path
from typing import Any

from wikillm.eval.banco import calcular_ingesta_minima
from wikillm.ingest.gold import leer_gold

RAZON_PRELIMINAR = "sin revisión cruzada del otro autor"
FORMATO = re.compile(r"[*_`$\\]")


class CitaNoEncontrada(ValueError):
    """Una cita no está en ningún fragmento del paper indicado."""


def normalizar(texto: str) -> str:
    texto = texto.replace("−", "-").replace(" ", " ")
    return re.sub(r"\s+", " ", FORMATO.sub("", texto)).lower().strip()


def reordenar_banco(banco: list[dict[str, Any]], orden: dict[str, int]) -> list[dict[str, Any]]:
    """Copia del banco con `ingesta_minima` y los pasos de T4 recalculados con el nuevo orden."""
    resultado = copy.deepcopy(banco)
    for p in resultado:
        fuentes = p.get("fuentes_requeridas") or []
        if p["tipo"] == "T5":
            p["ingesta_minima"] = None
        elif p["tipo"] == "T4" and p.get("respuesta_por_paso"):
            pasos = sorted(orden[f] for f in fuentes)
            p["ingesta_minima"] = pasos[0]
            for tramo in p["respuesta_por_paso"]:
                tramo["desde"] = pasos[-1]
        else:
            p["ingesta_minima"] = calcular_ingesta_minima(fuentes, {f: orden[f] for f in fuentes})
    return resultado


def acordar_por_decision(
    preguntas: list[dict[str, Any]], *, decision: str, fecha: str
) -> list[dict[str, Any]]:
    """Copia con las preguntas en «acordado» por una decisión de los autores, sin revisión cruzada.

    Es una persona quien decide (la decisión queda en `docs/decisiones/`); el código solo lo anota.
    El registro deja claro que ninguna otra persona revisó la pregunta.
    """
    resultado = copy.deepcopy(preguntas)
    for p in resultado:
        p["estado_verificacion"] = "acordado"
        p.setdefault("revision", {})["acordado"] = {
            "fecha": fecha,
            "por_decision": decision,
            "revision_cruzada": False,
        }
    return resultado


def _resolver(
    pid: str,
    paper: str,
    cita: str,
    spans: list[dict[str, Any]],
    cuerpos: dict[str, str],
    carpeta_gold: Path,
) -> dict[str, str]:
    if paper not in cuerpos:
        cuerpos[paper] = leer_gold(carpeta_gold / f"{paper}.md")[1]
    cuerpo = cuerpos[paper]
    buscada = normalizar(cita)
    for span in spans:
        if span["arxiv_id"] == paper and buscada in normalizar(
            cuerpo[int(span["inicio"]) : int(span["fin"])]
        ):
            return {"span_id": span["span_id"], "sha256": span["sha256"]}
    raise CitaNoEncontrada(f"{pid}: la cita no está en ningún fragmento de {paper}: {cita[:70]!r}")


def construir_preguntas(
    definiciones: list[dict[str, Any]],
    spans: list[dict[str, Any]],
    carpeta_gold: Path,
    origen: str,
    fecha: str = "2026-11-15",
) -> list[dict[str, Any]]:
    """Preguntas del banco a partir de definiciones con citas; quedan como preliminares."""
    cuerpos: dict[str, str] = {}
    preguntas = []
    for d in definiciones:
        fuentes = list(d.get("fuentes_requeridas") or [])
        evidencia: list[dict[str, str]] = []
        for c in d.get("citas") or []:
            if c["paper"] not in fuentes:
                raise CitaNoEncontrada(
                    f"{d['id']}: la cita es de {c['paper']}, que no está en fuentes_requeridas"
                )
            hallada = _resolver(d["id"], c["paper"], c["cita"], spans, cuerpos, carpeta_gold)
            if hallada not in evidencia:
                evidencia.append(hallada)
        autor = d.get("autor", "A")
        preguntas.append(
            {
                "id": d["id"],
                "texto": d["texto"],
                "tipo": d["tipo"],
                "respuesta_oraculo": d["respuesta_oraculo"],
                "respuesta_clave": list(d.get("respuesta_clave") or []),
                "evidencia": evidencia,
                "fuentes_requeridas": fuentes,
                "ingesta_minima": None,
                "autor": autor,
                "redactado_por": d.get("redactado_por", "claude (propuesta de ampliación)"),
                "estado_verificacion": f"verificado_{autor.lower()}",
                "revision": {
                    "verificado_por": d.get("verificado_por", "Juan Diego Ramírez"),
                    "fecha": fecha,
                    "decision_revisor": "aceptar",
                    "notas_revisor": d.get("notas", ""),
                    "origen": origen,
                    "preliminar": RAZON_PRELIMINAR,
                },
            }
        )
    return preguntas
