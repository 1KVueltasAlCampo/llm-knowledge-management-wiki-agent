"""Orden de consola del brazo RAG.

    uv run python -m wikillm.rag indexar [--paso 10]
    uv run python -m wikillm.rag preguntar "What does HippoRAG use PageRank for?" [--paso 10]

Los papers se ingieren en el ``orden_ingesta`` del manifest; ``--paso N`` ingiere solo los
primeros N. ``preguntar`` hace una llamada real al modelo y gasta saldo.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

from wikillm.common.config import Settings, load_settings
from wikillm.common.modelo import ClienteModelo, ErrorDeModelo, TopeDeGastoError
from wikillm.rag.brazo import BrazoRag
from wikillm.rag.indice import (
    K_POR_DEFECTO,
    RUTA_CHROMA_POR_DEFECTO,
    RUTA_SPANS_POR_DEFECTO,
    ErrorDeDispositivo,
    GoldDistinto,
    IndiceRag,
    cargar_span_ids,
    crear_embeddings,
    medidor_de_tokens,
)

RUTA_MANIFEST_POR_DEFECTO = Path("data/manifest_corpus.jsonl")


def _crear_indice_real(argumentos: argparse.Namespace, ajustes: Settings) -> IndiceRag:
    return IndiceRag(
        argumentos.gold,
        argumentos.chroma,
        embeddings=crear_embeddings(ajustes),
        medir=medidor_de_tokens(ajustes.embedding_model),
        modelo_embeddings=ajustes.embedding_model,
    )


def _ids_en_orden(manifest: Path, paso: int | None) -> list[str]:
    lineas = manifest.read_text(encoding="utf-8").splitlines()
    filas = sorted((json.loads(linea) for linea in lineas if linea.strip()), key=_orden)
    ids = [fila["arxiv_id"] for fila in filas]
    return ids if paso is None else ids[:paso]


def _orden(fila: dict[str, Any]) -> int:
    return int(fila["orden_ingesta"])


def _analizar(argv: Sequence[str] | None) -> argparse.Namespace:
    analizador = argparse.ArgumentParser(prog="python -m wikillm.rag", description=__doc__)
    comunes = argparse.ArgumentParser(add_help=False)
    comunes.add_argument("--gold", type=Path, default=Path("data/gold"))
    comunes.add_argument("--chroma", type=Path, default=RUTA_CHROMA_POR_DEFECTO)
    comunes.add_argument("--manifest", type=Path, default=RUTA_MANIFEST_POR_DEFECTO)
    comunes.add_argument("--spans", type=Path, default=RUTA_SPANS_POR_DEFECTO)
    comunes.add_argument("--paso", type=int, default=None, help="ingerir solo los primeros N")
    subordenes = analizador.add_subparsers(dest="orden", required=True)
    subordenes.add_parser("indexar", parents=[comunes], help="ingiere los papers en orden")
    preguntar = subordenes.add_parser(
        "preguntar", parents=[comunes], help="responde una pregunta (gasta saldo)"
    )
    preguntar.add_argument("pregunta")
    preguntar.add_argument("--k", type=int, default=K_POR_DEFECTO)
    return analizador.parse_args(argv)


def principal(
    argv: Sequence[str] | None = None,
    *,
    salida: Callable[[str], None] = print,
    crear_indice: Callable[[argparse.Namespace, Settings], Any] = _crear_indice_real,
    crear_modelo: Callable[[Settings], ClienteModelo] = ClienteModelo,
) -> int:
    argumentos = _analizar(argv)
    ajustes = load_settings()
    try:
        indice = crear_indice(argumentos, ajustes)
        ids = _ids_en_orden(argumentos.manifest, argumentos.paso)
        total = 0.0
        for numero, arxiv_id in enumerate(ids, start=1):
            ingesta = indice.ingerir(arxiv_id)
            total += ingesta.segundos
            salida(f"[{numero}/{len(ids)}] {arxiv_id}: {ingesta.segundos:.1f} s")
        salida(
            f"Ingeridos {len(ids)} papers en {total:.1f} s; el índice tiene "
            f"{indice.total_fragmentos} fragmentos "
            f"(modelo {ajustes.embedding_model}, dispositivo {ajustes.embedding_device})"
        )
        if argumentos.orden == "indexar":
            return 0
        spans = argumentos.spans
        brazo = BrazoRag(
            crear_modelo(ajustes),
            indice,
            k=argumentos.k,
            spans_validos=cargar_span_ids(spans) if spans.exists() else None,
        )
        resultado = brazo.responder(argumentos.pregunta)
    except (
        ErrorDeDispositivo,
        GoldDistinto,
        FileNotFoundError,
        ErrorDeModelo,
        TopeDeGastoError,
    ) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    salida(f"\nRespuesta:\n{resultado.respuesta}\n")
    salida(f"Citas: {', '.join(resultado.citas) or '(ninguna)'}")
    salida(f"Abstención: {'sí' if resultado.abstuvo else 'no'}")
    salida(
        f"Tokens: {resultado.tokens_entrada} de entrada ({resultado.tokens_contexto} de contexto) "
        f"y {resultado.tokens_salida} de salida · {resultado.segundos:.1f} s · "
        f"{resultado.usd:.6f} USD estimados"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(principal())
