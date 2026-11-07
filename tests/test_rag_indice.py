"""Índice vectorial con embeddings falsos: sin GPU, sin descargas y sin red."""

import hashlib
import re
from dataclasses import replace

import pytest
import yaml
from langchain_core.embeddings import Embeddings

from wikillm.common.config import Settings
from wikillm.rag.indice import ErrorDeDispositivo, abrir_indice, crear_embeddings, recuperar

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


def escribir_gold(carpeta, arxiv_id, titulo, secciones):
    cuerpo = f"# {titulo}\n\n" + "\n\n".join(f"## {n}\n\n{t}" for n, t in secciones)
    encabezado = yaml.safe_dump({"arxiv_id": arxiv_id, "titulo": titulo})
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
            ("1 Intro", "Los grafos de conocimiento mejoran la memoria de los modelos."),
            ("2 Método", "El algoritmo PageRank personalizado recorre el grafo de entidades."),
        ],
    )
    escribir_gold(
        carpeta,
        "2502.00002",
        "Wikis compilados",
        [("1 Intro", "Un wiki mantenido por un modelo guarda páginas de markdown revisadas.")],
    )
    return carpeta


def abrir(gold, tmp_path, embeddings, **cambios):
    parametros = {
        "embeddings": embeddings,
        "medir": palabras,
        "modelo_embeddings": "falso",
        "max_tokens": 50,
        "solapamiento": 5,
        **cambios,
    }
    return abrir_indice(gold, tmp_path / "chroma", **parametros)


def test_primera_construccion_calcula_todos_los_fragmentos(gold, tmp_path):
    embeddings = EmbeddingsFalsos()
    _, informe = abrir(gold, tmp_path, embeddings)
    assert informe.reconstruido
    assert informe.fragmentos == 3
    assert embeddings.textos_calculados == 3


def test_gold_sin_cambios_no_recalcula(gold, tmp_path):
    abrir(gold, tmp_path, EmbeddingsFalsos())
    otros = EmbeddingsFalsos()
    _, informe = abrir(gold, tmp_path, otros)
    assert not informe.reconstruido
    assert informe.fragmentos == 3
    assert otros.textos_calculados == 0


def test_gold_modificado_reconstruye_sin_restos(gold, tmp_path):
    abrir(gold, tmp_path, EmbeddingsFalsos())
    escribir_gold(gold, "2502.00002", "Wikis compilados", [("1 Intro", "Texto nuevo y distinto.")])
    almacen, informe = abrir(gold, tmp_path, EmbeddingsFalsos())
    assert informe.reconstruido
    assert informe.fragmentos == 3
    textos = [r.fragmento.texto for r in recuperar(almacen, "wiki páginas markdown", k=10)]
    assert not any("markdown revisadas" in t for t in textos)
    assert any("Texto nuevo y distinto" in t for t in textos)


def test_cambiar_los_parametros_de_fragmentacion_reconstruye(gold, tmp_path):
    abrir(gold, tmp_path, EmbeddingsFalsos())
    _, informe = abrir(gold, tmp_path, EmbeddingsFalsos(), max_tokens=30)
    assert informe.reconstruido


def test_recuperar_respeta_k_orden_y_metadatos(gold, tmp_path):
    almacen, _ = abrir(gold, tmp_path, EmbeddingsFalsos())
    resultados = recuperar(almacen, "algoritmo PageRank personalizado grafo", k=2)
    assert len(resultados) == 2
    assert resultados[0].distancia <= resultados[1].distancia
    primero = resultados[0].fragmento
    assert (primero.arxiv_id, primero.seccion, primero.titulo) == (
        "2401.00001",
        "2 Método",
        "Memoria de grafos",
    )
    assert primero.texto.startswith("Memoria de grafos — 2 Método")


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
