"""Selección de brazos de `arnes correr --brazos`, con piezas falsas: sin modelo ni red."""

from types import SimpleNamespace

import pytest

from test_arnes import BrazoFalso
from test_arnes_cli import BANCO_MIXTO, Entorno
from wikillm.arnes.__main__ import _brazos_declarados, _error_de_brazos, nombres_de_brazos
from wikillm.arnes.registro import leer_corrida, leer_lineas


def _argumentos(**extra):
    return SimpleNamespace(k=5, max_acciones=8, **extra)


def test_sin_brazos_todo_queda_como_antes():
    argumentos = _argumentos()
    assert nombres_de_brazos(argumentos) == ["rag", "wiki"]
    assert list(_brazos_declarados(argumentos)) == ["rag", "wiki"]
    assert _error_de_brazos(argumentos) is None


def test_se_eligen_los_brazos_en_el_orden_de_siempre():
    argumentos = _argumentos(brazos="wiki,rag")
    assert nombres_de_brazos(argumentos) == ["rag", "wiki"]
    solo_rag = _argumentos(brazos="rag")
    assert nombres_de_brazos(solo_rag) == ["rag"]
    assert _brazos_declarados(solo_rag) == {"rag": {"k": 5, "base_vectorial": "qdrant"}}


def test_el_brazo_con_grafo_se_elige_con_graphify_y_va_con_el_wiki():
    argumentos = _argumentos(brazos="wiki,wiki_grafo", graphify="graphify")
    assert nombres_de_brazos(argumentos) == ["wiki", "wiki_grafo"]
    assert list(_brazos_declarados(argumentos)) == ["wiki", "wiki_grafo"]
    assert _error_de_brazos(argumentos) is None


@pytest.mark.parametrize(
    "extra, fragmento",
    [
        ({"brazos": "rag,otro"}, "desconocido otro"),
        ({"brazos": "wiki_grafo,wiki"}, "--graphify"),
        ({"brazos": "rag,wiki", "graphify": "graphify"}, "inclúyelo en --brazos"),
        ({"brazos": "rag,wiki_grafo", "graphify": "graphify"}, "incluye también wiki"),
        ({"brazos": "rag", "wiki_de": "construccion-1"}, "--wiki-de es del brazo wiki"),
    ],
)
def test_combinaciones_incoherentes_dan_un_mensaje_claro(extra, fragmento):
    assert fragmento in _error_de_brazos(_argumentos(**extra))


class EntornoSoloRag(Entorno):
    def crear_brazos(self, modelo, ajustes, argumentos):
        self.fabricas += 1
        return [BrazoFalso("rag", [])]


def test_una_corrida_solo_con_rag_declara_estima_y_responde_solo_con_rag(tmp_path):
    e = EntornoSoloRag(tmp_path, BANCO_MIXTO)
    assert e.correr("--pasos", "0,2", "--brazos", "rag", "--k", "10") == 0
    datos = leer_corrida(e.carpeta / "corrida.json")
    assert datos["brazos"] == {"rag": {"k": 10, "base_vectorial": "qdrant"}}
    filas = leer_lineas(e.carpeta / "respuestas.jsonl")
    assert {f["system"] for f in filas} == {"rag"} and len(filas) == 2 * 2
    assert "2 preguntas × 2 pasos × 1 brazos = 4 respuestas" in e.texto


def test_brazos_invalidos_terminan_con_error_sin_crear_la_corrida(tmp_path, capsys):
    e = Entorno(tmp_path, BANCO_MIXTO)
    assert e.correr("--pasos", "0", "--brazos", "wiki_grafo") == 1
    assert "Error:" in capsys.readouterr().err
    assert e.fabricas == 0 and not (tmp_path / "results").exists()


def test_no_se_reanuda_una_corrida_con_otros_brazos(tmp_path, capsys):
    e = EntornoSoloRag(tmp_path, BANCO_MIXTO)
    assert e.correr("--pasos", "0", "--brazos", "rag") == 0
    assert e.correr("--pasos", "0") == 1
    assert "brazos" in capsys.readouterr().err
