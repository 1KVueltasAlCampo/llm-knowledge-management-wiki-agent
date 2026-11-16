"""Informe de una corrida: cortes por tipo, tablas y figuras SVG (sin red ni modelo)."""

from __future__ import annotations

import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

import pytest

from wikillm.eval import __main__ as cli
from wikillm.eval.informe import escribir_informe, por_tipo


def _fila(
    sistema: str,
    paso: int,
    tipo: str,
    *,
    respondible: bool = True,
    veredicto: str = "correcta",
    contexto: int = 100,
    costo: float = 0.001,
) -> dict[str, Any]:
    return {
        "run_id": "demo",
        "question_id": f"{tipo}-{paso}",
        "system": sistema,
        "ingest_step": paso,
        "tipo": tipo,
        "respondible": respondible,
        "veredicto": veredicto,
        "tras_cambio": False,
        "obsoleta": False,
        "fundamentacion": 1.0,
        "context_tokens": contexto,
        "cost_usd": costo,
    }


def _evaluados() -> list[dict[str, Any]]:
    filas = []
    for paso in (0, 5, 10):
        for sistema in ("rag", "wiki"):
            ok = "correcta" if (sistema == "wiki" or paso == 10) else "incorrecta"
            filas.append(_fila(sistema, paso, "T1", veredicto=ok, contexto=1000 * (paso + 1)))
            filas.append(_fila(sistema, paso, "T5", respondible=False))
    return filas


def _guardar(carpeta: Path, filas: list[dict[str, Any]]) -> None:
    carpeta.mkdir(parents=True, exist_ok=True)
    texto = "\n".join(json.dumps(f) for f in filas) + "\n"
    (carpeta / "evaluados.jsonl").write_text(texto, encoding="utf-8")


def test_por_tipo_separa_filas_y_deja_vacia_la_cobertura_sin_respondibles():
    filas = por_tipo(_evaluados())
    claves = {(f["system"], f["tipo"], f["ingest_step"]) for f in filas}
    assert ("rag", "T1", 5) in claves and ("wiki", "T5", 10) in claves
    t5 = next(f for f in filas if f["tipo"] == "T5")
    assert t5["cobertura"] is None
    t1_rag_5 = next(
        f for f in filas if (f["system"], f["tipo"], f["ingest_step"]) == ("rag", "T1", 5)
    )
    assert t1_rag_5["cobertura"] == 0.0 and t1_rag_5["n_respondibles"] == 1


def test_escribe_los_cinco_archivos_y_el_resumen_muestra_denominadores(tmp_path: Path):
    _guardar(tmp_path, _evaluados())
    escribir_informe(tmp_path)
    informe = tmp_path / "informe"
    for nombre in (
        "por_sistema_paso.csv",
        "por_tipo.csv",
        "resumen.md",
        "cobertura_por_paso.svg",
        "contexto_por_paso.svg",
        "costo_acumulado.svg",
    ):
        assert (informe / nombre).is_file(), nombre
    cabecera = (informe / "por_tipo.csv").read_text(encoding="utf-8").splitlines()[0]
    assert cabecera.startswith("system,tipo,ingest_step")
    resumen = (informe / "resumen.md").read_text(encoding="utf-8")
    assert "n_respondibles" in resumen and "| rag |" in resumen


def test_el_informe_es_identico_al_repetirlo(tmp_path: Path):
    _guardar(tmp_path, _evaluados())
    escribir_informe(tmp_path)
    primera = {p.name: p.read_bytes() for p in (tmp_path / "informe").iterdir()}
    escribir_informe(tmp_path)
    segunda = {p.name: p.read_bytes() for p in (tmp_path / "informe").iterdir()}
    assert primera == segunda


def test_figura_de_cobertura_es_svg_valido_con_una_polilinea_por_sistema(tmp_path: Path):
    _guardar(tmp_path, _evaluados())
    escribir_informe(tmp_path)
    raiz = ET.fromstring((tmp_path / "informe" / "cobertura_por_paso.svg").read_text("utf-8"))
    espacio = "{http://www.w3.org/2000/svg}"
    assert raiz.tag == f"{espacio}svg"
    assert len(raiz.findall(f".//{espacio}polyline")) == 2
    assert raiz.find(f"{espacio}title") is not None


def test_costo_acumulado_no_decrece(tmp_path: Path):
    _guardar(tmp_path, _evaluados())
    escribir_informe(tmp_path)
    raiz = ET.fromstring((tmp_path / "informe" / "costo_acumulado.svg").read_text("utf-8"))
    espacio = "{http://www.w3.org/2000/svg}"
    for linea in raiz.findall(f".//{espacio}polyline"):
        ys = [float(p.split(",")[1]) for p in linea.attrib["points"].split()]
        assert ys == sorted(ys, reverse=True)  # en SVG, y menor = valor mayor


def test_sin_evaluados_falla_con_mensaje_y_no_crea_carpeta(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
):
    monkeypatch.setattr(sys, "argv", ["wikillm.eval", "informe", "--corrida", str(tmp_path)])
    assert cli.main() == 1
    assert "metricas" in capsys.readouterr().out
    assert not (tmp_path / "informe").exists()


def test_comando_informe_termina_en_cero(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    _guardar(tmp_path, _evaluados())
    monkeypatch.setattr(sys, "argv", ["wikillm.eval", "informe", "--corrida", str(tmp_path)])
    assert cli.main() == 0
    assert (tmp_path / "informe" / "resumen.md").is_file()
