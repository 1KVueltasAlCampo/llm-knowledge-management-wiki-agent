"""Comparar cada brazo consigo mismo entre dos corridas (mismo banco, corpus más grande)."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest

from wikillm.eval import __main__ as cli
from wikillm.eval.entre_corridas import comparar_corridas, escribir_comparacion


def _ev(q: str, sistema: str, paso: int, ok: bool, tipo: str = "T1", respondible: bool = True):
    return {
        "question_id": q,
        "system": sistema,
        "ingest_step": paso,
        "tipo": tipo,
        "respondible": respondible,
        "veredicto": "correcta" if ok else "incorrecta",
        "context_tokens": 100 if sistema == "rag" else 400,
        "cost_usd": 0.001,
    }


def _escribir(carpeta: Path, nombre: str, filas: list[dict[str, Any]]) -> None:
    carpeta.mkdir(parents=True, exist_ok=True)
    (carpeta / nombre).write_text("\n".join(json.dumps(f) for f in filas) + "\n", encoding="utf-8")


def _corridas(tmp_path: Path) -> tuple[Path, Path]:
    base, amp = tmp_path / "base", tmp_path / "amp"
    ev_base = []
    for q, tipo, rag, wiki in (("Q1", "T1", 1, 1), ("Q2", "T1", 0, 1), ("Q3", "T3", 0, 0)):
        ev_base += [_ev(q, "rag", 5, bool(rag), tipo), _ev(q, "wiki", 5, bool(wiki), tipo)]
    ev_base.append(_ev("QX", "rag", 5, True, respondible=False))
    ev_amp = []
    for q, tipo, rag, wiki in (("Q1", "T1", 1, 1), ("Q2", "T1", 1, 0), ("Q3", "T3", 0, 1)):
        ev_amp += [_ev(q, "rag", 10, bool(rag), tipo), _ev(q, "wiki", 10, bool(wiki), tipo)]
    ev_amp += [_ev("QN", "rag", 10, True), _ev("QN", "wiki", 10, False)]  # solo en la ampliada
    _escribir(base, "evaluados.jsonl", ev_base)
    _escribir(amp, "evaluados.jsonl", ev_amp)
    _escribir(base, "respuestas.jsonl", [{"system": "rag", "cost_usd": 0.5}])
    _escribir(amp, "respuestas.jsonl", [{"system": "rag", "cost_usd": 0.7}])
    _escribir(base, "ingestas.jsonl", [{"system": "wiki", "cost_usd": 1.0}])
    _escribir(amp, "ingestas.jsonl", [{"system": "wiki", "cost_usd": 2.5}])
    return base, amp


def test_pares_por_sistema_con_discordantes_y_solo_preguntas_comunes(tmp_path: Path):
    base, amp = _corridas(tmp_path)
    r = comparar_corridas(base, amp, 5, 10)
    rag = next(f for f in r["pares"] if f["sistema"] == "rag" and f["tipo"] == "")
    assert rag["n"] == 3  # QN y QX no entran
    assert rag["cobertura_base"] == pytest.approx(1 / 3)
    assert rag["cobertura_ampliada"] == pytest.approx(2 / 3)
    assert rag["diferencia"] == pytest.approx(1 / 3)
    assert (rag["solo_base"], rag["solo_ampliada"]) == (0, 1)
    wiki = next(f for f in r["pares"] if f["sistema"] == "wiki" and f["tipo"] == "")
    assert (wiki["solo_base"], wiki["solo_ampliada"]) == (1, 1) and wiki["p_mcnemar"] == 1.0


def test_hay_filas_por_tipo(tmp_path: Path):
    base, amp = _corridas(tmp_path)
    r = comparar_corridas(base, amp, 5, 10)
    claves = {(f["sistema"], f["tipo"]) for f in r["pares"]}
    assert {("rag", "T1"), ("rag", "T3"), ("wiki", "T1"), ("wiki", "T3")} <= claves


def test_preguntas_nuevas_van_aparte(tmp_path: Path):
    base, amp = _corridas(tmp_path)
    r = comparar_corridas(base, amp, 5, 10)
    nuevas = r["nuevas"]
    assert nuevas["n"] == 1 and nuevas["solo_rag"] == 1 and nuevas["solo_wiki"] == 0
    assert nuevas["cobertura_rag"] == 1.0 and nuevas["cobertura_wiki"] == 0.0


def test_escribe_archivos_con_limites_y_es_identico_al_repetirlo(tmp_path: Path):
    base, amp = _corridas(tmp_path)
    salida = tmp_path / "salida"
    escribir_comparacion(base, amp, 5, 10, salida)
    cabecera = (salida / "comparacion.csv").read_text(encoding="utf-8").splitlines()[0]
    assert cabecera == (
        "sistema,tipo,n,cobertura_base,cobertura_ampliada,diferencia,ic95_inf,ic95_sup,"
        "solo_base,solo_ampliada,p_mcnemar"
    )
    texto = (salida / "comparacion.md").read_text(encoding="utf-8")
    assert "preliminares" in texto and "comparaciones múltiples" in texto
    assert "orden" in texto and "tamaño" in texto
    assert "2.5" in texto  # costo de ingesta de la ampliada
    primero = {p.name: p.read_bytes() for p in salida.iterdir()}
    escribir_comparacion(base, amp, 5, 10, salida)
    assert {p.name: p.read_bytes() for p in salida.iterdir()} == primero


def test_comando_falla_sin_evaluados_y_no_crea_salida(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    base, _ = _corridas(tmp_path)
    vacia = tmp_path / "vacia"
    vacia.mkdir()
    salida = tmp_path / "salida"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "wikillm.eval",
            "comparar-corridas",
            "--base",
            str(base),
            "--ampliada",
            str(vacia),
            "--paso-base",
            "5",
            "--paso-ampliada",
            "10",
            "--salida",
            str(salida),
        ],
    )
    assert cli.main() == 1
    assert not salida.exists()


def test_comando_termina_en_cero(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    base, amp = _corridas(tmp_path)
    salida = tmp_path / "salida"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "wikillm.eval",
            "comparar-corridas",
            "--base",
            str(base),
            "--ampliada",
            str(amp),
            "--paso-base",
            "5",
            "--paso-ampliada",
            "10",
            "--salida",
            str(salida),
        ],
    )
    assert cli.main() == 0
    assert (salida / "comparacion.md").is_file()
