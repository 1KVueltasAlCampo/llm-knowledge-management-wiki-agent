"""Bucle del agente que consulta el wiki, con un modelo guionado (sin red ni saldo)."""

import json

import pytest

from cliente_guionado import modelo_guionado
from wikillm.common.modelo import TopeDeGastoError
from wikillm.common.responder import FRASE_ABSTENCION
from wikillm.common.respuesta import REGLAS_DE_RESPUESTA
from wikillm.ingest.gold import aproximar_tokens
from wikillm.rag.brazo import INSTRUCCIONES as INSTRUCCIONES_RAG
from wikillm.wiki.almacen import Pagina, Wiki
from wikillm.wiki.consulta import (
    INSTRUCCIONES_AGENTE,
    INSTRUCCIONES_SIN_HERRAMIENTAS,
    ConsultaWiki,
    analizar_accion,
)
from wikillm.wiki.ingesta import ErrorDeFormato

S1 = "2405.14831#s2.p5"
S2 = "2502.14802#s14.p10"
AJENO = "2411.00001#s1.p1"


def accion(**datos):
    return json.dumps(datos)


def buscar(consulta):
    return accion(action="search", query=consulta)


def leer(*paginas):
    return accion(action="read", pages=list(paginas))


def responder(texto):
    return accion(action="answer", answer=texto)


@pytest.fixture
def wiki(tmp_path):
    w = Wiki(tmp_path / "wiki")
    w.escribir(
        Pagina(
            "hipporag",
            "HippoRAG",
            "paper",
            "Memoria con un grafo.",
            ["2405.14831"],
            1,
            f"Usa PageRank personalizado [{S1}].",
        )
    )
    w.escribir(
        Pagina(
            "resultados",
            "Resultados",
            "concepto",
            "Comparación de métodos.",
            ["2502.14802"],
            2,
            f"Obtiene 74.7 de recall [{S2}]. Ver [[hipporag]].",
        )
    )
    w.regenerar_indice()
    return w


def consulta(tmp_path, wiki, textos, **kwargs):
    modelo, http = modelo_guionado(tmp_path, textos)
    return ConsultaWiki(modelo, wiki, **kwargs), http


def test_buscar_leer_y_responder_son_tres_llamadas_con_las_citas_de_lo_leido(tmp_path, wiki):
    agente, http = consulta(
        tmp_path,
        wiki,
        [buscar("PageRank"), leer("hipporag"), responder(f"It uses personalized PageRank [{S1}].")],
        spans_validos={S1, S2},
    )
    resultado = agente.responder("What algorithm does HippoRAG use?")
    assert len(http.solicitudes) == 3 and resultado.llamadas == 3
    assert resultado.citas == (S1,) and not resultado.abstuvo
    assert (agente.traza.acciones, agente.traza.busquedas, agente.traza.lecturas) == (2, 1, 1)
    assert agente.traza.paginas_leidas == ["hipporag"]
    primero = http.solicitudes[0]["messages"]
    assert primero[0] == {"role": "system", "content": INSTRUCCIONES_AGENTE}
    assert primero[1]["content"] == "Question: What algorithm does HippoRAG use?"
    ultimo = http.solicitudes[2]["messages"]
    assert "=== Page hipporag ===" in ultimo[-1]["content"]


def test_el_contexto_son_los_resultados_de_las_herramientas_sin_repetirlos_por_turno(
    tmp_path, wiki
):
    agente, _ = consulta(
        tmp_path,
        wiki,
        [buscar("recall"), leer("resultados", "hipporag"), responder(f"74.7 [{S2}]")],
    )
    resultado = agente.responder("What recall?")
    esperado = "\n\n".join(
        [
            "- resultados [concepto] Resultados: Comparación de métodos.",
            f"{wiki_texto(wiki, 'resultados', 'hipporag')}",
        ]
    )
    assert resultado.tokens_contexto == aproximar_tokens(esperado)
    assert resultado.tokens_entrada > resultado.tokens_contexto  # el costo sí reenvía todo


def wiki_texto(wiki, *slugs):
    from wikillm.wiki.herramientas import wiki_read

    return wiki_read(wiki, list(slugs)).texto


def test_una_cita_que_no_esta_en_lo_leido_o_inventada_no_cuenta(tmp_path, wiki):
    agente, _ = consulta(
        tmp_path,
        wiki,
        [leer("hipporag"), responder(f"A [{S1}]. B [{S2}]. C [{AJENO}]. D [2405.14831#s9.p9].")],
        spans_validos={S1, S2, AJENO},
    )
    assert agente.responder("Q?").citas == (S1,)


def test_la_abstencion_no_lleva_citas(tmp_path, wiki):
    agente, _ = consulta(
        tmp_path, wiki, [leer("hipporag"), responder(f"{FRASE_ABSTENCION} [{S1}]")]
    )
    resultado = agente.responder("Unknown?")
    assert resultado.abstuvo and resultado.citas == ()


def test_al_agotar_el_tope_se_pide_una_respuesta_final(tmp_path, wiki):
    agente, http = consulta(
        tmp_path,
        wiki,
        [buscar("a"), leer("hipporag"), responder(f"Done [{S1}]")],
        max_acciones=2,
    )
    resultado = agente.responder("Q?")
    assert len(http.solicitudes) == 3 and resultado.citas == (S1,)
    assert "budget is used up" in http.solicitudes[2]["messages"][-1]["content"]


def test_tres_busquedas_vacias_seguidas_cierran_con_lo_leido(tmp_path, wiki):
    agente, http = consulta(
        tmp_path,
        wiki,
        [buscar("zzz"), buscar("yyy"), buscar("xxx"), responder(FRASE_ABSTENCION)],
    )
    resultado = agente.responder("Unknown?")
    assert len(http.solicitudes) == 4 and resultado.abstuvo and resultado.citas == ()
    assert "found nothing" in http.solicitudes[3]["messages"][-1]["content"]


def test_responder_sin_leer_obliga_a_leer_primero(tmp_path, wiki):
    agente, http = consulta(
        tmp_path,
        wiki,
        [responder("Guess"), leer("hipporag"), responder(f"Real [{S1}]")],
    )
    resultado = agente.responder("Q?")
    assert len(http.solicitudes) == 3 and resultado.respuesta == f"Real [{S1}]"
    assert "Read at least one page" in http.solicitudes[1]["messages"][-1]["content"]


def test_una_pagina_inexistente_se_informa_al_agente(tmp_path, wiki):
    agente, http = consulta(
        tmp_path, wiki, [leer("no-existe", "hipporag"), responder(f"Ok [{S1}]")]
    )
    agente.responder("Q?")
    assert "Not found: no-existe." in http.solicitudes[1]["messages"][-1]["content"]


def test_una_accion_mal_formada_que_se_repite_bien_cuesta_una_llamada_mas(tmp_path, wiki):
    agente, http = consulta(tmp_path, wiki, ["hola", leer("hipporag"), responder(f"Ok [{S1}]")])
    resultado = agente.responder("Q?")
    assert resultado.llamadas == 3 and agente.traza.incidencias == []
    assert "not a valid action" in http.solicitudes[1]["messages"][-1]["content"]
    assert agente.traza.acciones == 1


def test_una_accion_mal_formada_dos_veces_se_toma_como_respuesta_y_se_registra(tmp_path, wiki):
    agente, _ = consulta(tmp_path, wiki, ["texto libre", "otra vez texto libre"])
    resultado = agente.responder("Q?")
    assert resultado.respuesta == "otra vez texto libre" and resultado.llamadas == 2
    assert len(agente.traza.incidencias) == 1


def test_con_el_wiki_vacio_se_hace_una_sola_llamada_con_contexto_sin_paginas(tmp_path):
    agente, http = consulta(tmp_path, Wiki(tmp_path / "vacio"), [FRASE_ABSTENCION])
    resultado = agente.responder("Anything?")
    assert len(http.solicitudes) == 1 and resultado.abstuvo and resultado.citas == ()
    sistema, usuario = http.solicitudes[0]["messages"]
    assert sistema["content"] == INSTRUCCIONES_SIN_HERRAMIENTAS
    assert "(no pages)" in usuario["content"] and usuario["content"].endswith("Question: Anything?")


def test_un_error_del_modelo_llega_al_llamador(tmp_path, wiki):
    modelo, _ = modelo_guionado(tmp_path, [buscar("a")])
    modelo._gasto = modelo._ajustes.max_usd_per_run  # tope de gasto alcanzado
    with pytest.raises(TopeDeGastoError):
        ConsultaWiki(modelo, wiki).responder("Q?")


def test_el_analisis_de_acciones_valida_cada_forma():
    assert analizar_accion('```json\n{"action":"search","query":" x "}\n```') == ("search", "x")
    assert analizar_accion('{"action":"read","pages":"a"}') == ("read", ["a"])
    for malo in ('{"action":"search"}', '{"action":"read","pages":[]}', '{"action":"dance"}', "x"):
        with pytest.raises(ErrorDeFormato):
            analizar_accion(malo)


def test_el_rag_y_el_wiki_comparten_las_mismas_reglas_de_respuesta():
    for instrucciones in (INSTRUCCIONES_RAG, INSTRUCCIONES_AGENTE, INSTRUCCIONES_SIN_HERRAMIENTAS):
        assert REGLAS_DE_RESPUESTA in instrucciones
