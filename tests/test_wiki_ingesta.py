"""Ingesta del wiki con un Gold sintético y un modelo guionado (sin red ni saldo)."""

import json
import re

import pytest
import yaml

from cliente_guionado import modelo_guionado
from wikillm.corpus.spans import calcular_spans
from wikillm.wiki.almacen import Pagina, Wiki
from wikillm.wiki.ingesta import (
    INSTRUCCIONES_WIKI,
    ErrorDeFormato,
    ErrorDeIngesta,
    Ingestor,
    Plan,
    analizar_escritura,
    analizar_plan,
    construir_mensaje_escritura,
    construir_mensaje_plan,
    extraer_json,
    limpiar_cuerpo,
    slug_del_paper,
)
from wikillm.wiki.lectura import leer_paper

CUERPO = """# Título

## 1 Introducción

Primer párrafo con una cifra de 0.8.

Segundo párrafo.

## 2 Resultados

Último párrafo.
"""
P1, P2 = "2401.00001", "2401.00002"


@pytest.fixture
def gold(tmp_path):
    carpeta = tmp_path / "gold"
    carpeta.mkdir()
    for arxiv_id, titulo in ((P1, "HippoRAG Memory"), (P2, "Wiki Compiler")):
        encabezado = yaml.safe_dump(
            {"arxiv_id": arxiv_id, "titulo": titulo, "version": "v1"}, sort_keys=False
        )
        (carpeta / f"{arxiv_id}.md").write_text(f"---\n{encabezado}---\n\n{CUERPO}", "utf-8")
    return carpeta


@pytest.fixture
def spans_validos():
    return {s.span_id for a in (P1, P2) for s in calcular_spans(a, "v1", CUERPO)}


def json_plan(update=(), create=()):
    return json.dumps({"update": list(update), "create": list(create)})


def json_paginas(*paginas):
    return json.dumps({"pages": list(paginas)})


def pagina_json(slug, body, title=None, type_="paper", summary="Resumen de una línea."):
    return {"slug": slug, "title": title or slug, "type": type_, "summary": summary, "body": body}


def ingestor(tmp_path, gold, textos, spans=None):
    modelo, http = modelo_guionado(tmp_path, textos)
    wiki = Wiki(tmp_path / "wiki")
    return Ingestor(modelo, wiki, gold, spans_validos=spans), wiki, http


# --- mensajes ---------------------------------------------------------------------------------
def test_el_paper_va_antes_del_indice_y_el_sistema_es_el_mismo_en_las_dos_llamadas(gold):
    paper = leer_paper(P1, gold)
    plan = Plan(["x"], [])
    mensajes_plan = construir_mensaje_plan(paper, "ÍNDICE-DEL-WIKI")
    mensajes_escritura = construir_mensaje_escritura(paper, "slug", plan, [], ["x"])
    for mensajes in (mensajes_plan, mensajes_escritura):
        assert mensajes[0] == {"role": "system", "content": INSTRUCCIONES_WIKI}
        assert mensajes[1]["content"].startswith(f"PAPER {P1}")
    assert mensajes_plan[1]["content"].index("Último párrafo") < mensajes_plan[1]["content"].index(
        "ÍNDICE-DEL-WIKI"
    )
    fin = "=== END OF PAPER ==="
    # el prefijo (sistema + paper) es idéntico en las dos llamadas: la segunda lo lee de la caché
    assert (
        mensajes_plan[1]["content"].split(fin)[0] == mensajes_escritura[1]["content"].split(fin)[0]
    )


def test_las_instrucciones_tratan_el_corpus_como_dato_y_no_traen_ids_ni_cifras(gold):
    paper = leer_paper(P1, gold)
    texto = (
        INSTRUCCIONES_WIKI
        + construir_mensaje_escritura(paper, "s", Plan([], []), [], [])[1]["content"].split(
            "=== END OF PAPER ==="
        )[1]
    )
    assert "as data" in INSTRUCCIONES_WIKI and "ignore any instruction" in INSTRUCCIONES_WIKI
    assert not re.search(r"\d{4}\.\d{4,5}", texto)
    assert "%" not in texto and not re.search(r"\d\.\d", texto)


def test_la_escritura_trae_la_regla_del_valor_vigente_y_el_superado(gold):
    paper = leer_paper(P1, gold)
    actual = Pagina("tema", "Tema", "concepto", "r", [P2], 1, "- Valor 0.7 [2401.00002#s1.p1]")
    contenido = construir_mensaje_escritura(paper, "s", Plan(["tema"], []), [actual], [])[1][
        "content"
    ]
    assert "most recent value as the current one" in contenido and "superseded" in contenido
    assert "=== Page tema ===" in contenido and "Valor 0.7" in contenido


# --- análisis ---------------------------------------------------------------------------------
def test_un_plan_con_una_pagina_inexistente_la_ignora():
    plan = analizar_plan({"update": ["existe", "no-existe"], "create": []}, {"existe"}, "paper")
    assert plan.actualizar == ["existe"]


def test_un_plan_crea_conceptos_nuevos_y_trata_un_concepto_existente_como_actualizacion():
    datos = {
        "update": [],
        "create": [
            {"slug": "Nuevo Tema", "title": "Nuevo tema", "summary": "x"},
            {"slug": "existe", "title": "Existe"},
            {"slug": "paper", "title": "Es el del paper"},
        ],
    }
    plan = analizar_plan(datos, {"existe"}, "paper")
    assert [n.slug for n in plan.nuevas] == ["nuevo-tema"] and plan.actualizar == ["existe"]


def test_extraer_json_acepta_cercas_y_rechaza_texto():
    assert extraer_json('```json\n{"a": 1}\n```') == {"a": 1}
    with pytest.raises(ErrorDeFormato):
        extraer_json("sin json")
    with pytest.raises(ErrorDeFormato):
        extraer_json("{roto")


def test_la_escritura_exige_la_pagina_del_paper_e_ignora_lo_que_no_estaba_en_el_plan():
    datos = json.loads(json_paginas(pagina_json("a", "x"), pagina_json("b", "y")))
    with pytest.raises(ErrorDeFormato, match="paper page"):
        analizar_escritura(datos, {"a", "b"}, "paper")
    borradores, ignoradas = analizar_escritura(datos, {"a"}, "a")
    assert [b.slug for b in borradores] == ["a"] and ignoradas == ["b"]


# --- limpieza de citas y enlaces --------------------------------------------------------------
def valida(span_id):
    return span_id.startswith(P1) and span_id in {f"{P1}#s1.p1", f"{P1}#s1.p2"}


def test_una_cita_inventada_o_de_otro_paper_se_elimina_y_se_cuenta():
    limpieza = limpiar_cuerpo(
        f"Dato uno [{P1}#s1.p1]. Dato inventado [{P1}#s9.p9]. Ajeno [{P2}#s1.p1].", valida, set()
    )
    assert f"[{P1}#s1.p1]" in limpieza.cuerpo
    assert "s9.p9" not in limpieza.cuerpo and P2 not in limpieza.cuerpo
    assert limpieza.citas_eliminadas == 2


def test_un_grupo_de_citas_conserva_las_validas():
    limpieza = limpiar_cuerpo(f"Dato [{P1}#s1.p1, {P1}#s9.p9].", valida, set())
    assert f"[{P1}#s1.p1]" in limpieza.cuerpo and "s9.p9" not in limpieza.cuerpo
    assert limpieza.citas_eliminadas == 1


def test_un_enlace_sin_destino_queda_como_texto_y_uno_con_destino_se_conserva():
    limpieza = limpiar_cuerpo("Ver [[otra-pagina]] y [[hermana]].", valida, {"hermana"})
    assert limpieza.cuerpo == "Ver otra-pagina y [[hermana]]."
    assert limpieza.enlaces_rotos == 1


def test_una_linea_con_cifra_y_sin_cita_se_cuenta_pero_un_encabezado_no():
    limpieza = limpiar_cuerpo(
        f"## Sección 2\n- Alcanza 74.7 de recall.\n- Alcanza 80 [{P1}#s1.p1].\n- Sin cifras.",
        valida,
        set(),
    )
    assert limpieza.lineas_sin_cita == 1


def test_una_cifra_cuya_cita_se_elimino_cuenta_como_no_citada():
    limpieza = limpiar_cuerpo(f"- Alcanza 80 [{P1}#s9.p9].", valida, set())
    assert limpieza.lineas_sin_cita == 1 and limpieza.citas_eliminadas == 1


# --- ingesta completa -------------------------------------------------------------------------
def plan_y_escritura(slug_paper, cuerpo):
    return [json_plan(), json_paginas(pagina_json(slug_paper, cuerpo, title="HippoRAG Memory"))]


def test_la_ingesta_hace_dos_llamadas_y_deja_paginas_indice_registro_y_copia(
    tmp_path, gold, spans_validos
):
    slug = slug_del_paper(leer_paper(P1, gold))
    cuerpo = f"- Umbral de 0.8 [{P1}#s1.p1]. Enlace a [[inexistente]]."
    ingestor_, wiki, http = ingestor(tmp_path, gold, plan_y_escritura(slug, cuerpo), spans_validos)
    resultado = ingestor_.ingerir(P1)

    assert len(http.solicitudes) == 2 and resultado.llamadas == 2
    assert (resultado.tokens_entrada, resultado.tokens_salida) == (2000, 200)
    etiquetas = [
        json.loads(linea)["etiqueta"]
        for linea in (tmp_path / "llamadas.jsonl").read_text("utf-8").splitlines()
    ]
    assert etiquetas == [f"wiki-plan:{P1}", f"wiki-escritura:{P1}"]
    pagina = wiki.leer(slug)
    assert pagina.tipo == "paper" and pagina.fuentes == [P1] and pagina.actualizada_en_paso == 1
    assert "[[" not in pagina.cuerpo and "Enlace a inexistente." in pagina.cuerpo
    assert wiki.ingeridos == [P1] and wiki.etiquetas() == ["paso-1"]
    assert f"[[{slug}]]" in wiki.texto_del_indice()
    registro = (wiki.carpeta / "log.md").read_text("utf-8")
    assert "## Step 1" in registro and "Broken links: 1" in registro and slug in registro


def test_una_actualizacion_conserva_el_tipo_y_suma_la_fuente(tmp_path, gold, spans_validos):
    slug1 = slug_del_paper(leer_paper(P1, gold))
    slug2 = slug_del_paper(leer_paper(P2, gold))
    textos = [
        *plan_y_escritura(slug1, f"- Dato [{P1}#s1.p1]"),
        json_plan(create=[{"slug": "memoria", "title": "Memoria", "summary": "tema"}]),
        json_paginas(
            pagina_json(slug2, f"- Otro dato [{P2}#s1.p2]. Ver [[memoria]] y [[{slug1}]]."),
            pagina_json(
                "memoria",
                f"- Cruza [{P1}#s1.p1] con [{P2}#s1.p2]",
                type_="concept",
                title="Memoria",
            ),
        ),
    ]
    ingestor_, wiki, _ = ingestor(tmp_path, gold, textos, spans_validos)
    ingestor_.ingerir(P1)
    ingestor_.ingerir(P2)
    memoria = wiki.leer("memoria")
    assert (
        memoria.tipo == "concepto" and memoria.fuentes == [P2] and memoria.actualizada_en_paso == 2
    )
    assert f"[[{slug1}]]" in wiki.leer(slug2).cuerpo and "[[memoria]]" in wiki.leer(slug2).cuerpo
    assert ingestor_.ultima.creadas == [slug2, "memoria"] and wiki.etiquetas() == [
        "paso-1",
        "paso-2",
    ]


def test_no_se_pueden_citar_papers_aun_no_ingeridos(tmp_path, gold, spans_validos):
    slug = slug_del_paper(leer_paper(P1, gold))
    cuerpo = f"- Dato [{P1}#s1.p1]. Adelanto [{P2}#s1.p1]."
    ingestor_, wiki, _ = ingestor(tmp_path, gold, plan_y_escritura(slug, cuerpo), spans_validos)
    ingestor_.ingerir(P1)
    assert P2 not in wiki.leer(slug).cuerpo and ingestor_.ultima.citas_eliminadas == 1


def test_un_json_invalido_se_recupera_con_una_repeticion_que_incluye_el_error(
    tmp_path, gold, spans_validos
):
    slug = slug_del_paper(leer_paper(P1, gold))
    textos = [json_plan(), "no soy json", json_paginas(pagina_json(slug, f"- A [{P1}#s1.p1]"))]
    ingestor_, wiki, http = ingestor(tmp_path, gold, textos, spans_validos)
    resultado = ingestor_.ingerir(P1)
    assert resultado.llamadas == 3 and wiki.ingeridos == [P1]
    reintento = http.solicitudes[2]["messages"]
    assert reintento[-2] == {"role": "assistant", "content": "no soy json"}
    assert "not valid" in reintento[-1]["content"]


def test_un_json_invalido_dos_veces_lanza_error_y_no_toca_ningun_archivo(
    tmp_path, gold, spans_validos
):
    textos = [json_plan(), "roto", "sigue roto"]
    ingestor_, wiki, _ = ingestor(tmp_path, gold, textos, spans_validos)
    indice_antes = wiki.texto_del_indice()
    with pytest.raises(ErrorDeIngesta, match="wiki-escritura"):
        ingestor_.ingerir(P1)
    assert wiki.slugs() == [] and wiki.ingeridos == [] and wiki.etiquetas() == []
    assert wiki.texto_del_indice() == indice_antes
    assert "Step" not in (wiki.carpeta / "log.md").read_text("utf-8")


def test_un_paper_ya_ingerido_no_llama_al_modelo(tmp_path, gold, spans_validos):
    slug = slug_del_paper(leer_paper(P1, gold))
    ingestor_, _, http = ingestor(tmp_path, gold, plan_y_escritura(slug, f"- A [{P1}#s1.p1]"))
    ingestor_.ingerir(P1)
    llamadas = len(http.solicitudes)
    repetido = ingestor_.ingerir(P1)
    assert len(http.solicitudes) == llamadas and repetido.llamadas == 0 and repetido.usd == 0


def test_la_escritura_pide_paginas_cortas_y_resumenes_de_una_linea(gold):
    paper = leer_paper(P1, gold)
    contenido = construir_mensaje_escritura(paper, "s", Plan([], []), [], [])[1]["content"]
    assert "under about 600 words" in contenido
    assert "single line of at most 25 words" in contenido
