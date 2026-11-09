"""Visor del panel: solo archivos de la lista blanca, nunca rutas libres."""

import pytest

from wikillm.panel.archivos import LIMITE_BYTES, ArchivoNoPermitido, Archivos, coincide, normalizar


def crear(raiz, ruta, texto="x"):
    destino = raiz / ruta
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(texto, encoding="utf-8")
    return destino


@pytest.fixture
def raiz(tmp_path):
    crear(tmp_path, "README.md", "# Título")
    crear(tmp_path, "data/wiki/demo/pages/a.md", "Página")
    crear(tmp_path, "results/demo/comparaciones.jsonl", '{"a": 1}\n')
    crear(tmp_path, "src/wikillm/rag/brazo.py", "x = 1\n")
    crear(tmp_path, ".env", "DEEPSEEK_API_KEY=secreta")
    crear(tmp_path, "data/gold/2405.14831.md", "texto de arXiv")
    crear(tmp_path, "secreto.txt", "no está en la lista")
    return tmp_path


def test_un_archivo_de_la_lista_se_devuelve_con_su_tipo_y_su_texto(raiz):
    r = Archivos(raiz).leer("README.md")
    assert r == {
        "ruta": "README.md",
        "tipo": "markdown",
        "texto": "# Título",
        "truncado": False,
        "bytes": len("# Título".encode()),
    }


def test_el_tipo_sale_de_la_extension(raiz):
    visor = Archivos(raiz)
    assert visor.leer("results/demo/comparaciones.jsonl")["tipo"] == "jsonl"
    assert visor.leer("src/wikillm/rag/brazo.py")["tipo"] == "codigo"


@pytest.mark.parametrize(
    "ruta",
    [
        "../.env",
        "docs/../.env",
        "data/gold/../../.env",
        "..\\.env",
        "/etc/passwd",
        "C:/Windows/win.ini",
        ".env",
        ".env.local",
        ".git/config",
        "data/wiki/demo/.git/config",
        "",
        "   ",
        "README.md\x00.txt",
    ],
)
def test_las_rutas_sospechosas_se_rechazan(raiz, ruta):
    with pytest.raises(ArchivoNoPermitido):
        Archivos(raiz).leer(ruta)


@pytest.mark.parametrize(
    "ruta", ["secreto.txt", "data/gold/2405.14831.md", "data/wiki/demo/otro.md"]
)
def test_un_archivo_que_existe_pero_no_esta_en_la_lista_se_rechaza(raiz, ruta):
    with pytest.raises(ArchivoNoPermitido):
        Archivos(raiz).leer(ruta)


def test_un_archivo_grande_se_trunca_y_se_avisa(raiz):
    crear(raiz, "README.md", "a" * (LIMITE_BYTES + 100))
    r = Archivos(raiz).leer("README.md")
    assert r["truncado"] is True and len(r["texto"]) == LIMITE_BYTES
    assert r["bytes"] == LIMITE_BYTES + 100


def test_la_lista_agrupa_y_solo_incluye_lo_que_existe(raiz):
    lista = Archivos(raiz).listar()
    rutas = {x["ruta"]: x["grupo"] for x in lista}
    assert rutas["README.md"] == "Repositorio"
    assert rutas["data/wiki/demo/pages/a.md"] == "Wiki de la demostración"
    assert rutas["src/wikillm/rag/brazo.py"] == "Código"
    assert "secreto.txt" not in rutas and ".env" not in rutas
    assert "docs/demo.md" not in rutas  # está en la lista, pero no existe aquí


def test_normalizar_acepta_barras_invertidas_y_devuelve_barras_normales():
    assert normalizar("docs\\decisiones\\0001.md") == "docs/decisiones/0001.md"


def test_coincide_acepta_el_patron_aunque_el_archivo_no_exista():
    assert coincide("data/wiki/demo/pages/cualquiera.md")
    assert coincide("docs/decisiones/0001-algo.md")
    assert coincide("README.md")
    assert not coincide("data/gold/2405.14831.md")
    assert not coincide("docs/a/b/c.md")
    assert not coincide(".env")
