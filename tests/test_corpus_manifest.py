import json

from wikillm.corpus.manifest import construir_manifest, mitad, ordenar
from wikillm.ingest.gold import escribir_gold


def _registro(arxiv_id, fecha, **extra):
    return {
        "arxiv_id": arxiv_id,
        "version": "v1",
        "titulo": f"Paper {arxiv_id}",
        "autores": ["A"],
        "fecha_publicacion": fecha,
        "fecha_version": fecha,
        "categoria": "cs.CL",
        "resumen": "",
        **extra,
    }


def _captura(raiz, arxiv_id, estado):
    carpeta = raiz / arxiv_id
    carpeta.mkdir(parents=True)
    (carpeta / "capture.jsonl").write_text(
        json.dumps({"tipo": "html", "estado": estado}) + "\n", encoding="utf-8"
    )


def test_orden_por_fecha_con_empate_por_id_y_mitad_alterna():
    registros = [
        _registro("2603.2", "2026-03-01"),
        _registro("2603.1", "2026-03-01"),
        _registro("2601.9", "2026-01-01"),
    ]
    assert [r["arxiv_id"] for r in ordenar(registros)] == ["2601.9", "2603.1", "2603.2"]
    assert [mitad(i) for i in range(1, 5)] == ["A", "B", "A", "B"]


def test_manifest_con_senales_y_referencias(tmp_path):
    raw, gold = tmp_path / "raw", tmp_path / "gold"
    _captura(raw, "2405.1", 200)
    _captura(raw, "2606.1", 200)
    _captura(raw, "2607.1", 404)
    escribir_gold(
        gold / "2606.1.md",
        {"arxiv_id": "2606.1", "version": "v2", "tokens": 10, "referencias_en_corpus": ["2405.1"]},
        "Code: https://github.com/org/repo\n",
    )
    candidatos = {
        "2405.1": _registro("2405.1", "2024-05-01", journal_ref="NeurIPS 2024"),
        "2606.1": _registro("2606.1", "2026-06-01"),
        "2607.1": _registro("2607.1", "2026-07-01"),
    }
    filas = construir_manifest(["2607.1", "2606.1", "2405.1"], candidatos, raw, gold)
    por_id = {f["arxiv_id"]: f for f in filas}

    assert [f["arxiv_id"] for f in filas] == ["2405.1", "2606.1", "2607.1"]
    assert [f["orden_ingesta"] for f in filas] == [1, 2, 3]
    assert [f["mitad"] for f in filas] == ["A", "B", "A"]
    assert por_id["2405.1"]["pre_corte"] is True
    assert por_id["2405.1"]["estado_publicacion"] == "revisado"
    assert por_id["2405.1"]["citado_por_en_corpus"] == 1
    assert por_id["2606.1"]["version"] == "v2"
    assert por_id["2606.1"]["senal_codigo"] is True
    assert por_id["2606.1"]["referencias_en_corpus"] == ["2405.1"]
    assert por_id["2606.1"]["estado_publicacion"] == "preprint"
    assert por_id["2607.1"]["html_available"] is False
    assert por_id["2607.1"]["en_gold"] is False
