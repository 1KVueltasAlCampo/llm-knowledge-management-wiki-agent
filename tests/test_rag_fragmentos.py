"""Fragmentación del Gold con un medidor falso (palabras): sin modelos ni red."""

import pytest
import yaml

from wikillm.rag.fragmentos import dividir_paper, leer_fragmentos


def palabras(texto: str) -> int:
    return len(texto.split())


def parrafo(n: int, marca: str = "x") -> str:
    return " ".join(f"{marca}{i}" for i in range(n))


def cuerpo(*secciones: tuple[str, str]) -> str:
    partes = ["# Título del paper\n"]
    partes += [f"## {nombre}\n\n{texto}\n" for nombre, texto in secciones]
    return "\n".join(partes)


def dividir(texto, **kwargs):
    kwargs.setdefault("max_tokens", 50)
    kwargs.setdefault("solapamiento", 5)
    return dividir_paper("2401.00001", "Paper", texto, medir=palabras, **kwargs)


def test_seccion_corta_es_un_fragmento_con_titulo_y_seccion():
    fragmentos = dividir(cuerpo(("1 Intro", "Texto corto de la introducción.")))
    assert len(fragmentos) == 1
    f = fragmentos[0]
    assert f.texto.startswith("Paper — 1 Intro\n\n")
    assert (f.arxiv_id, f.titulo, f.seccion, f.posicion) == ("2401.00001", "Paper", "1 Intro", 0)
    assert f.id == "2401.00001-0"


def test_la_seccion_larga_se_subdivide_y_conserva_sus_metadatos():
    texto = "\n\n".join(parrafo(20, f"p{i}_") for i in range(6))
    fragmentos = dividir(cuerpo(("2 Método", texto)))
    assert len(fragmentos) > 1
    assert {f.seccion for f in fragmentos} == {"2 Método"}
    assert [f.posicion for f in fragmentos] == list(range(len(fragmentos)))
    assert all(f.texto.startswith("Paper — 2 Método\n\n") for f in fragmentos)


def test_un_parrafo_gigante_se_parte_respetando_el_maximo():
    fragmentos = dividir(cuerpo(("3 Anexo", parrafo(300))))
    assert len(fragmentos) > 5
    assert all(palabras(f.texto) <= 50 for f in fragmentos)


def test_ningun_fragmento_supera_el_maximo():
    texto = "\n\n".join(parrafo(33, f"q{i}_") for i in range(10))
    fragmentos = dividir(cuerpo(("1 A", texto), ("2 B", parrafo(120))))
    assert all(palabras(f.texto) <= 50 for f in fragmentos)


def test_las_subsecciones_quedan_dentro_de_su_seccion():
    texto = "Intro de la sección.\n\n### 1.1 Detalle\n\nTexto del detalle."
    fragmentos = dividir(cuerpo(("1 Intro", texto)))
    assert len(fragmentos) == 1
    assert "### 1.1 Detalle" in fragmentos[0].texto


def test_se_descarta_lo_anterior_al_primer_encabezado_y_las_secciones_vacias():
    fragmentos = dividir(cuerpo(("Vacía", ""), ("Con texto", "Hola mundo.")))
    assert [f.seccion for f in fragmentos] == ["Con texto"]
    assert all("Título del paper" not in f.texto for f in fragmentos)


def test_un_titulo_que_no_deja_espacio_al_texto_falla():
    with pytest.raises(ValueError, match="no dejan espacio"):
        dividir_paper(
            "2401.00001", parrafo(60), cuerpo(("A", "texto")), medir=palabras, max_tokens=50
        )


def escribir_gold_minimo(carpeta, arxiv_id, titulo, texto):
    encabezado = yaml.safe_dump({"arxiv_id": arxiv_id, "titulo": titulo})
    (carpeta / f"{arxiv_id}.md").write_text(f"---\n{encabezado}---\n\n{texto}", encoding="utf-8")


def test_leer_fragmentos_recorre_todos_los_gold_en_orden(tmp_path):
    escribir_gold_minimo(tmp_path, "2502.00002", "Segundo", cuerpo(("1 A", "Texto B.")))
    escribir_gold_minimo(tmp_path, "2401.00001", "Primero", cuerpo(("1 A", "Texto A.")))
    (tmp_path / "corpus.jsonl").write_text("{}", encoding="utf-8")
    fragmentos = leer_fragmentos(tmp_path, medir=palabras, max_tokens=50, solapamiento=5)
    assert [f.arxiv_id for f in fragmentos] == ["2401.00001", "2502.00002"]
    assert fragmentos[1].titulo == "Segundo"
