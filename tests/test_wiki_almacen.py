"""El wiki en disco, con una carpeta temporal y Git real (sin red ni modelo)."""

import pytest

from wikillm.wiki.almacen import ErrorDeAlmacen, Pagina, Wiki, slug_de


def pagina(slug="hipporag", tipo="paper", **cambios):
    base = {
        "slug": slug,
        "titulo": "HippoRAG",
        "tipo": tipo,
        "resumen": "Memoria a largo plazo con un grafo.",
        "fuentes": ["2405.14831"],
        "actualizada_en_paso": 1,
        "cuerpo": "- Umbral de sinonimia 0.8 [2405.14831#s11.p1]",
    }
    return Pagina(**{**base, **cambios})


def test_un_wiki_nuevo_tiene_indice_registro_y_repositorio_sin_paginas(tmp_path):
    wiki = Wiki(tmp_path / "w")
    assert (wiki.carpeta / "index.md").exists() and (wiki.carpeta / "log.md").exists()
    assert (wiki.carpeta / "pages").is_dir() and (wiki.carpeta / ".git").is_dir()
    assert wiki.slugs() == [] and wiki.ingeridos == [] and wiki.paso == 0


def test_escribir_y_leer_una_pagina_da_los_mismos_campos(tmp_path):
    wiki = Wiki(tmp_path / "w")
    original = pagina(fuentes=["2405.14831", "2502.14802"], resumen="Con: dos puntos y áccéntos.")
    wiki.escribir(original)
    leida = wiki.leer("hipporag")
    assert leida == original
    assert wiki.existe("hipporag") and not wiki.existe("otra")


def test_un_nombre_o_un_tipo_invalido_se_rechaza(tmp_path):
    with pytest.raises(ErrorDeAlmacen, match="no válido"):
        pagina(slug="../fuera")
    with pytest.raises(ErrorDeAlmacen, match="Tipo"):
        pagina(tipo="otro")
    with pytest.raises(ErrorDeAlmacen, match="No existe"):
        Wiki(tmp_path / "w").leer("../fuera")


def test_el_indice_lista_todas_las_paginas_por_tipo_con_su_resumen(tmp_path):
    wiki = Wiki(tmp_path / "w")
    wiki.escribir(pagina())
    wiki.escribir(
        pagina(slug="recuperacion", tipo="concepto", titulo="Recuperación", resumen="Temas")
    )
    wiki.marcar_ingerido("2405.14831")
    wiki.regenerar_indice()
    indice = wiki.texto_del_indice()
    assert "Papers ingested: 1. Pages: 2." in indice
    assert "## Papers" in indice and "## Concepts" in indice
    assert "- [[hipporag]] **HippoRAG**: Memoria a largo plazo con un grafo." in indice
    assert "- [[recuperacion]] **Recuperación**: Temas" in indice


def test_el_indice_de_un_wiki_vacio_dice_que_no_hay_paginas(tmp_path):
    wiki = Wiki(tmp_path / "w")
    wiki.regenerar_indice()
    assert "no pages yet" in wiki.texto_del_indice()


def test_anotar_agrega_entradas_al_registro_sin_borrar_las_anteriores(tmp_path):
    wiki = Wiki(tmp_path / "w")
    wiki.anotar("## Step 1")
    wiki.anotar("## Step 2")
    registro = (wiki.carpeta / "log.md").read_text(encoding="utf-8")
    assert registro.index("## Step 1") < registro.index("## Step 2")


def test_guardar_copia_hace_un_commit_con_etiqueta_por_paso(tmp_path):
    wiki = Wiki(tmp_path / "w")
    wiki.escribir(pagina())
    primero = wiki.guardar_copia(1, "ingest 1")
    wiki.escribir(pagina(cuerpo="- Otro dato [2405.14831#s2.p1]", actualizada_en_paso=2))
    segundo = wiki.guardar_copia(2, "ingest 2")
    assert primero != segundo and len(primero) == 40
    assert wiki.etiquetas() == ["paso-1", "paso-2"]
    # la etiqueta paso-1 recuerda el contenido de ese momento
    antiguo = wiki._git("show", "paso-1:pages/hipporag.md")
    assert "Umbral de sinonimia" in antiguo and "Otro dato" not in antiguo


def test_lo_ingerido_persiste_entre_instancias_y_no_se_repite(tmp_path):
    Wiki(tmp_path / "w").marcar_ingerido("2405.14831")
    otra = Wiki(tmp_path / "w")
    otra.marcar_ingerido("2405.14831")
    otra.marcar_ingerido("2502.14802")
    assert otra.ingeridos == ["2405.14831", "2502.14802"] and otra.paso == 2


def test_slug_de_un_titulo_es_seguro_y_legible():
    assert slug_de("HippoRAG 2: From RAG to Memory") == "hipporag-2-from-rag-to-memory"
    assert slug_de("Recuperación & Memoria") == "recuperacion-memoria"
    assert slug_de("¿¿??") == "pagina"
