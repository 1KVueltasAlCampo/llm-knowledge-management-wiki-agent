"""Ampliar el banco al corpus de 100 papers: reordenar, resolver citas y construir preguntas."""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from typing import Any

import pytest

from wikillm.corpus.spans import calcular_spans
from wikillm.eval import __main__ as cli
from wikillm.eval.ampliacion import CitaNoEncontrada, construir_preguntas, reordenar_banco
from wikillm.eval.banco import validar_banco

ORDEN = {"P1": 3, "P2": 41, "P3": 60}


def _viejas() -> list[dict[str, Any]]:
    base = {"autor": "A", "estado_verificacion": "acordado", "evidencia": []}
    return [
        {
            **base,
            "id": "Q1",
            "texto": "t1",
            "tipo": "T1",
            "respuesta_oraculo": "o",
            "fuentes_requeridas": ["P2"],
            "ingesta_minima": 7,
        },
        {
            **base,
            "id": "Q5",
            "texto": "t5",
            "tipo": "T5",
            "respuesta_oraculo": "no",
            "fuentes_requeridas": [],
            "ingesta_minima": None,
        },
        {
            **base,
            "id": "Q4",
            "texto": "t4",
            "tipo": "T4",
            "respuesta_oraculo": "viejo",
            "respuesta_clave": ["1"],
            "fuentes_requeridas": ["P1", "P3"],
            "ingesta_minima": 2,
            "respuesta_por_paso": [
                {"desde": 9, "respuesta_oraculo": "nuevo", "respuesta_clave": ["2"]}
            ],
        },
    ]


def test_reordenar_recalcula_t1_t5_y_t4_sin_mutar_la_entrada():
    banco = _viejas()
    copia = copy.deepcopy(banco)
    nuevo = {p["id"]: p for p in reordenar_banco(banco, ORDEN)}
    assert nuevo["Q1"]["ingesta_minima"] == 41
    assert nuevo["Q5"]["ingesta_minima"] is None
    assert nuevo["Q4"]["ingesta_minima"] == 3
    assert nuevo["Q4"]["respuesta_por_paso"][0]["desde"] == 60
    assert banco == copia


CUERPO = (
    "# Intro\n\nFirst paragraph about nothing.\n\n"
    "RAPTOR paired with **GPT-4** sets a new state-of-the-art with an accuracy of 82.6%.\n\n"
    "Last paragraph.\n"
)


def _spans() -> list[dict[str, Any]]:
    return [s.como_dict() for s in calcular_spans("P1", "v1", CUERPO)]


def _gold(carpeta: Path) -> None:
    carpeta.mkdir(parents=True, exist_ok=True)
    (carpeta / "P1.md").write_text(
        f"---\narxiv_id: P1\nversion: v1\n---\n\n{CUERPO}", encoding="utf-8"
    )


def _definicion(**cambios: Any) -> dict[str, Any]:
    base = {
        "id": "JDi-01",
        "texto": "What accuracy does RAPTOR reach on QuALITY with GPT-4?",
        "tipo": "T1",
        "respuesta_oraculo": "82.6%",
        "respuesta_clave": ["82.6"],
        "fuentes_requeridas": ["P1"],
        "citas": [{"paper": "P1", "cita": "paired with GPT-4 sets a new state-of-the-art"}],
        "notas": "ok",
    }
    return {**base, **cambios}


def test_construye_pregunta_con_evidencia_resuelta_y_estado_preliminar(tmp_path: Path):
    _gold(tmp_path / "gold")
    nuevas = construir_preguntas([_definicion()], _spans(), tmp_path / "gold", origen="def.json")
    p = nuevas[0]
    assert p["estado_verificacion"] == "verificado_a" and p["autor"] == "A"
    assert "cruzada" not in p["revision"] and p["revision"]["origen"] == "def.json"
    assert len(p["evidencia"]) == 1
    span = next(s for s in _spans() if s["span_id"] == p["evidencia"][0]["span_id"])
    assert p["evidencia"][0]["sha256"] == span["sha256"]
    assert span["inicio"] > 0  # no es el primer bloque


def test_cita_inexistente_falla(tmp_path: Path):
    _gold(tmp_path / "gold")
    definicion = _definicion(citas=[{"paper": "P1", "cita": "texto que no existe"}])
    with pytest.raises(CitaNoEncontrada, match="JDi-01"):
        construir_preguntas([definicion], _spans(), tmp_path / "gold", origen="def.json")


def test_t5_no_lleva_evidencia_ni_fuentes(tmp_path: Path):
    _gold(tmp_path / "gold")
    t5 = _definicion(
        id="JDi-13",
        tipo="T5",
        respuesta_clave=[],
        fuentes_requeridas=[],
        citas=[],
        respuesta_oraculo="The ingested corpus does not contain this information.",
    )
    p = construir_preguntas([t5], _spans(), tmp_path / "gold", origen="def.json")[0]
    assert p["evidencia"] == [] and p["fuentes_requeridas"] == [] and p["ingesta_minima"] is None


def _escribir(ruta: Path, filas: list[dict[str, Any]]) -> None:
    ruta.write_text("\n".join(json.dumps(f) for f in filas) + "\n", encoding="utf-8")


def _armar(tmp_path: Path, definicion: dict[str, Any]) -> list[str]:
    _gold(tmp_path / "gold")
    _escribir(tmp_path / "spans.jsonl", _spans())
    _escribir(
        tmp_path / "manifest.jsonl",
        [{"arxiv_id": a, "orden_ingesta": o} for a, o in ORDEN.items()],
    )
    banco = [dict(p, fuentes_requeridas=[f for f in p["fuentes_requeridas"]]) for p in _viejas()]
    _escribir(tmp_path / "banco.jsonl", banco)
    (tmp_path / "def.json").write_text(json.dumps([definicion]), encoding="utf-8")
    return [
        "wikillm.eval",
        "ampliar-banco",
        "--banco",
        str(tmp_path / "banco.jsonl"),
        "--definiciones",
        str(tmp_path / "def.json"),
        "--manifest",
        str(tmp_path / "manifest.jsonl"),
        "--spans",
        str(tmp_path / "spans.jsonl"),
        "--gold",
        str(tmp_path / "gold"),
        "--salida",
        str(tmp_path / "banco_100.jsonl"),
    ]


def test_comando_escribe_un_banco_valido(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(sys, "argv", _armar(tmp_path, _definicion()))
    assert cli.main() == 0
    banco = [json.loads(x) for x in (tmp_path / "banco_100.jsonl").read_text("utf-8").splitlines()]
    assert len(banco) == 4
    assert validar_banco(banco, ORDEN) == []
    assert next(p for p in banco if p["id"] == "JDi-01")["ingesta_minima"] == 3


def test_comando_con_cita_inexistente_da_codigo_1_y_no_escribe(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    malo = _definicion(citas=[{"paper": "P1", "cita": "no existe"}])
    monkeypatch.setattr(sys, "argv", _armar(tmp_path, malo))
    assert cli.main() == 1
    assert not (tmp_path / "banco_100.jsonl").exists()


def test_acordar_por_decision_anota_que_no_hubo_revision_cruzada_y_no_muta_la_entrada():
    from wikillm.eval.ampliacion import acordar_por_decision

    entrada = [{"id": "X1", "estado_verificacion": "verificado_b", "revision": {"origen": "x"}}]
    salida = acordar_por_decision(entrada, decision="0010", fecha="2026-11-16")
    assert salida[0]["estado_verificacion"] == "acordado"
    assert salida[0]["revision"]["origen"] == "x"
    assert salida[0]["revision"]["acordado"] == {
        "fecha": "2026-11-16",
        "por_decision": "0010",
        "revision_cruzada": False,
    }
    assert entrada[0]["estado_verificacion"] == "verificado_b"
