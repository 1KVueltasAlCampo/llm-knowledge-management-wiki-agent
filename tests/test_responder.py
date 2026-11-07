"""Pruebas del contrato de los brazos. Ninguna llama a la API real ni gasta saldo."""

import json
from dataclasses import replace
from types import SimpleNamespace

import pytest

from wikillm.common.config import Settings
from wikillm.common.modelo import ClienteModelo, Respuesta, TopeDeGastoError
from wikillm.common.responder import (
    FRASE_ABSTENCION,
    Brazo,
    ResultadoBrazo,
    ResultadoIngesta,
    a_linea_ingesta,
    a_linea_resultado,
    es_abstencion,
)
from wikillm.eval.metricas import leer_resultados

A = "2405.14831#s2.p1"
B = "2405.14831#s5.p3"
C = "2502.14802#s3.p4"


def resultado(**cambios):
    base = {
        "respuesta": "Según el paper, X.",
        "citas": [A, C],
        "abstuvo": False,
        "tokens_contexto": 500,
        "tokens_entrada": 1000,
        "tokens_salida": 50,
        "segundos": 1.5,
        "usd": 0.0002,
        "llamadas": 1,
    }
    return ResultadoBrazo(**{**base, **cambios})


def llamada(sin_cache=800, cache=200, salida=50, usd=0.0001):
    return Respuesta("texto", sin_cache, cache, salida, 0, 1.0, usd, 1)


def test_resultado_valido_con_y_sin_citas():
    assert resultado().citas == (A, C)
    assert resultado(citas=[]).citas == ()


def test_las_fuentes_se_derivan_de_las_citas_sin_repetir():
    r = resultado(citas=[A, B, C])
    assert r.citas == (A, B, C)
    assert r.fuentes == ("2405.14831", "2502.14802")


@pytest.mark.parametrize(
    ("cambios", "motivo"),
    [
        ({"respuesta": "   "}, "vacía"),
        ({"tokens_entrada": -1}, "tokens_entrada"),
        ({"tokens_contexto": -1}, "tokens_contexto"),
        ({"usd": -0.1}, "usd"),
        ({"citas": ["2405.14831"]}, "2405.14831"),  # solo el paper, no un span
        ({"citas": ["hola"]}, "hola"),
        ({"citas": [A, A]}, "repetidas"),
        ({"abstuvo": True}, "abstención"),  # abstenerse con citas
    ],
)
def test_resultado_invalido_indica_el_motivo(cambios, motivo):
    with pytest.raises(ValueError, match=motivo):
        resultado(**cambios)


def test_una_abstencion_sin_citas_es_valida():
    r = resultado(respuesta=FRASE_ABSTENCION, citas=[], abstuvo=True)
    assert r.abstuvo and r.fuentes == ()


def test_a_dict_es_serializable_y_tiene_los_campos_del_contrato():
    datos = resultado().a_dict()
    assert json.loads(json.dumps(datos)) == datos
    assert set(datos) == {
        "respuesta",
        "citas",
        "abstuvo",
        "tokens_contexto",
        "tokens_entrada",
        "tokens_salida",
        "segundos",
        "usd",
        "llamadas",
    }


def test_la_frase_de_abstencion_se_reconoce_con_otra_puntuacion():
    assert es_abstencion(FRASE_ABSTENCION)
    assert es_abstencion("the ingested corpus does not contain this information")
    assert es_abstencion("  THE INGESTED CORPUS DOES NOT CONTAIN THIS INFORMATION!! ")
    assert not es_abstencion("The accuracy is 0.71 [2405.14831#s2.p1].")


def test_desde_una_llamada_suma_entrada_con_y_sin_cache():
    r = ResultadoBrazo.desde_llamadas("Hola", [A], [llamada()], 2.0)
    assert (r.tokens_entrada, r.tokens_salida, r.llamadas, r.segundos) == (1000, 50, 1, 2.0)
    assert r.citas == (A,) and not r.abstuvo and r.tokens_contexto == 0


def test_desde_tres_llamadas_suma_todo():
    llamadas = [llamada(usd=0.1), llamada(usd=0.2, salida=10), llamada(usd=0.3, salida=5)]
    r = ResultadoBrazo.desde_llamadas("Hola", [], llamadas, 4.0)
    assert (r.tokens_entrada, r.tokens_salida, r.llamadas) == (3000, 65, 3)
    assert r.usd == pytest.approx(0.6)


def test_tokens_de_contexto_son_un_token_cada_cuatro_caracteres():
    r = ResultadoBrazo.desde_llamadas("Hola", [], [llamada()], 1.0, contexto="x" * 4000)
    assert r.tokens_contexto == 1000


def test_una_abstencion_descarta_las_citas_que_trajera_el_modelo():
    r = ResultadoBrazo.desde_llamadas(FRASE_ABSTENCION, [A], [llamada()], 1.0)
    assert r.abstuvo and r.citas == ()


def test_resultado_de_ingesta_suma_llamadas_y_valida():
    r = ResultadoIngesta.desde_llamadas([llamada(), llamada(usd=0.3)], 2.5)
    assert (r.tokens_entrada, r.tokens_salida, r.llamadas, r.segundos) == (2000, 100, 2, 2.5)
    assert r.usd == pytest.approx(0.3001)
    sin_modelo = ResultadoIngesta.desde_llamadas([], 1.2)
    assert (sin_modelo.llamadas, sin_modelo.tokens_entrada, sin_modelo.usd) == (0, 0, 0)
    assert json.loads(json.dumps(sin_modelo.a_dict()))["segundos"] == 1.2
    with pytest.raises(ValueError, match="usd"):
        ResultadoIngesta(0, 0, 1.0, -1.0, 0)


def test_la_linea_de_resultado_la_acepta_el_lector_de_metricas(tmp_path):
    r = ResultadoBrazo.desde_llamadas(
        "Es 0.8 [2405.14831#s2.p1].", [A], [llamada()], 2.0, "x" * 400
    )
    linea = a_linea_resultado(
        r,
        run_id="corrida-1",
        question_id="A001-T1-01",
        system="rag",
        ingest_step=5,
        model="deepseek-flash",
        temperature=0.0,
        timestamp="2026-11-07T12:00:00Z",
    )
    assert linea["citations"] == [A]
    assert linea["abstained"] is False
    assert (linea["context_tokens"], linea["input_tokens"], linea["output_tokens"]) == (
        100,
        1000,
        50,
    )
    assert linea["latency_s"] == 2.0 and linea["cost_usd"] == pytest.approx(0.0001)
    ruta = tmp_path / "respuestas.jsonl"
    ruta.write_text(json.dumps(linea) + "\n", encoding="utf-8")
    assert leer_resultados(ruta)[0]["question_id"] == "A001-T1-01"


def test_la_linea_de_ingesta_nombra_el_paper_y_el_paso():
    r = ResultadoIngesta.desde_llamadas([llamada()], 3.0)
    linea = a_linea_ingesta(
        r,
        run_id="corrida-1",
        system="wiki",
        ingest_step=7,
        arxiv_id="2405.14831",
        model="deepseek-flash",
        timestamp="2026-11-07T12:00:00Z",
    )
    assert (linea["arxiv_id"], linea["ingest_step"], linea["calls"]) == ("2405.14831", 7, 1)
    assert json.loads(json.dumps(linea)) == linea


class BrazoFalso:
    nombre = "falso"

    def __init__(self, modelo):
        self.modelo = modelo

    def ingerir(self, arxiv_id):
        return ResultadoIngesta.desde_llamadas([], 0.1)

    def responder(self, pregunta):
        llamadas = [self.modelo.generar([{"role": "user", "content": pregunta}], etiqueta="falso")]
        return ResultadoBrazo.desde_llamadas(llamadas[0].texto, [A], llamadas, 0.1)


def test_un_objeto_sin_nombre_ingerir_o_responder_no_es_brazo():
    assert isinstance(BrazoFalso(None), Brazo)
    assert not isinstance(SimpleNamespace(ingerir=lambda i: None, responder=lambda p: None), Brazo)
    assert not isinstance(SimpleNamespace(nombre="x", responder=lambda p: None), Brazo)
    assert not isinstance(SimpleNamespace(nombre="x", ingerir=lambda i: None), Brazo)


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
    modelo = ClienteModelo(AJUSTES, ruta_registro=tmp_path / "l.jsonl", cliente=ClienteHttpFalso())
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
