import csv
import json
from dataclasses import dataclass

from wikillm.corpus.spans import calcular_spans
from wikillm.eval.banco import validar_banco
from wikillm.eval.plan_borradores import ejecutar, escribir_hoja, planear
from wikillm.eval.redaccion import Fuente, anclar, construir_mensajes, interpretar
from wikillm.ingest.gold import escribir_gold

CUERPO_1 = """# Paper uno

## 1 Results

The compiled wiki reached an accuracy of 0.71 on the
benchmark, against 0.64 for vector RAG.
"""
CUERPO_2 = """# Paper dos

## 4 Evaluation

With progressive disclosure the wiki accuracy rises to 0.80 while using fewer tokens.
"""
F1 = Fuente("2601.1", 1, CUERPO_1, "v1")
F2 = Fuente("2602.1", 2, CUERPO_2, "v2")


def test_anclar_ignora_espacios_y_rechaza_citas_inventadas():
    spans = calcular_spans("2601.1", "v1", CUERPO_1)
    span = anclar("reached an accuracy of 0.71 on the benchmark", CUERPO_1, spans)
    assert span is not None and span.span_id == "2601.1#s1.p1"
    assert anclar("reached an accuracy of 0.99 on the benchmark", CUERPO_1, spans) is None
    assert anclar("0.71", CUERPO_1, spans) is None  # demasiado corta para anclar


def test_mensajes_marcan_el_paper_como_datos():
    mensajes = construir_mensajes([F1], {"T1": 2})
    assert "DATA" in mensajes[0]["content"]
    assert '<paper arxiv_id="2601.1"' in mensajes[1]["content"]
    assert "Write 2 T1" in mensajes[1]["content"]


def _salida(*preguntas):
    return "Here you go:\n" + json.dumps({"questions": list(preguntas)})


def test_interpretar_acepta_solo_evidencia_literal_y_marca_borrador():
    buena = {
        "type": "T1",
        "question": "What accuracy did the compiled wiki reach?",
        "answer": "0.71",
        "answer_keys": ["0.71"],
        "evidence": [{"arxiv_id": "2601.1", "evidence_quote": "accuracy of 0.71 on the benchmark"}],
    }
    inventada = {
        **buena,
        "evidence": [{"arxiv_id": "2601.1", "evidence_quote": "accuracy of 0.93 overall"}],
    }
    sin_claves = {**buena, "answer_keys": []}
    tipo_raro = {**buena, "type": "T3"}
    preguntas, citas, descartes = interpretar(
        _salida(buena, inventada, sin_claves, tipo_raro), {"T1"}, [F1], "A", "redactor-x", "A001"
    )
    assert len(preguntas) == 1
    p = preguntas[0]
    assert p["estado_verificacion"] == "borrador"
    assert p["redactado_por"] == "redactor-x"
    assert p["evidencia"][0]["span_id"] == "2601.1#s1.p1"
    assert p["ingesta_minima"] == 1
    assert citas[0]["question_id"] == p["id"]
    assert len(descartes) == 3
    assert any("no aparece literal" in d for d in descartes)
    assert validar_banco(preguntas, {"2601.1": 1}) == []


def test_t4_queda_con_respuesta_por_paso_valida():
    t4 = {
        "type": "T4",
        "question": "What is the best reported wiki accuracy?",
        "answer": "0.80",
        "answer_before": "0.71",
        "answer_keys": ["0.80"],
        "evidence": [
            {"arxiv_id": "2601.1", "evidence_quote": "accuracy of 0.71 on the benchmark"},
            {"arxiv_id": "2602.1", "evidence_quote": "the wiki accuracy rises to 0.80"},
        ],
    }
    una_fuente = {**t4, "evidence": t4["evidence"][:1]}
    preguntas, _, descartes = interpretar(
        _salida(t4, una_fuente), {"T4"}, [F1, F2], "B", "r", "B001"
    )
    assert len(preguntas) == 1 and len(descartes) == 1
    p = preguntas[0]
    assert p["ingesta_minima"] == 1
    assert p["respuesta_por_paso"][0]["desde"] == 2
    assert validar_banco(preguntas, {"2601.1": 1, "2602.1": 2}) == []


MANIFEST = [
    {
        "arxiv_id": "2601.1",
        "orden_ingesta": 1,
        "mitad": "A",
        "en_gold": True,
        "tokens": 100,
        "referencias_en_corpus": [],
    },
    {
        "arxiv_id": "2602.1",
        "orden_ingesta": 2,
        "mitad": "B",
        "en_gold": True,
        "tokens": 200,
        "referencias_en_corpus": ["2601.1"],
    },
    {
        "arxiv_id": "2603.1",
        "orden_ingesta": 3,
        "mitad": "A",
        "en_gold": True,
        "tokens": 50,
        "referencias_en_corpus": ["2602.1"],
    },
]


def test_planear_asigna_pares_al_autor_del_paper_posterior_y_estima_tokens():
    plan_a = planear(MANIFEST, "A")
    assert [t.etiqueta for t in plan_a.tareas] == ["T1:2601.1", "T1:2603.1", "par:2602.1>2603.1"]
    plan_b = planear(MANIFEST, "B")
    assert [t.etiqueta for t in plan_b.tareas] == ["T1:2602.1", "par:2601.1>2602.1"]
    assert plan_a.tareas[2].tokens_entrada == 250 + 700
    assert plan_a.costo(1.0, 0.0) == plan_a.tokens_entrada / 1e6


@dataclass
class _Resp:
    texto: str
    usd: float = 0.0


def test_ejecutar_y_hoja_de_anotacion(tmp_path):
    escribir_gold(tmp_path / "2601.1.md", {"arxiv_id": "2601.1", "version": "v1"}, CUERPO_1)
    salida = _salida(
        {
            "type": "T1",
            "question": "q?",
            "answer": "0.71",
            "answer_keys": ["0.71"],
            "evidence": [
                {"arxiv_id": "2601.1", "evidence_quote": "accuracy of 0.71 on the benchmark"}
            ],
        }
    )

    class _Cliente:
        def generar(self, mensajes, etiqueta):
            return _Resp(salida)

    plan = planear(MANIFEST[:1], "A")
    preguntas, citas, _ = ejecutar(plan, MANIFEST[:1], tmp_path, _Cliente(), "r", lambda _m: None)
    hoja = tmp_path / "hoja.csv"
    escribir_hoja(hoja, preguntas, citas)
    filas = list(csv.DictReader(hoja.open(encoding="utf-8")))
    assert filas[0]["decision"] == ""
    assert "accuracy of 0.71" in filas[0]["cita_literal"]


def test_ejecutar_conserva_lo_redactado_si_se_alcanza_el_tope(tmp_path):
    from wikillm.common.modelo import TopeDeGastoError

    escribir_gold(tmp_path / "2601.1.md", {"arxiv_id": "2601.1", "version": "v1"}, CUERPO_1)
    escribir_gold(tmp_path / "2603.1.md", {"arxiv_id": "2603.1", "version": "v1"}, CUERPO_1)
    buena = _salida(
        {
            "type": "T1",
            "question": "q?",
            "answer": "0.71",
            "answer_keys": ["0.71"],
            "evidence": [
                {"arxiv_id": "2601.1", "evidence_quote": "accuracy of 0.71 on the benchmark"}
            ],
        }
    )

    class _Cliente:
        llamadas = 0

        def generar(self, mensajes, etiqueta):
            self.llamadas += 1
            if self.llamadas > 1:
                raise TopeDeGastoError("tope")
            return _Resp(buena)

    manifest = [MANIFEST[0], {**MANIFEST[2], "referencias_en_corpus": []}]
    plan = planear(manifest, "A")
    preguntas, _, descartes = ejecutar(plan, manifest, tmp_path, _Cliente(), "r", lambda _m: None)
    assert len(preguntas) == 1
    assert any("detenida" in d for d in descartes)
