"""Orden de consola del brazo RAG.

    uv run python -m wikillm.rag indexar
    uv run python -m wikillm.rag preguntar "¿Qué propone HippoRAG?"

``preguntar`` hace una llamada real al modelo y gasta saldo.
"""

from __future__ import annotations

import argparse
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
    ErrorDeDispositivo,
    InformeIndice,
    abrir_indice,
    crear_embeddings,
    medidor_de_tokens,
)

Apertura = Callable[[argparse.Namespace, Settings], tuple[Any, InformeIndice]]


def _abrir_real(argumentos: argparse.Namespace, ajustes: Settings) -> tuple[Any, InformeIndice]:
    return abrir_indice(
        argumentos.gold,
        argumentos.chroma,
        embeddings=crear_embeddings(ajustes),
        medir=medidor_de_tokens(ajustes.embedding_model),
        modelo_embeddings=ajustes.embedding_model,
    )


def _analizar(argv: Sequence[str] | None) -> argparse.Namespace:
    analizador = argparse.ArgumentParser(prog="python -m wikillm.rag", description=__doc__)
    comunes = argparse.ArgumentParser(add_help=False)
    comunes.add_argument("--gold", type=Path, default=Path("data/gold"))
    comunes.add_argument("--chroma", type=Path, default=RUTA_CHROMA_POR_DEFECTO)
    subordenes = analizador.add_subparsers(dest="orden", required=True)
    subordenes.add_parser("indexar", parents=[comunes], help="construye o reutiliza el índice")
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
    abrir: Apertura = _abrir_real,
    crear_modelo: Callable[[Settings], ClienteModelo] = ClienteModelo,
) -> int:
    argumentos = _analizar(argv)
    ajustes = load_settings()
    try:
        almacen, informe = abrir(argumentos, ajustes)
        estado = "reconstruido" if informe.reconstruido else "reutilizado"
        salida(
            f"Índice {estado}: {informe.fragmentos} fragmentos en {informe.segundos:.1f} s "
            f"(modelo {ajustes.embedding_model}, dispositivo {ajustes.embedding_device})"
        )
        if argumentos.orden == "indexar":
            return 0
        brazo = BrazoRag(crear_modelo(ajustes), almacen, k=argumentos.k)
        resultado = brazo.responder(argumentos.pregunta)
    except (ErrorDeDispositivo, ErrorDeModelo, TopeDeGastoError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    salida(f"\nRespuesta:\n{resultado.respuesta}\n")
    salida(f"Fuentes: {', '.join(resultado.fuentes) or '(ninguna)'}")
    salida(
        f"Tokens: {resultado.tokens_entrada} de entrada y {resultado.tokens_salida} de salida · "
        f"{resultado.segundos:.1f} s · {resultado.usd:.6f} USD estimados"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(principal())
