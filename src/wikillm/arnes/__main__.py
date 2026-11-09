"""Orden de consola del arnés de comparación.

    uv run python -m wikillm.arnes correr --corrida piloto-1 --estimar
    uv run python -m wikillm.arnes correr --corrida piloto-1 --pasos 0,5 \\
        --estado-minimo borrador --tipos T1,T5
    uv run python -m wikillm.arnes correr --corrida 2026-12-01 --confirmo-usd 6
    uv run python -m wikillm.arnes comparar "What does HippoRAG use PageRank for?" \\
        --wiki data/wiki/dev2

``comparar`` hace una sola pregunta a los dos sistemas y muestra respuesta, citas con su fragmento,
pasos del agente y costo; el paso de ingesta es el del wiki indicado.

``correr`` ingiere los papers en ``orden_ingesta`` y, en cada paso, hace las preguntas del banco al
RAG y al wiki. Escribe en ``results/<corrida>/``: ``respuestas.jsonl`` (el contrato de resultados),
``ingestas.jsonl``, ``trazas.jsonl`` y ``corrida.json``. Si se corta, repetir la misma orden
continúa donde quedó. Hace llamadas reales al modelo y gasta saldo.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from wikillm.arnes.comparar import comparar, crear_resolutor, formatear, registrar
from wikillm.arnes.corrida import (
    CORRIDA,
    PASOS_POR_DEFECTO,
    Configuracion,
    ErrorDeCorrida,
    ejecutar,
    formatear_resumen,
    leer_orden,
    resumir,
    validar_pasos,
)
from wikillm.arnes.estimacion import (
    LIMITE_SIN_CONFIRMAR_USD,
    ExcesoDeCosto,
    aviso_de_hora_pico,
    estimar,
    exigir_confirmacion,
)
from wikillm.arnes.registro import (
    actualizar_corrida,
    escribir_corrida,
    huella_archivo,
    info_git,
    leer_corrida,
)
from wikillm.arnes.seleccion import (
    ESTADO_PARA_INFORME,
    ErrorDeSeleccion,
    conteo_por_estado,
    seleccionar,
    valida_para_informe,
)
from wikillm.common.config import Settings, load_settings
from wikillm.common.modelo import ClienteModelo, ErrorDeModelo, TopeDeGastoError
from wikillm.common.responder import Brazo
from wikillm.eval.banco import ESTADOS, leer_banco
from wikillm.wiki.almacen import ErrorDeAlmacen
from wikillm.wiki.ingesta import ErrorDeIngesta

BRAZOS = ("rag", "wiki")
RUTA_BANCO = Path("data/preguntas/banco.jsonl")
RUTA_MANIFEST = Path("data/manifest_corpus.jsonl")
RUTA_SPANS = Path("data/gold/spans.jsonl")


def _ahora() -> datetime:
    return datetime.now(UTC)


def _crear_modelo(ajustes: Settings, ruta_registro: Path) -> ClienteModelo:
    return ClienteModelo(ajustes, ruta_registro=ruta_registro)


def _crear_brazos_reales(
    modelo: ClienteModelo, ajustes: Settings, argumentos: argparse.Namespace
) -> list[Brazo]:
    # importaciones aquí: cargan Chroma y torch, que no hacen falta para estimar
    from wikillm.rag.brazo import BrazoRag
    from wikillm.rag.indice import (
        IndiceRag,
        cargar_span_ids,
        crear_embeddings,
        medidor_de_tokens,
    )
    from wikillm.wiki.almacen import Wiki
    from wikillm.wiki.brazo import BrazoWiki

    spans = cargar_span_ids(argumentos.spans) if argumentos.spans.exists() else None
    carpeta_indice = getattr(argumentos, "chroma", None) or Path("data/chroma") / argumentos.corrida
    carpeta_wiki = getattr(argumentos, "wiki", None) or Path("data/wiki") / argumentos.corrida
    indice = IndiceRag(
        argumentos.gold,
        carpeta_indice,
        embeddings=crear_embeddings(ajustes),
        medir=medidor_de_tokens(ajustes.embedding_model),
        modelo_embeddings=ajustes.embedding_model,
    )
    return [
        BrazoRag(modelo, indice, k=argumentos.k, spans_validos=spans),
        BrazoWiki(
            modelo,
            Wiki(carpeta_wiki),
            argumentos.gold,
            max_acciones=argumentos.max_acciones,
            spans_validos=spans,
        ),
    ]


def _lista(texto: str | None) -> list[str] | None:
    return [x.strip() for x in texto.split(",") if x.strip()] if texto else None


def _analizar(argv: Sequence[str] | None) -> argparse.Namespace:
    analizador = argparse.ArgumentParser(prog="python -m wikillm.arnes", description=__doc__)
    ordenes = analizador.add_subparsers(dest="orden", required=True)
    correr = ordenes.add_parser("correr", help="ejecuta los dos brazos sobre el banco (gasta)")
    correr.add_argument("--corrida", required=True, help="nombre; repetirlo reanuda la corrida")
    correr.add_argument("--pasos", default=",".join(str(p) for p in PASOS_POR_DEFECTO))
    correr.add_argument("--banco", type=Path, default=RUTA_BANCO)
    correr.add_argument("--manifest", type=Path, default=RUTA_MANIFEST)
    correr.add_argument("--gold", type=Path, default=Path("data/gold"))
    correr.add_argument("--spans", type=Path, default=RUTA_SPANS)
    correr.add_argument("--resultados", type=Path, default=Path("results"))
    correr.add_argument("--estado-minimo", choices=ESTADOS, default=ESTADO_PARA_INFORME)
    correr.add_argument("--tipos", help="solo estos tipos, separados por comas (T1,T4)")
    correr.add_argument("--preguntas", help="solo estos id, separados por comas")
    correr.add_argument("--k", type=int, default=5, help="fragmentos que recupera el RAG")
    correr.add_argument("--max-acciones", type=int, default=8, help="tope del agente del wiki")
    correr.add_argument("--estimar", action="store_true", help="solo imprime el costo esperado")
    correr.add_argument("--confirmo-usd", type=float, default=0.0, help="acepta gasto mayor de 5")
    cmp_ = ordenes.add_parser(
        "comparar", help="hace una pregunta a los dos sistemas y muestra todo (gasta centavos)"
    )
    cmp_.add_argument("pregunta")
    cmp_.add_argument(
        "--wiki", type=Path, default=Path("data/wiki/demo"), help="wiki ya construido"
    )
    cmp_.add_argument("--chroma", type=Path, default=Path("data/chroma"), help="índice del RAG")
    cmp_.add_argument("--manifest", type=Path, default=RUTA_MANIFEST)
    cmp_.add_argument("--gold", type=Path, default=Path("data/gold"))
    cmp_.add_argument("--spans", type=Path, default=RUTA_SPANS)
    cmp_.add_argument("--resultados", type=Path, default=Path("results"))
    cmp_.add_argument("--k", type=int, default=5, help="fragmentos que recupera el RAG")
    cmp_.add_argument("--max-acciones", type=int, default=8, help="tope del agente del wiki")
    cmp_.set_defaults(corrida="demo")
    return analizador.parse_args(argv)


def _errores_conocidos() -> tuple[type[BaseException], ...]:
    from wikillm.rag.indice import ErrorDeDispositivo, GoldDistinto

    return (
        ErrorDeModelo,
        TopeDeGastoError,
        ErrorDeCorrida,
        ErrorDeAlmacen,
        ErrorDeIngesta,
        ErrorDeDispositivo,
        GoldDistinto,
        FileNotFoundError,
    )


def _metadatos(
    argumentos: argparse.Namespace,
    ajustes: Settings,
    pasos: tuple[int, ...],
    preguntas: list[dict[str, Any]],
    valida: bool,
    total_estimado: float,
    inicio: str,
) -> dict[str, Any]:
    return {
        "corrida": argumentos.corrida,
        "inicio": inicio,
        **info_git(),
        "modelo": ajustes.model,
        "temperatura": ajustes.temperature,
        "razonamiento": ajustes.thinking,
        "precios_usd_por_millon": {
            "entrada_sin_cache": ajustes.price_input_cache_miss,
            "entrada_con_cache": ajustes.price_input_cache_hit,
            "salida": ajustes.price_output,
        },
        "max_usd_por_run": ajustes.max_usd_per_run,
        "pasos": list(pasos),
        "brazos": {"rag": {"k": argumentos.k}, "wiki": {"max_acciones": argumentos.max_acciones}},
        "banco": {
            "ruta": str(argumentos.banco),
            "sha256": huella_archivo(argumentos.banco),
            "estado_minimo": argumentos.estado_minimo,
            "preguntas": [p["id"] for p in preguntas],
            "por_estado": conteo_por_estado(preguntas),
        },
        "valida_para_informe": valida,
        "estimacion_usd": round(total_estimado, 4),
    }


def _comprobar_reanudacion(previa: dict[str, Any], nueva: dict[str, Any]) -> None:
    for clave in ("pasos", "brazos", "modelo", "temperatura"):
        if previa.get(clave) != nueva.get(clave):
            raise ErrorDeCorrida(
                f"La corrida {nueva['corrida']} se hizo con otro valor de {clave!r}: "
                f"{previa.get(clave)} y ahora {nueva.get(clave)}. Usa otro nombre de corrida."
            )
    if previa["banco"]["sha256"] != nueva["banco"]["sha256"] or (
        previa["banco"]["preguntas"] != nueva["banco"]["preguntas"]
    ):
        raise ErrorDeCorrida(
            f"El banco o las preguntas cambiaron desde que empezó la corrida "
            f"{nueva['corrida']}. Usa otro nombre de corrida."
        )


def _comparar(
    argumentos: argparse.Namespace,
    ajustes: Settings,
    salida: Callable[[str], None],
    crear_brazos: Callable[[ClienteModelo, Settings, argparse.Namespace], list[Brazo]],
    crear_modelo: Callable[[Settings, Path], ClienteModelo],
    ahora: Callable[[], datetime],
) -> int:
    carpeta = argumentos.resultados / "demo"
    try:
        orden = leer_orden(argumentos.manifest)
        brazos = crear_brazos(
            crear_modelo(ajustes, carpeta / "llamadas.jsonl"), ajustes, argumentos
        )
        # el wiki ya construido fija el paso; el RAG se pone en el mismo estado
        paso = max(
            (len(b.ingeridos) for b in brazos if getattr(b, "ingeridos", None) is not None),
            default=0,
        )
        resultado = comparar(
            brazos,
            argumentos.pregunta,
            orden,
            paso,
            modelo=ajustes.model,
            ahora=ahora,
            avisar=salida,
        )
    except _errores_conocidos() as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    for linea in formatear(resultado, crear_resolutor(argumentos.gold, argumentos.spans)):
        salida(linea)
    registrar(carpeta / "comparaciones.jsonl", resultado)
    salida(f"Evidencia añadida a {carpeta / 'comparaciones.jsonl'}")
    return 0


def principal(
    argv: Sequence[str] | None = None,
    *,
    salida: Callable[[str], None] = print,
    crear_brazos: Callable[[ClienteModelo, Settings, argparse.Namespace], list[Brazo]] = (
        _crear_brazos_reales
    ),
    crear_modelo: Callable[[Settings, Path], ClienteModelo] = _crear_modelo,
    ahora: Callable[[], datetime] = _ahora,
) -> int:
    argumentos = _analizar(argv)
    ajustes = load_settings()
    if argumentos.orden == "comparar":
        return _comparar(argumentos, ajustes, salida, crear_brazos, crear_modelo, ahora)
    try:
        orden = leer_orden(argumentos.manifest)
        pasos = validar_pasos([int(p) for p in argumentos.pasos.split(",")], len(orden))
        preguntas = seleccionar(
            leer_banco(argumentos.banco),
            estado_minimo=argumentos.estado_minimo,
            tipos=_lista(argumentos.tipos),
            ids=_lista(argumentos.preguntas),
        )
    except (ErrorDeCorrida, ErrorDeSeleccion, FileNotFoundError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    valida = valida_para_informe(preguntas)
    estimacion = estimar(
        list(BRAZOS), preguntas=len(preguntas), pasos=len(pasos), papers=max(pasos)
    )
    salida(
        f"{len(preguntas)} preguntas × {len(pasos)} pasos × {len(BRAZOS)} brazos = "
        f"{estimacion.llamadas_de_pregunta * len(BRAZOS)} respuestas; {max(pasos)} papers por "
        f"ingerir. Estimado (cota alta): {estimacion.total:.2f} USD "
        f"({estimacion.usd_ingesta:.2f} de ingesta y {estimacion.usd_preguntas:.2f} de preguntas)."
    )
    aviso_pico = aviso_de_hora_pico(ahora())
    if aviso_pico:
        salida(f"Aviso: {aviso_pico}")
    if not valida:
        salida(
            "Aviso: hay preguntas que no están 'acordado'; esta corrida NO vale para el informe."
        )
    if argumentos.estimar:
        return 0
    try:
        exigir_confirmacion(estimacion, argumentos.confirmo_usd, LIMITE_SIN_CONFIRMAR_USD)
    except ExcesoDeCosto as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    carpeta = argumentos.resultados / argumentos.corrida
    inicio = ahora().strftime("%Y-%m-%dT%H:%M:%SZ")
    nuevos = _metadatos(argumentos, ajustes, pasos, preguntas, valida, estimacion.total, inicio)
    try:
        previa = leer_corrida(carpeta / CORRIDA)
        if previa is None:
            escribir_corrida(carpeta / CORRIDA, nuevos)
        else:
            _comprobar_reanudacion(previa, nuevos)
            actualizar_corrida(
                carpeta / CORRIDA, reanudaciones=[*previa.get("reanudaciones", []), inicio]
            )
            salida(f"Se reanuda la corrida {argumentos.corrida}.")
        modelo = crear_modelo(ajustes, carpeta / "llamadas.jsonl")
        brazos = crear_brazos(modelo, ajustes, argumentos)
        config = Configuracion(
            corrida=argumentos.corrida,
            carpeta=carpeta,
            pasos=pasos,
            orden=orden,
            preguntas=tuple(preguntas),
            modelo=ajustes.model,
            temperatura=ajustes.temperature,
        )
        ejecutar(brazos, config, ahora=ahora, salida=salida)
    except _errores_conocidos() as error:
        print(f"Error: {error}", file=sys.stderr)
        print(
            "Lo escrito se conserva. Para reanudar, repite la misma orden con la misma --corrida.",
            file=sys.stderr,
        )
        return 1

    filas = resumir(carpeta)
    actualizar_corrida(
        carpeta / CORRIDA,
        fin=ahora().strftime("%Y-%m-%dT%H:%M:%SZ"),
        gasto_usd=round(sum(f["usd_ingesta"] + f["usd_preguntas"] for f in filas), 6),
    )
    for linea in formatear_resumen(filas, argumentos.corrida):
        salida(linea)
    if not valida:
        salida("Recordatorio: esta corrida NO vale para el informe (hay preguntas sin acordar).")
    return 0


if __name__ == "__main__":
    raise SystemExit(principal())
