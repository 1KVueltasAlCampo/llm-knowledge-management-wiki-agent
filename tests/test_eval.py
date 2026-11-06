import json
from dataclasses import dataclass

import pytest

from wikillm.eval.acuerdo import acuerdo_de_hojas, kappa_cohen
from wikillm.eval.banco import esperado_en_paso, validar_banco
from wikillm.eval.correctitud import (
    CORRECTA,
    INCORRECTA,
    INDETERMINADA,
    clave_presente,
    evaluar,
    extraer_numeros,
)
from wikillm.eval.juez import Juez, interpretar
from wikillm.eval.metricas import agregar, evaluar_resultados, fundamentacion
from wikillm.eval.modelos import _SinExtraBody
from wikillm.eval.sinteticos import generar

ORDEN = {"2601.1": 1, "2602.1": 2, "2603.1": 3}


def _pregunta(**cambios):
    base = {
        "id": "A-T1-001",
        "texto": "¿Qué exactitud obtuvo el wiki?",
        "tipo": "T1",
        "respuesta_oraculo": "0,71",
        "respuesta_clave": ["0.71"],
        "evidencia": [{"span_id": "2602.1#s1.p1", "sha256": "x"}],
        "fuentes_requeridas": ["2602.1"],
        "ingesta_minima": 2,
        "autor": "A",
        "estado_verificacion": "borrador",
    }
    return {**base, **cambios}


def test_numeros_con_coma_punto_miles_y_porcentaje():
    assert extraer_numeros("0,71 y 1,234.5 y 71 %") == [0.71, 1234.5, 71.0, 0.71]
    assert clave_presente("0.71", "obtuvo 71% de exactitud")
    assert clave_presente("HippoRAG 2", "supera a hipporag-2 claramente")
    assert not clave_presente("0.71", "obtuvo 0,72")


def test_evaluar_capa1():
    pregunta = _pregunta()
    respondible = esperado_en_paso(pregunta, 2)
    assert evaluar(respondible, "La exactitud fue 0,71.", False) == CORRECTA
    assert evaluar(respondible, "Fue bastante alta.", False) == INDETERMINADA
    assert evaluar(respondible, "", True) == INCORRECTA
    antes = esperado_en_paso(pregunta, 1)
    assert evaluar(antes, "No consta.", True) == CORRECTA
    assert evaluar(antes, "0,71", False) == INCORRECTA


def test_t4_cambia_la_respuesta_esperada_con_el_paso():
    pregunta = _pregunta(
        tipo="T4",
        respuesta_por_paso=[{"desde": 3, "respuesta_oraculo": "0,80", "respuesta_clave": ["0.80"]}],
    )
    assert esperado_en_paso(pregunta, 2).respuesta_clave == ["0.71"]
    assert esperado_en_paso(pregunta, 3).respuesta_clave == ["0.80"]


def test_validar_banco_detecta_problemas():
    assert validar_banco([_pregunta()], ORDEN) == []
    malas = [
        _pregunta(id="x", ingesta_minima=1),
        _pregunta(id="x", tipo="T9"),
        _pregunta(id="y", tipo="T2"),
        _pregunta(id="z", fuentes_requeridas=["9999.9"]),
        _pregunta(id="w", estado_verificacion="aprobado"),
    ]
    problemas = " | ".join(validar_banco(malas, ORDEN))
    for fragmento in (
        "ingesta_minima 1",
        "id repetido",
        "tipo inválido",
        "al menos dos fuentes",
        "fuera del corpus",
        "estado inválido",
    ):
        assert fragmento in problemas


def test_kappa_de_cohen_valores_conocidos():
    perfecto = kappa_cohen(["s", "n", "s"], ["s", "n", "s"])
    assert perfecto.porcentaje == 1.0 and perfecto.kappa == pytest.approx(1.0)
    # Ejemplo clásico: 20 SS, 5 SN, 10 NS, 15 NN → kappa = 0,4
    a = ["s"] * 25 + ["n"] * 25
    b = ["s"] * 20 + ["n"] * 5 + ["s"] * 10 + ["n"] * 15
    resultado = kappa_cohen(a, b)
    assert resultado.porcentaje == pytest.approx(0.7)
    assert resultado.kappa == pytest.approx(0.4)
    assert kappa_cohen(["s", "s"], ["s", "s"]).kappa is None


def test_acuerdo_de_hojas_csv(tmp_path):
    (tmp_path / "a.csv").write_text("question_id,veredicto\nq1,si\nq2,no\nq3,\n", encoding="utf-8")
    (tmp_path / "b.csv").write_text(
        "question_id,veredicto\nq1,si\nq2,si\nq3,si\n", encoding="utf-8"
    )
    resultado = acuerdo_de_hojas(tmp_path / "a.csv", tmp_path / "b.csv", "veredicto")
    assert resultado.n == 2
    assert resultado.porcentaje == 0.5


def test_fundamentacion_exige_span_existente_y_paper_ya_ingerido():
    spans = {"2601.1#s1.p1": {"arxiv_id": "2601.1"}, "2603.1#s1.p1": {"arxiv_id": "2603.1"}}
    citas = ["2601.1#s1.p1", "2603.1#s1.p1", "inventada#s9.p9"]
    assert fundamentacion(citas, 2, spans, ORDEN) == pytest.approx(1 / 3)
    assert fundamentacion(citas, 3, spans, ORDEN) == pytest.approx(2 / 3)
    assert fundamentacion([], 3, spans, ORDEN) is None


def test_juez_interpreta_y_solo_se_usa_en_indeterminadas():
    assert interpretar('ok {"veredicto": "Correcta", "motivo": "igual"}') == (CORRECTA, "igual")
    assert interpretar("sin json")[0] == INDETERMINADA
    assert interpretar('{"veredicto": "quizá"}')[0] == INDETERMINADA

    @dataclass
    class _Resp:
        texto: str

    class _Cliente:
        def __init__(self):
            self.llamadas = 0

        def generar(self, mensajes, etiqueta, max_tokens):
            self.llamadas += 1
            assert "0,71" in mensajes[1]["content"]
            return _Resp('{"veredicto": "correcta", "motivo": "parafrasea"}')

    cliente = _Cliente()
    banco = {"A-T1-001": _pregunta()}
    base = {"question_id": "A-T1-001", "system": "wiki", "ingest_step": 2, "abstained": False}
    resultados = [
        {**base, "answer": "fue 0,71", "citations": []},
        {**base, "answer": "setenta y uno por ciento", "citations": []},
    ]
    evaluados = evaluar_resultados(resultados, banco, {}, ORDEN, Juez(cliente))
    assert [e["origen_veredicto"] for e in evaluados] == ["determinista", "juez"]
    assert cliente.llamadas == 1


def test_sin_extra_body_quita_la_opcion_de_deepseek():
    class _Fake:
        def __init__(self):
            self.chat = self
            self.completions = self
            self.recibido = None

        def create(self, **kw):
            self.recibido = kw
            return "ok"

    fake = _Fake()
    _SinExtraBody(fake).chat.completions.create(model="m", extra_body={"thinking": {}})
    assert fake.recibido == {"model": "m"}


def test_metricas_de_punta_a_punta_con_sinteticos():
    banco = [
        _pregunta(),
        _pregunta(
            id="A-T5-001",
            tipo="T5",
            fuentes_requeridas=[],
            evidencia=[],
            ingesta_minima=None,
            respuesta_clave=[],
        ),
    ]
    spans = {"2602.1#s1.p1": {"arxiv_id": "2602.1"}}
    filas = generar(banco, [1, 3], {"2602.1": ["2602.1#s1.p1"]})
    assert len(filas) == 2 * 2 * 2
    json.dumps(filas)  # serializable tal como lo pide el contrato
    evaluados = evaluar_resultados(filas, {p["id"]: p for p in banco}, spans, ORDEN)
    agregados = agregar(evaluados)
    claves = {(a["system"], a["ingest_step"]) for a in agregados}
    assert claves == {("rag", 1), ("rag", 3), ("wiki", 1), ("wiki", 3)}
    paso1 = next(a for a in agregados if a["system"] == "wiki" and a["ingest_step"] == 1)
    assert paso1["n_respondibles"] == 0 and paso1["cobertura"] is None


def test_libro_cerrado_produce_el_contrato_y_detecta_abstencion():
    from wikillm.eval.libro_cerrado import correr
    from wikillm.eval.metricas import OBLIGATORIOS_RESULTADO

    @dataclass
    class _R:
        texto: str
        tokens_entrada_sin_cache: int = 10
        tokens_entrada_cache: int = 0
        tokens_salida: int = 5
        segundos: float = 0.1
        usd: float = 0.0

    class _Cliente:
        def generar(self, mensajes, etiqueta, max_tokens):
            assert len(mensajes) == 2  # sin contexto del corpus
            return _R("I don’t know.")

    banco = [_pregunta(), _pregunta(id="A-T5-001", tipo="T5")]
    filas = correr(banco, _Cliente(), "m", 50, "r")
    assert len(filas) == 1  # T5 no aplica
    assert filas[0]["abstained"] is True
    assert all(c in filas[0] for c in OBLIGATORIOS_RESULTADO)


def test_precios_del_redactor_usan_cota_superior_o_env(monkeypatch):
    from dataclasses import replace as reemplazar

    from wikillm.common.config import load_settings
    from wikillm.eval.modelos import precios_redactor

    for nombre in (
        "DRAFT_PRICE_INPUT_CACHE_MISS_USD_PER_M",
        "DRAFT_PRICE_INPUT_CACHE_HIT_USD_PER_M",
        "DRAFT_PRICE_OUTPUT_USD_PER_M",
    ):
        monkeypatch.delenv(nombre, raising=False)
    monkeypatch.setattr("wikillm.eval.modelos.load_dotenv", lambda: None)
    base = reemplazar(
        load_settings(), price_input_cache_miss=0.15, price_input_cache_hit=0.003, price_output=0.6
    )
    assert precios_redactor(base) == pytest.approx((0.6, 0.012, 2.4))
    monkeypatch.setenv("DRAFT_PRICE_OUTPUT_USD_PER_M", "1.5")
    assert precios_redactor(base)[2] == 1.5


def test_validar_banco_rechaza_claves_que_ya_estan_en_la_pregunta():
    mala = _pregunta(texto="¿Qué supera a HippoRAG?", respuesta_clave=["hipporag"])
    assert any("presente en la pregunta" in p for p in validar_banco([mala], ORDEN))


def test_juez_por_defecto_es_flash_lite_y_respeta_judge_model(monkeypatch):
    from wikillm.eval.modelos import crear_juez

    monkeypatch.setattr("wikillm.eval.modelos.load_dotenv", lambda: None)
    monkeypatch.setattr("wikillm.common.config.load_dotenv", lambda: None)  # sin leer .env
    monkeypatch.delenv("JUDGE_MODEL", raising=False)
    juez = crear_juez("/dev/null", cliente=object())
    assert juez._ajustes.model == "gemini-3.1-flash-lite"
    assert juez._ajustes.temperature == 0.0
    monkeypatch.setenv("JUDGE_MODEL", "otro-modelo")
    assert crear_juez("/dev/null", cliente=object())._ajustes.model == "otro-modelo"
