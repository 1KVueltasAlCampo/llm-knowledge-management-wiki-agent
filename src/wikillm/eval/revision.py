"""Página HTML local para revisar borradores: marcar, corregir, elegir y exportar.

La página trae citas literales de arXiv, así que se escribe en `data/preguntas/anotacion/`
(ignorada por Git). Lo que decide la persona se guarda en el navegador y se exporta como CSV
(compatible con `acuerdo`) y JSON (para pasar al banco).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from wikillm.eval.banco import validar_banco

PLANTILLA = Path(__file__).with_name("plantilla_revision.html")


def preparar_items(
    preguntas: list[dict[str, Any]],
    citas: list[dict[str, Any]],
    manifest: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    por_paper = {f["arxiv_id"]: f for f in manifest}
    orden = {f["arxiv_id"]: int(f["orden_ingesta"]) for f in manifest}
    por_pregunta: dict[str, list[dict[str, str]]] = {}
    for cita in citas:
        por_pregunta.setdefault(cita["question_id"], []).append(
            {"span_id": cita["span_id"], "cita": cita["cita"]}
        )
    items = []
    for p in preguntas:
        problemas = [
            texto.split(": ", 1)[1]
            for texto in validar_banco([p], orden)
            if texto.startswith(f"{p['id']}:")
        ]
        fuentes = []
        for arxiv_id in p.get("fuentes_requeridas") or []:
            fila = por_paper.get(arxiv_id, {})
            version = fila.get("version", "")
            fuentes.append(
                {
                    "arxiv_id": arxiv_id,
                    "titulo": fila.get("titulo", ""),
                    "orden": fila.get("orden_ingesta"),
                    "url": f"https://arxiv.org/html/{arxiv_id}{version}",
                }
            )
        externo = p.get("fuente_externa")
        if externo:
            fuentes.append(
                {
                    "arxiv_id": externo["arxiv_id"],
                    "titulo": f"(fuera del corpus) término: {externo['termino']}",
                    "orden": None,
                    "url": f"https://arxiv.org/abs/{externo['arxiv_id']}",
                }
            )
        items.append(
            {
                "id": p["id"],
                "tipo": p["tipo"],
                "texto": p["texto"],
                "respuesta": p["respuesta_oraculo"],
                "claves": p.get("respuesta_clave") or [],
                "por_paso": p.get("respuesta_por_paso") or [],
                "ingesta_minima": p.get("ingesta_minima"),
                "fuentes": fuentes,
                "evidencias": por_pregunta.get(p["id"], []),
                "problemas": problemas,
            }
        )
    return items


def _json_seguro(datos: Any) -> str:
    # Evita que un "</script>" dentro de una cita cierre la etiqueta.
    return json.dumps(datos, ensure_ascii=False).replace("</", "<\\/")


def escribir_html(ruta: Path, items: list[dict[str, Any]], autor: str) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    plantilla = PLANTILLA.read_text(encoding="utf-8")
    html = plantilla.replace("__DATOS__", _json_seguro(items)).replace("__AUTOR__", autor)
    ruta.write_text(html, encoding="utf-8")
