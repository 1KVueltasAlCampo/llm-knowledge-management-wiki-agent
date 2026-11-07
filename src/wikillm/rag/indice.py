"""Índice vectorial persistente (Chroma) con ingesta por paper.

``ingerir`` añade los fragmentos de un paper y guarda en cada uno la huella de su Gold: si el
paper ya estaba con la misma huella no se recalcula nada, y si el Gold cambió se reemplazan sus
fragmentos. La recuperación se limita a los papers ingeridos en esta corrida, así que un índice
con los 50 papers ya calculados no se filtra a pasos anteriores.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from pathlib import Path

import chromadb
from langchain_chroma import Chroma
from langchain_core.embeddings import Embeddings

from wikillm.common.config import Settings
from wikillm.common.responder import ResultadoIngesta
from wikillm.ingest.gold import leer_gold
from wikillm.rag.fragmentos import (
    MAX_TOKENS_POR_DEFECTO,
    SOLAPAMIENTO_POR_DEFECTO,
    Fragmento,
    Medidor,
    dividir_paper,
)

RUTA_CHROMA_POR_DEFECTO = Path("data/chroma")
RUTA_CORPUS_POR_DEFECTO = Path("data/gold/corpus.jsonl")
RUTA_SPANS_POR_DEFECTO = Path("data/gold/spans.jsonl")
NOMBRE_COLECCION = "gold_v2"
COLECCION_ANTERIOR = "gold"  # la de la v1 (sin spans): se borra para no ocupar disco
K_POR_DEFECTO = 5
TAMANO_LOTE = 64


class ErrorDeDispositivo(RuntimeError):
    """El dispositivo pedido para los embeddings no está disponible."""


class GoldDistinto(RuntimeError):
    """El Gold local no es el que versionó el corpus: los span_id no apuntarían al mismo texto."""


@dataclass(frozen=True)
class Recuperado:
    fragmento: Fragmento
    distancia: float


def medidor_de_tokens(modelo: str) -> Medidor:
    """Cuenta tokens con el tokenizador del modelo de embeddings (sin tokens especiales)."""
    from transformers import AutoTokenizer

    tokenizador = AutoTokenizer.from_pretrained(modelo)
    tokenizador.model_max_length = 10**9  # medimos secciones enteras; no es el límite del modelo
    return lambda texto: len(tokenizador.encode(texto, add_special_tokens=False))


def crear_embeddings(ajustes: Settings) -> Embeddings:
    """Embeddings locales en el dispositivo de ``EMBEDDING_DEVICE`` (GPU por defecto)."""
    if ajustes.embedding_device.startswith("cuda"):
        import torch

        if not torch.cuda.is_available():
            raise ErrorDeDispositivo(
                "EMBEDDING_DEVICE es 'cuda' pero no hay GPU disponible para PyTorch. "
                "Pon EMBEDDING_DEVICE=cpu en tu .env."
            )
    from langchain_huggingface import HuggingFaceEmbeddings

    return HuggingFaceEmbeddings(
        model_name=ajustes.embedding_model,
        model_kwargs={"device": ajustes.embedding_device},
        encode_kwargs={"normalize_embeddings": True},
    )


def cargar_span_ids(ruta: Path | str = RUTA_SPANS_POR_DEFECTO) -> set[str]:
    """Identificadores de todos los fragmentos citables versionados (``spans.jsonl``)."""
    lineas = Path(ruta).read_text(encoding="utf-8").splitlines()
    return {json.loads(linea)["span_id"] for linea in lineas if linea.strip()}


def _hashes_versionados(ruta: Path) -> dict[str, str]:
    lineas = ruta.read_text(encoding="utf-8").splitlines()
    filas = [json.loads(linea) for linea in lineas if linea.strip()]
    return {fila["arxiv_id"]: fila["hash"] for fila in filas}


class IndiceRag:
    def __init__(
        self,
        carpeta_gold: Path | str,
        ruta_chroma: Path | str = RUTA_CHROMA_POR_DEFECTO,
        *,
        embeddings: Embeddings,
        medir: Medidor,
        modelo_embeddings: str,
        max_tokens: int = MAX_TOKENS_POR_DEFECTO,
        solapamiento: int = SOLAPAMIENTO_POR_DEFECTO,
        corpus_jsonl: Path | str | None = RUTA_CORPUS_POR_DEFECTO,
    ) -> None:
        self._carpeta = Path(carpeta_gold)
        self._medir = medir
        self._parametros = {
            "modelo": modelo_embeddings,
            "max_tokens": max_tokens,
            "solapamiento": solapamiento,
        }
        self._hashes = (
            _hashes_versionados(Path(corpus_jsonl))
            if corpus_jsonl is not None and Path(corpus_jsonl).exists()
            else None
        )
        cliente = chromadb.PersistentClient(path=str(ruta_chroma))
        try:
            cliente.delete_collection(COLECCION_ANTERIOR)
        except Exception:  # no existe: nada que borrar
            pass
        self._almacen = Chroma(
            client=cliente,
            collection_name=NOMBRE_COLECCION,
            embedding_function=embeddings,
            collection_metadata={"hnsw:space": "cosine"},
        )
        self.ingeridos: list[str] = []

    @property
    def total_fragmentos(self) -> int:
        return self._almacen._collection.count()

    def reiniciar(self) -> None:
        """Empieza una corrida nueva: los vectores quedan en disco pero nada está ingerido."""
        self.ingeridos = []

    def _comprobar_hash(self, arxiv_id: str, encabezado: dict) -> None:
        if self._hashes is None:
            return
        esperado = self._hashes.get(arxiv_id)
        if esperado is None or encabezado.get("hash") != esperado:
            raise GoldDistinto(
                f"El Gold local de {arxiv_id} no coincide con el versionado en corpus.jsonl; "
                "vuelve a ejecutar `uv run python -m wikillm.ingest`"
            )

    def _huella(self, ruta: Path) -> str:
        resumen = hashlib.sha256(json.dumps(self._parametros, sort_keys=True).encode("utf-8"))
        resumen.update(ruta.read_bytes())
        return resumen.hexdigest()

    def ingerir(self, arxiv_id: str) -> ResultadoIngesta:
        """Añade el paper al corpus de esta corrida; calcula embeddings solo si hace falta."""
        inicio = time.perf_counter()
        ruta = self._carpeta / f"{arxiv_id}.md"
        if not ruta.exists():
            raise FileNotFoundError(f"No hay Gold de {arxiv_id}; ejecuta wikillm.ingest")
        encabezado, cuerpo = leer_gold(ruta)
        self._comprobar_hash(arxiv_id, encabezado)
        huella = self._huella(ruta)
        coleccion = self._almacen._collection
        previo = coleccion.get(where={"arxiv_id": arxiv_id}, limit=1, include=["metadatas"])
        vigente = bool(previo["ids"]) and previo["metadatas"][0].get("huella") == huella
        if not vigente:
            if previo["ids"]:
                coleccion.delete(where={"arxiv_id": arxiv_id})
            fragmentos = dividir_paper(
                arxiv_id,
                str(encabezado["titulo"]),
                str(encabezado["version"]),
                cuerpo,
                medir=self._medir,
                max_tokens=self._parametros["max_tokens"],
                solapamiento=self._parametros["solapamiento"],
            )
            for i in range(0, len(fragmentos), TAMANO_LOTE):
                lote = fragmentos[i : i + TAMANO_LOTE]
                self._almacen.add_texts(
                    [f.texto for f in lote],
                    metadatas=[
                        {
                            "arxiv_id": f.arxiv_id,
                            "titulo": f.titulo,
                            "seccion": f.seccion,
                            "posicion": f.posicion,
                            "span_ids": ",".join(f.span_ids),
                            "huella": huella,
                        }
                        for f in lote
                    ],
                    ids=[f.id for f in lote],
                )
        if arxiv_id not in self.ingeridos:
            self.ingeridos.append(arxiv_id)
        return ResultadoIngesta(0, 0, time.perf_counter() - inicio, 0.0, 0)

    def recuperar(self, pregunta: str, k: int = K_POR_DEFECTO) -> list[Recuperado]:
        """Los ``k`` fragmentos más cercanos entre los ingeridos, ordenados por distancia."""
        if not self.ingeridos:
            return []
        resultados = self._almacen.similarity_search_with_score(
            pregunta, k=k, filter={"arxiv_id": {"$in": list(self.ingeridos)}}
        )
        recuperados = []
        for documento, distancia in resultados:
            datos = documento.metadata
            fragmento = Fragmento(
                texto=documento.page_content,
                arxiv_id=str(datos["arxiv_id"]),
                titulo=str(datos["titulo"]),
                seccion=str(datos["seccion"]),
                posicion=int(datos["posicion"]),
                span_ids=tuple(str(datos["span_ids"]).split(",")),
            )
            recuperados.append(Recuperado(fragmento, float(distancia)))
        return recuperados
