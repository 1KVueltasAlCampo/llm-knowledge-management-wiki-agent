"""Lectura de un paper con rótulos de fragmento, con un Gold sintético."""

import re

import pytest
import yaml

from wikillm.corpus.spans import calcular_spans
from wikillm.wiki.lectura import leer_paper, rotular

CUERPO = """# Título del paper

## 1 Introducción

Primer párrafo con una cifra de 0.8.

Segundo párrafo.

| a | b |
|---|---|
| 1 | 2 |

## 2 Resultados

Último párrafo.
"""


def test_cada_fragmento_lleva_su_rotulo_y_los_encabezados_no():
    texto, ids = rotular(CUERPO, "2401.00001", "v1")
    esperados = [s.span_id for s in calcular_spans("2401.00001", "v1", CUERPO)]
    assert len(esperados) == 4 and ids == frozenset(esperados)
    assert "[2401.00001#s1.p1] Primer párrafo con una cifra de 0.8." in texto
    assert "[2401.00001#s1.p3] | a | b |" in texto
    assert "[2401.00001#s2.p1] Último párrafo." in texto
    assert "\n## 1 Introducción\n" in texto and "[2401.00001#s1.p1] ## " not in texto


def test_quitando_los_rotulos_se_recupera_el_texto_original():
    texto, _ = rotular(CUERPO, "2401.00001", "v1")
    assert re.sub(r"\[2401\.00001#s\d+\.p\d+\] ", "", texto) == CUERPO


def test_los_rotulos_coinciden_con_los_de_spans_jsonl(tmp_path):
    encabezado = yaml.safe_dump(
        {"arxiv_id": "2401.00001", "titulo": "Un paper", "version": "v2"}, sort_keys=False
    )
    (tmp_path / "2401.00001.md").write_text(f"---\n{encabezado}---\n\n{CUERPO}", encoding="utf-8")
    paper = leer_paper("2401.00001", tmp_path)
    assert (paper.arxiv_id, paper.titulo, paper.version) == ("2401.00001", "Un paper", "v2")
    assert all(f"[{span_id}]" in paper.texto for span_id in paper.span_ids)


def test_un_paper_sin_gold_pide_ejecutar_la_ingesta(tmp_path):
    with pytest.raises(FileNotFoundError, match="wikillm.ingest"):
        leer_paper("1111.11111", tmp_path)
