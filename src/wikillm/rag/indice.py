"""Índice vectorial persistente (Chroma) construido a partir de los archivos Gold.

El índice guarda una huella del contenido del Gold y de los parámetros de fragmentación. Si la
huella coincide con la guardada, se reutiliza; si no, se reconstruye por completo. Con unos pocos
papers la reconstrucción tarda segundos, así que no se complican las actualizaciones parciales.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from pathlib import Path

import chromadb
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from wikillm.common.config import Settings
from wikillm.rag.fragmentos import (
    MAX_TOKENS_POR_DEFECTO,
    SOLAPAMIENTO_POR_DEFECTO,
    Fragmento,
    Medidor,
    leer_fragmentos,
)

RUTA_CHROMA_POR_DEFECTO = Path("data/chroma")
NOMBRE_COLECCION = "gold"
K_POR_DEFECTO = 5
TAMANO_LOTE = 64


class ErrorDeDispositivo(RuntimeError):
    """El dispositivo pedido para los embeddings no está disponible."""


@dataclass(frozen=True)
class InformeIndice:
    fragmentos: int
    reconstruido: bool
    segundos: float


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


def huella_gold(carpeta_gold: Path | str, parametros: dict[str, object]) -> str:
    resumen = hashlib.sha256(json.dumps(parametros, sort_keys=True).encode("utf-8"))
    for ruta in sorted(Path(carpeta_gold).glob("*.md")):
        resumen.update(ruta.name.encode("utf-8"))
        resumen.update(ruta.read_bytes())
    return resumen.hexdigest()


def _coleccion_vigente(cliente: chromadb.ClientAPI, huella: str) -> bool:
    try:
        coleccion = cliente.get_collection(NOMBRE_COLECCION)
    except Exception:  # no existe todavía; cada versión de Chroma lanza otra clase
        return False
    return (coleccion.metadata or {}).get("huella") == huella


def abrir_indice(
    carpeta_gold: Path | str,
    ruta_chroma: Path | str = RUTA_CHROMA_POR_DEFECTO,
    *,
    embeddings: Embeddings,
    medir: Medidor,
    modelo_embeddings: str,
    max_tokens: int = MAX_TOKENS_POR_DEFECTO,
    solapamiento: int = SOLAPAMIENTO_POR_DEFECTO,
) -> tuple[Chroma, InformeIndice]:
    """Devuelve el índice del Gold, construyéndolo solo si no existe o el Gold cambió."""
    inicio = time.perf_counter()
    huella = huella_gold(
        carpeta_gold,
        {"modelo": modelo_embeddings, "max_tokens": max_tokens, "solapamiento": solapamiento},
    )
    cliente = chromadb.PersistentClient(path=str(ruta_chroma))
    reconstruir = not _coleccion_vigente(cliente, huella)
    if reconstruir:
        try:
            cliente.delete_collection(NOMBRE_COLECCION)
        except Exception:  # puede no existir
            pass
    almacen = Chroma(
        client=cliente,
        collection_name=NOMBRE_COLECCION,
        embedding_function=embeddings,
        collection_metadata={"hnsw:space": "cosine", "huella": huella},
    )
    if reconstruir:
        fragmentos = leer_fragmentos(
            carpeta_gold, medir=medir, max_tokens=max_tokens, solapamiento=solapamiento
        )
        for i in range(0, len(fragmentos), TAMANO_LOTE):
            lote = fragmentos[i : i + TAMANO_LOTE]
            almacen.add_texts(
                [f.texto for f in lote],
                metadatas=[
                    {
                        "arxiv_id": f.arxiv_id,
                        "titulo": f.titulo,
                        "seccion": f.seccion,
                        "posicion": f.posicion,
                    }
                    for f in lote
                ],
                ids=[f.id for f in lote],
            )
    total = almacen._collection.count()
    return almacen, InformeIndice(total, reconstruir, time.perf_counter() - inicio)


def _a_fragmento(documento: Document) -> Fragmento:
    datos = documento.metadata
    return Fragmento(
        texto=documento.page_content,
        arxiv_id=str(datos["arxiv_id"]),
        titulo=str(datos["titulo"]),
        seccion=str(datos["seccion"]),
        posicion=int(datos["posicion"]),
    )


def recuperar(almacen: Chroma, pregunta: str, k: int = K_POR_DEFECTO) -> list[Recuperado]:
    """Los ``k`` fragmentos más cercanos a la pregunta, del más al menos cercano."""
    resultados = almacen.similarity_search_with_score(pregunta, k=k)
    return [Recuperado(_a_fragmento(doc), float(distancia)) for doc, distancia in resultados]
