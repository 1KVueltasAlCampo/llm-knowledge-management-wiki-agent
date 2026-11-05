from pathlib import Path

import pytest

from wikillm.ingest.markdown import html_a_markdown

FIXTURE = Path(__file__).parent / "fixtures" / "paper_sintetico.html"


@pytest.fixture(scope="module")
def resultado():
    return html_a_markdown(FIXTURE.read_text(encoding="utf-8"))


def test_estructura_y_orden_de_los_encabezados(resultado):
    md = resultado.markdown
    orden = [
        "# Un paper sintético de prueba",
        "## Abstract",
        "## 1 Introduction",
        "### 1.1 Detalle",
        "## 2 Resultados",
    ]
    posiciones = [md.index(texto) for texto in orden]
    assert posiciones == sorted(posiciones)


def test_formato_en_linea(resultado):
    md = resultado.markdown
    assert "*énfasis*" in md
    assert "**negrita**" in md
    assert "`codigo`" in md
    assert "(Autor, 2024)" in md
    assert "(nota: Una nota al pie.)" in md


def test_ecuaciones_en_linea_y_en_bloque(resultado):
    assert "$x^2$" in resultado.markdown
    assert "$$a=b+c$$" in resultado.markdown
    assert resultado.ecuaciones == 2


def test_listas(resultado):
    md = resultado.markdown
    assert "1. Primer elemento" in md
    assert "2. Segundo elemento" in md
    assert "- Viñeta" in md


def test_tablas_como_markdown_y_pies_de_figura(resultado):
    md = resultado.markdown
    assert "**Table 1: Resultados sintéticos.**" in md
    assert "| Método | Puntaje |" in md
    assert "|---|---|" in md
    assert "| A | 1.0 |" in md
    assert "| fila combinada |  |" in md  # la celda combinada se rellena con una vacía
    assert "*Figure 1: Una figura.*" in md
    assert resultado.tablas == 1


def test_elimina_ruido_bibliografia_y_html(resultado):
    md = resultado.markdown
    for ruido in ("Menu de navegacion", "Logo de la pagina", "Pie de pagina", "ruido"):
        assert ruido not in md
    assert "References" not in md
    assert "arXiv:2401.00001" not in md
    assert "Ada Ejemplo" not in md  # los autores salen de los metadatos, no del cuerpo
    assert "x.png" not in md
    assert "<" not in md.replace("$", "")


def test_cuenta_secciones_y_extrae_referencias_de_arxiv(resultado):
    assert resultado.secciones == 2
    assert resultado.referencias_arxiv == {"2401.00001", "2402.00002"}
    assert "un trabajo citado" in resultado.texto_bibliografia


def test_un_html_que_no_es_de_arxiv_se_rechaza():
    with pytest.raises(ValueError, match="article.ltx_document"):
        html_a_markdown("<html><body><p>hola</p></body></html>")
