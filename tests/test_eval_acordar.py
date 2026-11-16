"""Acuerdo entre autores sobre una mitad del banco y paso a «acordado»."""

import pytest

from wikillm.eval.acordar import acordar, decisiones, medir_acuerdo


def rev(*pares):
    return [{"question_id": q, "decision": d} for q, d in pares]


def banco():
    return [
        {"id": q, "estado_verificacion": "verificado_a", "revision": {"verificado_por": "x"}}
        for q in ("q1", "q2", "q3")
    ]


def test_solo_cuentan_las_decisiones_validas():
    r = rev(("q1", "aceptar"), ("q2", ""), ("q3", "descartar"))
    assert decisiones(r) == {"q1": "aceptar", "q3": "descartar"}


def test_el_acuerdo_compara_aceptar_con_ajustar_en_las_preguntas_decididas_por_ambos():
    a = rev(("q1", "aceptar"), ("q2", "corregir"), ("q3", "aceptar"))
    b = rev(("q1", "aceptar"), ("q2", "descartar"), ("q3", "corregir"))
    acuerdo, discrepan = medir_acuerdo(a, b, {"q1", "q2", "q3"})
    assert acuerdo.n == 3 and discrepan == ["q3"]  # corregir y descartar cuentan como ajustar
    assert acuerdo.porcentaje == pytest.approx(2 / 3)


def test_una_pregunta_sin_decision_de_algun_autor_no_entra_en_la_medida():
    a = rev(("q1", "aceptar"), ("q2", ""))
    b = rev(("q1", "aceptar"), ("q2", "aceptar"))
    acuerdo, _ = medir_acuerdo(a, b, {"q1", "q2"})
    assert acuerdo.n == 1


def test_acordar_deja_las_pendientes_como_estaban_y_anota_el_acuerdo():
    acuerdo, _ = medir_acuerdo(rev(("q1", "aceptar")), rev(("q1", "aceptar")), {"q1"})
    nuevo = acordar(banco(), pendientes=["q3"], fecha="2026-11-09", acuerdo=acuerdo)
    estados = {p["id"]: p["estado_verificacion"] for p in nuevo}
    assert estados == {"q1": "acordado", "q2": "acordado", "q3": "verificado_a"}
    assert nuevo[0]["revision"]["acordado"] == {
        "fecha": "2026-11-09",
        "porcentaje_acuerdo": 1.0,
        "kappa": None,
    }
    assert "acordado" not in nuevo[2]["revision"]


def test_acordar_no_modifica_el_banco_original_y_rechaza_pendientes_inexistentes():
    original = banco()
    acuerdo, _ = medir_acuerdo([], [], set())
    acordar(original, pendientes=[], fecha="2026-11-09", acuerdo=acuerdo)
    assert all(p["estado_verificacion"] == "verificado_a" for p in original)
    with pytest.raises(ValueError, match="q9"):
        acordar(original, pendientes=["q9"], fecha="2026-11-09", acuerdo=acuerdo)
