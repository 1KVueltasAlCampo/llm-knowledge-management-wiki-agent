"""Métricas sobre el archivo de resultados del arnés (`specs/contrato-resultados.md`)."""

from __future__ import annotations

import json
import statistics
from collections import defaultdict
from collections.abc import Callable
from pathlib import Path
from typing import Any

from wikillm.eval.banco import esperado_en_paso
from wikillm.eval.correctitud import CORRECTA, INDETERMINADA, clave_presente, evaluar

OBLIGATORIOS_RESULTADO = (
    "run_id",
    "question_id",
    "system",
    "ingest_step",
    "answer",
    "abstained",
    "citations",
    "context_tokens",
    "input_tokens",
    "output_tokens",
    "latency_s",
    "cost_usd",
    "model",
)

Juez = Callable[[dict[str, Any], dict[str, Any], Any], str]


def leer_resultados(ruta: Path) -> list[dict[str, Any]]:
    filas = [
        json.loads(linea)
        for linea in ruta.read_text(encoding="utf-8").splitlines()
        if linea.strip()
    ]
    for numero, fila in enumerate(filas, start=1):
        faltan = [c for c in OBLIGATORIOS_RESULTADO if c not in fila]
        if faltan:
            raise ValueError(f"línea {numero}: faltan campos {faltan}")
    return filas


def fundamentacion(
    citas: list[str], paso: int, spans: dict[str, dict[str, Any]], orden: dict[str, int]
) -> float | None:
    """Proporción de citas que existen en el Gold y vienen de un paper ya ingerido."""
    if not citas:
        return None
    validas = 0
    for cita in citas:
        span = spans.get(cita)
        if span is None:
            continue
        if orden.get(span["arxiv_id"], paso + 1) <= paso:
            validas += 1
    return validas / len(citas)


def tras_cambio(pregunta: dict[str, Any], paso: int) -> bool:
    """Una T4 cuya respuesta ya cambió: el paso alcanzó al primer tramo de `respuesta_por_paso`."""
    tramos = pregunta.get("respuesta_por_paso") or []
    return bool(tramos) and paso >= min(int(t["desde"]) for t in tramos)


def es_obsoleta(pregunta: dict[str, Any], paso: int, respuesta: str, veredicto: str) -> bool:
    """Tras el cambio, no es correcta y repite todas las claves de la respuesta previa."""
    claves = pregunta.get("respuesta_clave") or []
    if veredicto == CORRECTA or not claves or not tras_cambio(pregunta, paso):
        return False
    return all(clave_presente(c, respuesta) for c in claves)


def evaluar_resultados(
    resultados: list[dict[str, Any]],
    banco: dict[str, dict[str, Any]],
    spans: dict[str, dict[str, Any]],
    orden: dict[str, int],
    juez: Juez | None = None,
) -> list[dict[str, Any]]:
    """Añade a cada resultado su veredicto (capa 1 y, si hay juez, capa 2) y su fundamentación."""
    evaluados = []
    for r in resultados:
        pregunta = banco[r["question_id"]]
        esperado = esperado_en_paso(pregunta, int(r["ingest_step"]))
        capa1 = evaluar(esperado, r["answer"], bool(r["abstained"]))
        veredicto, origen = capa1, "determinista"
        if capa1 == INDETERMINADA and juez is not None:
            veredicto, origen = juez(pregunta, r, esperado), "juez"
        evaluados.append(
            {
                **r,
                "tipo": pregunta["tipo"],
                "respondible": esperado.respondible,
                "veredicto_capa1": capa1,
                "veredicto": veredicto,
                "origen_veredicto": origen,
                "tras_cambio": tras_cambio(pregunta, int(r["ingest_step"])),
                "obsoleta": es_obsoleta(pregunta, int(r["ingest_step"]), r["answer"], veredicto),
                "fundamentacion": fundamentacion(
                    r["citations"], int(r["ingest_step"]), spans, orden
                ),
            }
        )
    return evaluados


def _media(valores: list[float]) -> float | None:
    return statistics.fmean(valores) if valores else None


def agregar(evaluados: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Una fila por (sistema, paso) con cobertura, abstención, fundamentación, contexto y costo."""
    grupos: dict[tuple[str, int], list[dict[str, Any]]] = defaultdict(list)
    for e in evaluados:
        grupos[(e["system"], int(e["ingest_step"]))].append(e)
    filas = []
    for (sistema, paso), grupo in sorted(grupos.items()):
        respondibles = [e for e in grupo if e["respondible"]]
        no_respondibles = [e for e in grupo if not e["respondible"]]
        correctas = [e for e in respondibles if e["veredicto"] == CORRECTA]
        fundadas = [e["fundamentacion"] for e in grupo if e["fundamentacion"] is not None]
        contexto = [float(e["context_tokens"]) for e in grupo]
        actualizadas = [e for e in grupo if e["tras_cambio"]]
        obsoletas = sum(e["obsoleta"] for e in actualizadas)
        filas.append(
            {
                "system": sistema,
                "ingest_step": paso,
                "n": len(grupo),
                "n_respondibles": len(respondibles),
                "cobertura": len(correctas) / len(respondibles) if respondibles else None,
                "indeterminadas": sum(e["veredicto"] == INDETERMINADA for e in grupo),
                "abstencion_correcta": (
                    sum(e["veredicto"] == CORRECTA for e in no_respondibles) / len(no_respondibles)
                    if no_respondibles
                    else None
                ),
                "n_t4_actualizadas": len(actualizadas),
                "obsoletas": obsoletas,
                "tasa_obsoleta": obsoletas / len(actualizadas) if actualizadas else None,
                "fundamentacion_media": _media(fundadas),
                "context_tokens_media": _media(contexto),
                "context_tokens_mediana": statistics.median(contexto) if contexto else None,
                "tokens_por_correcta": sum(contexto) / len(correctas) if correctas else None,
                "costo_usd_total": sum(float(e["cost_usd"]) for e in grupo),
            }
        )
    return filas
