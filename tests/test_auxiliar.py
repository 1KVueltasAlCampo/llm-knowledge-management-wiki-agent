"""Evaluación auxiliar: exportar ítems ciegos e importar veredictos de un segundo juez."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest

from wikillm.eval import __main__ as cli
from wikillm.eval.auxiliar import exportar, importar


def _banco() -> list[dict[str, Any]]:
    return [
        {
            "id": f"Q{n}",
            "texto": f"Question {n}?",
            "tipo": "T1",
            "respuesta_oraculo": f"Reference {n}",
            "respuesta_clave": [str(n)],
            "ingesta_minima": 1,
        }
        for n in range(1, 9)
    ]


def _evaluado(n: int, sistema: str, capa1: str, veredicto: str, origen: str) -> dict[str, Any]:
    return {
        "question_id": f"Q{n}",
        "system": sistema,
        "ingest_step": 5,
        "answer": f"Answer {n}",
        "respondible": True,
        "veredicto_capa1": capa1,
        "veredicto": veredicto,
        "origen_veredicto": origen,
    }


def _evaluados() -> list[dict[str, Any]]:
    filas = []
    for n in range(1, 9):
        for sistema in ("rag", "wiki"):
            if n <= 3:  # indeterminadas en la capa 1, resueltas por el juez
                filas.append(_evaluado(n, sistema, "indeterminada", "correcta", "juez"))
            else:
                filas.append(_evaluado(n, sistema, "correcta", "correcta", "determinista"))
    return filas


def _preparar(tmp_path: Path) -> Path:
    tmp_path.mkdir(exist_ok=True)
    texto = "\n".join(json.dumps(f) for f in _evaluados()) + "\n"
    (tmp_path / "evaluados.jsonl").write_text(texto, encoding="utf-8")
    return tmp_path


def _leer(ruta: Path) -> list[dict[str, Any]]:
    return [json.loads(x) for x in ruta.read_text(encoding="utf-8").splitlines() if x.strip()]


def test_items_ciegos_sin_veredicto_sistema_ni_paso(tmp_path: Path):
    carpeta = _preparar(tmp_path)
    exportar(carpeta, _banco(), muestra=4, semilla=1)
    items = _leer(carpeta / "auxiliar" / "items.jsonl")
    assert items
    for item in items:
        assert set(item) == {"item_id", "question", "reference_answer", "answer_to_grade"}
    assert not any("rag" in i["item_id"] or "wiki" in i["item_id"] for i in items)


def test_las_indeterminadas_siempre_entran_aunque_la_muestra_sea_cero(tmp_path: Path):
    carpeta = _preparar(tmp_path)
    n = exportar(carpeta, _banco(), muestra=0, semilla=1)
    assert n == 6  # 3 preguntas indeterminadas × 2 sistemas
    claves = _leer(carpeta / "auxiliar" / "claves.jsonl")
    assert {c["question_id"] for c in claves} == {"Q1", "Q2", "Q3"}


def test_muestra_reproducible_con_la_misma_semilla(tmp_path: Path):
    carpeta = _preparar(tmp_path)
    exportar(carpeta, _banco(), muestra=5, semilla=7)
    primera = (carpeta / "auxiliar" / "items.jsonl").read_bytes()
    exportar(carpeta, _banco(), muestra=5, semilla=7)
    assert (carpeta / "auxiliar" / "items.jsonl").read_bytes() == primera
    assert len(_leer(carpeta / "auxiliar" / "items.jsonl")) == 6 + 5


def _veredictos(carpeta: Path, cambios: dict[str, str] | None = None, meta: bool = True) -> None:
    claves = _leer(carpeta / "auxiliar" / "claves.jsonl")
    lineas: list[dict[str, Any]] = []
    if meta:
        lineas.append({"meta": {"modelo": "claude-test", "fecha": "2026-11-15"}})
    for c in claves:
        v = (cambios or {}).get(c["question_id"], "correcta")
        lineas.append({"item_id": c["item_id"], "veredicto": v, "motivo": "ok"})
    texto = "\n".join(json.dumps(x) for x in lineas) + "\n"
    (carpeta / "auxiliar" / "veredictos_claude.jsonl").write_text(texto, encoding="utf-8")


def test_importar_calcula_acuerdo_total_por_origen_y_por_sistema(tmp_path: Path):
    carpeta = _preparar(tmp_path)
    exportar(carpeta, _banco(), muestra=4, semilla=1)
    _veredictos(carpeta, cambios={"Q1": "incorrecta"})
    resultado = importar(carpeta)
    assert resultado["total"]["n"] == 10
    assert resultado["total"]["porcentaje"] == pytest.approx(0.8)  # Q1 × 2 sistemas discrepan
    assert resultado["por_origen"]["juez"]["porcentaje"] == pytest.approx(4 / 6)
    assert resultado["por_origen"]["determinista"]["porcentaje"] == 1.0
    assert set(resultado["por_sistema"]) == {"rag", "wiki"}
    assert (carpeta / "auxiliar" / "acuerdo.json").is_file()


def test_acuerdo_md_se_rotula_auxiliar_y_cita_el_modelo(tmp_path: Path):
    carpeta = _preparar(tmp_path)
    exportar(carpeta, _banco(), muestra=0, semilla=1)
    _veredictos(carpeta)
    importar(carpeta)
    texto = (carpeta / "auxiliar" / "acuerdo.md").read_text(encoding="utf-8")
    assert "auxiliar" in texto.lower() and "claude-test" in texto
    assert "consumo.csv" in texto


def test_veredicto_invalido_falla_sin_escribir_acuerdo(tmp_path: Path):
    carpeta = _preparar(tmp_path)
    exportar(carpeta, _banco(), muestra=0, semilla=1)
    _veredictos(carpeta, cambios={"Q1": "tal vez"})
    with pytest.raises(ValueError, match="tal vez"):
        importar(carpeta)
    assert not (carpeta / "auxiliar" / "acuerdo.json").exists()


def test_item_desconocido_falla(tmp_path: Path):
    carpeta = _preparar(tmp_path)
    exportar(carpeta, _banco(), muestra=0, semilla=1)
    ruta = carpeta / "auxiliar" / "veredictos_claude.jsonl"
    ruta.write_text('{"item_id": "zzz", "veredicto": "correcta"}\n', encoding="utf-8")
    with pytest.raises(ValueError, match="zzz"):
        importar(carpeta)


def test_comando_auxiliar_exportar_e_importar(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    carpeta = _preparar(tmp_path / "corrida")
    banco = tmp_path / "banco.jsonl"
    banco.write_text("\n".join(json.dumps(p) for p in _banco()) + "\n", encoding="utf-8")
    base = ["wikillm.eval", "auxiliar"]
    monkeypatch.setattr(
        sys, "argv", [*base, "exportar", "--corrida", str(carpeta), "--banco", str(banco)]
    )
    assert cli.main() == 0
    _veredictos(carpeta)
    monkeypatch.setattr(sys, "argv", [*base, "importar", "--corrida", str(carpeta)])
    assert cli.main() == 0
    assert (carpeta / "auxiliar" / "acuerdo.md").is_file()


def test_importar_sin_veredictos_da_codigo_1(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
):
    carpeta = _preparar(tmp_path)
    monkeypatch.setattr(
        sys, "argv", ["wikillm.eval", "auxiliar", "importar", "--corrida", str(carpeta)]
    )
    assert cli.main() == 1
    assert "veredictos_claude.jsonl" in capsys.readouterr().out
