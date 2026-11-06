import json

from wikillm.eval.banco import esperado_en_paso, validar_banco
from wikillm.eval.correctitud import CORRECTA, INCORRECTA, evaluar
from wikillm.eval.t5 import construir_mensajes, elegir_externos, interpretar

EXTERNOS = [
    {
        "arxiv_id": "2609.9",
        "titulo": "LazyMem: Construct Memory Selectively",
        "resumen": "LazyMem cuts memory construction cost by 63% on LongMemEval.",
        "fecha_publicacion": "2026-09-01",
    },
    {
        "arxiv_id": "2609.8",
        "titulo": "HippoRAG Reloaded memory",
        "resumen": "We extend HippoRAG with a new index that reaches 71% recall.",
        "fecha_publicacion": "2026-09-02",
    },
]
CORPUS = ["# Paper\n\nHippoRAG builds a knowledge graph over passages."]


def _salida(*preguntas):
    return json.dumps({"questions": list(preguntas)})


def test_t5_acepta_solo_cita_literal_y_termino_ausente_del_corpus():
    buena = {
        "arxiv_id": "2609.9",
        "question": "By how much does LazyMem cut memory construction cost?",
        "distinctive_term": "LazyMem",
        "evidence_quote": "LazyMem cuts memory construction cost by 63% on LongMemEval.",
    }
    en_corpus = {
        **buena,
        "arxiv_id": "2609.8",
        "distinctive_term": "HippoRAG",
        "evidence_quote": "reaches 71% recall",
    }
    inventada = {**buena, "evidence_quote": "LazyMem cuts cost by 90%."}
    preguntas, citas, descartes = interpretar(
        _salida(buena, en_corpus, inventada), EXTERNOS, CORPUS, "A", "r", "AT5"
    )
    assert [p["id"] for p in preguntas] == ["AT5-T5-01"]
    p = preguntas[0]
    assert p["tipo"] == "T5" and p["estado_verificacion"] == "borrador"
    assert p["fuentes_requeridas"] == [] and p["ingesta_minima"] is None
    assert p["fuente_externa"]["arxiv_id"] == "2609.9"
    assert citas[0]["span_id"] == "externo:2609.9"
    assert any("aparece en el corpus" in d for d in descartes)
    assert any("no aparece literal" in d for d in descartes)
    assert validar_banco(preguntas, {}) == []


def test_t5_abstenerse_es_correcto_en_cualquier_paso():
    preguntas, _, _ = interpretar(
        _salida(
            {
                "arxiv_id": "2609.9",
                "question": "q LazyMem?",
                "distinctive_term": "LazyMem",
                "evidence_quote": "cuts memory construction cost by 63%",
            }
        ),
        EXTERNOS,
        CORPUS,
        "A",
        "r",
        "AT5",
    )
    for paso in (1, 30, 50):
        esperado = esperado_en_paso(preguntas[0], paso)
        assert evaluar(esperado, "No consta.", True) == CORRECTA
        assert evaluar(esperado, "63%", False) == INCORRECTA


def test_elegir_externos_excluye_corpus_y_es_reproducible():
    candidatos = EXTERNOS + [{**EXTERNOS[0], "arxiv_id": "2605.1"}]
    a = elegir_externos(candidatos, {"2605.1"}, 5, semilla=0)
    assert {c["arxiv_id"] for c in a} == {"2609.9", "2609.8"}
    assert a == elegir_externos(candidatos, {"2605.1"}, 5, semilla=0)
    mensajes = construir_mensajes(a, 2)
    assert "DATA" in mensajes[0]["content"] and "<abstract" in mensajes[1]["content"]
