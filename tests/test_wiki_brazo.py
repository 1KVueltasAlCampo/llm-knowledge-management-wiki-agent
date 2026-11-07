"""Brazo WikiLLM y su orden de consola, con un Gold sintético y un modelo guionado."""

import json

import pytest
import yaml

from cliente_guionado import modelo_guionado
from test_responder import AJUSTES
from wikillm.common.responder import Brazo
from wikillm.wiki.__main__ import estimar_usd, principal
from wikillm.wiki.almacen import Wiki
from wikillm.wiki.brazo import BrazoWiki

CUERPO = "# Título\n\n## 1 Introducción\n\nPrimer párrafo con una cifra de 0.8.\n\nSegundo.\n"
P1, P2 = "2401.00001", "2401.00002"
SLUG1 = "hipporag-memory"
S1 = f"{P1}#s1.p1"


@pytest.fixture
def entorno(tmp_path):
    gold = tmp_path / "gold"
    gold.mkdir()
    for arxiv_id, titulo in ((P1, "HippoRAG Memory"), (P2, "Wiki Compiler")):
        encabezado = yaml.safe_dump(
            {"arxiv_id": arxiv_id, "titulo": titulo, "version": "v1"}, sort_keys=False
        )
        (gold / f"{arxiv_id}.md").write_text(f"---\n{encabezado}---\n\n{CUERPO}", "utf-8")
    filas = [
        {"arxiv_id": P2, "orden_ingesta": 2, "tokens": 20_000},
        {"arxiv_id": P1, "orden_ingesta": 1, "tokens": 10_000},
    ]
    manifest = tmp_path / "manifest.jsonl"
    manifest.write_text("\n".join(json.dumps(f) for f in filas) + "\n", encoding="utf-8")
    return tmp_path, gold, manifest


def plan_y_escritura(slug=SLUG1):
    pagina = {
        "slug": slug,
        "title": "HippoRAG Memory",
        "type": "paper",
        "summary": "Memoria con un grafo.",
        "body": f"- Umbral de 0.8 [{S1}].",
    }
    return [json.dumps({"update": [], "create": []}), json.dumps({"pages": [pagina]})]


def test_el_brazo_cumple_el_contrato_ingiere_y_responde(entorno):
    tmp_path, gold, _ = entorno
    respuesta = json.dumps({"action": "answer", "answer": f"Threshold 0.8 [{S1}]."})
    textos = [
        *plan_y_escritura(),
        json.dumps({"action": "search", "query": "HippoRAG"}),
        json.dumps({"action": "read", "pages": [SLUG1]}),
        respuesta,
    ]
    modelo, http = modelo_guionado(tmp_path, textos)
    brazo = BrazoWiki(modelo, Wiki(tmp_path / "wiki"), gold, spans_validos={S1})
    assert isinstance(brazo, Brazo) and brazo.nombre == "wiki"

    ingesta = brazo.ingerir(P1)
    assert ingesta.llamadas == 2 and ingesta.usd > 0
    resultado = brazo.responder("What threshold?")
    assert resultado.citas == (S1,) and resultado.llamadas == 3
    assert len(http.solicitudes) == 5


def cli(tmp_path, gold, manifest, textos, *argv):
    modelo, http = modelo_guionado(tmp_path, textos)
    lineas = []
    codigo = principal(
        [
            *argv,
            "--wiki",
            str(tmp_path / "wiki"),
            "--gold",
            str(gold),
            "--spans",
            str(tmp_path / "no-existe.jsonl"),
            *(["--manifest", str(manifest)] if argv[0] == "ingerir" else []),
        ],
        salida=lineas.append,
        crear_modelo=lambda ajustes: modelo,
    )
    return codigo, "\n".join(lineas), http


def test_estimar_no_llama_al_modelo_y_muestra_el_costo(entorno):
    tmp_path, gold, manifest = entorno
    codigo, texto, http = cli(tmp_path, gold, manifest, [], "ingerir", "--estimar")
    assert codigo == 0 and http.solicitudes == []
    assert "2 papers por ingerir de 2" in texto and "USD" in texto
    assert not (tmp_path / "wiki" / "estado.json").exists()


def test_el_estimado_crece_con_los_tokens_del_paper(entorno):
    pequeno = estimar_usd([{"tokens": 1_000}], AJUSTES)
    grande = estimar_usd([{"tokens": 100_000}], AJUSTES)
    assert 0 < pequeno < grande


def test_ingerir_con_paso_sigue_el_orden_del_manifest_e_informa_lo_aplicado(entorno):
    tmp_path, gold, manifest = entorno
    codigo, texto, http = cli(
        tmp_path, gold, manifest, plan_y_escritura(), "ingerir", "--paso", "1"
    )
    assert codigo == 0 and len(http.solicitudes) == 2
    assert f"[1/1] {P1}" in texto and "creadas 1, actualizadas 0" in texto
    assert "Wiki con 1 papers y 1 páginas" in texto
    assert Wiki(tmp_path / "wiki").ingeridos == [P1]


def test_volver_a_ingerir_lo_ya_ingerido_no_llama_al_modelo(entorno):
    tmp_path, gold, manifest = entorno
    cli(tmp_path, gold, manifest, plan_y_escritura(), "ingerir", "--paso", "1")
    codigo, texto, http = cli(tmp_path, gold, manifest, [], "ingerir", "--paso", "1")
    assert codigo == 0 and http.solicitudes == [] and "0 papers por ingerir de 1" in texto


def test_preguntar_muestra_respuesta_citas_acciones_y_metricas(entorno):
    tmp_path, gold, manifest = entorno
    cli(tmp_path, gold, manifest, plan_y_escritura(), "ingerir", "--paso", "1")
    textos = [
        json.dumps({"action": "read", "pages": [SLUG1]}),
        json.dumps({"action": "answer", "answer": "It is 0.8."}),
    ]
    codigo, texto, _ = cli(tmp_path, gold, manifest, textos, "preguntar", "What threshold?")
    assert codigo == 0 and "It is 0.8." in texto and "Abstención: no" in texto
    assert "Acciones: 1 (0 búsquedas, 1 lecturas)" in texto and SLUG1 in texto
    assert "2 llamadas" in texto


def test_un_gold_que_falta_devuelve_codigo_1_con_el_mensaje(entorno, capsys):
    tmp_path, gold, manifest = entorno
    (gold / f"{P1}.md").unlink()
    codigo, _, _ = cli(tmp_path, gold, manifest, [], "ingerir", "--paso", "1")
    assert codigo == 1 and "wikillm.ingest" in capsys.readouterr().err


def test_un_json_invalido_dos_veces_devuelve_codigo_1_y_deja_el_wiki_intacto(entorno, capsys):
    tmp_path, gold, manifest = entorno
    codigo, _, _ = cli(tmp_path, gold, manifest, ["x", "y"], "ingerir", "--paso", "1")
    assert codigo == 1 and "wiki-plan" in capsys.readouterr().err
    assert Wiki(tmp_path / "wiki").ingeridos == []
