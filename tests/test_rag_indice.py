"""Índice vectorial con embeddings falsos: sin GPU, sin descargas y sin red."""

import hashlib
import json
import re
from dataclasses import replace

import pytest
import yaml
from langchain_core.embeddings import Embeddings

from wikillm.common.config import Settings
from wikillm.rag.indice import (
    ErrorDeDispositivo,
    GoldDistinto,
    IndiceRag,
    cargar_span_ids,
    crear_embeddings,
)

DIMENSIONES = 64


class EmbeddingsFalsos(Embeddings):
    """Bolsa de palabras con hash: textos con palabras en común quedan cerca."""

    def __init__(self):
        self.textos_calculados = 0

    def _vector(self, texto):
        vector = [0.0] * DIMENSIONES
        for palabra in re.findall(r"\w+", texto.lower()):
            indice = int(hashlib.md5(palabra.encode()).hexdigest(), 16) % DIMENSIONES
            vector[indice] += 1.0
        norma = sum(x * x for x in vector) ** 0.5 or 1.0
        return [x / norma for x in vector]

    def embed_documents(self, textos):
        self.textos_calculados += len(textos)
        return [self._vector(t) for t in textos]

    def embed_query(self, texto):
        return self._vector(texto)


def palabras(texto: str) -> int:
    return len(texto.split())


def escribir_gold(carpeta, arxiv_id, titulo, secciones, hash_="sha256:aaa"):
    cuerpo = f"# {titulo}\n\n" + "\n\n".join(
        f"## {nombre}\n\n" + "\n\n".join(parrafos) for nombre, parrafos in secciones
    )
    encabezado = yaml.safe_dump(
        {"arxiv_id": arxiv_id, "titulo": titulo, "version": "v1", "hash": hash_}
    )
    (carpeta / f"{arxiv_id}.md").write_text(f"---\n{encabezado}---\n\n{cuerpo}\n", encoding="utf-8")


@pytest.fixture
def gold(tmp_path):
    carpeta = tmp_path / "gold"
    carpeta.mkdir()
    escribir_gold(
        carpeta,
        "2401.00001",
        "Memoria de grafos",
        [
            ("1 Intro", ["Los grafos de conocimiento mejoran la memoria de los modelos."]),
            ("2 Método", ["El algoritmo PageRank personalizado recorre el grafo de entidades."]),
        ],
    )
    escribir_gold(
        carpeta,
        "2502.00002",
        "Wikis compilados",
        [("1 Intro", ["Un wiki mantenido por un modelo guarda páginas de markdown revisadas."])],
    )
    return carpeta


def indice(gold, tmp_path, embeddings, corpus_jsonl=None, **cambios):
    parametros = {
        "embeddings": embeddings,
        "medir": palabras,
        "modelo_embeddings": "falso",
        "max_tokens": 60,
        "solapamiento": 5,
        "corpus_jsonl": corpus_jsonl,
        **cambios,
    }
    return IndiceRag(gold, tmp_path / "chroma", **parametros)


def test_primera_ingesta_calcula_los_embeddings_y_no_gasta_modelo(gold, tmp_path):
    embeddings = EmbeddingsFalsos()
    resultado = indice(gold, tmp_path, embeddings).ingerir("2401.00001")
    assert embeddings.textos_calculados == 2  # una sección corta por fragmento
    assert (resultado.llamadas, resultado.tokens_entrada, resultado.usd) == (0, 0, 0)
    assert resultado.segundos > 0


def test_un_paper_ya_ingerido_con_el_mismo_gold_no_recalcula(gold, tmp_path):
    indice(gold, tmp_path, EmbeddingsFalsos()).ingerir("2401.00001")
    otros = EmbeddingsFalsos()
    nuevo = indice(gold, tmp_path, otros)  # misma carpeta de Chroma: otra corrida
    nuevo.ingerir("2401.00001")
    assert otros.textos_calculados == 0
    assert nuevo.total_fragmentos == 2
    assert nuevo.ingeridos == ["2401.00001"]


def test_si_cambia_el_gold_se_reemplazan_sus_fragmentos(gold, tmp_path):
    primero = indice(gold, tmp_path, EmbeddingsFalsos())
    primero.ingerir("2502.00002")
    escribir_gold(
        gold, "2502.00002", "Wikis compilados", [("1 Intro", ["Texto nuevo y distinto."])]
    )
    segundo = indice(gold, tmp_path, EmbeddingsFalsos())
    segundo.ingerir("2502.00002")
    textos = [r.fragmento.texto for r in segundo.recuperar("wiki páginas markdown", k=10)]
    assert not any("markdown revisadas" in t for t in textos)
    assert any("Texto nuevo y distinto" in t for t in textos)
    assert segundo.total_fragmentos == 1


def test_cambiar_los_parametros_de_fragmentacion_reemplaza_los_fragmentos(gold, tmp_path):
    indice(gold, tmp_path, EmbeddingsFalsos()).ingerir("2401.00001")
    otros = EmbeddingsFalsos()
    indice(gold, tmp_path, otros, max_tokens=50).ingerir("2401.00001")
    assert otros.textos_calculados == 2


def test_recuperar_respeta_k_orden_metadatos_y_span_ids(gold, tmp_path):
    almacen = indice(gold, tmp_path, EmbeddingsFalsos())
    almacen.ingerir("2401.00001")
    almacen.ingerir("2502.00002")
    resultados = almacen.recuperar("algoritmo PageRank personalizado grafo", k=2)
    assert len(resultados) == 2
    assert resultados[0].distancia <= resultados[1].distancia
    primero = resultados[0].fragmento
    assert (primero.arxiv_id, primero.seccion, primero.titulo) == (
        "2401.00001",
        "2 Método",
        "Memoria de grafos",
    )
    assert primero.span_ids == ("2401.00001#s2.p1",)
    assert primero.texto.startswith("Memoria de grafos — 2 Método")


def test_un_paper_no_ingerido_no_aparece_aunque_este_en_el_indice(gold, tmp_path):
    almacen = indice(gold, tmp_path, EmbeddingsFalsos())
    almacen.ingerir("2401.00001")
    almacen.ingerir("2502.00002")
    nueva_corrida = indice(gold, tmp_path, EmbeddingsFalsos())
    nueva_corrida.ingerir("2401.00001")
    papers = {r.fragmento.arxiv_id for r in nueva_corrida.recuperar("wiki markdown grafo", k=10)}
    assert papers == {"2401.00001"}
    assert nueva_corrida.total_fragmentos == 3  # el otro sigue en disco, pero no cuenta


def test_con_el_corpus_vacio_no_se_recupera_nada_y_no_falla(gold, tmp_path):
    assert indice(gold, tmp_path, EmbeddingsFalsos()).recuperar("lo que sea") == []


def test_reiniciar_olvida_lo_ingerido_pero_no_los_vectores(gold, tmp_path):
    almacen = indice(gold, tmp_path, EmbeddingsFalsos())
    almacen.ingerir("2401.00001")
    almacen.reiniciar()
    assert almacen.recuperar("grafo") == [] and almacen.total_fragmentos == 2


def test_el_hash_del_gold_debe_coincidir_con_el_versionado(gold, tmp_path):
    corpus = tmp_path / "corpus.jsonl"
    corpus.write_text(json.dumps({"arxiv_id": "2401.00001", "hash": "sha256:distinto"}) + "\n")
    with pytest.raises(GoldDistinto, match="2401.00001"):
        indice(gold, tmp_path, EmbeddingsFalsos(), corpus_jsonl=corpus).ingerir("2401.00001")
    corpus.write_text(json.dumps({"arxiv_id": "2401.00001", "hash": "sha256:aaa"}) + "\n")
    indice(gold, tmp_path, EmbeddingsFalsos(), corpus_jsonl=corpus).ingerir("2401.00001")


def test_un_paper_que_no_figura_en_el_corpus_versionado_tambien_falla(gold, tmp_path):
    corpus = tmp_path / "corpus.jsonl"
    corpus.write_text(json.dumps({"arxiv_id": "9999.99999", "hash": "sha256:aaa"}) + "\n")
    with pytest.raises(GoldDistinto):
        indice(gold, tmp_path, EmbeddingsFalsos(), corpus_jsonl=corpus).ingerir("2401.00001")


def test_un_paper_sin_gold_pide_ejecutar_la_ingesta(gold, tmp_path):
    with pytest.raises(FileNotFoundError, match="wikillm.ingest"):
        indice(gold, tmp_path, EmbeddingsFalsos()).ingerir("1111.11111")


def test_cargar_span_ids_lee_el_manifiesto_de_spans(tmp_path):
    ruta = tmp_path / "spans.jsonl"
    ruta.write_text('{"span_id": "a#s1.p1"}\n{"span_id": "a#s1.p2"}\n', encoding="utf-8")
    assert cargar_span_ids(ruta) == {"a#s1.p1", "a#s1.p2"}


AJUSTES = Settings(
    api_key="sk-prueba",
    base_url="https://api.deepseek.com",
    model="deepseek-flash",
    thinking="disabled",
    reasoning_effort="",
    temperature=0.0,
    max_retries=0,
    timeout_seconds=30.0,
    price_input_cache_miss=0.15,
    price_input_cache_hit=0.003,
    price_output=0.60,
    max_usd_per_run=2.0,
    embedding_model="BAAI/bge-small-en-v1.5",
    embedding_device="cuda",
)


def test_sin_gpu_el_error_indica_cambiar_a_cpu(monkeypatch):
    import torch

    monkeypatch.setattr(torch.cuda, "is_available", lambda: False)
    with pytest.raises(ErrorDeDispositivo, match="EMBEDDING_DEVICE=cpu"):
        crear_embeddings(replace(AJUSTES, embedding_device="cuda"))
