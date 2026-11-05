"""Prueba de punta a punta de Bronze, Silver y Gold con una red falsa (sin tocar arXiv)."""

import hashlib
from pathlib import Path
from types import SimpleNamespace

from wikillm.ingest.arxiv import ClienteArxiv
from wikillm.ingest.pipeline import construir_corpus

ROBOTS = b"User-agent: *\nCrawl-delay: 15\nAllow: /html\nAllow: /abs\n"


def html_paper(titulo: str, bibliografia: str, version: str = "v2", arxiv_id: str = "") -> bytes:
    cuerpo = "Texto sintético de prueba para el cuerpo del paper. " * 10
    return f"""<html><body><article class="ltx_document">
<h1 class="ltx_title ltx_title_document">{titulo}</h1>
<div class="ltx_abstract"><p class="ltx_p">Resumen de {titulo}.</p></div>
<section class="ltx_section"><h2 class="ltx_title ltx_title_section">1 Introduction</h2>
<div class="ltx_para"><p class="ltx_p">{cuerpo}</p></div></section>
<section class="ltx_bibliography"><h2 class="ltx_title ltx_title_bibliography">References</h2>
<ul class="ltx_biblist"><li class="ltx_bibitem">{bibliografia}</li></ul></section>
<a href="https://arxiv.org/pdf/{arxiv_id}{version}">pdf</a>
</article></body></html>""".encode()


def pagina_abs(titulo: str, fecha: str) -> bytes:
    return f"""<html><head>
<meta name="citation_title" content="{titulo}"/>
<meta name="citation_author" content="Ejemplo, Ada"/>
<meta name="citation_date" content="{fecha}"/>
<meta name="citation_online_date" content="{fecha}"/>
</head><body><span class="primary-subject">Computation and Language (cs.CL)</span></body></html>
""".encode()


RESPUESTAS = {
    "https://arxiv.org/robots.txt": (200, ROBOTS),
    # El paper nuevo cita al antiguo por identificador
    "https://arxiv.org/html/2605.00002": (
        200,
        html_paper(
            "Paper Nuevo Sobre Memoria",
            "Un trabajo. arXiv:2405.00001, 2024.",
            arxiv_id="2605.00002",
        ),
    ),
    "https://arxiv.org/abs/2605.00002": (
        200,
        pagina_abs("Paper Nuevo Sobre Memoria", "2026/05/10"),
    ),
    # El antiguo no cita a nadie del corpus
    "https://arxiv.org/html/2405.00001": (
        200,
        html_paper(
            "Paper Antiguo Sobre Recuperacion",
            "Otra referencia sin identificador.",
            arxiv_id="2405.00001",
        ),
    ),
    "https://arxiv.org/abs/2405.00001": (
        200,
        pagina_abs("Paper Antiguo Sobre Recuperacion", "2024/05/23"),
    ),
}


class SesionFalsa:
    def __init__(self, respuestas):
        self.respuestas = respuestas
        self.llamadas = []

    def get(self, url, headers=None, timeout=None, allow_redirects=True):
        self.llamadas.append(url)
        estado, contenido = self.respuestas.get(url, (404, b""))
        return SimpleNamespace(status_code=estado, content=contenido, url=url)


def preparar(tmp_path: Path, respuestas=None, ids="2605.00002\n2405.00001\n"):
    ruta_ids = tmp_path / "ids.txt"
    ruta_ids.write_text(ids, encoding="utf-8")
    sesion = SesionFalsa(respuestas or RESPUESTAS)
    cliente = ClienteArxiv(sesion, dormir=lambda _s: None, reloj=lambda: 0.0)
    return ruta_ids, sesion, cliente


def huellas(carpeta: Path) -> dict[str, str]:
    return {
        str(archivo.relative_to(carpeta)): hashlib.sha256(archivo.read_bytes()).hexdigest()
        for archivo in sorted(carpeta.rglob("*"))
        if archivo.is_file() and archivo.name != "capture.jsonl"
    }


def test_punta_a_punta_produce_un_gold_valido(tmp_path):
    ruta_ids, _, cliente = preparar(tmp_path)
    mensajes = []
    informe = construir_corpus(ruta_ids, tmp_path / "data", cliente=cliente, salida=mensajes.append)
    assert informe.correcto, (informe.fallos, informe.problemas)
    assert {r.arxiv_id for r in informe.resumenes} == {"2605.00002", "2405.00001"}
    gold = tmp_path / "data" / "gold"
    assert (gold / "2605.00002.md").exists()
    assert (gold / "2405.00001.md").exists()
    assert len((gold / "corpus.jsonl").read_text(encoding="utf-8").splitlines()) == 2
    assert (tmp_path / "data" / "processed" / "2605.00002.md").exists()
    assert any("2605.00002" in m for m in mensajes)


def test_el_paper_nuevo_cita_al_antiguo_dentro_del_corpus(tmp_path):
    ruta_ids, _, cliente = preparar(tmp_path)
    informe = construir_corpus(ruta_ids, tmp_path / "data", cliente=cliente, salida=lambda _m: None)
    por_id = {r.arxiv_id: r for r in informe.resumenes}
    assert por_id["2605.00002"].referencias == ["2405.00001"]
    assert por_id["2405.00001"].referencias == []


def test_el_paper_se_cita_tambien_por_su_titulo_completo(tmp_path):
    respuestas = dict(RESPUESTAS)
    respuestas["https://arxiv.org/html/2605.00002"] = (
        200,
        html_paper(
            "Paper Nuevo Sobre Memoria",
            "Autor. Paper Antiguo Sobre Recuperacion. Revista, 2024.",
            arxiv_id="2605.00002",
        ),
    )
    ruta_ids, _, cliente = preparar(tmp_path, respuestas)
    informe = construir_corpus(ruta_ids, tmp_path / "data", cliente=cliente, salida=lambda _m: None)
    por_id = {r.arxiv_id: r for r in informe.resumenes}
    assert por_id["2605.00002"].referencias == ["2405.00001"]


def test_segunda_ejecucion_no_descarga_ni_cambia_archivos(tmp_path):
    ruta_ids, sesion, cliente = preparar(tmp_path)
    datos = tmp_path / "data"
    construir_corpus(ruta_ids, datos, cliente=cliente, salida=lambda _m: None)
    antes = huellas(datos)
    peticiones = len(sesion.llamadas)
    otro = ClienteArxiv(sesion, dormir=lambda _s: None, reloj=lambda: 0.0)
    informe = construir_corpus(ruta_ids, datos, cliente=otro, salida=lambda _m: None)
    assert informe.correcto
    assert len(sesion.llamadas) == peticiones
    assert huellas(datos) == antes


def test_un_paper_sin_html_se_informa_y_el_resto_continua(tmp_path):
    respuestas = {k: v for k, v in RESPUESTAS.items() if "2405.00001" not in k}
    ruta_ids, _, cliente = preparar(tmp_path, respuestas)
    informe = construir_corpus(ruta_ids, tmp_path / "data", cliente=cliente, salida=lambda _m: None)
    assert not informe.correcto
    assert any("2405.00001" in fallo for fallo in informe.fallos)
    assert [r.arxiv_id for r in informe.resumenes] == ["2605.00002"]
