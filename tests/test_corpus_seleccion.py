import pytest

from wikillm.corpus.seleccion import seleccionar


def _c(fecha, bib=True):
    return {"fecha_publicacion": fecha, "origen": ["bib"] if bib else ["busqueda:x"]}


CANDIDATOS = {
    "2405.1": _c("2024-05-01"),
    "2512.1": _c("2025-12-01"),
    "2601.1": _c("2026-01-02"),
    "2602.1": _c("2026-02-01"),
    "2603.1": _c("2026-03-01", bib=False),
    "2604.1": _c("2026-04-01", bib=False),
    "2605.1": _c("2026-05-01", bib=False),
}


def test_seleccion_semillas_bib_y_relleno_por_enlaces():
    # 2605.1 cita a 2601.1 y a 2603.1 (2 enlaces); 2603.1 recibe 1; 2604.1 no tiene enlaces
    referencias = {"2605.1": ["2601.1", "2603.1", "2602.1"]}
    elegidos, reservas = seleccionar(
        CANDIDATOS,
        semillas=["2405.1"],
        preseleccion=["2604.1", "2603.1", "2605.1"],
        referencias=referencias,
        tiene_html=lambda i: i != "2602.1",
        n=4,
    )
    # 2512.1 es anterior al corte y no es semilla; 2602.1 no tiene HTML
    assert elegidos == ["2405.1", "2601.1", "2605.1", "2603.1"]
    assert reservas == ["2604.1"]


def test_seleccion_falla_si_los_obligatorios_superan_n():
    with pytest.raises(ValueError):
        seleccionar(CANDIDATOS, ["2405.1"], [], {}, lambda _i: True, n=1)
