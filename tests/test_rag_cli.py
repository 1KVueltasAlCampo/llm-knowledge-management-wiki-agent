"""Orden de consola del RAG con piezas falsas: no abre modelos ni llama a la API."""

import json

from test_rag_brazo import RECUPERADOS, S1, ClienteHttpFalso, IndiceFalso
from test_responder import AJUSTES
from wikillm.common.modelo import ClienteModelo, TopeDeGastoError
from wikillm.rag.__main__ import principal
from wikillm.rag.indice import GoldDistinto


class IndiceConTotal(IndiceFalso):
    total_fragmentos = 42


def manifest(tmp_path):
    # desordenado a propósito: la ingesta debe seguir orden_ingesta
    filas = [
        {"arxiv_id": "2603.0003", "orden_ingesta": 3},
        {"arxiv_id": "2601.0001", "orden_ingesta": 1},
        {"arxiv_id": "2602.0002", "orden_ingesta": 2},
    ]
    ruta = tmp_path / "manifest.jsonl"
    ruta.write_text("\n".join(json.dumps(f) for f in filas) + "\n", encoding="utf-8")
    return str(ruta)


def ejecutar(argv, tmp_path, indice=None, texto=f"Respuesta [{S1}]."):
    indice = indice or IndiceConTotal(RECUPERADOS)
    http = ClienteHttpFalso(texto)
    lineas = []
    codigo = principal(
        [*argv, "--manifest", manifest(tmp_path), "--spans", str(tmp_path / "no-existe.jsonl")],
        salida=lineas.append,
        crear_indice=lambda argumentos, ajustes: indice,
        crear_modelo=lambda ajustes: ClienteModelo(
            AJUSTES, ruta_registro=tmp_path / "llamadas.jsonl", cliente=http
        ),
    )
    return codigo, "\n".join(lineas), http, indice


def test_indexar_ingiere_en_orden_y_no_llama_al_modelo(tmp_path):
    codigo, texto, http, indice = ejecutar(["indexar"], tmp_path)
    assert codigo == 0
    assert indice.ingeridos == ["2601.0001", "2602.0002", "2603.0003"]
    assert "[3/3] 2603.0003" in texto
    assert "Ingeridos 3 papers" in texto and "42 fragmentos" in texto
    assert http.solicitudes == []


def test_paso_ingiere_solo_los_primeros_n(tmp_path):
    _, _, _, indice = ejecutar(["indexar", "--paso", "2"], tmp_path)
    assert indice.ingeridos == ["2601.0001", "2602.0002"]


def test_preguntar_muestra_respuesta_citas_y_metricas(tmp_path):
    codigo, texto, http, _ = ejecutar(["preguntar", "What method?"], tmp_path)
    assert codigo == 0
    assert f"Respuesta [{S1}]." in texto
    assert f"Citas: {S1}" in texto
    assert "Abstención: no" in texto
    assert "2000 de entrada" in texto and "80 de salida" in texto
    assert len(http.solicitudes) == 1


def test_preguntar_con_abstencion_lo_indica(tmp_path):
    _, texto, _, _ = ejecutar(
        ["preguntar", "Hello?"],
        tmp_path,
        texto="The ingested corpus does not contain this information.",
    )
    assert "Citas: (ninguna)" in texto and "Abstención: sí" in texto


def test_un_gold_distinto_devuelve_codigo_1_con_el_mensaje(tmp_path, capsys):
    class IndiceRoto(IndiceConTotal):
        def ingerir(self, arxiv_id):
            raise GoldDistinto(f"El Gold local de {arxiv_id} no coincide")

    codigo, _, _, _ = ejecutar(["indexar"], tmp_path, indice=IndiceRoto(RECUPERADOS))
    assert codigo == 1
    assert "2601.0001 no coincide" in capsys.readouterr().err


def test_el_tope_de_gasto_devuelve_codigo_1(tmp_path, capsys):
    class ModeloSinSaldo:
        def generar(self, *args, **kwargs):
            raise TopeDeGastoError("Tope alcanzado")

    lineas = []
    codigo = principal(
        ["preguntar", "Hello?", "--manifest", manifest(tmp_path), "--spans", str(tmp_path / "x")],
        salida=lineas.append,
        crear_indice=lambda a, s: IndiceConTotal(RECUPERADOS),
        crear_modelo=lambda ajustes: ModeloSinSaldo(),
    )
    assert codigo == 1
    assert "Tope alcanzado" in capsys.readouterr().err


def test_la_carpeta_del_indice_es_qdrant_y_chroma_queda_como_alias():
    from pathlib import Path

    from wikillm.rag.__main__ import _analizar

    assert _analizar(["indexar"]).indice == Path("data/qdrant")
    assert _analizar(["indexar", "--indice", "otra"]).indice == Path("otra")
    assert _analizar(["indexar", "--chroma", "vieja"]).indice == Path("vieja")
