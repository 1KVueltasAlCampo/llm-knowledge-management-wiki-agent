"""Punto de equilibrio entre wiki y RAG (script de análisis; no llama a ningún modelo)."""

from __future__ import annotations

import importlib.util
from pathlib import Path

RUTA = Path(__file__).resolve().parent.parent / "scripts" / "punto_de_equilibrio.py"
_spec = importlib.util.spec_from_file_location("punto_de_equilibrio", RUTA)
assert _spec and _spec.loader
modulo = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(modulo)


def test_equilibrio_cuando_el_wiki_es_mas_barato_por_consulta() -> None:
    # el wiki cuesta 1.00 más de ingesta y ahorra 0.01 por consulta: se amortiza en 100 consultas
    assert modulo.equilibrio(1.10, 0.01, 0.10, 0.02) == 100.0


def test_no_hay_equilibrio_si_el_wiki_es_mas_caro_por_consulta() -> None:
    assert modulo.equilibrio(1.0, 0.002, 0.0, 0.001) is None


def test_equilibrio_cero_si_el_wiki_no_cuesta_mas_en_ningun_momento() -> None:
    assert modulo.equilibrio(0.0, 0.001, 0.0, 0.002) == 0.0


def test_tabla_acumula_la_ingesta_y_promedia_la_consulta() -> None:
    def ingesta(sistema: str, paso: int, costo: float) -> dict:
        return {"system": sistema, "ingest_step": paso, "cost_usd": costo, "latency_s": 2.0}

    def respuesta(sistema: str, paso: int, costo: float) -> dict:
        return {"system": sistema, "ingest_step": paso, "cost_usd": costo, "latency_s": 1.0}

    ingestas = [
        ingesta("wiki", 1, 0.5),
        ingesta("wiki", 2, 0.5),
        ingesta("rag", 1, 0),
        ingesta("rag", 2, 0),
    ]
    respuestas = [
        respuesta("wiki", 2, 0.001),
        respuesta("wiki", 2, 0.003),
        respuesta("rag", 2, 0.002),
        respuesta("rag", 0, 0.002),  # el paso 0 no tiene los dos sistemas completos de ingesta
    ]
    filas = modulo.tabla(ingestas, respuestas)
    assert [f["paso"] for f in filas] == [2]
    fila = filas[0]
    assert fila["ingesta_usd_wiki"] == 1.0
    assert abs(fila["consulta_usd_wiki"] - 0.002) < 1e-12
    assert fila["equilibrio_usd"] is None  # mismo costo por consulta: no se amortiza
