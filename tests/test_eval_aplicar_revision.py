import pytest

from wikillm.eval.aplicar_revision import AjusteInvalido, aplicar
from wikillm.eval.banco import validar_banco

ORDEN = {"2601.1": 1, "2605.1": 5}
SPANS = {
    "2601.1#s1.p1": {"sha256": "a"},
    "2601.1#s2.p1": {"sha256": "b"},
    "2605.1#s1.p1": {"sha256": "c"},
}


def _p(pid, tipo="T1", fuentes=("2601.1",), **extra):
    return {
        "id": pid,
        "texto": f"pregunta {pid}",
        "tipo": tipo,
        "respuesta_oraculo": "0.71",
        "respuesta_clave": ["0.71"],
        "evidencia": [{"span_id": f"{f}#s1.p1", "sha256": "x"} for f in fuentes],
        "fuentes_requeridas": list(fuentes),
        "ingesta_minima": max(ORDEN[f] for f in fuentes),
        "autor": "A",
        "estado_verificacion": "borrador",
        **extra,
    }


BORRADORES = [_p("q1"), _p("q2"), _p("q3"), _p("q4", "T2", ("2601.1", "2605.1"))]
REVISION = [
    {"question_id": "q1", "decision": "aceptar", "elegida": True, "notas": "ok"},
    {"question_id": "q2", "decision": "descartar", "elegida": True, "notas": ""},
    {
        "question_id": "q3",
        "decision": "corregir",
        "elegida": True,
        "respuesta_corregida": "0.80",
        "claves_corregidas": "0.80",
        "notas": "",
    },
    {"question_id": "q4", "decision": "", "elegida": False, "notas": ""},
]


def test_solo_entran_las_elegidas_no_descartadas_con_estado_y_procedencia():
    ajustes = {"autor": "A", "revisor": "JD", "fecha": "2026-11-06", "ajustes": []}
    banco = aplicar(BORRADORES, REVISION, ajustes, ORDEN, SPANS)
    assert [p["id"] for p in banco] == ["q1", "q3"]
    assert all(p["estado_verificacion"] == "verificado_a" for p in banco)
    assert banco[1]["respuesta_oraculo"] == "0.80" and banco[1]["respuesta_clave"] == ["0.80"]
    assert banco[0]["revision"]["verificado_por"] == "JD"
    assert banco[0]["revision"]["notas_revisor"] == "ok"
    assert BORRADORES[2]["respuesta_oraculo"] == "0.71"  # no muta los borradores


def test_ajustes_descartan_agregan_y_convierten_en_t4():
    ajustes = {
        "autor": "A",
        "revisor": "JD",
        "fecha": "f",
        "ajustes": [
            {"question_id": "q1", "accion": "descartar", "motivo": "m"},
            {
                "question_id": "q4",
                "accion": "agregar",
                "pregunta": "¿Qué valor se reportó más recientemente?",
                "respuesta_antes": "0.71",
                "claves_antes": ["0.71"],
                "respuesta_despues": "0.80",
                "claves_despues": ["0.80"],
                "evidencia_reemplazar": {"2601.1#s1.p1": "2601.1#s2.p1"},
                "motivo": "nueva T4",
            },
        ],
    }
    banco = aplicar(BORRADORES, REVISION, ajustes, ORDEN, SPANS)
    assert [p["id"] for p in banco] == ["q3", "q4"]
    t4 = banco[1]
    assert t4["tipo"] == "T4" and t4["ingesta_minima"] == 1
    assert t4["respuesta_por_paso"][0]["desde"] == 5
    assert t4["evidencia"][0] == {"span_id": "2601.1#s2.p1", "sha256": "b"}
    assert t4["revision"]["ajuste"] == "nueva T4"
    assert validar_banco(banco, ORDEN) == []


def test_ajuste_con_fragmento_o_pregunta_inexistente_falla():
    malo = {
        "autor": "A",
        "revisor": "",
        "fecha": "",
        "ajustes": [
            {"question_id": "q1", "accion": "corregir", "evidencia_agregar": ["nada#s9.p9"]}
        ],
    }
    with pytest.raises(AjusteInvalido):
        aplicar(BORRADORES, REVISION, malo, ORDEN, SPANS)
    otro = {
        "autor": "A",
        "revisor": "",
        "fecha": "",
        "ajustes": [{"question_id": "zz", "accion": "descartar"}],
    }
    with pytest.raises(AjusteInvalido):
        aplicar(BORRADORES, REVISION, otro, ORDEN, SPANS)
