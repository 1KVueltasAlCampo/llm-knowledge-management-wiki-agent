"""Búsqueda y lectura de páginas del wiki, con páginas escritas a mano (sin modelo ni red)."""

import pytest

from wikillm.wiki.almacen import Pagina, Wiki
from wikillm.wiki.herramientas import (
    palabras,
    texto_de_busqueda,
    wiki_read,
    wiki_search,
)


def pagina(slug, titulo, resumen, cuerpo, tipo="paper"):
    return Pagina(slug, titulo, tipo, resumen, ["2405.14831"], 1, cuerpo)


@pytest.fixture
def wiki(tmp_path):
    w = Wiki(tmp_path / "w")
    w.escribir(
        pagina(
            "hipporag",
            "HippoRAG",
            "Memoria con un grafo de conocimiento.",
            "Usa Personalized PageRank sobre el grafo [2405.14831#s2.p5]. Menciona MuSiQue.",
        )
    )
    w.escribir(
        pagina(
            "musique-resultados",
            "Resultados en MuSiQue",
            "Comparación de métodos en el benchmark.",
            "HippoRAG obtiene 74.7 de recall [2502.14802#s14.p10].",
            tipo="concepto",
        )
    )
    w.escribir(
        pagina("wiki-compilado", "LLM-Wiki", "Wiki navegado por herramientas.", "Sin grafo.")
    )
    return w


def test_la_coincidencia_en_el_titulo_gana_a_la_del_cuerpo(wiki):
    resultados = wiki_search(wiki, "MuSiQue")
    assert [r.slug for r in resultados][:2] == ["musique-resultados", "hipporag"]


def test_la_busqueda_devuelve_slug_tipo_titulo_y_resumen(wiki):
    primero = wiki_search(wiki, "HippoRAG")[0]
    assert (primero.slug, primero.tipo, primero.titulo) == ("hipporag", "paper", "HippoRAG")
    assert primero.a_texto() == "- hipporag [paper] HippoRAG: Memoria con un grafo de conocimiento."


def test_sin_coincidencias_la_lista_esta_vacia(wiki):
    assert wiki_search(wiki, "criptografia cuantica") == []
    assert wiki_search(wiki, "the of and") == []  # solo palabras vacías
    assert texto_de_busqueda([]) == "No pages match this search."


def test_el_orden_es_determinista_y_tiene_tope(wiki):
    assert wiki_search(wiki, "grafo MuSiQue HippoRAG") == wiki_search(
        wiki, "grafo MuSiQue HippoRAG"
    )
    assert len(wiki_search(wiki, "grafo", maximo=1)) == 1


def test_los_identificadores_de_cita_no_cuentan_como_palabras(wiki):
    assert "s2" not in palabras("Dato [2405.14831#s2.p5] y [[hipporag]]")
    assert wiki_search(wiki, "14831") == []


def test_un_wiki_vacio_no_devuelve_resultados(tmp_path):
    assert wiki_search(Wiki(tmp_path / "w"), "lo que sea") == []


def test_leer_devuelve_las_paginas_e_informa_de_las_que_no_existen(wiki):
    lectura = wiki_read(wiki, ["hipporag", "musique-resultados", "no-existe"])
    assert lectura.leidas == ["hipporag", "musique-resultados"]
    assert lectura.no_encontradas == ["no-existe"]
    assert "=== Page hipporag ===" in lectura.texto and "Personalized PageRank" in lectura.texto
    assert "Not found: no-existe." in lectura.texto


def test_leer_acepta_tres_paginas_por_vez_e_informa_del_resto(wiki):
    wiki.escribir(pagina("extra", "Extra", "x", "y"))
    lectura = wiki_read(wiki, ["hipporag", "musique-resultados", "wiki-compilado", "extra"])
    assert len(lectura.leidas) == 3 and lectura.no_leidas == ["extra"]
    assert "Not read" in lectura.texto and "=== Page extra ===" not in lectura.texto


def test_el_indice_se_puede_leer_como_una_pagina(wiki):
    wiki.regenerar_indice()
    lectura = wiki_read(wiki, ["index"])
    assert lectura.leidas == ["index"] and "[[hipporag]]" in lectura.texto


def test_los_nombres_con_corchetes_o_repetidos_se_normalizan(wiki):
    lectura = wiki_read(wiki, ["[[hipporag]]", "hipporag"])
    assert lectura.leidas == ["hipporag"]
