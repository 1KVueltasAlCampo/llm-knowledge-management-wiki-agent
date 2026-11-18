"""Comparar cada brazo consigo mismo entre dos corridas: mismo banco, corpus de otro tamaño.

Empareja por pregunta el paso final de la corrida base con el de la ampliada, y reutiliza el
bootstrap y el McNemar exacto de `estadistica`. Las preguntas que solo existen en la ampliada se
muestran aparte como preliminares.
"""

from __future__ import annotations

import json
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

from wikillm.eval.correctitud import CORRECTA
from wikillm.eval.estadistica import bootstrap_diferencia, mcnemar_exacto
from wikillm.eval.informe import _celda, _escribir_csv

LIMITES = (
    "Las dos corridas difieren en el **orden** de ingesta y en el **tamaño** del corpus, así "
    "que el efecto de añadir papers se mezcla con el del cambio de orden. Los intervalos "
    "suponen preguntas independientes y no hay corrección por comparaciones múltiples; con "
    "pocas preguntas por tipo son orientativos. El wiki no es determinista y cada corrida es "
    "una sola ejecución."
)
COLUMNAS_NUEVAS = (
    "n",
    "cobertura_rag",
    "cobertura_wiki",
    "diferencia",
    "ic95_inf",
    "ic95_sup",
    "solo_rag",
    "solo_wiki",
    "p_mcnemar",
)
COLUMNAS_COSTOS = (
    "corrida",
    "sistema",
    "paso",
    "contexto_medio",
    "costo_por_respuesta",
    "costo_preguntas_total",
    "costo_ingesta_total",
)
COLUMNAS_PARES = (
    "sistema",
    "tipo",
    "n",
    "cobertura_base",
    "cobertura_ampliada",
    "diferencia",
    "ic95_inf",
    "ic95_sup",
    "solo_base",
    "solo_ampliada",
    "p_mcnemar",
)


def _leer(carpeta: Path, nombre: str) -> list[dict[str, Any]]:
    ruta = carpeta / nombre
    if not ruta.is_file():
        return []
    return [json.loads(x) for x in ruta.read_text(encoding="utf-8").splitlines() if x.strip()]


def _en_paso(evaluados: list[dict[str, Any]], paso: int) -> dict[tuple[str, str], dict[str, Any]]:
    return {(e["system"], e["question_id"]): e for e in evaluados if int(e["ingest_step"]) == paso}


def _fila_par(sistema: str, tipo: str, pares: list[tuple[int, int]]) -> dict[str, Any]:
    base = [b for b, _ in pares]
    amp = [a for _, a in pares]
    n = len(pares)
    solo_base = sum(1 for b, a in pares if b and not a)
    solo_amp = sum(1 for b, a in pares if a and not b)
    inf, sup = bootstrap_diferencia(base, amp)
    return {
        "sistema": sistema,
        "tipo": tipo,
        "n": n,
        "cobertura_base": sum(base) / n,
        "cobertura_ampliada": sum(amp) / n,
        "diferencia": (sum(amp) - sum(base)) / n,
        "ic95_inf": inf,
        "ic95_sup": sup,
        "solo_base": solo_base,
        "solo_ampliada": solo_amp,
        "p_mcnemar": mcnemar_exacto(solo_base, solo_amp),
    }


def _pares(
    base: dict[tuple[str, str], dict[str, Any]],
    amp: dict[tuple[str, str], dict[str, Any]],
    comunes: set[str],
) -> list[dict[str, Any]]:
    grupos: dict[tuple[str, str], list[tuple[int, int]]] = defaultdict(list)
    for (sistema, qid), b in sorted(base.items()):
        a = amp.get((sistema, qid))
        if qid not in comunes or a is None or not b["respondible"] or not a["respondible"]:
            continue
        par = (int(b["veredicto"] == CORRECTA), int(a["veredicto"] == CORRECTA))
        grupos[(sistema, "")].append(par)
        grupos[(sistema, b["tipo"])].append(par)
    return [_fila_par(s, t, p) for (s, t), p in sorted(grupos.items())]


def _nuevas(amp: dict[tuple[str, str], dict[str, Any]], nuevas: set[str]) -> dict[str, Any]:
    pares = []
    for qid in sorted(nuevas):
        rag, wiki = amp.get(("rag", qid)), amp.get(("wiki", qid))
        if rag and wiki and rag["respondible"] and wiki["respondible"]:
            pares.append((int(rag["veredicto"] == CORRECTA), int(wiki["veredicto"] == CORRECTA)))
    if not pares:
        return {"n": 0}
    rag_ok, wiki_ok = [r for r, _ in pares], [w for _, w in pares]
    solo_rag = sum(1 for r, w in pares if r and not w)
    solo_wiki = sum(1 for r, w in pares if w and not r)
    inf, sup = bootstrap_diferencia(rag_ok, wiki_ok)
    n = len(pares)
    return {
        "n": n,
        "cobertura_rag": sum(rag_ok) / n,
        "cobertura_wiki": sum(wiki_ok) / n,
        "diferencia": (sum(wiki_ok) - sum(rag_ok)) / n,
        "ic95_inf": inf,
        "ic95_sup": sup,
        "solo_rag": solo_rag,
        "solo_wiki": solo_wiki,
        "p_mcnemar": mcnemar_exacto(solo_rag, solo_wiki),
    }


def _costos(nombre: str, carpeta: Path, paso: int, en_paso: dict[Any, Any]) -> list[dict[str, Any]]:
    filas = []
    for sistema in ("rag", "wiki"):
        del_paso = [e for (s, _), e in en_paso.items() if s == sistema]
        total_preguntas = sum(
            float(r.get("cost_usd", 0))
            for r in _leer(carpeta, "respuestas.jsonl")
            if r["system"] == sistema
        )
        total_ingesta = sum(
            float(r.get("cost_usd", 0))
            for r in _leer(carpeta, "ingestas.jsonl")
            if r["system"] == sistema
        )
        filas.append(
            {
                "corrida": nombre,
                "sistema": sistema,
                "paso": paso,
                "contexto_medio": statistics.fmean(e["context_tokens"] for e in del_paso)
                if del_paso
                else None,
                "costo_por_respuesta": statistics.fmean(float(e["cost_usd"]) for e in del_paso)
                if del_paso
                else None,
                "costo_preguntas_total": total_preguntas,
                "costo_ingesta_total": total_ingesta,
            }
        )
    return filas


def comparar_corridas(
    base: Path, ampliada: Path, paso_base: int, paso_ampliada: int
) -> dict[str, Any]:
    ev_base = _leer(base, "evaluados.jsonl")
    ev_amp = _leer(ampliada, "evaluados.jsonl")
    preguntas_base = {e["question_id"] for e in ev_base}
    preguntas_amp = {e["question_id"] for e in ev_amp}
    en_base, en_amp = _en_paso(ev_base, paso_base), _en_paso(ev_amp, paso_ampliada)
    return {
        "pares": _pares(en_base, en_amp, preguntas_base & preguntas_amp),
        "nuevas": _nuevas(en_amp, preguntas_amp - preguntas_base),
        "costos": [
            *_costos(base.name, base, paso_base, en_base),
            *_costos(ampliada.name, ampliada, paso_ampliada, en_amp),
        ],
    }


def _tabla(filas: list[dict[str, Any]], columnas: tuple[str, ...]) -> str:
    lineas = ["| " + " | ".join(columnas) + " |", "|" + "|".join(["---"] * len(columnas)) + "|"]
    for f in filas:
        lineas.append("| " + " | ".join(_celda(f.get(c)) for c in columnas) + " |")
    return "\n".join(lineas)


def escribir_comparacion(
    base: Path, ampliada: Path, paso_base: int, paso_ampliada: int, salida: Path
) -> Path:
    r = comparar_corridas(base, ampliada, paso_base, paso_ampliada)
    salida.mkdir(parents=True, exist_ok=True)
    _escribir_csv(
        salida / "comparacion.csv", [{c: f[c] for c in COLUMNAS_PARES} for f in r["pares"]]
    )
    totales = [f for f in r["pares"] if f["tipo"] == ""]
    por_tipo = [f for f in r["pares"] if f["tipo"] != ""]
    nuevas = r["nuevas"]
    if nuevas["n"]:
        seccion_nuevas = (
            f"Son {nuevas['n']} preguntas que solo están en `{ampliada.name}`; con pocas "
            "preguntas por tipo y una sola ejecución, sus resultados son preliminares.\n\n"
            f"{_tabla([nuevas], COLUMNAS_NUEVAS)}"
        )
    else:
        seccion_nuevas = "No hay preguntas que existan solo en la corrida ampliada."
    columnas = COLUMNAS_PARES
    texto = (
        f"# Comparación entre corridas: `{base.name}` (paso {paso_base}) y "
        f"`{ampliada.name}` (paso {paso_ampliada})\n\n"
        "Pares: preguntas respondibles en ambos pasos y presentes en las dos corridas, por "
        "sistema. `diferencia` = cobertura de la ampliada menos la de la base; `solo_base` y "
        "`solo_ampliada` "
        "son los pares discordantes.\n\n"
        f"{LIMITES}\n\n"
        "## Por sistema\n\n"
        f"{_tabla(totales, columnas)}\n\n"
        "## Por sistema y tipo de pregunta\n\n"
        f"{_tabla(por_tipo, columnas)}\n\n"
        "## Preguntas nuevas (preliminares)\n\n"
        f"{seccion_nuevas}\n\n"
        "## Contexto y costo\n\n"
        f"{_tabla(r['costos'], COLUMNAS_COSTOS)}\n"
    )
    (salida / "comparacion.md").write_text(texto, encoding="utf-8")
    return salida
