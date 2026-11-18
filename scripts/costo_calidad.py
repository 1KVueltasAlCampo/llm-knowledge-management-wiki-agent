"""Calidad frente a costo y tiempo: ingesta por paso, consulta por sistema y escenarios de uso.

Une tres fuentes ya guardadas (no llama a ningún modelo):
- ``results/construccion-1/ingesta.log``: costo y segundos de construir el wiki, paper por paper;
- ``results/<corrida>/evaluados.jsonl``: costo, tiempo y veredicto de cada respuesta;
- ``results/<corrida>/ingestas.jsonl``: segundos que tardó el RAG en ingerir (embeddings).

Escribe en ``results/costo-calidad/`` el costo de ingesta por paso (CSV y SVG), la tabla de calidad
y costo por sistema y paso, y los escenarios de «cuántas consultas se atienden». Uso:
  python scripts/costo_calidad.py [--corrida results/ampliado-fases-1]
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

from wikillm.eval.informe import _figura

PATRON_LINEA = re.compile(r"\[(\d+)/\d+\] (\S+): ([\d.]+) s · (\d+) llamadas · ([\d.]+) USD")
ESCENARIOS = (100, 1_000, 10_000)


def leer_jsonl(ruta: Path) -> list[dict[str, Any]]:
    return [json.loads(x) for x in ruta.read_text("utf-8").splitlines() if x.strip()]


def ingesta_del_wiki(log: Path) -> list[dict[str, Any]]:
    """Un paper por fila, en el orden de ingesta, con su costo y su costo acumulado.

    Si un paper aparece dos veces (reanudación), vale la última línea.
    """
    por_paper: dict[str, dict[str, Any]] = {}
    for linea in log.read_text("utf-8").splitlines():
        m = PATRON_LINEA.search(linea)
        if m:
            _, arxiv, segundos, llamadas, usd = m.groups()
            por_paper[arxiv] = {
                "arxiv_id": arxiv,
                "segundos": float(segundos),
                "llamadas": int(llamadas),
                "usd": float(usd),
            }
    filas = list(por_paper.values())
    acumulado_usd = acumulado_s = 0.0
    for paso, fila in enumerate(filas, start=1):
        acumulado_usd += fila["usd"]
        acumulado_s += fila["segundos"]
        fila.update(paso=paso, usd_acumulado=acumulado_usd, segundos_acumulados=acumulado_s)
    return filas


def por_sistema_y_paso(evaluados: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grupos: dict[tuple[str, int], list[dict[str, Any]]] = defaultdict(list)
    for e in evaluados:
        grupos[(e["system"], int(e["ingest_step"]))].append(e)
    filas = []
    for (sistema, paso), g in sorted(grupos.items(), key=lambda kv: (kv[0][1], kv[0][0])):
        correctas = sum(e["veredicto"] == "correcta" for e in g)
        usd = sum(e["cost_usd"] for e in g)
        filas.append(
            {
                "sistema": sistema,
                "paso": paso,
                "preguntas": len(g),
                "exactitud": correctas / len(g),
                "usd_por_consulta": usd / len(g),
                "usd_por_correcta": usd / correctas if correctas else None,
                "segundos_media": statistics.mean(e["latency_s"] for e in g),
                "segundos_mediana": statistics.median(e["latency_s"] for e in g),
                "tokens_entrada_media": statistics.mean(e["input_tokens"] for e in g),
            }
        )
    return filas


def escenarios(
    filas: list[dict[str, Any]], construccion_usd: float, construccion_s: float, paso: int
) -> list[dict[str, Any]]:
    """Costo total y por respuesta correcta al atender N consultas con el corpus completo."""
    base = {f["sistema"]: f for f in filas if f["paso"] == paso}
    salida = []
    for n in ESCENARIOS:
        for sistema, f in sorted(base.items()):
            fijo_usd = construccion_usd if sistema == "wiki" else 0.0
            fijo_s = construccion_s if sistema == "wiki" else 0.0
            total = fijo_usd + n * f["usd_por_consulta"]
            salida.append(
                {
                    "consultas": n,
                    "sistema": sistema,
                    "usd_total": total,
                    "usd_por_correcta": total / (n * f["exactitud"]),
                    "horas_total": (fijo_s + n * f["segundos_media"]) / 3600,
                }
            )
    return salida


def escribir_csv(ruta: Path, filas: list[dict[str, Any]]) -> None:
    with ruta.open("w", encoding="utf-8", newline="") as f:
        escritor = csv.DictWriter(f, fieldnames=list(filas[0]))
        escritor.writeheader()
        escritor.writerows(filas)


def main() -> None:
    a = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    a.add_argument("--corrida", type=Path, default=Path("results/ampliado-fases-1"))
    a.add_argument("--construccion", type=Path, default=Path("results/construccion-1/ingesta.log"))
    a.add_argument("--salida", type=Path, default=Path("results/costo-calidad"))
    args = a.parse_args()
    args.salida.mkdir(parents=True, exist_ok=True)

    wiki = ingesta_del_wiki(args.construccion)
    if not wiki:
        raise SystemExit(f"{args.construccion} no trae líneas de ingesta")
    escribir_csv(args.salida / "ingesta_wiki_por_paper.csv", wiki)
    total_usd, total_s = wiki[-1]["usd_acumulado"], wiki[-1]["segundos_acumulados"]
    ingestas_rag = [i for i in leer_jsonl(args.corrida / "ingestas.jsonl") if i["system"] == "rag"]
    rag_s = sum(i["latency_s"] for i in ingestas_rag)

    pasos = [p for p in range(10, len(wiki) + 1, 10)]
    for nombre, campo, etiqueta in (
        ("ingesta_usd_acumulado", "usd_acumulado", "USD acumulados de ingesta"),
        ("ingesta_minutos_acumulados", "segundos_acumulados", "Minutos acumulados de ingesta"),
    ):
        escala = 60 if campo == "segundos_acumulados" else 1
        serie = [
            (f["paso"], f[campo] / escala) for f in wiki if f["paso"] in pasos or f["paso"] == 1
        ]
        sin_costo = [(x, 0.0) for x, _ in serie] if campo == "usd_acumulado" else None
        series = {"wiki": serie}
        if sin_costo:
            series["rag"] = sin_costo
        titulo = f"{etiqueta}: wiki frente a RAG"
        (args.salida / f"{nombre}.svg").write_text(_figura(titulo, etiqueta, series), "utf-8")

    evaluados = leer_jsonl(args.corrida / "evaluados.jsonl")
    filas = por_sistema_y_paso(evaluados)
    escribir_csv(args.salida / "calidad_costo_por_paso.csv", filas)
    ultimo = max(f["paso"] for f in filas)
    casos = escenarios(filas, total_usd, total_s, ultimo)
    escribir_csv(args.salida / "escenarios.csv", casos)

    por = {(f["sistema"], f["paso"]): f for f in filas}
    r, w = por[("rag", ultimo)], por[("wiki", ultimo)]
    adicionales = (w["exactitud"] - r["exactitud"]) * w["preguntas"]
    resumen = {
        "construccion_wiki_usd": round(total_usd, 4),
        "construccion_wiki_horas": round(total_s / 3600, 2),
        "papers": len(wiki),
        "ingesta_rag_segundos": round(rag_s, 1),
        "usd_primer_paper": wiki[0]["usd"],
        "usd_ultimo_paper": wiki[-1]["usd"],
        "razon_costo_consulta": round(w["usd_por_consulta"] / r["usd_por_consulta"], 2),
        "razon_tiempo_consulta": round(w["segundos_media"] / r["segundos_media"], 2),
        "respuestas_correctas_adicionales": round(adicionales, 1),
        "usd_por_correcta_adicional_solo_consulta": round(
            (w["usd_por_consulta"] - r["usd_por_consulta"]) * w["preguntas"] / adicionales, 5
        )
        if adicionales > 0
        else None,
    }
    (args.salida / "resumen.json").write_text(json.dumps(resumen, indent=2), "utf-8")

    print(json.dumps(resumen, indent=2))
    for f in filas:
        print(
            f"{f['sistema']:>4} paso {f['paso']:>3}: exactitud {f['exactitud']:.2f} | "
            f"{f['usd_por_consulta']:.6f} USD/consulta | {f['segundos_media']:.1f} s media "
            f"({f['segundos_mediana']:.1f} mediana) | USD/correcta {f['usd_por_correcta']:.6f}"
        )
    for c in casos:
        print(
            f"{c['consultas']:>6} consultas {c['sistema']:>4}: {c['usd_total']:.2f} USD, "
            f"{c['usd_por_correcta']:.5f} USD/correcta, {c['horas_total']:.1f} h"
        )


if __name__ == "__main__":
    main()
