"""Pasa al banco las preguntas que una persona eligió y verificó.

Entradas: los borradores, la revisión exportada desde la página (`revision_<autor>_por_<autor>`)
y un archivo de ajustes acordados con el revisor (`ajustes_<autor>.json`). El estado
`verificado_<autor>` sale de esa revisión humana; el código solo la transcribe y deja la
procedencia de cada cambio en el campo `revision`.
"""

from __future__ import annotations

import copy
from typing import Any

from wikillm.eval.banco import calcular_ingesta_minima


class AjusteInvalido(ValueError):
    """Un ajuste apunta a una pregunta o un fragmento que no existe."""


def _evidencia(span_id: str, spans: dict[str, dict[str, Any]]) -> dict[str, str]:
    if span_id not in spans:
        raise AjusteInvalido(f"el fragmento {span_id} no existe en spans.jsonl")
    return {"span_id": span_id, "sha256": spans[span_id]["sha256"]}


def _aplicar(p: dict[str, Any], a: dict[str, Any], spans: dict[str, dict[str, Any]]) -> None:
    if "pregunta" in a:
        p["texto"] = a["pregunta"]
    if "respuesta" in a:
        p["respuesta_oraculo"] = a["respuesta"]
    if "claves" in a:
        p["respuesta_clave"] = list(a["claves"])
    if "tipo" in a:
        p["tipo"] = a["tipo"]
        if a["tipo"] != "T4":
            p.pop("respuesta_por_paso", None)
    if "fuentes_requeridas" in a:
        p["fuentes_requeridas"] = list(a["fuentes_requeridas"])
    evidencia = list(p.get("evidencia") or [])
    for viejo, nuevo in (a.get("evidencia_reemplazar") or {}).items():
        evidencia = [_evidencia(nuevo, spans) if e["span_id"] == viejo else e for e in evidencia]
    quitar = set(a.get("evidencia_quitar") or [])
    evidencia = [e for e in evidencia if e["span_id"] not in quitar]
    vistos = {e["span_id"] for e in evidencia}
    for span_id in a.get("evidencia_agregar") or []:
        if span_id not in vistos:
            evidencia.append(_evidencia(span_id, spans))
    p["evidencia"] = evidencia
    if "respuesta_antes" in a:  # T4 con respuesta que cambia según el paso
        p["tipo"] = "T4"
        p["respuesta_oraculo"] = a["respuesta_antes"]
        p["respuesta_clave"] = list(a.get("claves_antes") or [])


def _recalcular_pasos(p: dict[str, Any], orden: dict[str, int], a: dict[str, Any]) -> None:
    fuentes = p.get("fuentes_requeridas") or []
    if p["tipo"] == "T5":
        p["ingesta_minima"] = None
        return
    if p["tipo"] == "T4" and ("respuesta_despues" in a or p.get("respuesta_por_paso")):
        pasos = sorted(orden[f] for f in fuentes)
        p["ingesta_minima"] = pasos[0]
        if "respuesta_despues" in a:
            p["respuesta_por_paso"] = [
                {
                    "desde": pasos[-1],
                    "respuesta_oraculo": a["respuesta_despues"],
                    "respuesta_clave": list(a.get("claves_despues") or []),
                }
            ]
        else:
            for tramo in p["respuesta_por_paso"]:
                tramo["desde"] = pasos[-1]
        return
    p["ingesta_minima"] = calcular_ingesta_minima(fuentes, orden)


def aplicar(
    borradores: list[dict[str, Any]],
    revision: list[dict[str, Any]],
    ajustes: dict[str, Any],
    orden: dict[str, int],
    spans: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    autor = ajustes["autor"]
    por_id = {p["id"]: p for p in borradores}
    por_revision = {r["question_id"]: r for r in revision}
    por_ajuste = {a["question_id"]: a for a in ajustes.get("ajustes", [])}
    for pid in por_ajuste:
        if pid not in por_id:
            raise AjusteInvalido(f"el ajuste apunta a una pregunta inexistente: {pid}")

    elegidas = [
        pid
        for pid, r in por_revision.items()
        if r.get("elegida") and r.get("decision") != "descartar"
    ]
    elegidas += [pid for pid, a in por_ajuste.items() if a["accion"] == "agregar"]
    descartadas = {pid for pid, a in por_ajuste.items() if a["accion"] == "descartar"}

    banco = []
    for pid in dict.fromkeys(elegidas):
        if pid in descartadas:
            continue
        p = copy.deepcopy(por_id[pid])
        r = por_revision.get(pid, {})
        if r.get("pregunta_corregida"):
            p["texto"] = r["pregunta_corregida"]
        if r.get("respuesta_corregida"):
            p["respuesta_oraculo"] = r["respuesta_corregida"]
        if r.get("claves_corregidas"):
            p["respuesta_clave"] = [
                c.strip() for c in r["claves_corregidas"].split("|") if c.strip()
            ]
        a = por_ajuste.get(pid, {})
        _aplicar(p, a, spans)
        _recalcular_pasos(p, orden, a)
        p["estado_verificacion"] = f"verificado_{autor.lower()}"
        p["revision"] = {
            "verificado_por": ajustes["revisor"],
            "fecha": ajustes["fecha"],
            "decision_revisor": r.get("decision") or ("agregada" if a else ""),
            "notas_revisor": r.get("notas", ""),
            "ajuste": a.get("motivo"),
        }
        banco.append(p)
    return banco
