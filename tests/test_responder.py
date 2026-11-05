"""Pruebas del contrato de los brazos. Ninguna llama a la API real ni gasta saldo."""

import json
from dataclasses import replace
from types import SimpleNamespace

import pytest

from wikillm.common.config import Settings
from wikillm.common.modelo import ClienteModelo, Respuesta, TopeDeGastoError
from wikillm.common.responder import Brazo, ResultadoBrazo


def resultado(**cambios):
    base = {
        "respuesta": "Según el paper, X.",
        "fuentes": ["2405.14831", "2502.14802"],
        "tokens_entrada": 1000,
        "tokens_salida": 50,
        "segundos": 1.5,
        "usd": 0.0002,
        "llamadas": 1,
    }
    return ResultadoBrazo(**{**base, **cambios})


def llamada(sin_cache=800, cache=200, salida=50, usd=0.0001, segundos=1.0):
    return Respuesta("texto", sin_cache, cache, salida, 0, segundos, usd, 1)


def test_resultado_valido_con_y_sin_fuentes():
    assert resultado().fuentes == ("2405.14831", "2502.14802")
    assert resultado(fuentes=[]).fuentes == ()


@pytest.mark.parametrize(
    ("cambios", "motivo"),
    [
        ({"respuesta": "   "}, "vacía"),
        ({"tokens_entrada": -1}, "tokens_entrada"),
        ({"usd": -0.1}, "usd"),
        ({"fuentes": ["2405.14831v2"]}, "2405.14831v2"),
        ({"fuentes": ["hola"]}, "hola"),
        ({"fuentes": ["2405.14831", "2405.14831"]}, "repetidas"),
    ],
)
def test_resultado_invalido_indica_el_motivo(cambios, motivo):
    with pytest.raises(ValueError, match=motivo):
        resultado(**cambios)


def test_a_dict_es_serializable_y_tiene_los_campos_del_contrato():
    datos = resultado().a_dict()
    assert json.loads(json.dumps(datos)) == datos
    assert set(datos) == {
        "respuesta",
        "fuentes",
        "tokens_entrada",
        "tokens_salida",
        "segundos",
        "usd",
        "llamadas",
    }


def test_desde_una_llamada_suma_entrada_con_y_sin_cache():
    r = ResultadoBrazo.desde_llamadas("Hola", ["2405.14831"], [llamada()], 2.0)
    assert (r.tokens_entrada, r.tokens_salida, r.llamadas, r.segundos) == (1000, 50, 1, 2.0)


def test_desde_tres_llamadas_suma_todo():
    llamadas = [llamada(usd=0.1), llamada(usd=0.2, salida=10), llamada(usd=0.3, salida=5)]
    r = ResultadoBrazo.desde_llamadas("Hola", [], llamadas, 4.0)
    assert r.tokens_entrada == 3000
    assert r.tokens_salida == 65
    assert r.llamadas == 3
    assert r.usd == pytest.approx(0.6)


class BrazoFalso:
    nombre = "falso"

    def __init__(self, modelo):
        self.modelo = modelo

    def responder(self, pregunta):
        llamadas = [self.modelo.generar([{"role": "user", "content": pregunta}], etiqueta="falso")]
        return ResultadoBrazo.desde_llamadas(llamadas[0].texto, ["2405.14831"], llamadas, 0.1)


def test_un_objeto_sin_nombre_o_sin_responder_no_es_brazo():
    assert isinstance(BrazoFalso(None), Brazo)
    assert not isinstance(SimpleNamespace(responder=lambda p: None), Brazo)
    assert not isinstance(SimpleNamespace(nombre="x"), Brazo)


AJUSTES = Settings(
    api_key="sk-prueba",
    base_url="https://api.deepseek.com",
    model="deepseek-flash",
    thinking="disabled",
    reasoning_effort="",
    temperature=0.0,
    max_retries=0,
    timeout_seconds=30.0,
    price_input_cache_miss=0.15,
    price_input_cache_hit=0.003,
    price_output=0.60,
    max_usd_per_run=2.0,
    embedding_model="BAAI/bge-small-en-v1.5",
    embedding_device="cuda",
)


class ClienteHttpFalso:
    def __init__(self):
        uso = SimpleNamespace(
            prompt_tokens=1000,
            prompt_cache_hit_tokens=200,
            prompt_cache_miss_tokens=800,
            completion_tokens=50,
            completion_tokens_details=SimpleNamespace(reasoning_tokens=0),
        )
        self._bruta = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="Respuesta"))], usage=uso
        )
        self.llamadas = 0
        self.chat = SimpleNamespace(completions=self)

    def create(self, **_argumentos):
        self.llamadas += 1
        return self._bruta


def test_brazo_con_cliente_falso_devuelve_metricas_sumadas(tmp_path):
    http = ClienteHttpFalso()
    modelo = ClienteModelo(AJUSTES, ruta_registro=tmp_path / "l.jsonl", cliente=http)
    r = BrazoFalso(modelo).responder("¿Qué propone HippoRAG?")
    assert (r.respuesta, r.tokens_entrada, r.tokens_salida, r.llamadas) == (
        "Respuesta",
        1000,
        50,
        1,
    )
    assert r.usd > 0


def test_el_tope_de_gasto_se_propaga_sin_resultado(tmp_path):
    http = ClienteHttpFalso()
    sin_saldo = replace(AJUSTES, max_usd_per_run=0.0)
    modelo = ClienteModelo(sin_saldo, ruta_registro=tmp_path / "l.jsonl", cliente=http)
    with pytest.raises(TopeDeGastoError):
        BrazoFalso(modelo).responder("¿Hola?")
    assert http.llamadas == 0
