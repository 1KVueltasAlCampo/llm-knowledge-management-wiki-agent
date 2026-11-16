"""Análisis de fallos: una categoría por respuesta no correcta, a partir de datos guardados."""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from typing import Any

import pytest

from wikillm.eval import __main__ as cli
from wikillm.eval.fallos import categorizar, escribir_fallos

BANCO = {
    "Q1": {"id": "Q1", "tipo": "T2", "fuentes_requeridas": ["A", "B"]},
    "Q2": {"id": "Q2", "tipo": "T1", "fuentes_requeridas": ["A"]},
    "Q5": {"id": "Q5", "tipo": "T5", "fuentes_requeridas": []},
}


def _r(
    q: str,
    *,
    veredicto: str = "incorrecta",
    abstuvo: bool = False,
    citas: tuple[str, ...] = (),
    respondible: bool = True,
    obsoleta: bool = False,
    sistema: str = "rag",
) -> dict[str, Any]:
    return {
        "question_id": q,
        "system": sistema,
        "ingest_step": 10,
        "tipo": BANCO[q]["tipo"],
        "respondible": respondible,
        "veredicto": veredicto,
        "abstained": abstuvo,
        "citations": [f"{c}#s1.p1" for c in citas],
        "obsoleta": obsoleta,
    }


def test_categorias_de_respondibles():
    assert categorizar(_r("Q2", abstuvo=True), BANCO) == "abstencion_erronea"
    assert categorizar(_r("Q2", citas=("Z",)), BANCO) == "sin_fuente"
    assert categorizar(_r("Q2"), BANCO) == "sin_fuente"
    assert categorizar(_r("Q1", citas=("A",)), BANCO) == "fuente_parcial"
    assert categorizar(_r("Q1", citas=("A", "B")), BANCO) == "fuentes_completas_error"
    assert categorizar(_r("Q2", citas=("A",)), BANCO) == "fuentes_completas_error"


def test_obsoleta_e_indeterminada_tienen_prioridad():
    assert categorizar(_r("Q2", citas=("A",), obsoleta=True), BANCO) == "obsoleta"
    assert categorizar(_r("Q2", veredicto="indeterminada", citas=("A",)), BANCO) == "indeterminada"


def test_no_respondible_que_no_se_abstuvo():
    fila = _r("Q5", respondible=False, citas=("A",))
    assert categorizar(fila, BANCO) == "no_se_abstuvo"


def test_las_correctas_no_tienen_categoria():
    assert categorizar(_r("Q2", veredicto="correcta", citas=("A",)), BANCO) is None


def _guardar(carpeta: Path, filas: list[dict[str, Any]]) -> None:
    carpeta.mkdir(parents=True, exist_ok=True)
    (carpeta / "evaluados.jsonl").write_text(
        "\n".join(json.dumps(f) for f in filas) + "\n", encoding="utf-8"
    )


FILAS = [
    _r("Q2", abstuvo=True),
    _r("Q2", citas=("A",), sistema="wiki"),
    _r("Q1", citas=("A",)),
    _r("Q1", veredicto="correcta", citas=("A", "B"), sistema="wiki"),
    _r("Q5", respondible=False, citas=("A",)),
]


def test_escribe_detalle_y_resumen_con_nota(tmp_path: Path):
    _guardar(tmp_path, FILAS)
    escribir_fallos(tmp_path, list(BANCO.values()))
    detalle = (tmp_path / "fallos" / "detalle.csv").read_text(encoding="utf-8").splitlines()
    assert detalle[0] == "question_id,system,ingest_step,tipo,categoria"
    assert len(detalle) == 1 + 4  # la correcta no aparece
    resumen = (tmp_path / "fallos" / "resumen.md").read_text(encoding="utf-8")
    assert "abstencion_erronea" in resumen and "pista" in resumen


def test_es_identico_al_repetirlo_y_no_muta_la_entrada(tmp_path: Path):
    _guardar(tmp_path, FILAS)
    copia = copy.deepcopy(FILAS)
    escribir_fallos(tmp_path, list(BANCO.values()))
    antes = {p.name: p.read_bytes() for p in (tmp_path / "fallos").iterdir()}
    escribir_fallos(tmp_path, list(BANCO.values()))
    assert {p.name: p.read_bytes() for p in (tmp_path / "fallos").iterdir()} == antes
    assert FILAS == copia


def test_comando_sin_evaluados_da_codigo_1(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(sys, "argv", ["wikillm.eval", "fallos", "--corrida", str(tmp_path)])
    assert cli.main() == 1
    assert not (tmp_path / "fallos").exists()


def test_comando_fallos_termina_en_cero(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    _guardar(tmp_path / "corrida", FILAS)
    banco = tmp_path / "banco.jsonl"
    banco.write_text("\n".join(json.dumps(p) for p in BANCO.values()) + "\n", encoding="utf-8")
    monkeypatch.setattr(
        sys,
        "argv",
        ["wikillm.eval", "fallos", "--corrida", str(tmp_path / "corrida"), "--banco", str(banco)],
    )
    assert cli.main() == 0
    assert (tmp_path / "corrida" / "fallos" / "resumen.md").is_file()
