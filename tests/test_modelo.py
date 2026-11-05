"""Pruebas del cliente del modelo con un cliente falso: no tocan la red ni gastan saldo."""

import json
from dataclasses import replace
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from wikillm.common.config import Settings
from wikillm.common.modelo import ClienteModelo, ErrorDeModelo, TopeDeGastoError

CLAVE = "sk-clave-secreta-de-prueba"
FUERA_DE_PICO = datetime(2026, 11, 9, 12, 0, tzinfo=UTC)  # lunes 12:00 UTC
EN_PICO = datetime(2026, 11, 9, 2, 0, tzinfo=UTC)  # lunes 02:00 UTC
MENSAJES = [{"role": "user", "content": "Hola, ¿cómo estás?"}]

AJUSTES = Settings(
    api_key=CLAVE,
    base_url="https://api.deepseek.com",
    model="deepseek-flash",
    thinking="disabled",
    reasoning_effort="",
    temperature=0.0,
    max_retries=2,
    timeout_seconds=30.0,
    price_input_cache_miss=0.15,
    price_input_cache_hit=0.003,
    price_output=0.60,
    max_usd_per_run=2.0,
    embedding_model="BAAI/bge-small-en-v1.5",
    embedding_device="cuda",
)


class ErrorHttp(Exception):
    def __init__(self, codigo: int, mensaje: str = "fallo"):
        super().__init__(mensaje)
        self.status_code = codigo


def respuesta_falsa(texto="Hola", entrada=1000, cache=0, salida=500, razonamiento=0):
    uso = SimpleNamespace(
        prompt_tokens=entrada,
        prompt_cache_hit_tokens=cache,
        prompt_cache_miss_tokens=entrada - cache,
        completion_tokens=salida,
        completion_tokens_details=SimpleNamespace(reasoning_tokens=razonamiento),
    )
    mensaje = SimpleNamespace(content=texto)
    return SimpleNamespace(choices=[SimpleNamespace(message=mensaje)], usage=uso)


class ClienteFalso:
    """Imita client.chat.completions.create devolviendo, en orden, respuestas o errores."""

    def __init__(self, guion):
        self.guion = list(guion)
        self.llamadas = []
        self.chat = SimpleNamespace(completions=self)

    def create(self, **argumentos):
        self.llamadas.append(argumentos)
        siguiente = self.guion.pop(0)
        if isinstance(siguiente, Exception):
            raise siguiente
        return siguiente


def crear(tmp_path, guion, ajustes=AJUSTES, ahora=FUERA_DE_PICO):
    cliente = ClienteFalso(guion)
    esperas = []
    modelo = ClienteModelo(
        ajustes,
        ruta_registro=tmp_path / "llamadas.jsonl",
        cliente=cliente,
        dormir=esperas.append,
        ahora=lambda: ahora,
    )
    return modelo, cliente, esperas


def leer_registro(tmp_path):
    lineas = (tmp_path / "llamadas.jsonl").read_text(encoding="utf-8").splitlines()
    return [json.loads(linea) for linea in lineas]


def test_llamada_exitosa_devuelve_texto_y_metricas(tmp_path):
    modelo, _, _ = crear(tmp_path, [respuesta_falsa("Respuesta", 1000, 200, 500, 30)])
    respuesta = modelo.generar(MENSAJES, etiqueta="rag")
    assert respuesta.texto == "Respuesta"
    assert respuesta.tokens_entrada_sin_cache == 800
    assert respuesta.tokens_entrada_cache == 200
    assert respuesta.tokens_salida == 500
    assert respuesta.tokens_razonamiento == 30
    assert respuesta.intentos == 1
    assert respuesta.segundos >= 0
    esperado = (800 * 0.15 + 200 * 0.003 + 500 * 0.60) / 1_000_000
    assert respuesta.usd == pytest.approx(esperado)
    assert modelo.gasto_acumulado == pytest.approx(esperado)


def test_usa_el_modelo_de_la_configuracion(tmp_path):
    modelo, cliente, _ = crear(tmp_path, [respuesta_falsa()], replace(AJUSTES, model="otro-modelo"))
    modelo.generar(MENSAJES)
    assert cliente.llamadas[0]["model"] == "otro-modelo"
    assert leer_registro(tmp_path)[0]["modelo"] == "otro-modelo"


def test_razonamiento_desactivado_aplica_la_temperatura(tmp_path):
    modelo, cliente, _ = crear(tmp_path, [respuesta_falsa()])
    modelo.generar(MENSAJES)
    llamada = cliente.llamadas[0]
    assert llamada["extra_body"]["thinking"] == {"type": "disabled"}
    assert llamada["temperature"] == 0.0


def test_razonamiento_activado_envia_el_esfuerzo_y_no_la_temperatura(tmp_path):
    ajustes = replace(AJUSTES, thinking="enabled", reasoning_effort="high")
    modelo, cliente, _ = crear(tmp_path, [respuesta_falsa()], ajustes)
    modelo.generar(MENSAJES)
    llamada = cliente.llamadas[0]
    assert llamada["extra_body"] == {"thinking": {"type": "enabled"}, "reasoning_effort": "high"}
    assert "temperature" not in llamada


def test_costo_en_hora_pico_es_el_doble(tmp_path):
    normal, _, _ = crear(tmp_path / "a", [respuesta_falsa()])
    pico, _, _ = crear(tmp_path / "b", [respuesta_falsa()], ahora=EN_PICO)
    assert pico.generar(MENSAJES).usd == pytest.approx(2 * normal.generar(MENSAJES).usd)


def test_el_registro_guarda_mensajes_respuesta_y_metricas(tmp_path):
    modelo, _, _ = crear(tmp_path, [respuesta_falsa("La respuesta completa")])
    modelo.generar(MENSAJES, etiqueta="wiki")
    (linea,) = leer_registro(tmp_path)
    assert linea["resultado"] == "ok"
    assert linea["etiqueta"] == "wiki"
    assert linea["mensajes"] == MENSAJES
    assert linea["respuesta"] == "La respuesta completa"
    assert linea["tokens_salida"] == 500
    assert len(linea["huella"]) == 64


def test_el_tope_de_gasto_impide_nuevas_llamadas(tmp_path):
    ajustes = replace(AJUSTES, max_usd_per_run=0.0004)  # una llamada cuesta 0,00045
    modelo, cliente, _ = crear(tmp_path, [respuesta_falsa(), respuesta_falsa()], ajustes)
    modelo.generar(MENSAJES)
    with pytest.raises(TopeDeGastoError):
        modelo.generar(MENSAJES)
    assert len(cliente.llamadas) == 1


def test_error_transitorio_se_recupera_con_espera_creciente(tmp_path):
    modelo, cliente, esperas = crear(tmp_path, [ErrorHttp(429), ErrorHttp(503), respuesta_falsa()])
    respuesta = modelo.generar(MENSAJES)
    assert respuesta.intentos == 3
    assert len(cliente.llamadas) == 3
    assert esperas == [1, 2]
    assert leer_registro(tmp_path)[0]["intentos"] == 3


def test_credencial_invalida_falla_sin_reintentos(tmp_path):
    modelo, cliente, esperas = crear(tmp_path, [ErrorHttp(401, "clave inválida")])
    with pytest.raises(ErrorDeModelo):
        modelo.generar(MENSAJES)
    assert len(cliente.llamadas) == 1
    assert esperas == []


def test_errores_transitorios_agotan_los_reintentos_y_se_registran(tmp_path):
    modelo, cliente, _ = crear(tmp_path, [ErrorHttp(500), ErrorHttp(500), ErrorHttp(500)])
    with pytest.raises(ErrorDeModelo):
        modelo.generar(MENSAJES)
    assert len(cliente.llamadas) == 3  # el intento inicial más 2 reintentos
    (linea,) = leer_registro(tmp_path)
    assert linea["resultado"] == "error"
    assert linea["mensajes"] == MENSAJES
    assert "respuesta" not in linea


def test_la_clave_no_aparece_en_errores_ni_en_el_registro(tmp_path):
    modelo, _, _ = crear(tmp_path, [ErrorHttp(401, f"Bearer {CLAVE} rechazada")])
    with pytest.raises(ErrorDeModelo) as excepcion:
        modelo.generar(MENSAJES)
    assert CLAVE not in str(excepcion.value)
    assert CLAVE not in (tmp_path / "llamadas.jsonl").read_text(encoding="utf-8")
    assert CLAVE not in repr(AJUSTES)


def test_sin_clave_y_sin_cliente_falla_con_mensaje_claro(tmp_path):
    with pytest.raises(ErrorDeModelo, match="DEEPSEEK_API_KEY"):
        ClienteModelo(replace(AJUSTES, api_key=""), ruta_registro=tmp_path / "x.jsonl")


def test_modo_de_razonamiento_invalido_se_rechaza(tmp_path):
    with pytest.raises(ValueError, match="DEEPSEEK_THINKING"):
        ClienteModelo(replace(AJUSTES, thinking="quizas"), cliente=ClienteFalso([]))
