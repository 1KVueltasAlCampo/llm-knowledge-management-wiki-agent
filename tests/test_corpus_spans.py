import pytest

from wikillm.corpus.spans import SpanInvalido, calcular_spans, resolver, spans_de_carpeta
from wikillm.ingest.gold import escribir_gold

CUERPO = """# Título del paper

Resumen en un párrafo.

## 1 Introducción

Primer párrafo
en dos líneas.

Segundo párrafo.

## 2 Resultados

| a | b |
|---|---|
| 1 | 2 |

**Table 1: Resultados.**

*Figure 1: Un diagrama.*

$$x = 1$$

- uno
- dos
"""


def test_spans_por_bloque_con_seccion_tipo_y_posicion_exacta():
    spans = calcular_spans("2601.00001", "v2", CUERPO)
    ids = [s.span_id for s in spans]
    assert ids == [
        "2601.00001#s0.p1",
        "2601.00001#s1.p1",
        "2601.00001#s1.p2",
        "2601.00001#s2.p1",
        "2601.00001#s2.p2",
        "2601.00001#s2.p3",
        "2601.00001#s2.p4",
        "2601.00001#s2.p5",
    ]
    tipos = [s.tipo for s in spans]
    assert tipos == [
        "parrafo",
        "parrafo",
        "parrafo",
        "tabla",
        "pie_tabla",
        "pie_figura",
        "ecuacion",
        "lista",
    ]
    assert spans[1].seccion == "1 Introducción"
    assert CUERPO[spans[1].inicio : spans[1].fin] == "Primer párrafo\nen dos líneas."
    assert all(s.version == "v2" for s in spans)


def test_spans_son_deterministas():
    assert calcular_spans("x", "v1", CUERPO) == calcular_spans("x", "v1", CUERPO)


def test_resolver_devuelve_texto_y_detecta_cambios():
    span = calcular_spans("x", "v1", CUERPO)[2].como_dict()
    assert resolver(span, CUERPO) == "Segundo párrafo."
    with pytest.raises(SpanInvalido):
        resolver(span, CUERPO.replace("Segundo", "Tercer"))
    with pytest.raises(SpanInvalido):
        resolver({**span, "fin": len(CUERPO) + 10}, CUERPO)


def test_spans_de_carpeta_usa_el_cuerpo_que_devuelve_leer_gold(tmp_path):
    escribir_gold(tmp_path / "2601.00001.md", {"arxiv_id": "2601.00001", "version": "v3"}, CUERPO)
    filas = spans_de_carpeta(tmp_path, ["2601.00001", "9999.99999"])
    assert len(filas) == 8
    assert filas[0]["version"] == "v3"
    from wikillm.ingest.gold import leer_gold

    _, cuerpo = leer_gold(tmp_path / "2601.00001.md")
    assert all(resolver(f, cuerpo) for f in filas)
