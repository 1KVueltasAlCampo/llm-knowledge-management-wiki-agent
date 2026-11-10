"""Índice vectorial persistente (Qdrant en modo local) con ingesta por paper.

``ingerir`` añade los fragmentos de un paper y guarda en cada uno la huella de su Gold: si el
paper ya estaba con la misma huella no se recalcula nada, y si el Gold cambió se reemplazan sus
fragmentos. La recuperación se limita a los papers ingeridos en esta corrida, así que un índice
con los 50 papers ya calculados no se filtra a pasos anteriores.

Qdrant local no usa servidor: guarda la colección en una carpeta y busca de forma exacta. Solo un
cliente puede abrir esa carpeta a la vez, así que dentro de un proceso se comparte un cliente por
carpeta (decisión 0005).
"""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import dataclass
from pathlib import Path

from langchain_core.embeddings import Embeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient, models

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

RUTA_INDICE_POR_DEFECTO = Path("data/qdrant")
RUTA_CORPUS_POR_DEFECTO = Path("data/gold/corpus.jsonl")
RUTA_SPANS_POR_DEFECTO = Path("data/gold/spans.jsonl")
NOMBRE_COLECCION = "gold_v2"
CLAVE_METADATOS = "metadata"  # donde langchain-qdrant guarda los metadatos en el payload
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


_CLIENTES: dict[str, QdrantClient] = {}


def _cliente(ruta: Path) -> QdrantClient:
    """Un cliente por carpeta y proceso: Qdrant local bloquea la carpeta para un solo cliente."""
    clave = str(ruta.resolve())
    if clave not in _CLIENTES:
        ruta.mkdir(parents=True, exist_ok=True)
        _CLIENTES[clave] = QdrantClient(path=clave)
    return _CLIENTES[clave]


def _filtro_por_papers(arxiv_ids: list[str]) -> models.Filter:
    return models.Filter(
        must=[
            models.FieldCondition(
                key=f"{CLAVE_METADATOS}.arxiv_id", match=models.MatchAny(any=arxiv_ids)
            )
        ]
    )


def _id_de_punto(id_fragmento: str) -> str:
    # Qdrant solo admite enteros o UUID como id; uuid5 es determinista.
    return str(uuid.uuid5(uuid.NAMESPACE_URL, id_fragmento))


class IndiceRag:
    def __init__(
        self,
        carpeta_gold: Path | str,
        ruta_indice: Path | str = RUTA_INDICE_POR_DEFECTO,
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
        self._ruta = Path(ruta_indice)
        self._cliente = _cliente(self._ruta)
        if not self._cliente.collection_exists(NOMBRE_COLECCION):
            dimension = len(embeddings.embed_query("dimensión"))
            self._cliente.create_collection(
                NOMBRE_COLECCION,
                vectors_config=models.VectorParams(size=dimension, distance=models.Distance.COSINE),
            )
        self._almacen = QdrantVectorStore(
            client=self._cliente,
            collection_name=NOMBRE_COLECCION,
            embedding=embeddings,
            metadata_payload_key=CLAVE_METADATOS,
            validate_collection_config=False,  # la colección ya se creó arriba con su dimensión
        )
        self.ingeridos: list[str] = []

    @property
    def total_fragmentos(self) -> int:
        return self._cliente.count(NOMBRE_COLECCION, exact=True).count

    def cerrar(self) -> None:
        """Libera la carpeta para que otro proceso pueda abrirla."""
        cliente = _CLIENTES.pop(str(self._ruta.resolve()), None)
        if cliente is not None:
            cliente.close()

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
        del_paper = _filtro_por_papers([arxiv_id])
        previo, _ = self._cliente.scroll(
            NOMBRE_COLECCION, scroll_filter=del_paper, limit=1, with_payload=True
        )
        vigente = (
            bool(previo)
            and (previo[0].payload or {}).get(CLAVE_METADATOS, {}).get("huella") == huella
        )
        if not vigente:
            if previo:
                self._cliente.delete(
                    NOMBRE_COLECCION, points_selector=models.FilterSelector(filter=del_paper)
                )
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
                            "id_fragmento": f.id,
                        }
                        for f in lote
                    ],
                    ids=[_id_de_punto(f.id) for f in lote],
                )
        if arxiv_id not in self.ingeridos:
            self.ingeridos.append(arxiv_id)
        return ResultadoIngesta(0, 0, time.perf_counter() - inicio, 0.0, 0)

    def recuperar(self, pregunta: str, k: int = K_POR_DEFECTO) -> list[Recuperado]:
        """Los ``k`` fragmentos más cercanos entre los ingeridos, ordenados por distancia."""
        if not self.ingeridos:
            return []
        resultados = self._almacen.similarity_search_with_score(
            pregunta, k=k, filter=_filtro_por_papers(list(self.ingeridos))
        )
        recuperados = []
        for documento, similitud in resultados:
            distancia = 1.0 - similitud  # Qdrant da similitud coseno; se conserva la distancia
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
