"""Cliente del modelo observado: avisa de cada llamada sin alterar la respuesta ni el registro."""

import json
from types import SimpleNamespace

import pytest

from cliente_guionado import ClienteGuionado
from test_responder import AJUSTES
from wikillm.common.modelo import ClienteModelo, ErrorDeModelo
from wikillm.panel.observado import LARGO_TEXTO, ClienteObservado

MENSAJES = [{"role": "user", "content": "Pregunta"}]


def observado(tmp_path, textos):
    eventos = []
    http = ClienteGuionado(textos)
    cliente = ClienteObservado(
        AJUSTES, emitir=eventos.append, ruta_registro=tmp_path / "llamadas.jsonl", cliente=http
    )
    return cliente, eventos


def test_cada_llamada_emite_un_aviso_al_empezar_y_otro_al_terminar_con_sus_metricas(tmp_path):
    cliente, eventos = observado(tmp_path, ['{"action": "search", "query": "PageRank"}'])
    respuesta = cliente.generar(MENSAJES, etiqueta="wiki")
    assert [e["t"] for e in eventos] == ["llamando", "llamada"]
    assert eventos[0] == {"t": "llamando", "etiqueta": "wiki"}
    llamada = eventos[1]
    assert llamada["etiqueta"] == "wiki"
    assert llamada["tokens_entrada"] == 1000 and llamada["tokens_cache"] == 0
    assert llamada["tokens_salida"] == 100
    assert llamada["usd"] == respuesta.usd and llamada["segundos"] >= 0
    assert llamada["texto"] == '{"action": "search", "query": "PageRank"}'


def test_la_respuesta_y_el_registro_son_los_del_cliente_normal(tmp_path):
    cliente, _ = observado(tmp_path, ["Texto de respuesta"])
    normal = ClienteModelo(
        AJUSTES,
        ruta_registro=tmp_path / "normal.jsonl",
        cliente=ClienteGuionado(["Texto de respuesta"]),
    )
    a, b = cliente.generar(MENSAJES, etiqueta="rag"), normal.generar(MENSAJES, etiqueta="rag")
    assert (a.texto, a.tokens_entrada_sin_cache, a.tokens_salida, a.usd) == (
        b.texto,
        b.tokens_entrada_sin_cache,
        b.tokens_salida,
        b.usd,
    )
    fila = json.loads((tmp_path / "llamadas.jsonl").read_text("utf-8").splitlines()[0])
    assert fila["etiqueta"] == "rag" and fila["respuesta"] == "Texto de respuesta"
    assert cliente.gasto_acumulado == a.usd


def test_el_texto_del_aviso_se_recorta_pero_la_respuesta_no(tmp_path):
    largo = "x" * (LARGO_TEXTO + 300)
    cliente, eventos = observado(tmp_path, [largo])
    assert cliente.generar(MENSAJES).texto == largo
    assert eventos[1]["texto"] == "x" * LARGO_TEXTO


def test_una_llamada_fallida_avisa_y_vuelve_a_lanzar_el_error(tmp_path):
    class Rechaza:
        def __init__(self):
            self.chat = SimpleNamespace(completions=self)

        def create(self, **_):
            error = Exception("clave inválida")
            error.status_code = 401
            raise error

    eventos = []
    cliente = ClienteObservado(
        AJUSTES, emitir=eventos.append, ruta_registro=tmp_path / "l.jsonl", cliente=Rechaza()
    )
    with pytest.raises(ErrorDeModelo):
        cliente.generar(MENSAJES, etiqueta="wiki")
    assert [e["t"] for e in eventos] == ["llamando", "llamada_fallida"]
    assert eventos[1]["etiqueta"] == "wiki" and "clave inválida" in eventos[1]["motivo"]
