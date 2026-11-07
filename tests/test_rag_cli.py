"""Orden de consola del RAG con piezas falsas: no abre modelos ni llama a la API."""

from types import SimpleNamespace

from test_rag_brazo import DOCUMENTOS, AlmacenFalso, ClienteHttpFalso
from test_rag_indice import AJUSTES
from wikillm.common.modelo import ClienteModelo, TopeDeGastoError
from wikillm.rag.__main__ import principal
from wikillm.rag.indice import ErrorDeDispositivo, InformeIndice


def abrir_falso(argumentos, ajustes):
    return AlmacenFalso(DOCUMENTOS), InformeIndice(3, True, 0.5)


def modelo_falso(tmp_path, texto="Respuesta [2405.14831]."):
    http = ClienteHttpFalso(texto)
    return lambda ajustes: ClienteModelo(
        AJUSTES, ruta_registro=tmp_path / "llamadas.jsonl", cliente=http
    ), http


def ejecutar(argv, tmp_path, abrir=abrir_falso, texto="Respuesta [2405.14831]."):
    fabrica, http = modelo_falso(tmp_path, texto)
    lineas = []
    codigo = principal(argv, salida=lineas.append, abrir=abrir, crear_modelo=fabrica)
    return codigo, "\n".join(lineas), http


def test_indexar_informa_el_indice_y_no_llama_al_modelo(tmp_path):
    codigo, texto, http = ejecutar(["indexar"], tmp_path)
    assert codigo == 0
    assert "Índice reconstruido: 3 fragmentos" in texto
    assert http.solicitudes == []


def test_preguntar_muestra_respuesta_fuentes_y_metricas(tmp_path):
    codigo, texto, http = ejecutar(["preguntar", "¿Qué método usa?"], tmp_path)
    assert codigo == 0
    assert "Respuesta [2405.14831]." in texto
    assert "Fuentes: 2405.14831" in texto
    assert "2000 de entrada y 80 de salida" in texto
    assert len(http.solicitudes) == 1


def test_preguntar_sin_fuentes_lo_indica(tmp_path):
    _, texto, _ = ejecutar(["preguntar", "¿Hola?"], tmp_path, texto="No hay datos.")
    assert "Fuentes: (ninguna)" in texto


def test_un_error_de_dispositivo_devuelve_codigo_1_con_el_mensaje(tmp_path, capsys):
    def sin_gpu(argumentos, ajustes):
        raise ErrorDeDispositivo("Pon EMBEDDING_DEVICE=cpu en tu .env.")

    codigo, _, _ = ejecutar(["indexar"], tmp_path, abrir=sin_gpu)
    assert codigo == 1
    assert "EMBEDDING_DEVICE=cpu" in capsys.readouterr().err


def test_el_tope_de_gasto_devuelve_codigo_1(tmp_path, capsys):
    def con_tope(ajustes):
        return SimpleNamespace(
            generar=lambda *a, **k: (_ for _ in ()).throw(TopeDeGastoError("Tope alcanzado"))
        )

    lineas = []
    codigo = principal(
        ["preguntar", "¿Hola?"], salida=lineas.append, abrir=abrir_falso, crear_modelo=con_tope
    )
    assert codigo == 1
    assert "Tope alcanzado" in capsys.readouterr().err
