"""Fragmentación a partir de spans con un medidor falso (palabras): sin modelos ni red."""

import pytest
import yaml

from wikillm.rag.fragmentos import dividir_paper, fragmentos_de_gold


def palabras(texto: str) -> int:
    return len(texto.split())


def parrafo(n: int, marca: str = "x") -> str:
    return " ".join(f"{marca}{i}" for i in range(n))


def cuerpo(*secciones: tuple[str, list[str]]) -> str:
    partes = ["# Título del paper\n"]
    for nombre, parrafos in secciones:
        partes.append(f"## {nombre}\n")
        partes += [f"{p}\n" for p in parrafos]
    return "\n".join(partes)


def dividir(texto, **kwargs):
    kwargs.setdefault("max_tokens", 60)
    kwargs.setdefault("solapamiento", 5)
    return dividir_paper("2401.00001", "Paper", "v1", texto, medir=palabras, **kwargs)


def test_spans_cortos_de_una_seccion_van_juntos_y_rotulados():
    fragmentos = dividir(cuerpo(("1 Intro", ["Primer párrafo.", "Segundo párrafo.", "Tercero."])))
    assert len(fragmentos) == 1
    f = fragmentos[0]
    assert f.span_ids == ("2401.00001#s1.p1", "2401.00001#s1.p2", "2401.00001#s1.p3")
    assert f.texto.startswith("Paper — 1 Intro\n\n")
    assert "[2401.00001#s1.p2] Segundo párrafo." in f.texto
    assert (f.arxiv_id, f.titulo, f.seccion, f.posicion, f.id) == (
        "2401.00001",
        "Paper",
        "1 Intro",
        0,
        "2401.00001-0",
    )


def test_una_seccion_larga_se_reparte_sin_repetir_spans():
    texto = cuerpo(("2 Método", [parrafo(20, f"p{i}_") for i in range(6)]))
    fragmentos = dividir(texto)
    assert len(fragmentos) > 1
    todos = [s for f in fragmentos for s in f.span_ids]
    assert sorted(todos) == sorted(set(todos))  # cada span, en un solo fragmento
    assert len(todos) == 6
    assert [f.posicion for f in fragmentos] == list(range(len(fragmentos)))


def test_los_spans_de_secciones_distintas_no_se_mezclan():
    fragmentos = dividir(cuerpo(("1 A", ["Uno."]), ("2 B", ["Dos."])))
    assert [f.seccion for f in fragmentos] == ["1 A", "2 B"]
    assert fragmentos[0].span_ids == ("2401.00001#s1.p1",)
    assert fragmentos[1].span_ids == ("2401.00001#s2.p1",)


def test_un_span_gigante_se_parte_y_conserva_su_span_id():
    fragmentos = dividir(cuerpo(("3 Anexo", [parrafo(300)])))
    assert len(fragmentos) > 5
    assert {s for f in fragmentos for s in f.span_ids} == {"2401.00001#s1.p1"}
    assert all(palabras(f.texto) <= 60 for f in fragmentos)
    assert all("[2401.00001#s1.p1]" in f.texto for f in fragmentos)


def test_ningun_fragmento_supera_el_maximo():
    texto = cuerpo(("1 A", [parrafo(33, f"q{i}_") for i in range(10)]), ("2 B", [parrafo(150)]))
    assert all(palabras(f.texto) <= 60 for f in dividir(texto))


def test_el_titulo_no_cuenta_como_span_ni_sale_en_el_texto_del_cuerpo():
    fragmentos = dividir(cuerpo(("1 A", ["Solo este párrafo."])))
    assert all("#s0" not in s for f in fragmentos for s in f.span_ids)


def test_un_titulo_que_no_deja_espacio_al_texto_falla():
    with pytest.raises(ValueError, match="no dejan espacio"):
        dividir_paper(
            "2401.00001",
            parrafo(70),
            "v1",
            cuerpo(("A", ["texto"])),
            medir=palabras,
            max_tokens=60,
        )


def test_fragmentos_de_gold_lee_el_encabezado(tmp_path):
    encabezado = yaml.safe_dump({"arxiv_id": "2502.00002", "titulo": "Segundo", "version": "v2"})
    ruta = tmp_path / "2502.00002.md"
    ruta.write_text(f"---\n{encabezado}---\n\n{cuerpo(('1 A', ['Texto B.']))}", encoding="utf-8")
    fragmentos = fragmentos_de_gold(ruta, medir=palabras, max_tokens=60, solapamiento=5)
    assert fragmentos[0].arxiv_id == "2502.00002"
    assert fragmentos[0].titulo == "Segundo"
    assert fragmentos[0].span_ids == ("2502.00002#s1.p1",)
