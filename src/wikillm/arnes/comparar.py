"""Comparación puntual: una pregunta a los dos sistemas, con citas, traza del agente y costo.

La corrida del arnés responde un banco entero; esta orden responde **una** pregunta y deja ver lo
que cada sistema hace. Sirve para inspeccionar un caso, depurar el agente y demostrar el sistema.
El paso de ingesta lo fija el wiki indicado: el RAG se pone en el mismo estado y se comprueba que
ambos tienen exactamente los primeros N papers del manifest antes de preguntar.
"""

from __future__ import annotations

import textwrap
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from wikillm.arnes.corrida import ErrorDeCorrida, comprobar_estado
from wikillm.arnes.registro import anexar_linea, leer_lineas
from wikillm.common.responder import Brazo, ResultadoBrazo
from wikillm.corpus.spans import SpanInvalido, resolver
from wikillm.ingest.gold import leer_gold

LARGO_FRAGMENTO = 230
ANCHO = 98
NOMBRES = {"rag": "RAG simple", "wiki": "WikiLLM"}
DESCRIPCIONES = {
    "rag": "recupera los fragmentos más cercanos a la pregunta y responde en una sola llamada",
    "wiki": "un agente busca y lee páginas del wiki, y después responde",
}
VERBOS = {"search": "buscó", "read": "leyó", "answer": "respondió"}

Resolutor = Callable[[str], str | None]


@dataclass(frozen=True)
class RespuestaDeBrazo:
    sistema: str
    resultado: ResultadoBrazo
    traza: dict[str, Any] | None


@dataclass(frozen=True)
class Comparacion:
    pregunta: str
    paso: int
    modelo: str
    momento: str
    respuestas: tuple[RespuestaDeBrazo, ...]


def comparar(
    brazos: Sequence[Brazo],
    pregunta: str,
    orden: Sequence[str],
    paso: int,
    *,
    modelo: str,
    ahora: Callable[[], datetime] = lambda: datetime.now(UTC),
    avisar: Callable[[str], None] = lambda _: None,
) -> Comparacion:
    """Pone los brazos en el paso ``paso``, comprueba su estado y les hace la misma pregunta."""
    if not 0 <= paso <= len(orden):
        raise ErrorDeCorrida(f"El paso {paso} no está entre 0 y {len(orden)} papers")
    esperados = list(orden[:paso])
    for brazo in brazos:
        avisar(f"Poniendo el brazo {brazo.nombre} en el paso {paso}…")
        for arxiv_id in esperados:
            brazo.ingerir(arxiv_id)  # idempotente: lo ya ingerido no cuesta nada
    comprobar_estado(brazos, esperados, paso)
    respuestas = []
    for brazo in brazos:
        avisar(f"Preguntando al brazo {brazo.nombre}…")
        resultado = brazo.responder(pregunta)
        traza = getattr(brazo, "traza", None)
        respuestas.append(
            RespuestaDeBrazo(brazo.nombre, resultado, traza() if callable(traza) else None)
        )
    return Comparacion(
        pregunta=pregunta,
        paso=paso,
        modelo=modelo,
        momento=ahora().strftime("%Y-%m-%dT%H:%M:%SZ"),
        respuestas=tuple(respuestas),
    )


def crear_resolutor(carpeta_gold: Path, ruta_spans: Path) -> Resolutor:
    """Texto del fragmento de un ``span_id``, comprobando su huella; None si no se puede."""
    if not ruta_spans.exists():
        return lambda _: None
    spans = {fila["span_id"]: fila for fila in leer_lineas(ruta_spans)}
    cuerpos: dict[str, str] = {}

    def resolutor(span_id: str) -> str | None:
        fila = spans.get(span_id)
        if fila is None:
            return None
        arxiv_id = fila["arxiv_id"]
        if arxiv_id not in cuerpos:
            ruta = carpeta_gold / f"{arxiv_id}.md"
            if not ruta.exists():
                return None
            cuerpos[arxiv_id] = leer_gold(ruta)[1]
        try:
            return resolver(fila, cuerpos[arxiv_id])
        except SpanInvalido:
            return None

    return resolutor


def _envolver(texto: str, sangria: str = "  ") -> list[str]:
    return textwrap.wrap(
        " ".join(texto.split()), width=ANCHO, initial_indent=sangria, subsequent_indent=sangria
    ) or [sangria]


def _recortar(texto: str, largo: int) -> str:
    plano = " ".join(texto.split())
    return plano if len(plano) <= largo else plano[: largo - 1].rstrip() + "…"


def _paso_del_agente(numero: int, paso: dict[str, Any]) -> str:
    argumento = paso.get("argumento")
    if isinstance(argumento, list):
        argumento = ", ".join(argumento)
    verbo = VERBOS.get(paso["accion"], paso["accion"])
    cabeza = f"{numero}. {verbo}" + (f" «{argumento}»" if argumento else "")
    resultado = paso.get("resultado")
    return _recortar(f"{cabeza} → {resultado}" if resultado else cabeza, ANCHO - 4)


def _bloque(r: RespuestaDeBrazo, resolutor: Resolutor) -> list[str]:
    res = r.resultado
    lineas = [
        "",
        f"▌ {NOMBRES.get(r.sistema, r.sistema)}  ({DESCRIPCIONES.get(r.sistema, '')})",
    ]
    detalle = (r.traza or {}).get("detalle") or []
    if detalle:
        lineas.append("  Qué hizo el agente:")
        lineas += [f"    {_paso_del_agente(i, p)}" for i, p in enumerate(detalle, start=1)]
    for incidencia in (r.traza or {}).get("incidencias") or []:
        lineas.append(f"  Incidencia: {incidencia}")
    lineas.append("  Respuesta:")
    lineas += _envolver(res.respuesta, "    ")
    if res.abstuvo:
        lineas.append("  Se abstuvo: declara que el corpus ingerido no tiene la información.")
    elif res.citas:
        lineas.append(f"  Citas ({len(res.citas)}), con el fragmento del corpus que las respalda:")
        for cita in res.citas:
            fragmento = resolutor(cita)
            texto = _recortar(fragmento, LARGO_FRAGMENTO) if fragmento else "(no disponible)"
            lineas += _envolver(f"[{cita}] «{texto}»", "    ")
    else:
        lineas.append("  Sin citas.")
    lineas.append(
        f"  Costo: {res.llamadas} llamada(s) · {res.tokens_entrada} tokens de entrada "
        f"({res.tokens_contexto} de contexto) · {res.tokens_salida} de salida · "
        f"{res.segundos:.1f} s · {res.usd:.6f} USD"
    )
    return lineas


def formatear(c: Comparacion, resolutor: Resolutor) -> list[str]:
    raya = "=" * ANCHO
    pregunta = textwrap.wrap(
        " ".join(c.pregunta.split()),
        width=ANCHO,
        initial_indent="PREGUNTA  ",
        subsequent_indent=" " * 10,
    )
    lineas = [raya, *pregunta, ""]
    lineas.append(f"CORPUS    {c.paso} papers ingeridos (paso {c.paso}) · mismo modelo: {c.modelo}")
    lineas.append(raya)
    for r in c.respuestas:
        lineas += _bloque(r, resolutor)
    lineas += ["", raya, "COMPARACIÓN"]
    lineas.append(
        f"  {'sistema':<12}{'abstención':<12}{'citas':>6}{'llamadas':>10}"
        f"{'t. entrada':>12}{'t. contexto':>13}{'segundos':>10}{'USD':>11}"
    )
    for r in c.respuestas:
        x = r.resultado
        lineas.append(
            f"  {NOMBRES.get(r.sistema, r.sistema):<12}{'sí' if x.abstuvo else 'no':<12}"
            f"{len(x.citas):>6}{x.llamadas:>10}{x.tokens_entrada:>12}{x.tokens_contexto:>13}"
            f"{x.segundos:>10.1f}{x.usd:>11.6f}"
        )
    lineas.append(raya)
    return lineas


def a_linea(c: Comparacion) -> dict[str, Any]:
    """Línea de evidencia: sin el texto de los fragmentos, solo sus identificadores."""
    return {
        "timestamp": c.momento,
        "modelo": c.modelo,
        "pregunta": c.pregunta,
        "paso": c.paso,
        "sistemas": [
            {
                "sistema": r.sistema,
                "respuesta": r.resultado.respuesta,
                "abstuvo": r.resultado.abstuvo,
                "citas": list(r.resultado.citas),
                "llamadas": r.resultado.llamadas,
                "tokens_entrada": r.resultado.tokens_entrada,
                "tokens_contexto": r.resultado.tokens_contexto,
                "tokens_salida": r.resultado.tokens_salida,
                "segundos": round(r.resultado.segundos, 3),
                "usd": r.resultado.usd,
                "traza": r.traza,
            }
            for r in c.respuestas
        ],
    }


def registrar(ruta: Path, c: Comparacion) -> None:
    anexar_linea(ruta, a_linea(c))
