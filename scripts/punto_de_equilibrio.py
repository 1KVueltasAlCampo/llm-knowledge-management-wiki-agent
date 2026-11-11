"""Punto de equilibrio entre compilar por adelantado (wiki) y recuperar en cada consulta (RAG).

Lee una corrida del arnés (``ingestas.jsonl`` y ``respuestas.jsonl``) y, para cada paso de ingesta
en que se hicieron preguntas, calcula por sistema:

- ``ingesta``: costo (y segundos) acumulado de ingerir los papers hasta ese paso;
- ``consulta``: costo (y segundos) medio de una respuesta en ese paso, incluidas las abstenciones.

Con eso, el wiki empata con el RAG cuando
``ingesta_wiki + n * consulta_wiki = ingesta_rag + n * consulta_rag``. Se despeja ``n``, el número
de consultas que amortiza la diferencia de ingesta. Si el wiki es más caro por consulta, ``n`` no
existe: compilar no se compensa nunca en esa métrica. No se llama a ningún modelo.

Uso:  python scripts/punto_de_equilibrio.py results/<corrida> [--salida equilibrio.csv]
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from collections.abc import Iterable
from pathlib import Path
from typing import Any

SISTEMAS = ("rag", "wiki")


def leer(ruta: Path) -> list[dict[str, Any]]:
    return [json.loads(x) for x in ruta.read_text("utf-8").splitlines() if x.strip()]


def equilibrio(ingesta_wiki: float, consulta_wiki: float, ingesta_rag: float, consulta_rag: float):
    """Consultas que igualan los dos costos totales; ``None`` si no hay punto de equilibrio.

    Devuelve 0.0 si el wiki ya cuesta menos o igual sin ninguna consulta y no es más caro después.
    """
    ahorro_por_consulta = consulta_rag - consulta_wiki
    sobrecosto_inicial = ingesta_wiki - ingesta_rag
    if sobrecosto_inicial <= 0 and ahorro_por_consulta >= 0:
        return 0.0
    if ahorro_por_consulta <= 0:
        return None
    return sobrecosto_inicial / ahorro_por_consulta


def tabla(ingestas: Iterable[dict[str, Any]], respuestas: Iterable[dict[str, Any]]) -> list[dict]:
    """Una fila por paso con preguntas: ingesta acumulada y consulta media de cada sistema."""
    acumulado = {s: defaultdict(float) for s in SISTEMAS}  # sistema -> paso -> costo de ESE paso
    segundos = {s: defaultdict(float) for s in SISTEMAS}
    for fila in ingestas:
        acumulado[fila["system"]][fila["ingest_step"]] += fila["cost_usd"]
        segundos[fila["system"]][fila["ingest_step"]] += fila["latency_s"]
    por_paso: dict[tuple[str, int], list[dict[str, Any]]] = defaultdict(list)
    for fila in respuestas:
        por_paso[(fila["system"], fila["ingest_step"])].append(fila)

    pasos = sorted({paso for (_, paso) in por_paso})
    filas = []
    for paso in pasos:
        if paso == 0:
            continue  # sin papers ingeridos no hay ingesta que amortizar
        datos: dict[str, float] = {"paso": paso}
        for s in SISTEMAS:
            resp = por_paso.get((s, paso), [])
            if not resp:
                break
            datos[f"ingesta_usd_{s}"] = sum(v for k, v in acumulado[s].items() if k <= paso)
            datos[f"ingesta_s_{s}"] = sum(v for k, v in segundos[s].items() if k <= paso)
            datos[f"consulta_usd_{s}"] = sum(r["cost_usd"] for r in resp) / len(resp)
            datos[f"consulta_s_{s}"] = sum(r["latency_s"] for r in resp) / len(resp)
            datos[f"n_{s}"] = len(resp)
        else:
            for unidad in ("usd", "s"):
                n = equilibrio(
                    datos[f"ingesta_{unidad}_wiki"],
                    datos[f"consulta_{unidad}_wiki"],
                    datos[f"ingesta_{unidad}_rag"],
                    datos[f"consulta_{unidad}_rag"],
                )
                datos[f"equilibrio_{unidad}"] = n
                datos[f"por_paper_{unidad}"] = None if n is None else n / paso
            filas.append(datos)
    return filas


def _fmt(valor: float | None, formato: str = "{:,.1f}") -> str:
    return "nunca" if valor is None else formato.format(valor)


def imprimir(filas: list[dict]) -> None:
    print("Consultas necesarias para que compilar (wiki) iguale a recuperar (RAG).")
    print("«nunca» = el wiki es más caro por consulta, así que la ingesta no se compensa.\n")
    print(
        f"{'paso':>4} {'ingesta wiki':>13} {'consulta wiki':>14} {'consulta RAG':>13} "
        f"{'n (USD)':>9} {'n/paper':>8} {'n (seg)':>9}"
    )
    for f in filas:
        print(
            f"{f['paso']:>4} {f['ingesta_usd_wiki']:>12.4f}$ {f['consulta_usd_wiki']:>13.6f}$ "
            f"{f['consulta_usd_rag']:>12.6f}$ {_fmt(f['equilibrio_usd']):>9} "
            f"{_fmt(f['por_paper_usd']):>8} {_fmt(f['equilibrio_s']):>9}"
        )


def main() -> int:
    analizador = argparse.ArgumentParser(description=__doc__)
    analizador.add_argument("corrida", type=Path, help="carpeta results/<corrida>")
    analizador.add_argument("--salida", type=Path, help="CSV opcional con la tabla completa")
    args = analizador.parse_args()
    ingestas = leer(args.corrida / "ingestas.jsonl")
    respuestas = leer(args.corrida / "respuestas.jsonl")
    filas = tabla(ingestas, respuestas)
    if not filas:
        print("La corrida no tiene pasos con respuestas de los dos sistemas.", file=sys.stderr)
        return 1
    imprimir(filas)
    if args.salida:
        with args.salida.open("w", newline="", encoding="utf-8") as destino:
            escritor = csv.DictWriter(destino, fieldnames=list(filas[0]))
            escritor.writeheader()
            escritor.writerows(filas)
        print(f"\nTabla completa en {args.salida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
