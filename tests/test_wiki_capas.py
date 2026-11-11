"""Capas opcionales del wiki (graphify y tgrep), con procesos y modelo falsos: sin red ni saldo."""

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from cliente_guionado import modelo_guionado
from wikillm.arnes.__main__ import _brazos_declarados, nombres_de_brazos
from wikillm.arnes.estimacion import estimar
from wikillm.wiki.almacen import Pagina, Wiki
from wikillm.wiki.brazo import BrazoWikiCapas
from wikillm.wiki.capas import (
    AVISO_LEER_PRIMERO,
    BusquedaTgrep,
    CapasDeConsulta,
    ErrorDeCapa,
    GrafoDelWiki,
    crear_capas,
    leer_por_secciones,
    nombre_del_brazo,
)
from wikillm.wiki.consulta import INSTRUCCIONES_AGENTE, ConsultaWiki, analizar_accion
from wikillm.wiki.ingesta import ErrorDeFormato

S1 = "2405.14831#s2.p5"
CUERPO = (
    f"Intro [{S1}].\n\n## Setup\nUsa PageRank personalizado [{S1}].\n\n## Results\nObtiene 74.7."
)


def accion(**datos):
    return json.dumps(datos)


@pytest.fixture
def wiki(tmp_path):
    w = Wiki(tmp_path / "wiki")
    w.escribir(
        Pagina("hipporag", "HippoRAG", "paper", "Memoria con grafo.", ["2405.14831"], 1, CUERPO)
    )
    w.regenerar_indice()
    w.marcar_ingerido("2405.14831")
    return w


class Procesos:
    """Sustituye a ``subprocess.run``: guarda las órdenes y responde según el subcomando."""

    def __init__(self, salida_consulta="NODE hipporag.md [src=pages/hipporag.md loc=L1]\n"):
        self.ordenes = []
        self.salida_consulta = salida_consulta
        self.codigo = 0

    def __call__(self, orden, **kwargs):
        self.ordenes.append(list(orden))
        if "update" in orden:
            destino = Path(next(o for o in orden if o.endswith("fuente")))
            (destino / "graphify-out").mkdir(parents=True, exist_ok=True)
            (destino / "graphify-out" / "graph.json").write_text("{}", encoding="utf-8")
            return SimpleNamespace(returncode=self.codigo, stdout="", stderr="")
        return SimpleNamespace(returncode=self.codigo, stdout=self.salida_consulta, stderr="")


def test_lectura_por_secciones_pagina_seccion_y_nombres_del_grafo(wiki):
    entera = leer_por_secciones(wiki, ["pages/hipporag.md"])
    assert "=== Page hipporag ===" in entera.texto and entera.leidas == ["hipporag"]
    seccion = leer_por_secciones(wiki, ["hipporag#Setup"])
    assert "=== Section hipporag#Setup ===" in seccion.texto
    assert "PageRank" in seccion.texto and "74.7" not in seccion.texto
    falta = leer_por_secciones(wiki, ["hipporag#Nada", "otra"])
    assert "Sections:" in falta.texto and falta.no_encontradas == ["otra"]


def test_el_grafo_se_construye_una_vez_por_paso_y_se_reconstruye_al_cambiar(tmp_path, wiki):
    procesos = Procesos()
    grafo = GrafoDelWiki(wiki, "graphify", tmp_path / "trabajo", ejecutor=procesos)
    texto, resumen = grafo.consultar("pagerank")
    assert resumen == "1 nodes" and "NODE hipporag.md" in texto
    grafo.consultar("otra")
    assert len([o for o in procesos.ordenes if "update" in o]) == 1  # el wiki no cambió de paso
    assert (tmp_path / "trabajo" / "fuente" / "pages" / "hipporag.md").exists()
    wiki.marcar_ingerido("2502.14802")
    grafo.consultar("otra")
    assert len([o for o in procesos.ordenes if "update" in o]) == 2


def test_el_grafo_sin_nodos_lo_dice_y_un_fallo_de_graphify_se_para(tmp_path, wiki):
    procesos = Procesos(salida_consulta="")
    grafo = GrafoDelWiki(wiki, "graphify", tmp_path / "t", ejecutor=procesos)
    assert grafo.consultar("nada") == ("No node matches.", "no nodes")
    roto = Procesos()
    roto.codigo = 1
    with pytest.raises(ErrorDeCapa):
        GrafoDelWiki(wiki, "graphify", tmp_path / "u", ejecutor=roto).consultar("x")

    def sin_programa(orden, **kwargs):
        raise FileNotFoundError(orden[0])

    with pytest.raises(ErrorDeCapa, match="graphify"):
        GrafoDelWiki(wiki, "no-existe", tmp_path / "v", ejecutor=sin_programa).consultar("x")


def test_tgrep_recorta_a_pocas_lineas_e_indexa_al_cambiar_de_paso(tmp_path, wiki):
    lineas = "\n".join(f"pages\\p{i}.md:{i}:texto {i}" for i in range(1, 8))
    procesos = Procesos(salida_consulta=lineas)
    tgrep = BusquedaTgrep(wiki, "tgrep", tmp_path / "t", maximo=3, ejecutor=procesos)
    texto, resumen = tgrep.consultar("texto")
    assert texto.splitlines() == [f"pages/p{i}.md:{i}:texto {i}" for i in (1, 2, 3)]
    assert resumen == "7 lines"
    busqueda = procesos.ordenes[-1]
    assert "-M" in busqueda and "300" in busqueda and "--max-columns-preview" in busqueda
    tgrep.consultar("otro")
    assert len([o for o in procesos.ordenes if o[1] == "index"]) == 1
    wiki.marcar_ingerido("2502.14802")
    tgrep.consultar("otro")
    assert len([o for o in procesos.ordenes if o[1] == "index"]) == 2


def test_tgrep_no_toca_las_barras_del_texto(tmp_path, wiki):
    procesos = Procesos(salida_consulta=r"pages\p.md:3:vale $\geq 4$")
    tgrep = BusquedaTgrep(wiki, "tgrep", tmp_path / "t", ejecutor=procesos)
    assert tgrep.consultar("geq")[0] == r"pages/p.md:3:vale $\geq 4$"


def test_tgrep_patron_invalido_y_sin_coincidencias(tmp_path, wiki):
    procesos = Procesos(salida_consulta="")
    tgrep = BusquedaTgrep(wiki, "tgrep", tmp_path / "t", ejecutor=procesos)
    assert tgrep.consultar("x") == ("No lines match this pattern.", "no lines match")
    procesos.codigo = 2
    assert tgrep.consultar("(")[1] == "invalid pattern"


def test_el_modo_con_capas_acepta_sus_acciones_y_rechaza_search():
    extras = {"graph": "query", "grep": "pattern"}
    assert analizar_accion(accion(action="graph", query=" pagerank "), extras) == (
        "graph",
        "pagerank",
    )
    for malo in (accion(action="search", query="x"), accion(action="graph", query="")):
        with pytest.raises(ErrorDeFormato):
            analizar_accion(malo, extras)
    assert analizar_accion(accion(action="search", query="x")) == ("search", "x")  # modo base


def test_el_agente_con_capas_usa_grafo_lee_por_seccion_y_grep_exige_leer_antes(tmp_path, wiki):
    procesos = Procesos()
    capas = crear_capas(wiki, "graphify", tmp_path / "t", tgrep="tgrep", ejecutor=procesos)
    modelo, http = modelo_guionado(
        tmp_path,
        [
            accion(action="graph", query="pagerank"),
            accion(action="grep", pattern="74"),  # aún no leyó: se rechaza
            accion(action="read", pages=["hipporag#Setup"]),
            accion(action="grep", pattern="PageRank"),
            accion(action="answer", answer=f"It uses personalized PageRank [{S1}]."),
        ],
    )
    agente = ConsultaWiki(modelo, wiki, spans_validos={S1}, capas=capas)
    resultado = agente.responder("What does HippoRAG use?")
    sistema = http.solicitudes[0]["messages"][0]["content"]
    assert sistema == capas.instrucciones() != INSTRUCCIONES_AGENTE
    assert '"action": "graph"' in sistema and '"action": "search"' not in sistema
    assert resultado.citas == (S1,) and not resultado.abstuvo
    pasos = [(p["accion"], p["resultado"]) for p in agente.traza.detalle]
    assert pasos[1] == ("grep", "rejected: read first")
    assert pasos[0][0] == "graph" and pasos[2][0] == "read"
    assert pasos[3][0] == "grep" and pasos[3][1] != "rejected: read first"
    assert AVISO_LEER_PRIMERO in http.solicitudes[2]["messages"][-1]["content"]
    assert agente.traza.paginas_leidas == ["hipporag"]  # el grep no cuenta como lectura


def test_sin_capas_el_agente_conserva_su_protocolo(tmp_path, wiki):
    modelo, http = modelo_guionado(
        tmp_path,
        [
            accion(action="search", query="PageRank"),
            accion(action="read", pages=["hipporag"]),
            accion(action="answer", answer=f"PageRank [{S1}]."),
        ],
    )
    ConsultaWiki(modelo, wiki, spans_validos={S1}).responder("q")
    assert http.solicitudes[0]["messages"][0]["content"] == INSTRUCCIONES_AGENTE


def test_el_brazo_con_capas_no_ingiere_y_comparte_el_wiki(tmp_path, wiki):
    modelo, _ = modelo_guionado(tmp_path, [])
    brazo = BrazoWikiCapas(
        nombre_del_brazo(False), modelo, wiki, CapasDeConsulta(()), spans_validos=set()
    )
    resultado = brazo.ingerir("2405.14831")
    assert (resultado.usd, resultado.llamadas, resultado.tokens_entrada) == (0.0, 0, 0)
    assert brazo.nombre == "wiki_grafo" and brazo.ingeridos == wiki.ingeridos
    assert nombre_del_brazo(True) == "wiki_grafo_tgrep"


def _argumentos(**extra):
    return SimpleNamespace(k=5, max_acciones=8, **extra)


def test_sin_las_opciones_la_corrida_declara_y_estima_igual_que_antes():
    argumentos = _argumentos()
    assert nombres_de_brazos(argumentos) == ["rag", "wiki"]
    assert set(_brazos_declarados(argumentos)) == {"rag", "wiki"}


def test_con_graphify_se_declara_un_brazo_mas_que_no_suma_ingesta():
    argumentos = _argumentos(graphify="graphify", tgrep="tgrep")
    assert nombres_de_brazos(argumentos) == ["rag", "wiki", "wiki_grafo_tgrep"]
    declarado = _brazos_declarados(argumentos)["wiki_grafo_tgrep"]
    assert declarado["capas"] == ["graphify", "tgrep"] and declarado["comparte_wiki_con"] == "wiki"
    dos = estimar(["rag", "wiki"], preguntas=10, pasos=2, papers=5)
    tres = estimar(["rag", "wiki", "wiki_grafo"], preguntas=10, pasos=2, papers=5)
    assert tres.usd_ingesta == dos.usd_ingesta and tres.usd_preguntas > dos.usd_preguntas
