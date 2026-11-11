"""Consulta del wiki como agente: busca páginas, las lee y responde con citas de lo leído.

El agente pide una acción JSON por turno (`search`, `read` o `answer`) y el código le devuelve el
resultado de la herramienta. Se usa el cliente único del modelo, sin llamadas nativas a
herramientas, para conservar el registro, el costo y el tope de gasto de cada llamada. El bucle
tiene tres frenos: un tope de acciones, una paciencia ante búsquedas vacías y la obligación de
leer al menos una página antes de responder.
"""

from __future__ import annotations

import time
from collections.abc import Callable, Collection, Mapping
from dataclasses import dataclass, field
from typing import Any

from wikillm.common.modelo import ClienteModelo, Respuesta
from wikillm.common.responder import ResultadoBrazo
from wikillm.common.respuesta import PATRON_SPAN_ID, REGLAS_DE_RESPUESTA, extraer_citas_leidas
from wikillm.wiki.almacen import Wiki
from wikillm.wiki.capas import AVISO_LEER_PRIMERO, CapasDeConsulta, leer_por_secciones, nombres_de
from wikillm.wiki.herramientas import (
    MAXIMO_PAGINAS_POR_LECTURA,
    MAXIMO_RESULTADOS,
    Lectura,
    texto_de_busqueda,
    wiki_read,
    wiki_search,
)
from wikillm.wiki.ingesta import ErrorDeFormato, extraer_json

MAX_ACCIONES_POR_DEFECTO = 8
PACIENCIA_POR_DEFECTO = 3
MAX_TOKENS_TURNO = 2_000
SIN_PAGINAS = "(no pages)"

PROTOCOLO = (
    "You answer questions about a corpus of arXiv papers using a wiki of pages that summarize "
    "them. Each turn, reply with exactly one JSON object and nothing else, using one of these "
    f'actions: {{"action": "search", "query": "keywords"}} returns up to {MAXIMO_RESULTADOS} '
    'page summaries; {"action": "read", "pages": ["slug", ...]} returns the full text of up to '
    f'{MAXIMO_PAGINAS_POR_LECTURA} pages (the page "index" lists every page); '
    '{"action": "answer", "answer": "your answer"} ends the task. Pages show span ids in square '
    "brackets and link to related pages with [[slug]]. Read the pages that bear on the "
    "question before you answer; search again with different keywords if nothing matches. "
    "The context is what the tools return. "
)
INSTRUCCIONES_AGENTE = PROTOCOLO + REGLAS_DE_RESPUESTA
INSTRUCCIONES_SIN_HERRAMIENTAS = (
    "You answer questions about a corpus of arXiv papers using ONLY the context given below. "
    + REGLAS_DE_RESPUESTA
)


@dataclass
class Traza:
    """Qué hizo el agente en la última pregunta, para el informe (no forma parte del contrato)."""

    acciones: int = 0
    busquedas: int = 0
    lecturas: int = 0
    paginas_leidas: list[str] = field(default_factory=list)
    incidencias: list[str] = field(default_factory=list)
    # Una entrada por acción, en orden: {"accion", "argumento", "resultado"}.
    detalle: list[dict[str, Any]] = field(default_factory=list)


def resumen_de_lectura(lectura: Lectura) -> str:
    partes = [f"read: {', '.join(lectura.leidas) or 'none'}"]
    if lectura.no_encontradas:
        partes.append(f"not found: {', '.join(lectura.no_encontradas)}")
    if lectura.no_leidas:
        partes.append(f"not read (limit): {', '.join(lectura.no_leidas)}")
    return "; ".join(partes)


def analizar_accion(texto: str, extras: Mapping[str, str] | None = None) -> tuple[str, Any]:
    """(acción, argumento) de una salida del agente; ErrorDeFormato si no es una acción válida.

    ``extras`` (acción → clave del argumento) activa el modo con capas: se aceptan esas acciones
    además de ``read`` y ``answer``, y ``search`` deja de estar disponible.
    """
    datos = extraer_json(texto)
    accion = str(datos.get("action", "")).strip().lower()
    if extras is not None:
        if accion in extras:
            argumento = str(datos.get(extras[accion], "")).strip()
            if not argumento:
                raise ErrorDeFormato(f'A "{accion}" action needs a non-empty "{extras[accion]}".')
            return accion, argumento
        if accion == "search":
            raise ErrorDeFormato(f'"action" must be one of: answer, {", ".join(extras)}, read.')
    if accion == "search":
        consulta = str(datos.get("query", "")).strip()
        if not consulta:
            raise ErrorDeFormato('A "search" action needs a non-empty "query".')
        return accion, consulta
    if accion == "read":
        paginas = datos.get("pages", datos.get("page"))
        if isinstance(paginas, str):
            paginas = [paginas]
        if not isinstance(paginas, list) or not paginas:
            raise ErrorDeFormato('A "read" action needs a non-empty "pages" list.')
        return accion, [str(p) for p in paginas]
    if accion == "answer":
        respuesta = str(datos.get("answer", "")).strip()
        if not respuesta:
            raise ErrorDeFormato('An "answer" action needs a non-empty "answer".')
        return accion, respuesta
    raise ErrorDeFormato('"action" must be "search", "read" or "answer".')


class ConsultaWiki:
    def __init__(
        self,
        modelo: ClienteModelo,
        wiki: Wiki,
        *,
        max_acciones: int = MAX_ACCIONES_POR_DEFECTO,
        paciencia: int = PACIENCIA_POR_DEFECTO,
        spans_validos: Collection[str] | None = None,
        reloj: Callable[[], float] = time.perf_counter,
        capas: CapasDeConsulta | None = None,
    ) -> None:
        self._modelo = modelo
        self._wiki = wiki
        # Sin capas, el protocolo y las herramientas son los del WikiLLM base, sin cambios.
        self._capas = capas
        self._extras = {h.nombre: h for h in capas.herramientas} if capas else {}
        self._instrucciones = capas.instrucciones() if capas else INSTRUCCIONES_AGENTE
        self._max_acciones = max_acciones
        self._paciencia = paciencia
        self._spans_validos = spans_validos
        self._reloj = reloj
        self.traza = Traza()

    def responder(self, pregunta: str) -> ResultadoBrazo:
        inicio = self._reloj()
        self.traza = Traza()
        if not self._wiki.slugs():
            return self._sin_paginas(pregunta, inicio)

        mensajes = [
            {"role": "system", "content": self._instrucciones},
            {"role": "user", "content": f"Question: {pregunta}"},
        ]
        llamadas: list[Respuesta] = []
        salidas: list[str] = []  # lo que devolvieron las herramientas
        leido: set[str] = set()  # span_id que aparecen en lo que devolvieron
        vacias = 0
        final_pedido = False
        fallo_en_turno = False

        while True:
            if not final_pedido and (
                self.traza.acciones >= self._max_acciones or vacias >= self._paciencia
            ):
                mensajes.append({"role": "user", "content": self._aviso_de_cierre(vacias)})
                final_pedido = True
            llamada = self._modelo.generar(mensajes, etiqueta="wiki", max_tokens=MAX_TOKENS_TURNO)
            llamadas.append(llamada)
            try:
                accion, argumento = analizar_accion(
                    llamada.texto, nombres_de(self._capas.herramientas) if self._capas else None
                )
                if final_pedido and accion != "answer":
                    raise ErrorDeFormato('No more tool actions are available: use "answer".')
            except ErrorDeFormato as error:
                if fallo_en_turno:
                    self.traza.incidencias.append(f"unparseable action, text taken: {error}")
                    return self._resultado(llamada.texto, leido, llamadas, salidas, inicio)
                fallo_en_turno = True
                mensajes += [
                    {"role": "assistant", "content": llamada.texto},
                    {
                        "role": "user",
                        "content": f"That reply was not a valid action: {error} Reply with "
                        "exactly one JSON object.",
                    },
                ]
                continue
            fallo_en_turno = False
            mensajes.append({"role": "assistant", "content": llamada.texto})

            if accion == "answer":
                if not self.traza.paginas_leidas and not final_pedido:
                    self.traza.acciones += 1  # asegura que el bucle termina
                    self.traza.detalle.append(
                        {"accion": "answer", "argumento": "", "resultado": "rejected: read first"}
                    )
                    mensajes.append(
                        {"role": "user", "content": "Read at least one page before answering."}
                    )
                    continue
                self.traza.detalle.append(
                    {"accion": "answer", "argumento": "", "resultado": "final answer"}
                )
                return self._resultado(argumento, leido, llamadas, salidas, inicio)

            self.traza.acciones += 1
            if accion in self._extras:
                herramienta = self._extras[accion]
                if herramienta.requiere_lectura and not self.traza.paginas_leidas:
                    texto, resumen = AVISO_LEER_PRIMERO, "rejected: read first"
                else:
                    texto, resumen = herramienta.ejecutar(argumento)
                self.traza.detalle.append(
                    {"accion": accion, "argumento": argumento, "resultado": resumen}
                )
            elif accion == "search":
                self.traza.busquedas += 1
                resultados = wiki_search(self._wiki, argumento)
                vacias = 0 if resultados else vacias + 1
                texto = texto_de_busqueda(resultados)
                self.traza.detalle.append(
                    {
                        "accion": "search",
                        "argumento": argumento,
                        "resultado": ", ".join(r.slug for r in resultados) or "no pages match",
                    }
                )
            else:
                self.traza.lecturas += 1
                lectura = (
                    leer_por_secciones(self._wiki, argumento)
                    if self._capas
                    else wiki_read(self._wiki, argumento)
                )
                self.traza.paginas_leidas += [
                    s for s in lectura.leidas if s not in self.traza.paginas_leidas
                ]
                texto = lectura.texto
                self.traza.detalle.append(
                    {
                        "accion": "read",
                        "argumento": list(argumento),
                        "resultado": resumen_de_lectura(lectura),
                    }
                )
            salidas.append(texto)
            leido.update(PATRON_SPAN_ID.findall(texto))
            restantes = max(self._max_acciones - self.traza.acciones, 0)
            mensajes.append(
                {"role": "user", "content": f"{texto}\n\n(Tool actions left: {restantes}.)"}
            )

    def _aviso_de_cierre(self, vacias: int) -> str:
        motivo = (
            "Several searches found nothing" if vacias >= self._paciencia else "The tool budget"
        )
        return (
            f"{motivo} is used up, so no more tool actions are available. Reply now with an "
            '"answer" action using only what you have read; if it is not enough, answer with '
            "the required sentence."
        )

    def _resultado(
        self,
        respuesta: str,
        leido: Collection[str],
        llamadas: list[Respuesta],
        salidas: list[str],
        inicio: float,
    ) -> ResultadoBrazo:
        return ResultadoBrazo.desde_llamadas(
            respuesta,
            extraer_citas_leidas(respuesta, leido, self._spans_validos),
            llamadas,
            self._reloj() - inicio,
            contexto="\n\n".join(salidas),
        )

    def _sin_paginas(self, pregunta: str, inicio: float) -> ResultadoBrazo:
        mensajes = [
            {"role": "system", "content": INSTRUCCIONES_SIN_HERRAMIENTAS},
            {"role": "user", "content": f"Context:\n\n{SIN_PAGINAS}\n\nQuestion: {pregunta}"},
        ]
        llamada = self._modelo.generar(mensajes, etiqueta="wiki", max_tokens=MAX_TOKENS_TURNO)
        return ResultadoBrazo.desde_llamadas(
            llamada.texto, [], [llamada], self._reloj() - inicio, contexto=SIN_PAGINAS
        )
