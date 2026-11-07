"""Orden de consola del brazo WikiLLM.

    uv run python -m wikillm.wiki ingerir --paso 5 --estimar
    uv run python -m wikillm.wiki ingerir --paso 5
    uv run python -m wikillm.wiki preguntar "What does HippoRAG use PageRank for?"

Los papers se ingieren en el ``orden_ingesta`` del manifest; ``--paso N`` ingiere hasta los
primeros N (los ya ingeridos no cuestan nada). ``--estimar`` solo imprime el costo esperado.
``ingerir`` y ``preguntar`` hacen llamadas reales al modelo y gastan saldo. El wiki queda en
``--wiki`` (por defecto ``data/wiki/dev``), una carpeta con su propio repositorio Git.
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
from wikillm.wiki.almacen import ErrorDeAlmacen, Wiki
from wikillm.wiki.brazo import BrazoWiki
from wikillm.wiki.consulta import MAX_ACCIONES_POR_DEFECTO
from wikillm.wiki.ingesta import ErrorDeIngesta

RUTA_MANIFEST_POR_DEFECTO = Path("data/manifest_corpus.jsonl")
RUTA_SPANS_POR_DEFECTO = Path("data/gold/spans.jsonl")
RUTA_WIKI_POR_DEFECTO = Path("data/wiki/dev")
TOKENS_DE_SALIDA_SUPUESTOS = 8_000  # por paper: plan breve y varias páginas reescritas


def _filas_en_orden(manifest: Path, paso: int | None) -> list[dict[str, Any]]:
    lineas = manifest.read_text(encoding="utf-8").splitlines()
    filas = sorted(
        (json.loads(linea) for linea in lineas if linea.strip()),
        key=lambda fila: int(fila["orden_ingesta"]),
    )
    return filas if paso is None else filas[:paso]


def _cargar_span_ids(ruta: Path) -> set[str] | None:
    if not ruta.exists():
        return None
    lineas = ruta.read_text(encoding="utf-8").splitlines()
    return {json.loads(linea)["span_id"] for linea in lineas if linea.strip()}


def estimar_usd(filas: Sequence[dict[str, Any]], ajustes: Settings) -> float:
    """Costo aproximado: el paper se lee dos veces (la segunda desde la caché) y se escribe."""
    millon = 1_000_000
    total = 0.0
    for fila in filas:
        tokens = int(fila.get("tokens", 0))
        total += tokens * ajustes.price_input_cache_miss / millon
        total += tokens * ajustes.price_input_cache_hit / millon
        total += TOKENS_DE_SALIDA_SUPUESTOS * ajustes.price_output / millon
    return total


def _analizar(argv: Sequence[str] | None) -> argparse.Namespace:
    analizador = argparse.ArgumentParser(prog="python -m wikillm.wiki", description=__doc__)
    comunes = argparse.ArgumentParser(add_help=False)
    comunes.add_argument("--wiki", type=Path, default=RUTA_WIKI_POR_DEFECTO)
    comunes.add_argument("--gold", type=Path, default=Path("data/gold"))
    comunes.add_argument("--spans", type=Path, default=RUTA_SPANS_POR_DEFECTO)
    subordenes = analizador.add_subparsers(dest="orden", required=True)
    ingerir = subordenes.add_parser(
        "ingerir", parents=[comunes], help="ingiere los papers en orden (gasta saldo)"
    )
    ingerir.add_argument("--manifest", type=Path, default=RUTA_MANIFEST_POR_DEFECTO)
    ingerir.add_argument("--paso", type=int, default=None, help="ingerir hasta los primeros N")
    ingerir.add_argument("--estimar", action="store_true", help="solo imprime el costo esperado")
    preguntar = subordenes.add_parser(
        "preguntar", parents=[comunes], help="responde una pregunta (gasta saldo)"
    )
    preguntar.add_argument("pregunta")
    preguntar.add_argument("--max-acciones", type=int, default=MAX_ACCIONES_POR_DEFECTO)
    return analizador.parse_args(argv)


def principal(
    argv: Sequence[str] | None = None,
    *,
    salida: Callable[[str], None] = print,
    crear_modelo: Callable[[Settings], ClienteModelo] = ClienteModelo,
) -> int:
    argumentos = _analizar(argv)
    ajustes = load_settings()
    try:
        wiki = Wiki(argumentos.wiki)
        if argumentos.orden == "ingerir":
            return _ingerir(argumentos, ajustes, wiki, salida, crear_modelo)
        return _preguntar(argumentos, ajustes, wiki, salida, crear_modelo)
    except (
        ErrorDeIngesta,
        ErrorDeAlmacen,
        FileNotFoundError,
        ErrorDeModelo,
        TopeDeGastoError,
    ) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


def _brazo(
    argumentos: argparse.Namespace,
    ajustes: Settings,
    wiki: Wiki,
    crear_modelo: Callable[[Settings], ClienteModelo],
    **kwargs: Any,
) -> BrazoWiki:
    return BrazoWiki(
        crear_modelo(ajustes),
        wiki,
        argumentos.gold,
        spans_validos=_cargar_span_ids(argumentos.spans),
        **kwargs,
    )


def _ingerir(
    argumentos: argparse.Namespace,
    ajustes: Settings,
    wiki: Wiki,
    salida: Callable[[str], None],
    crear_modelo: Callable[[Settings], ClienteModelo],
) -> int:
    filas = _filas_en_orden(argumentos.manifest, argumentos.paso)
    pendientes = [f for f in filas if f["arxiv_id"] not in wiki.ingeridos]
    salida(
        f"{len(pendientes)} papers por ingerir de {len(filas)}; estimado "
        f"{estimar_usd(pendientes, ajustes):.3f} USD (salida supuesta de "
        f"{TOKENS_DE_SALIDA_SUPUESTOS} tokens por paper, sin hora pico)"
    )
    if argumentos.estimar:
        return 0
    brazo = _brazo(argumentos, ajustes, wiki, crear_modelo)
    total = 0.0
    for numero, fila in enumerate(pendientes, start=1):
        resultado = brazo.ingerir(fila["arxiv_id"])
        total += resultado.usd
        aplicado = brazo.ingestor.ultima
        salida(
            f"[{numero}/{len(pendientes)}] {fila['arxiv_id']}: {resultado.segundos:.1f} s · "
            f"{resultado.llamadas} llamadas · {resultado.usd:.4f} USD · "
            f"creadas {len(aplicado.creadas)}, actualizadas {len(aplicado.actualizadas)}, "
            f"citas eliminadas {aplicado.citas_eliminadas}, enlaces rotos "
            f"{aplicado.enlaces_rotos}, líneas sin cita {aplicado.lineas_sin_cita}"
        )
    salida(
        f"Wiki con {len(wiki.ingeridos)} papers y {len(wiki.slugs())} páginas en {wiki.carpeta}; "
        f"gastado en esta orden {total:.4f} USD"
    )
    return 0


def _preguntar(
    argumentos: argparse.Namespace,
    ajustes: Settings,
    wiki: Wiki,
    salida: Callable[[str], None],
    crear_modelo: Callable[[Settings], ClienteModelo],
) -> int:
    brazo = _brazo(argumentos, ajustes, wiki, crear_modelo, max_acciones=argumentos.max_acciones)
    resultado = brazo.responder(argumentos.pregunta)
    traza = brazo.consulta.traza
    salida(f"\nRespuesta:\n{resultado.respuesta}\n")
    salida(f"Citas: {', '.join(resultado.citas) or '(ninguna)'}")
    salida(f"Abstención: {'sí' if resultado.abstuvo else 'no'}")
    salida(
        f"Acciones: {traza.acciones} ({traza.busquedas} búsquedas, {traza.lecturas} lecturas) · "
        f"páginas leídas: {', '.join(traza.paginas_leidas) or '(ninguna)'}"
    )
    for incidencia in traza.incidencias:
        salida(f"Incidencia: {incidencia}")
    salida(
        f"Tokens: {resultado.tokens_entrada} de entrada ({resultado.tokens_contexto} de contexto) "
        f"y {resultado.tokens_salida} de salida · {resultado.llamadas} llamadas · "
        f"{resultado.segundos:.1f} s · {resultado.usd:.6f} USD estimados"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(principal())
