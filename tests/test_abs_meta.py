"""Metadatos de un paper a partir de su página `abs` de arXiv ya descargada (sin API)."""

from __future__ import annotations

import json
from pathlib import Path

from wikillm.corpus.abs_meta import completar_candidatos, registro_desde_abs

ABS = """<html><head>
<meta name="citation_title" content="A Memory Paper">
<meta name="citation_author" content="Chhikara, Prateek">
<meta name="citation_author" content="Khant, Dev">
<meta name="citation_date" content="2025/04/28">
<meta name="citation_online_date" content="2025/06/02">
<meta name="citation_arxiv_id" content="2504.19413">
<meta name="citation_doi" content="10.1000/xyz">
</head><body>
<blockquote class="abstract"><span class="descriptor">Abstract:</span> We build memory.</blockquote>
<table><tr><td class="tablecell comments">12 pages</td></tr>
<tr><td class="tablecell subjects">
<span class="primary-subject">Computation and Language (cs.CL)</span>;
Artificial Intelligence (cs.AI)</td></tr></table>
<div class="submission-history"><h2>Submission history</h2>From: P <br/>
<strong>[v1]</strong> Mon, 28 Apr 2025 01:46:35 UTC (946 KB)<br/>
<strong>[v3]</strong> Mon, 2 Jun 2025 10:00:00 UTC (950 KB)<br/></div>
</body></html>"""


def test_registro_desde_abs_trae_los_campos_de_la_api():
    r = registro_desde_abs(ABS, "2504.19413")
    assert r["arxiv_id"] == "2504.19413" and r["version"] == "v3"
    assert r["titulo"] == "A Memory Paper"
    assert r["autores"] == ["Prateek Chhikara", "Dev Khant"]
    assert r["fecha_publicacion"] == "2025-04-28" and r["fecha_version"] == "2025-06-02"
    assert r["categoria"] == "cs.CL" and r["categorias"] == ["cs.CL", "cs.AI"]
    assert r["doi"] == "10.1000/xyz" and r["comentario"] == "12 pages"
    assert r["resumen"].startswith("We build memory")
    assert r["origen"] == ["abs"]


def test_completar_agrega_solo_los_que_faltan_y_no_toca_los_existentes(tmp_path: Path):
    raw = tmp_path / "raw"
    (raw / "api").mkdir(parents=True)
    (raw / "2504.19413").mkdir()
    (raw / "2504.19413" / "abs.html").write_text(ABS, encoding="utf-8")
    existente = {"arxiv_id": "9999.00001", "titulo": "ya estaba", "fecha_publicacion": "2020-01-01"}
    ruta = raw / "api" / "candidatos.jsonl"
    ruta.write_text(json.dumps(existente) + "\n", encoding="utf-8")
    faltan = completar_candidatos(raw, ["9999.00001", "2504.19413", "1111.11111"])
    assert faltan == ["1111.11111"]  # sin abs.html no se inventa nada
    filas = {json.loads(x)["arxiv_id"]: json.loads(x) for x in ruta.read_text("utf-8").splitlines()}
    assert filas["9999.00001"] == existente and filas["2504.19413"]["titulo"] == "A Memory Paper"
