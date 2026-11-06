from pathlib import Path

import pytest

from wikillm.ingest.gold import (
    CAMPOS_OBLIGATORIOS,
    Metadatos,
    aproximar_tokens,
    construir_encabezado,
    escribir_gold,
    escribir_manifiesto,
    leer_gold,
    parsear_abs,
    validar_gold,
    version_de_html,
)

ABS = """
<html><head>
<meta name="citation_title" content="Un título de prueba"/>
<meta name="citation_author" content="Ejemplo, Ada"/>
<meta name="citation_author" content="Prueba, Beto"/>
<meta name="citation_date" content="2026/05/18"/>
<meta name="citation_online_date" content="2026/10/02"/>
<meta name="citation_arxiv_id" content="2605.00001"/>
</head><body><span class="primary-subject">Computation and Language (cs.CL)</span></body></html>
"""
META = Metadatos("Un título de prueba", ["Ada Ejemplo"], "2026-05-18", "2026-10-02", "cs.CL")
CUERPO = "# Título\n\n" + "Texto de ejemplo para el cuerpo. " * 20 + "\n"


def encabezado_valido(arxiv_id="2605.00001", cuerpo=CUERPO):
    return construir_encabezado(
        arxiv_id,
        "v2",
        META,
        f"https://arxiv.org/html/{arxiv_id}",
        "2026-11-05T12:00:00+00:00",
        "ab" * 32,
        cuerpo,
        [],
    )


def escribir(carpeta: Path, arxiv_id="2605.00001", encabezado=None, cuerpo=CUERPO, nombre=None):
    escribir_gold(
        carpeta / (nombre or f"{arxiv_id}.md"), encabezado or encabezado_valido(arxiv_id), cuerpo
    )


def test_parsear_abs_extrae_los_metadatos():
    meta = parsear_abs(ABS)
    assert meta.titulo == "Un título de prueba"
    assert meta.autores == ["Ada Ejemplo", "Beto Prueba"]
    assert meta.fecha_publicacion == "2026-05-18"
    assert meta.fecha_version == "2026-10-02"
    assert meta.categoria == "cs.CL"


def test_parsear_abs_incompleto_falla():
    with pytest.raises(ValueError, match="metadatos"):
        parsear_abs("<html><head></head><body></body></html>")


def test_version_es_la_mayor_que_aparece_en_el_html():
    html = "x 2605.00001v1 y 2605.00001v3 z 2605.00001v2 y 2605.99999v9"
    assert version_de_html(html, "2605.00001") == "v3"
    assert version_de_html("sin versiones", "2605.00001") == "v1"


def test_encabezado_tiene_todos_los_campos_obligatorios():
    encabezado = encabezado_valido()
    assert all(campo in encabezado for campo in CAMPOS_OBLIGATORIOS)
    assert encabezado["estado_publicacion"] == "desconocido"
    assert encabezado["sources"] == ["https://arxiv.org/html/2605.00001"]
    assert encabezado["hash"].startswith("sha256:")
    assert encabezado["tokens"] == aproximar_tokens(CUERPO)


def test_escribir_y_leer_gold_dan_los_mismos_datos(tmp_path):
    encabezado = encabezado_valido()
    escribir_gold(tmp_path / "a.md", encabezado, CUERPO)
    leido, cuerpo = leer_gold(tmp_path / "a.md")
    assert leido == encabezado
    assert cuerpo == CUERPO
    assert (tmp_path / "a.md").read_text(encoding="utf-8").startswith("---\n")


def test_manifiesto_tiene_una_linea_por_paper(tmp_path):
    escribir_manifiesto(tmp_path, [{"arxiv_id": "a"}, {"arxiv_id": "b"}])
    lineas = (tmp_path / "corpus.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lineas) == 2


def test_un_gold_valido_no_tiene_problemas(tmp_path):
    escribir(tmp_path)
    assert validar_gold(tmp_path) == []


def test_html_dentro_de_codigo_o_matematicas_no_cuenta_como_residual(tmp_path):
    cuerpo = CUERPO + "Usa `sha256sum <archivo>` y la desigualdad $a<b>c$.\n"
    escribir(tmp_path, cuerpo=cuerpo, encabezado=encabezado_valido(cuerpo=cuerpo))
    assert validar_gold(tmp_path) == []


def test_marcadores_entre_angulos_del_paper_no_cuentan_como_html(tmp_path):
    cuerpo = (
        CUERPO
        + "Each command writes under results/<name>/run_*/ and replies FACT_NUMBER: <number or"
        " 0 if no fact matches>.\n"
    )
    escribir(tmp_path, cuerpo=cuerpo, encabezado=encabezado_valido(cuerpo=cuerpo))
    assert validar_gold(tmp_path) == []


def test_falta_un_campo_obligatorio(tmp_path):
    encabezado = encabezado_valido()
    del encabezado["sources"]
    escribir(tmp_path, encabezado=encabezado)
    assert any("sources" in p.motivo for p in validar_gold(tmp_path))


def test_identificador_repetido(tmp_path):
    escribir(tmp_path)
    escribir(tmp_path, encabezado=encabezado_valido(), nombre="otro.md")
    motivos = [p.motivo for p in validar_gold(tmp_path)]
    assert any("repetido" in m for m in motivos)


def test_cuerpo_vacio(tmp_path):
    escribir(tmp_path, cuerpo="\n", encabezado=encabezado_valido(cuerpo="\n"))
    assert any("vacío" in p.motivo for p in validar_gold(tmp_path))


def test_etiquetas_html_residuales(tmp_path):
    cuerpo = CUERPO + "Texto con <div class='x'>etiqueta</div> residual.\n"
    escribir(tmp_path, cuerpo=cuerpo, encabezado=encabezado_valido(cuerpo=cuerpo))
    assert any("HTML" in p.motivo for p in validar_gold(tmp_path))


def test_tokens_que_no_corresponden_al_cuerpo(tmp_path):
    encabezado = encabezado_valido()
    encabezado["tokens"] = 5
    escribir(tmp_path, encabezado=encabezado)
    assert any("tokens" in p.motivo for p in validar_gold(tmp_path))


def test_nombre_de_archivo_distinto_del_identificador(tmp_path):
    escribir(tmp_path, nombre="mal-nombre.md")
    assert any("nombre del archivo" in p.motivo for p in validar_gold(tmp_path))


def test_un_archivo_sin_encabezado_es_un_problema(tmp_path):
    (tmp_path / "x.md").write_text("solo cuerpo", encoding="utf-8")
    assert any("encabezado" in p.motivo for p in validar_gold(tmp_path))
