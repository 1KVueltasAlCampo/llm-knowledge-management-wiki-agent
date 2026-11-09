"""Lectura de resultados guardados para el panel: wiki, ingesta, comparación y piloto."""

import json

from test_arnes_comparar import CITA, FRAGMENTO, RECUPERADOS, TRAZA, preparar_gold
from wikillm.arnes.comparar import crear_resolutor
from wikillm.panel import datos

REGISTRO = (
    "# Registro\n\n## Step 1: 2401.00001 — Uno\n- Created: a\n- Updated: (none)\n"
    "- Citations removed: 0\n- Broken links: 0\n- Uncited numeric lines: 0\n\n"
    "## Step 2: 2401.00002 — Dos: con dos puntos\n- Created: (none)\n- Updated: p1, p2\n"
    "- Citations removed: 4\n- Broken links: x\n- Uncited numeric lines: 7\n"
)


def escribir(ruta, texto):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(texto, encoding="utf-8")


def test_el_estado_del_wiki_cuenta_papers_y_paginas(tmp_path):
    escribir(tmp_path / "w" / "estado.json", json.dumps({"ingeridos": ["a", "b"]}))
    escribir(tmp_path / "w" / "pages" / "x.md", "x")
    escribir(tmp_path / "w" / "pages" / "y.md", "y")
    assert datos.estado_del_wiki(tmp_path, "w") == {
        "carpeta": "w",
        "existe": True,
        "ingeridos": 2,
        "ids": ["a", "b"],
        "paginas": 2,
    }


def test_un_wiki_inexistente_se_describe_vacio(tmp_path):
    assert datos.estado_del_wiki(tmp_path, "no/hay") == {
        "carpeta": "no/hay",
        "existe": False,
        "ingeridos": 0,
        "ids": [],
        "paginas": 0,
    }


def test_la_ultima_ingesta_sale_de_la_ultima_entrada_del_registro(tmp_path):
    escribir(tmp_path / "w" / "log.md", REGISTRO)
    assert datos.ultima_ingesta(tmp_path, "w") == {
        "paso": 2,
        "arxiv_id": "2401.00002",
        "titulo": "Dos: con dos puntos",
        "creadas": [],  # "(none)" no es una página
        "actualizadas": ["p1", "p2"],
        "citas_eliminadas": 4,
        "enlaces_rotos": 0,  # un valor que no es número cuenta como 0
        "lineas_sin_cita": 7,
    }


def test_sin_registro_o_sin_entradas_no_hay_ultima_ingesta(tmp_path):
    assert datos.ultima_ingesta(tmp_path, "w") is None
    escribir(tmp_path / "w" / "log.md", "# Registro\n\nNada todavía.\n")
    assert datos.ultima_ingesta(tmp_path, "w") is None


def linea_de_comparacion():
    return {
        "timestamp": "2026-11-09T23:00:00Z",
        "modelo": "deepseek-flash",
        "pregunta": "q?",
        "paso": 2,
        "sistemas": [
            {
                "sistema": "rag",
                "respuesta": "It is 0.8.",
                "abstuvo": False,
                "citas": [CITA],
                "llamadas": 1,
                "tokens_entrada": 100,
                "tokens_contexto": 80,
                "tokens_salida": 10,
                "segundos": 1.5,
                "usd": 0.0001,
                "traza": None,
                "recuperados": RECUPERADOS,
            },
            {
                "sistema": "wiki",
                "respuesta": "No sé.",
                "abstuvo": True,
                "citas": [],
                "llamadas": 3,
                "tokens_entrada": 900,
                "tokens_contexto": 500,
                "tokens_salida": 40,
                "segundos": 4.0,
                "usd": 0.0007,
                "traza": TRAZA,
            },
        ],
    }


def test_la_comparacion_trae_cada_cita_con_su_fragmento_y_marca_lo_citado(tmp_path):
    carpeta, spans = preparar_gold(tmp_path)
    escribir(tmp_path / datos.EVIDENCIA, json.dumps({"pregunta": "anterior"}) + "\n")
    with (tmp_path / datos.EVIDENCIA).open("a", encoding="utf-8") as f:
        f.write(json.dumps(linea_de_comparacion()) + "\n")
    r = datos.resultado_de_comparacion(tmp_path, crear_resolutor(carpeta, spans))
    assert (r["pregunta"], r["paso"], r["momento"]) == ("q?", 2, "2026-11-09T23:00:00Z")
    rag, wiki = r["sistemas"]
    assert rag["citas"] == [{"span_id": CITA, "texto": FRAGMENTO}]
    assert [x["citado"] for x in rag["recuperados"]] == [True, False]
    assert rag["recuperados"][1]["texto"] is None
    assert wiki["abstuvo"] is True and wiki["citas"] == [] and wiki["recuperados"] is None
    assert wiki["traza"] == TRAZA and wiki["nombre"] == "WikiLLM"


def test_un_fragmento_largo_se_recorta_en_la_vista(tmp_path):
    largo = {"span_id": CITA}
    resolutor = lambda _: "palabra " * 200  # noqa: E731
    texto = datos._fragmento(resolutor, largo["span_id"], 50)
    assert len(texto) == 50 and texto.endswith("…")


def test_sin_evidencia_no_hay_comparacion(tmp_path):
    assert datos.resultado_de_comparacion(tmp_path, lambda _: None) is None


def test_las_metricas_unen_veredictos_con_el_texto_de_cada_pregunta(tmp_path):
    base = tmp_path / datos.PILOTO
    escribir(base / "metricas_por_paso.json", json.dumps([{"system": "rag", "ingest_step": 0}]))
    escribir(
        base / "corrida.json",
        json.dumps({"corrida": "piloto-1", "modelo": "m", "banco": {"preguntas": ["Q1", "Q2"]}}),
    )
    escribir(
        base / "evaluados.jsonl",
        json.dumps(
            {
                "question_id": "Q1",
                "system": "wiki",
                "ingest_step": 5,
                "tipo": "T1",
                "respondible": True,
                "veredicto": "correcta",
                "abstained": False,
                "answer": "0.8",
                "citations": ["a", "b"],
                "cost_usd": 0.0004,
                "latency_s": 2.3456,
            }
        )
        + "\n",
    )
    escribir(tmp_path / datos.BANCO, json.dumps({"id": "Q1", "texto": "¿Cuánto?"}) + "\n")
    r = datos.leer_metricas(tmp_path)
    assert r["filas"] == [{"system": "rag", "ingest_step": 0}]
    assert r["corrida"]["corrida"] == "piloto-1" and r["corrida"]["preguntas"] == 2
    [p] = r["preguntas"]
    assert p["texto"] == "¿Cuánto?" and p["veredicto"] == "correcta" and p["citas"] == 2
    assert p["segundos"] == 2.35 and p["sistema"] == "wiki" and p["paso"] == 5


def test_sin_piloto_las_metricas_vienen_vacias(tmp_path):
    r = datos.leer_metricas(tmp_path)
    assert r["filas"] == [] and r["preguntas"] == [] and r["corrida"]["preguntas"] == 0
