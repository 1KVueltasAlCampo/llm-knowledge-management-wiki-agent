"""Experimento exploratorio: ¿bajan los tokens de la consulta del wiki con tgrep o graphify?

Hace las mismas preguntas del banco al wiki con distintas herramientas de búsqueda y lectura y
mide, con el mismo modelo, las llamadas, los tokens y el costo, y si la respuesta sigue siendo
correcta. No cambia el código del proyecto: la variante ``actual`` ejecuta el ``ConsultaWiki``
real y las demás usan un agente con el mismo bucle y otras herramientas.

Variantes:
  actual    ConsultaWiki del proyecto: búsqueda léxica de resúmenes + lectura de páginas completas.
  generico  Mismas herramientas que ``actual`` en este agente (control de equivalencia).
  grep      Búsqueda de líneas por expresión regular (lo que devuelve tgrep) + lectura de páginas.
  secciones Búsqueda léxica + lectura de páginas o de una sola sección («slug#Sección»).
  esquema   Como secciones, pero la búsqueda lista los títulos de sección de cada página.
  graphify  Consulta al grafo de graphify (títulos y enlaces) + lectura por secciones.

Segunda ronda (``--variantes actual,generico,fragmentos,gist,vecinos``):
  fragmentos La búsqueda devuelve el párrafo más parecido a la consulta de cada página y cuenta
             como lectura: se puede responder sin abrir la página.
  gist       La búsqueda devuelve resumen + primer párrafo + enlaces (variante A3 de 2607.04576);
             la lectura previa a responder sigue siendo obligatoria.
  vecinos    Búsqueda léxica + herramienta ``links`` con las aristas ``references`` de graph.json.

Prueba con el binario real (``--variantes tgrep --tgrep <tgrep.exe> --tgrep-indice <carpeta>``):
  tgrep      tgrep v1.2.7 con índice en disco, ``-M 300 --max-columns-preview`` + lectura.
             El índice se crea antes con ``tgrep index . --index-path <carpeta> --no-require-git``.
  grep_recortado  Control: la búsqueda de Python de ``grep`` con las líneas recortadas a
             ``--tgrep-columnas`` caracteres, sin usar tgrep.

Uso (desde la raíz del repo; gasta centavos de saldo):
  uv run python scripts/comparar_herramientas.py --wiki data/wiki/prueba-herramientas \
      --grafo <graph.json> --graphify <graphify.exe> --repeticiones 2
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from wikillm.common.config import load_settings
from wikillm.common.modelo import ClienteModelo
from wikillm.common.responder import ResultadoBrazo, es_abstencion
from wikillm.common.respuesta import PATRON_SPAN_ID, REGLAS_DE_RESPUESTA, extraer_citas_leidas
from wikillm.eval.banco import leer_banco
from wikillm.eval.correctitud import clave_presente
from wikillm.ingest.gold import aproximar_tokens
from wikillm.wiki.almacen import Wiki
from wikillm.wiki.consulta import ConsultaWiki
from wikillm.wiki.herramientas import (
    MAXIMO_PAGINAS_POR_LECTURA,
    MAXIMO_RESULTADOS,
    palabras,
    texto_de_busqueda,
    wiki_read,
    wiki_search,
)
from wikillm.wiki.ingesta import ErrorDeFormato, extraer_json

PREGUNTAS = ("B001-T4-06", "A002-T1-02", "A003-T3-02", "B006-T1-01", "BT5-T5-07")
VARIANTES = ("actual", "generico", "grep", "secciones", "esquema", "graphify")
VARIANTES_NUEVAS = ("actual", "generico", "fragmentos", "gist", "vecinos")  # segunda ronda
MAXIMO_LINEAS_GREP = 10
MAX_TOKENS_TURNO = 2_000


# --- herramientas -----------------------------------------------------------------------------
@dataclass
class Herramienta:
    nombre: str
    argumento: str  # clave del JSON que lleva el argumento
    descripcion: str
    ejecutar: Callable[[Any], tuple[str, str, bool]]  # (texto para el modelo, resumen, vacío)
    es_lectura: bool = False


def _lista(valor: Any) -> list[str]:
    if isinstance(valor, str):
        return [valor]
    return [str(x) for x in valor] if isinstance(valor, list) else []


def herramienta_busqueda(wiki: Wiki) -> Herramienta:
    def ejecutar(consulta: Any) -> tuple[str, str, bool]:
        resultados = wiki_search(wiki, str(consulta))
        resumen = ", ".join(r.slug for r in resultados) or "no pages match"
        return texto_de_busqueda(resultados), resumen, not resultados

    return Herramienta(
        "search",
        "query",
        f'{{"action": "search", "query": "keywords"}} returns up to {MAXIMO_RESULTADOS} '
        "page summaries",
        ejecutar,
    )


def herramienta_lectura(wiki: Wiki) -> Herramienta:
    def ejecutar(paginas: Any) -> tuple[str, str, bool]:
        lectura = wiki_read(wiki, _lista(paginas))
        return lectura.texto, f"read: {', '.join(lectura.leidas) or 'none'}", False

    return Herramienta(
        "read",
        "pages",
        '{"action": "read", "pages": ["slug", ...]} returns the full text of up to '
        f'{MAXIMO_PAGINAS_POR_LECTURA} pages (the page "index" lists every page)',
        ejecutar,
        es_lectura=True,
    )


def _secciones(cuerpo: str) -> list[tuple[str, str]]:
    """Partes del cuerpo de una página: (encabezado, texto), la primera sin encabezado."""
    partes: list[tuple[str, list[str]]] = [("", [])]
    for linea in cuerpo.splitlines():
        coincide = re.match(r"^#{1,6}\s+(.*)$", linea)
        if coincide:
            partes.append((coincide.group(1).strip(), [linea]))
        else:
            partes[-1][1].append(linea)
    return [(titulo, "\n".join(lineas).strip()) for titulo, lineas in partes if "".join(lineas)]


def herramienta_lectura_por_secciones(wiki: Wiki) -> Herramienta:
    def ejecutar(elementos: Any) -> tuple[str, str, bool]:
        bloques: list[str] = []
        leidas: list[str] = []
        for elemento in _lista(elementos)[:MAXIMO_PAGINAS_POR_LECTURA]:
            slug, _, seccion = elemento.strip().strip("[]").partition("#")
            slug = re.sub(r"\.md$", "", re.sub(r"^pages/", "", slug.strip()))  # nombres del grafo
            if slug == "index":
                bloques.append(f"=== Page index ===\n{wiki.texto_del_indice().strip()}")
                leidas.append("index")
            elif not wiki.existe(slug):
                bloques.append(f"Not found: {slug}.")
            elif not seccion:
                bloques.append(f"=== Page {slug} ===\n{wiki.leer(slug).a_texto().strip()}")
                leidas.append(slug)
            else:
                partes = _secciones(wiki.leer(slug).cuerpo)
                clave = seccion.strip().casefold()
                elegidas = [t for titulo, t in partes if titulo.casefold() == clave] or [
                    t for titulo, t in partes if clave and clave in titulo.casefold()
                ]
                if elegidas:
                    bloques.append(f"=== Section {slug}#{seccion} ===\n" + "\n\n".join(elegidas))
                    leidas.append(f"{slug}#{seccion}")
                else:
                    titulos = ", ".join(t for t, _ in partes if t)
                    bloques.append(
                        f'Not found: section "{seccion}" of {slug}. Sections: {titulos}.'
                    )
        return (
            "\n\n".join(bloques) or "No pages requested.",
            f"read: {', '.join(leidas) or 'none'}",
            False,
        )

    return Herramienta(
        "read",
        "pages",
        '{"action": "read", "pages": ["slug", "slug#Section heading", ...]} returns the text of up '
        f"to {MAXIMO_PAGINAS_POR_LECTURA} items: a whole page, or only the section under a heading "
        '(for example "hipporag-neurobiologically-inspired-long-term-memory-for-lar#Setup")',
        ejecutar,
        es_lectura=True,
    )


def herramienta_busqueda_con_esquema(wiki: Wiki) -> Herramienta:
    """La búsqueda léxica de siempre, con los títulos de sección de cada página encontrada."""

    def ejecutar(consulta: Any) -> tuple[str, str, bool]:
        resultados = wiki_search(wiki, str(consulta))
        lineas = []
        for r in resultados:
            titulos = " | ".join(t for t, _ in _secciones(wiki.leer(r.slug).cuerpo) if t)
            lineas.append(r.a_texto() + (f"{chr(10)}    sections: {titulos}" if titulos else ""))
        texto = chr(10).join(lineas) or "No pages match this search."
        return texto, ", ".join(r.slug for r in resultados) or "no pages match", not resultados

    return Herramienta(
        "search",
        "query",
        f'{{"action": "search", "query": "keywords"}} returns up to {MAXIMO_RESULTADOS} page '
        "summaries, each with the headings of its sections",
        ejecutar,
    )


MAXIMO_FRAGMENTOS = 5
LARGO_FRAGMENTO = 700
LARGO_INICIO = 300


def _parrafos(cuerpo: str) -> list[tuple[str, str]]:
    """Párrafos del cuerpo como (encabezado vigente, texto), sin los encabezados sueltos."""
    encabezado = ""
    resultado: list[tuple[str, str]] = []
    for bloque in re.split(r"\n\s*\n", cuerpo):
        bloque = bloque.strip()
        coincide = re.match(r"^#{1,6}\s+(.*)$", bloque)
        if coincide and "\n" not in bloque:
            encabezado = coincide.group(1).strip()
        elif bloque:
            resultado.append((encabezado, bloque))
    return resultado


def _recortar(texto: str, largo: int) -> str:
    """Corta en el último cierre de cita o espacio antes de ``largo`` para no partir un span_id."""
    if len(texto) <= largo:
        return texto
    corte = texto.rfind("]", 0, largo)
    if corte < largo // 2:
        corte = texto.rfind(" ", 0, largo)
    return texto[: corte + 1].rstrip() + " …"


def _enlaces_de(cuerpo: str, propio: str, maximo: int = 5) -> list[str]:
    vistos = dict.fromkeys(s for s in re.findall(r"\[\[([^\]]+)\]\]", cuerpo) if s != propio)
    return list(vistos)[:maximo]


def herramienta_busqueda_con_fragmentos(wiki: Wiki) -> Herramienta:
    """Búsqueda léxica que devuelve el párrafo más parecido a la consulta de cada página."""

    def ejecutar(consulta: Any) -> tuple[str, str, bool]:
        resultados = wiki_search(wiki, str(consulta), maximo=MAXIMO_FRAGMENTOS)
        buscadas = set(palabras(str(consulta)))
        bloques = []
        for r in resultados:
            parrafos = _parrafos(wiki.leer(r.slug).cuerpo)
            mejor = max(parrafos, key=lambda p: len(buscadas & set(palabras(p[1]))), default=None)
            linea = r.a_texto()
            if mejor and buscadas & set(palabras(mejor[1])):
                encabezado = f"[{mejor[0]}] " if mejor[0] else ""
                linea += f"\n    passage: {encabezado}{_recortar(mejor[1], LARGO_FRAGMENTO)}"
            bloques.append(linea)
        texto = "\n".join(bloques) or "No pages match this search."
        return texto, ", ".join(r.slug for r in resultados) or "no pages match", not resultados

    return Herramienta(
        "search",
        "query",
        f'{{"action": "search", "query": "keywords"}} returns up to {MAXIMO_FRAGMENTOS} pages, '
        "each with its summary and the passage that best matches the query (with span ids); "
        "if the passages answer the question you can answer without reading the pages",
        ejecutar,
        es_lectura=True,
    )


def herramienta_busqueda_con_inicio_y_vecinos(wiki: Wiki) -> Herramienta:
    """El «gist» del estudio de progressive disclosure: resumen, primer párrafo y enlaces."""

    def ejecutar(consulta: Any) -> tuple[str, str, bool]:
        resultados = wiki_search(wiki, str(consulta))
        bloques = []
        for r in resultados:
            pagina = wiki.leer(r.slug)
            parrafos = _parrafos(pagina.cuerpo)
            linea = r.a_texto()
            if parrafos:
                linea += f"\n    lead: {_recortar(parrafos[0][1], LARGO_INICIO)}"
            enlaces = _enlaces_de(pagina.cuerpo, r.slug)
            if enlaces:
                linea += f"\n    links: {', '.join(enlaces)}"
            bloques.append(linea)
        texto = "\n".join(bloques) or "No pages match this search."
        return texto, ", ".join(r.slug for r in resultados) or "no pages match", not resultados

    return Herramienta(
        "search",
        "query",
        f'{{"action": "search", "query": "keywords"}} returns up to {MAXIMO_RESULTADOS} page '
        "summaries, each with the first paragraph of the page and the pages it links to",
        ejecutar,
    )


def herramienta_vecinos(wiki: Wiki, grafo: Path) -> Herramienta:
    """Vecinos de una página según las aristas ``references`` de graph.json (de graphify)."""
    datos = json.loads(grafo.read_text("utf-8"))
    archivo = {n["id"]: n.get("source_file", "") for n in datos["nodes"]}

    def _slug(identificador: str) -> str | None:
        coincide = re.match(r"^pages/(.+)\.md$", archivo.get(identificador, ""))
        return coincide.group(1) if coincide else None

    salientes: dict[str, list[str]] = {}
    entrantes: dict[str, list[str]] = {}
    for arista in datos["links"]:
        if arista.get("relation") != "references":
            continue
        origen, destino = _slug(arista["source"]), _slug(arista["target"])
        if origen and destino and origen != destino:
            if destino not in salientes.setdefault(origen, []):
                salientes[origen].append(destino)
            if origen not in entrantes.setdefault(destino, []):
                entrantes[destino].append(origen)

    def linea(slug: str) -> str:
        if not wiki.existe(slug):
            return f"- {slug}"
        pagina = wiki.leer(slug)
        return f"- {slug} [{pagina.tipo}] {pagina.titulo}: {pagina.resumen}"

    def ejecutar(pagina: Any) -> tuple[str, str, bool]:
        slug = re.sub(r"\.md$", "", re.sub(r"^pages/", "", str(pagina).strip().strip("[]")))
        if not wiki.existe(slug):
            return f"Not found: {slug}.", "not found", True
        salida = salientes.get(slug, [])[:8]
        entrada = entrantes.get(slug, [])[:8]
        partes = [f"Pages that {slug} links to:"] + [linea(s) for s in salida]
        partes += [f"Pages that link to {slug}:"] + [linea(s) for s in entrada]
        vacio = not salida and not entrada
        return "\n".join(partes), f"{len(salida)} out, {len(entrada)} in", vacio

    return Herramienta(
        "links",
        "page",
        '{"action": "links", "page": "slug"} returns the pages that page links to and the pages '
        "that link to it, each with its summary",
        ejecutar,
    )


def herramienta_grep(wiki: Wiki, columnas: int = 0) -> Herramienta:
    """Líneas que coinciden con una expresión regular, como las imprime tgrep -n.

    Con ``columnas`` > 0 recorta cada línea como ``-M N --max-columns-preview`` (control: separa
    el efecto del recorte del de usar tgrep).
    """

    def recortar(linea: str) -> str:
        if columnas and len(linea) > columnas:
            return linea[:columnas] + " [... omitted end of long line]"
        return linea

    def ejecutar(patron: Any) -> tuple[str, str, bool]:
        try:
            expresion = re.compile(str(patron), re.IGNORECASE)
        except re.error as error:
            return f"Invalid regular expression: {error}", "invalid pattern", True
        coincidencias: list[str] = []
        paginas: set[str] = set()
        total = 0
        for pagina in wiki.paginas():
            for numero, linea in enumerate(pagina.a_texto().splitlines(), start=1):
                if linea.strip() and expresion.search(linea):
                    total += 1
                    if len(coincidencias) < MAXIMO_LINEAS_GREP:
                        coincidencias.append(
                            f"pages/{pagina.slug}.md:{numero}:{recortar(linea.strip())}"
                        )
                        paginas.add(pagina.slug)
        if not total:
            return "No lines match this pattern.", "no lines match", True
        pie = (
            f"\n(showing {len(coincidencias)} of {total} matching lines)"
            if total > len(coincidencias)
            else ""
        )
        return "\n".join(coincidencias) + pie, f"{total} lines in {len(paginas)} pages", False

    return Herramienta(
        "grep",
        "pattern",
        f'{{"action": "grep", "pattern": "regex"}} returns up to {MAXIMO_LINEAS_GREP} matching '
        "lines as pages/<slug>.md:<line>:<text>, case-insensitive; use alternation such as "
        '"synonymy|threshold" and keep the pattern specific'
        + (f"; lines longer than {columnas} bytes are cut" if columnas else ""),
        ejecutar,
        es_lectura=True,
    )


def herramienta_tgrep(wiki_raiz: Path, tgrep: Path, indice: Path, columnas: int) -> Herramienta:
    """El binario real de tgrep (v1.2.7) con el índice en disco y sus líneas largas recortadas.

    Usa las opciones que recomienda su AGENTS.md para mantener la salida corta: ``-n -i`` y
    ``-M N --max-columns-preview``. tgrep no tiene tope global de resultados, así que se
    cortan las primeras ``MAXIMO_LINEAS_GREP`` líneas igual que en la variante ``grep``.
    """

    def ejecutar(patron: Any) -> tuple[str, str, bool]:
        orden = [str(tgrep), "-n", "-i", "--index-path", str(indice), "--no-require-git"]
        if columnas:
            orden += ["-M", str(columnas), "--max-columns-preview"]
        proceso = subprocess.run(
            [*orden, "--", str(patron), "pages"],
            cwd=wiki_raiz,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        if proceso.returncode == 2:
            return f"Invalid search: {proceso.stderr.strip()[:200]}", "invalid pattern", True
        lineas = [x.replace("\\", "/") for x in proceso.stdout.splitlines() if x.strip()]
        if not lineas:
            return "No lines match this pattern.", "no lines match", True
        pie = (
            f"\n(showing {MAXIMO_LINEAS_GREP} of {len(lineas)} matching lines)"
            if len(lineas) > MAXIMO_LINEAS_GREP
            else ""
        )
        texto = "\n".join(lineas[:MAXIMO_LINEAS_GREP]) + pie
        return texto, f"{len(lineas)} lines", False

    recorte = f"; lines longer than {columnas} bytes are cut" if columnas else ""
    return Herramienta(
        "grep",
        "pattern",
        f'{{"action": "grep", "pattern": "regex"}} returns up to {MAXIMO_LINEAS_GREP} matching '
        "lines as pages/<slug>.md:<line>:<text>, case-insensitive; use alternation such as "
        f'"synonymy|threshold" and keep the pattern specific{recorte}',
        ejecutar,
        es_lectura=True,
    )


def herramienta_grafo(
    grafo: Path, graphify: Path, presupuesto: int, profundidad: int
) -> Herramienta:
    def ejecutar(consulta: Any) -> tuple[str, str, bool]:
        proceso = subprocess.run(
            [
                str(graphify),
                "query",
                str(consulta),
                "--graph",
                str(grafo),
                "--budget",
                str(presupuesto),
                "--depth",
                str(profundidad),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
            env={**os.environ, "PYTHONUTF8": "1"},
        )
        texto = proceso.stdout.strip()
        nodos = len(re.findall(r"^NODE ", texto, re.MULTILINE))
        if proceso.returncode not in (0, 3) or not nodos:
            return (texto or proceso.stderr.strip() or "No node matches."), "no nodes", True
        return texto, f"{nodos} nodes", False

    return Herramienta(
        "graph",
        "query",
        '{"action": "graph", "query": "keywords"} returns the part of the wiki graph that matches: '
        "pages and their section headings (NODE lines with the page and line) and the links "
        "between pages, but not their text",
        ejecutar,
    )


# --- agente con herramientas intercambiables --------------------------------------------------
INTRODUCCION = (
    "You answer questions about a corpus of arXiv papers using a wiki of pages that summarize "
    "them. Each turn, reply with exactly one JSON object and nothing else, using one of these "
    "actions: "
)


class AgenteGenerico:
    """El bucle de ConsultaWiki (tope de acciones, paciencia, leer antes de responder)."""

    def __init__(
        self,
        modelo: ClienteModelo,
        herramientas: list[Herramienta],
        *,
        etiqueta: str,
        spans_validos: set[str] | None,
        max_acciones: int = 8,
        paciencia: int = 3,
    ) -> None:
        self._modelo = modelo
        self._herramientas = {h.nombre: h for h in herramientas}
        self._etiqueta = etiqueta
        self._spans = spans_validos
        self._max_acciones = max_acciones
        self._paciencia = paciencia
        acciones = "; ".join(h.descripcion for h in herramientas)
        self._sistema = (
            f"{INTRODUCCION}{acciones}; "
            '{"action": "answer", "answer": "your answer"} ends the task. Pages show span ids in '
            "square brackets and link to related pages with [[slug]]. Read the pages that bear on "
            "the question before you answer; search again with different keywords if nothing "
            "matches. The context is what the tools return. " + REGLAS_DE_RESPUESTA
        )

    def responder(self, pregunta: str) -> tuple[ResultadoBrazo, list[dict[str, Any]]]:
        inicio = time.perf_counter()
        mensajes = [
            {"role": "system", "content": self._sistema},
            {"role": "user", "content": f"Question: {pregunta}"},
        ]
        llamadas = []
        salidas: list[str] = []
        detalle: list[dict[str, Any]] = []
        leido: set[str] = set()
        acciones = vacias = 0
        final_pedido = fallo = False
        lecturas = 0
        while True:
            if not final_pedido and (acciones >= self._max_acciones or vacias >= self._paciencia):
                mensajes.append(
                    {
                        "role": "user",
                        "content": "The tool budget is used up, so no more tool actions are "
                        'available. Reply now with an "answer" action using only what you have '
                        "read; if it is not enough, answer with the required sentence.",
                    }
                )
                final_pedido = True
            llamada = self._modelo.generar(
                mensajes, etiqueta=self._etiqueta, max_tokens=MAX_TOKENS_TURNO
            )
            llamadas.append(llamada)
            try:
                datos = extraer_json(llamada.texto)
                accion = str(datos.get("action", "")).strip().lower()
                if final_pedido and accion != "answer":
                    raise ErrorDeFormato('No more tool actions are available: use "answer".')
                if accion != "answer" and accion not in self._herramientas:
                    raise ErrorDeFormato(
                        f'"action" must be one of: answer, {", ".join(self._herramientas)}.'
                    )
                herramienta = self._herramientas.get(accion)
                argumento = datos.get(herramienta.argumento) if herramienta else None
                if herramienta and not argumento:
                    raise ErrorDeFormato(
                        f'A "{accion}" action needs a non-empty "{herramienta.argumento}".'
                    )
                if accion == "answer" and not str(datos.get("answer", "")).strip():
                    raise ErrorDeFormato('An "answer" action needs a non-empty "answer".')
            except ErrorDeFormato as error:
                if fallo:
                    detalle.append({"accion": "formato", "resultado": str(error)})
                    return self._cerrar(llamada.texto, leido, llamadas, salidas, inicio), detalle
                fallo = True
                mensajes += [
                    {"role": "assistant", "content": llamada.texto},
                    {
                        "role": "user",
                        "content": f"That reply was not a valid action: {error} Reply with "
                        "exactly one JSON object.",
                    },
                ]
                continue
            fallo = False
            mensajes.append({"role": "assistant", "content": llamada.texto})
            if accion == "answer":
                if not lecturas and not final_pedido:
                    acciones += 1
                    detalle.append({"accion": "answer", "resultado": "rejected: read first"})
                    mensajes.append(
                        {"role": "user", "content": "Read at least one page before answering."}
                    )
                    continue
                detalle.append({"accion": "answer", "resultado": "final answer"})
                return self._cerrar(
                    str(datos["answer"]).strip(), leido, llamadas, salidas, inicio
                ), detalle
            acciones += 1
            assert herramienta is not None
            texto, resumen, vacio = herramienta.ejecutar(argumento)
            vacias = vacias + 1 if vacio else 0
            if herramienta.es_lectura and not vacio:
                lecturas += 1
            salidas.append(texto)
            leido.update(PATRON_SPAN_ID.findall(texto))
            detalle.append(
                {
                    "accion": accion,
                    "argumento": argumento,
                    "resultado": resumen,
                    "tokens_devueltos": aproximar_tokens(texto),
                }
            )
            restantes = max(self._max_acciones - acciones, 0)
            mensajes.append(
                {"role": "user", "content": f"{texto}\n\n(Tool actions left: {restantes}.)"}
            )

    def _cerrar(self, respuesta, leido, llamadas, salidas, inicio) -> ResultadoBrazo:  # type: ignore[no-untyped-def]
        return ResultadoBrazo.desde_llamadas(
            respuesta,
            extraer_citas_leidas(respuesta, leido, self._spans),
            llamadas,
            time.perf_counter() - inicio,
            contexto="\n\n".join(salidas),
        )


# --- ejecución --------------------------------------------------------------------------------
def claves_esperadas(pregunta: dict[str, Any], paso: int) -> list[str]:
    claves = list(pregunta.get("respuesta_clave") or [])
    for tramo in pregunta.get("respuesta_por_paso") or []:
        if paso >= tramo["desde"]:
            claves = list(tramo["respuesta_clave"])
    return claves


def es_correcta(pregunta: dict[str, Any], respuesta: str, paso: int) -> bool:
    if pregunta["tipo"] == "T5":
        return es_abstencion(respuesta)
    claves = claves_esperadas(pregunta, paso)
    return bool(claves) and all(clave_presente(c, respuesta) for c in claves)


def crear_agente(
    variante: str, modelo: ClienteModelo, wiki: Wiki, args: argparse.Namespace, spans: set[str]
):  # type: ignore[no-untyped-def]
    if variante == "actual":
        return ConsultaWiki(modelo, wiki, spans_validos=spans)
    # perezoso: cada variante solo construye lo que necesita (el grafo, el binario de tgrep...)
    herramientas = {
        "generico": lambda: [herramienta_busqueda(wiki), herramienta_lectura(wiki)],
        "grep": lambda: [herramienta_grep(wiki), herramienta_lectura(wiki)],
        "secciones": lambda: [herramienta_busqueda(wiki), herramienta_lectura_por_secciones(wiki)],
        "esquema": lambda: [
            herramienta_busqueda_con_esquema(wiki),
            herramienta_lectura_por_secciones(wiki),
        ],
        "graphify": lambda: [
            herramienta_grafo(
                args.grafo, args.graphify, args.presupuesto_grafo, args.profundidad_grafo
            ),
            herramienta_lectura_por_secciones(wiki),
        ],
        "grep_recortado": lambda: [
            herramienta_grep(wiki, args.tgrep_columnas),
            herramienta_lectura(wiki),
        ],
        "tgrep": lambda: [
            herramienta_tgrep(
                args.wiki.resolve(), args.tgrep, args.tgrep_indice, args.tgrep_columnas
            ),
            herramienta_lectura(wiki),
        ],
        "fragmentos": lambda: [
            herramienta_busqueda_con_fragmentos(wiki),
            herramienta_lectura(wiki),
        ],
        "gist": lambda: [
            herramienta_busqueda_con_inicio_y_vecinos(wiki),
            herramienta_lectura(wiki),
        ],
        "vecinos": lambda: [
            herramienta_busqueda(wiki),
            herramienta_vecinos(wiki, args.grafo),
            herramienta_lectura(wiki),
        ],
    }[variante]()
    return AgenteGenerico(modelo, herramientas, etiqueta=variante, spans_validos=spans)


def una_corrida(
    variante: str,
    pregunta: dict[str, Any],
    repeticion: int,
    args: argparse.Namespace,
    spans: set[str],
) -> dict[str, Any]:
    wiki = Wiki(args.wiki)
    modelo = ClienteModelo(load_settings(), ruta_registro=args.salida / "llamadas.jsonl")
    agente = crear_agente(variante, modelo, wiki, args, spans)
    detalle: list[dict[str, Any]] = []
    try:
        if variante == "actual":
            resultado = agente.responder(pregunta["texto"])
            detalle = list(agente.traza.detalle)
        else:
            resultado, detalle = agente.responder(pregunta["texto"])
    except Exception as error:  # noqa: BLE001 - se registra y se sigue con la siguiente
        return {
            "variante": variante,
            "pregunta": pregunta["id"],
            "repeticion": repeticion,
            "error": str(error),
        }
    paso = len(wiki.ingeridos)
    return {
        "variante": variante,
        "pregunta": pregunta["id"],
        "tipo": pregunta["tipo"],
        "repeticion": repeticion,
        "correcta": es_correcta(pregunta, resultado.respuesta, paso),
        "abstuvo": resultado.abstuvo,
        "respuesta": resultado.respuesta,
        "citas": list(resultado.citas),
        "llamadas": resultado.llamadas,
        "tokens_entrada": resultado.tokens_entrada,
        "tokens_contexto": resultado.tokens_contexto,
        "tokens_salida": resultado.tokens_salida,
        "usd": resultado.usd,
        "segundos": round(resultado.segundos, 2),
        "pasos": detalle,
    }


def resumir(filas: list[dict[str, Any]]) -> list[dict[str, Any]]:
    resumen = []
    for variante in dict.fromkeys(f["variante"] for f in filas):
        ok = [f for f in filas if f["variante"] == variante and "error" not in f]
        if not ok:
            continue
        n = len(ok)
        resumen.append(
            {
                "variante": variante,
                "n": n,
                "correctas": sum(f["correcta"] for f in ok),
                "llamadas": round(sum(f["llamadas"] for f in ok) / n, 2),
                "tokens_entrada": round(sum(f["tokens_entrada"] for f in ok) / n),
                "tokens_contexto": round(sum(f["tokens_contexto"] for f in ok) / n),
                "tokens_salida": round(sum(f["tokens_salida"] for f in ok) / n),
                "usd": round(sum(f["usd"] for f in ok) / n, 6),
                "segundos": round(sum(f["segundos"] for f in ok) / n, 1),
            }
        )
    return resumen


def main() -> int:
    analizador = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter
    )
    analizador.add_argument("--wiki", type=Path, default=Path("data/wiki/prueba-herramientas"))
    analizador.add_argument("--banco", type=Path, default=Path("data/preguntas/banco.jsonl"))
    analizador.add_argument("--spans", type=Path, default=Path("data/gold/spans.jsonl"))
    analizador.add_argument("--salida", type=Path, default=Path("results/herramientas"))
    analizador.add_argument("--grafo", type=Path)
    analizador.add_argument("--graphify", type=Path)
    analizador.add_argument("--tgrep", type=Path, help="tgrep.exe real (variante tgrep)")
    analizador.add_argument("--tgrep-indice", type=Path, help="carpeta del índice de tgrep")
    analizador.add_argument("--tgrep-columnas", type=int, default=300)
    analizador.add_argument("--presupuesto-grafo", type=int, default=800)
    analizador.add_argument("--profundidad-grafo", type=int, default=1)
    analizador.add_argument("--preguntas", default=",".join(PREGUNTAS))
    analizador.add_argument("--variantes", default=",".join(VARIANTES))
    analizador.add_argument("--repeticiones", type=int, default=1)
    analizador.add_argument("--hilos", type=int, default=4)
    args = analizador.parse_args()

    variantes = [v for v in args.variantes.split(",") if v]
    if "graphify" in variantes and not (args.grafo and args.graphify):
        print("La variante graphify necesita --grafo y --graphify", file=sys.stderr)
        return 1
    if "tgrep" in variantes and not (args.tgrep and args.tgrep_indice):
        print("La variante tgrep necesita --tgrep y --tgrep-indice", file=sys.stderr)
        return 1
    if "vecinos" in variantes and not args.grafo:
        print("La variante vecinos necesita --grafo", file=sys.stderr)
        return 1
    banco = {p["id"]: p for p in leer_banco(args.banco)}
    preguntas = [banco[i] for i in args.preguntas.split(",") if i]
    spans = {
        json.loads(x)["span_id"] for x in args.spans.read_text("utf-8").splitlines() if x.strip()
    }
    args.salida.mkdir(parents=True, exist_ok=True)
    trabajos = [
        (v, p, r) for r in range(1, args.repeticiones + 1) for p in preguntas for v in variantes
    ]
    papers = len(Wiki(args.wiki).ingeridos)
    print(
        f"{len(trabajos)} corridas ({len(variantes)} variantes × {len(preguntas)} preguntas × "
        f"{args.repeticiones}); wiki con {papers} papers"
    )
    with ThreadPoolExecutor(max_workers=args.hilos) as pool:
        filas = list(pool.map(lambda t: una_corrida(t[0], t[1], t[2], args, spans), trabajos))
    destino = args.salida / "corridas.jsonl"
    destino.write_text(
        "\n".join(json.dumps(f, ensure_ascii=False) for f in filas) + "\n", encoding="utf-8"
    )
    resumen = resumir(filas)
    (args.salida / "resumen.json").write_text(
        json.dumps(resumen, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    print(
        f"{'variante':<10}{'n':>3}{'ok':>4}{'llam.':>7}{'t.entrada':>11}{'t.contexto':>12}{'t.salida':>10}{'USD':>10}{'s':>7}"
    )
    for f in resumen:
        print(
            f"{f['variante']:<10}{f['n']:>3}{f['correctas']:>4}{f['llamadas']:>7}{f['tokens_entrada']:>11}{f['tokens_contexto']:>12}{f['tokens_salida']:>10}{f['usd']:>10.6f}{f['segundos']:>7}"
        )
    errores = [f for f in filas if "error" in f]
    for e in errores:
        print("ERROR", e["variante"], e["pregunta"], e["error"][:200])
    print(f"Detalle en {destino}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
