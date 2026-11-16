"""Análisis de fallos: por qué falla cada brazo, a partir de lo que guardó la corrida.

Una sola categoría por respuesta no correcta, calculada con la marca de abstención, los papers que
citó (por `span_id`) y las `fuentes_requeridas` de la pregunta. No llama a ningún modelo.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

from wikillm.eval.correctitud import CORRECTA, INDETERMINADA

CATEGORIAS = (
    "abstencion_erronea",
    "sin_fuente",
    "fuente_parcial",
    "fuentes_completas_error",
    "obsoleta",
    "indeterminada",
    "no_se_abstuvo",
)

NOTA = (
    "Las categorías son una pista, no un diagnóstico: citar todas las fuentes requeridas no prueba "
    "que el modelo las haya leído bien, y una respuesta correcta que la clave no reconoce cae en "
    "`fuentes_completas_error`. `detalle.csv` permite revisar casos a mano."
)


def _papers_citados(fila: dict[str, Any]) -> set[str]:
    return {str(c).split("#", 1)[0] for c in fila.get("citations") or []}


def categorizar(fila: dict[str, Any], banco: dict[str, dict[str, Any]]) -> str | None:
    """Categoría del fallo de una respuesta, o None si es correcta."""
    if fila["veredicto"] == CORRECTA:
        return None
    if not fila["respondible"]:
        return "no_se_abstuvo"
    if fila.get("obsoleta"):
        return "obsoleta"
    if fila["veredicto"] == INDETERMINADA:
        return "indeterminada"
    if fila.get("abstained"):
        return "abstencion_erronea"
    requeridas = set(banco[fila["question_id"]].get("fuentes_requeridas") or [])
    citadas = _papers_citados(fila) & requeridas
    if not citadas:
        return "sin_fuente"
    return "fuentes_completas_error" if citadas == requeridas else "fuente_parcial"


def _tabla_conteos(
    clave_titulos: tuple[str, ...], contadores: dict[tuple[str, ...], Counter[str]]
) -> str:
    columnas = (*clave_titulos, *CATEGORIAS, "total")
    lineas = ["| " + " | ".join(columnas) + " |", "|" + "|".join(["---"] * len(columnas)) + "|"]
    for clave in sorted(contadores):
        cuentas = contadores[clave]
        celdas = [*clave, *(str(cuentas.get(c, 0)) for c in CATEGORIAS), str(sum(cuentas.values()))]
        lineas.append("| " + " | ".join(celdas) + " |")
    return "\n".join(lineas)


def escribir_fallos(carpeta: Path, banco: list[dict[str, Any]]) -> Path:
    """Escribe `<carpeta>/fallos/detalle.csv` y `resumen.md`; devuelve esa carpeta."""
    evaluados = [
        json.loads(linea)
        for linea in (carpeta / "evaluados.jsonl").read_text(encoding="utf-8").splitlines()
        if linea.strip()
    ]
    por_id = {p["id"]: p for p in banco}
    filas = []
    for e in sorted(
        evaluados, key=lambda x: (x["system"], int(x["ingest_step"]), x["question_id"])
    ):
        categoria = categorizar(e, por_id)
        if categoria is not None:
            filas.append(
                {
                    "question_id": e["question_id"],
                    "system": e["system"],
                    "ingest_step": e["ingest_step"],
                    "tipo": e["tipo"],
                    "categoria": categoria,
                }
            )

    destino = carpeta / "fallos"
    destino.mkdir(exist_ok=True)
    columnas = ["question_id", "system", "ingest_step", "tipo", "categoria"]
    with (destino / "detalle.csv").open("w", encoding="utf-8", newline="") as f:
        escritor = csv.writer(f, lineterminator="\n")
        escritor.writerow(columnas)
        for fila in filas:
            escritor.writerow([fila[c] for c in columnas])

    por_sistema: dict[tuple[str, ...], Counter[str]] = {}
    por_tipo: dict[tuple[str, ...], Counter[str]] = {}
    for fila in filas:
        por_sistema.setdefault((fila["system"],), Counter())[fila["categoria"]] += 1
        por_tipo.setdefault((fila["system"], fila["tipo"]), Counter())[fila["categoria"]] += 1
    (destino / "resumen.md").write_text(
        f"# Análisis de fallos de la corrida {carpeta.name}\n\n{NOTA}\n\n"
        f"Respuestas no correctas: {len(filas)} de {len(evaluados)} (todos los pasos).\n\n"
        "## Por sistema\n\n"
        f"{_tabla_conteos(('system',), por_sistema)}\n\n"
        "## Por sistema y tipo de pregunta\n\n"
        f"{_tabla_conteos(('system', 'tipo'), por_tipo)}\n",
        encoding="utf-8",
    )
    return destino
