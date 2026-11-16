"""Capas opcionales de consulta del wiki: un grafo de navegación (graphify) y tgrep.

Son una opción apagada por defecto. El WikiLLM base sigue consultando con `search` y `read`; solo
el brazo adicional que pide quien lanza la corrida usa estas capas (ver `BrazoWikiCapas`). Ambas
herramientas son programas externos, no dependencias de Python: se invocan como procesos.

- **Grafo (graphify).** Se construye de forma determinista, sin llamar a ningún modelo, a partir de
  los `.md` que ya escribió el WikiLLM (archivos, títulos y enlaces `[[slug]]`). Devuelve nombres
  de páginas y secciones, no texto: el agente lee después. Se reconstruye solo cuando el wiki
  cambia de paso, así que no obliga a reingerir nada.
- **tgrep (Microsoft).** `grep` con índice. Va como herramienta opcional del agente: no cuenta
  como lectura, devuelve pocas líneas recortadas y solo está disponible tras leer una página.

Sus resultados de evaluación están en `docs/evaluacion-tgrep-graphify.md`: el grafo ayudó en
preguntas que combinan varios papers; tgrep no redujo el costo. Se conserva aquí para poder
reproducir y justificar esa comparación, no porque se recomiende para el wiki base.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from wikillm.common.respuesta import REGLAS_DE_RESPUESTA
from wikillm.wiki.almacen import Wiki
from wikillm.wiki.herramientas import MAXIMO_PAGINAS_POR_LECTURA, PAGINA_INDICE, Lectura

PRESUPUESTO_GRAFO = 800  # tokens aproximados que devuelve una consulta al grafo
PROFUNDIDAD_GRAFO = 1
COLUMNAS_TGREP = 300  # las líneas más largas se cortan (el wiki guarda un párrafo por línea)
MAXIMO_LINEAS_TGREP = 3
NOMBRE_GRAFO = "wiki_grafo"
NOMBRE_GRAFO_TGREP = "wiki_grafo_tgrep"

INTRODUCCION = (
    "You answer questions about a corpus of arXiv papers using a wiki of pages that summarize "
    "them. Each turn, reply with exactly one JSON object and nothing else, using one of these "
    "actions: "
)
DESCRIPCION_LECTURA = (
    '{"action": "read", "pages": ["slug", "slug#Section heading", ...]} returns the text of up '
    f"to {MAXIMO_PAGINAS_POR_LECTURA} items: a whole page, or only the section under a heading "
    '(for example "hipporag-neurobiologically-inspired-long-term-memory-for-lar#Setup")'
)
DESCRIPCION_GRAFO = (
    '{"action": "graph", "query": "keywords"} returns the part of the wiki graph that matches: '
    "pages and their section headings (NODE lines with the page and line) and the links "
    "between pages, but not their text"
)
DESCRIPCION_TGREP = (
    '{"action": "grep", "pattern": "regex"} OPTIONAL and rarely needed: prints a few matching '
    "lines as pages/<slug>.md:<line>:<text>. Use it only to check an exact number, name or "
    "term that the pages you got from graph or read did not show. It does not replace read"
)
AVISO_LEER_PRIMERO = "Use the read action first; grep is only for checking details."


class ErrorDeCapa(RuntimeError):
    """Una herramienta externa falló o no está disponible: se detiene con un mensaje claro."""


@dataclass(frozen=True)
class HerramientaExtra:
    nombre: str  # valor de "action" en el JSON del agente
    argumento: str  # clave del JSON que lleva el argumento
    descripcion: str  # texto que se añade al protocolo del agente
    ejecutar: Callable[[str], tuple[str, str]]  # (texto para el modelo, resumen para la traza)
    requiere_lectura: bool = False  # solo disponible tras leer al menos una página


@dataclass(frozen=True)
class CapasDeConsulta:
    """Herramientas del brazo adicional: sustituyen a `search` y leen también por sección."""

    herramientas: tuple[HerramientaExtra, ...]

    def instrucciones(self) -> str:
        descripciones = [h.descripcion for h in self.herramientas] + [DESCRIPCION_LECTURA]
        return (
            f"{INTRODUCCION}{'; '.join(descripciones)}; "
            '{"action": "answer", "answer": "your answer"} ends the task. Pages show span ids in '
            "square brackets and link to related pages with [[slug]]. Read the pages that bear on "
            "the question before you answer; search again with different keywords if nothing "
            "matches. The context is what the tools return. " + REGLAS_DE_RESPUESTA
        )


# --- lectura por secciones (la usa el brazo con capas) ----------------------------------------
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


def leer_por_secciones(
    wiki: Wiki, elementos: list[str], maximo: int = MAXIMO_PAGINAS_POR_LECTURA
) -> Lectura:
    """Lee páginas enteras o la sección de un encabezado (`slug#Encabezado`).

    Acepta también los nombres que devuelve el grafo (`pages/<slug>.md`).
    """
    pedidas = [e.strip().strip("[]") for e in elementos if e.strip()]
    bloques: list[str] = []
    leidas: list[str] = []
    no_encontradas: list[str] = []
    for elemento in pedidas[:maximo]:
        slug, _, seccion = elemento.partition("#")
        slug = re.sub(r"\.md$", "", re.sub(r"^pages/", "", slug.strip()))
        if slug == PAGINA_INDICE:
            bloques.append(f"=== Page index ===\n{wiki.texto_del_indice().strip()}")
            leidas.append(slug)
        elif not wiki.existe(slug):
            no_encontradas.append(slug)
        elif not seccion.strip():
            bloques.append(f"=== Page {slug} ===\n{wiki.leer(slug).a_texto().strip()}")
            leidas.append(slug)
        else:
            partes = _secciones(wiki.leer(slug).cuerpo)
            clave = seccion.strip().casefold()
            elegidas = [t for titulo, t in partes if titulo.casefold() == clave] or [
                t for titulo, t in partes if clave in titulo.casefold()
            ]
            if elegidas:
                bloques.append(
                    f"=== Section {slug}#{seccion.strip()} ===\n" + "\n\n".join(elegidas)
                )
                leidas.append(slug)
            else:
                titulos = ", ".join(t for t, _ in partes if t)
                bloques.append(f'Not found: section "{seccion}" of {slug}. Sections: {titulos}.')
    if no_encontradas:
        bloques.append(f"Not found: {', '.join(no_encontradas)}.")
    no_leidas = pedidas[maximo:]
    if no_leidas:
        bloques.append(
            f"Not read (at most {maximo} items per read): {', '.join(no_leidas)}. Ask again."
        )
    leidas = list(dict.fromkeys(leidas))
    return Lectura("\n\n".join(bloques) or "No pages requested.", leidas, no_encontradas, no_leidas)


# --- grafo (graphify) --------------------------------------------------------------------------
class GrafoDelWiki:
    """Consulta el grafo de los `.md` del wiki con `graphify query`, al día con el wiki."""

    def __init__(
        self,
        wiki: Wiki,
        graphify: Path | str,
        trabajo: Path | str,
        *,
        presupuesto: int = PRESUPUESTO_GRAFO,
        profundidad: int = PROFUNDIDAD_GRAFO,
        ejecutor: Callable[..., Any] = subprocess.run,
    ) -> None:
        self._wiki = wiki
        self._graphify = str(graphify)
        self._fuente = Path(trabajo) / "fuente"
        self._presupuesto = presupuesto
        self._profundidad = profundidad
        self._ejecutor = ejecutor
        self._paso: int | None = None

    @property
    def ruta_grafo(self) -> Path:
        return self._fuente / "graphify-out" / "graph.json"

    def _correr(self, argumentos: list[str]) -> Any:
        try:
            return self._ejecutor(
                [self._graphify, *argumentos],
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
                env={**os.environ, "PYTHONUTF8": "1"},
            )
        except OSError as error:
            raise ErrorDeCapa(
                f"No se pudo ejecutar graphify ({self._graphify}): {error}"
            ) from error

    def actualizar(self) -> None:
        """Reconstruye el grafo si cambió el número de papers ingeridos (determinista y gratis)."""
        paso = len(self._wiki.ingeridos)
        if self._paso == paso and self.ruta_grafo.exists():
            return
        self._fuente.mkdir(parents=True, exist_ok=True)
        shutil.rmtree(self._fuente / "pages", ignore_errors=True)
        shutil.copytree(self._wiki.carpeta / "pages", self._fuente / "pages")
        shutil.copy2(self._wiki.carpeta / "index.md", self._fuente / "index.md")
        proceso = self._correr(["update", str(self._fuente)])
        if proceso.returncode != 0 or not self.ruta_grafo.exists():
            detalle = (proceso.stderr or proceso.stdout or "").strip()[:300]
            raise ErrorDeCapa(f"graphify no pudo construir el grafo: {detalle}")
        self._paso = paso

    def consultar(self, consulta: str) -> tuple[str, str]:
        self.actualizar()
        proceso = self._correr(
            [
                "query",
                consulta,
                "--graph",
                str(self.ruta_grafo),
                "--budget",
                str(self._presupuesto),
                "--depth",
                str(self._profundidad),
            ]
        )
        texto = (proceso.stdout or "").strip()
        nodos = len(re.findall(r"^NODE ", texto, re.MULTILINE))
        if proceso.returncode not in (0, 3) or not nodos:
            return texto or (proceso.stderr or "").strip() or "No node matches.", "no nodes"
        return texto, f"{nodos} nodes"

    def herramienta(self) -> HerramientaExtra:
        return HerramientaExtra("graph", "query", DESCRIPCION_GRAFO, self.consultar)


# --- tgrep -------------------------------------------------------------------------------------
def _con_ruta_normal(linea: str) -> str:
    r"""Cambia ``\`` por ``/`` solo en la ruta (antes del primer ``:``), no en el texto."""
    ruta, separador, resto = linea.partition(":")
    return ruta.replace("\\", "/") + separador + resto


class BusquedaTgrep:
    """Busca líneas con el binario real de tgrep, con su índice al día y la salida recortada."""

    def __init__(
        self,
        wiki: Wiki,
        tgrep: Path | str,
        trabajo: Path | str,
        *,
        columnas: int = COLUMNAS_TGREP,
        maximo: int = MAXIMO_LINEAS_TGREP,
        ejecutor: Callable[..., Any] = subprocess.run,
    ) -> None:
        self._wiki = wiki
        self._tgrep = str(tgrep)
        self._indice = (Path(trabajo) / "tgrep-indice").resolve()
        self._columnas = columnas
        self._maximo = maximo
        self._ejecutor = ejecutor
        self._paso: int | None = None

    def _correr(self, argumentos: list[str]) -> Any:
        try:
            return self._ejecutor(
                [self._tgrep, *argumentos],
                cwd=self._wiki.carpeta,
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
            )
        except OSError as error:
            raise ErrorDeCapa(f"No se pudo ejecutar tgrep ({self._tgrep}): {error}") from error

    def actualizar(self) -> None:
        paso = len(self._wiki.ingeridos)
        if self._paso == paso:
            return
        self._indice.mkdir(parents=True, exist_ok=True)
        proceso = self._correr(
            ["index", ".", "--index-path", str(self._indice), "--no-require-git", "--force"]
        )
        if proceso.returncode != 0:
            raise ErrorDeCapa(f"tgrep no pudo indexar: {(proceso.stderr or '').strip()[:300]}")
        self._paso = paso

    def consultar(self, patron: str) -> tuple[str, str]:
        self.actualizar()
        orden = ["-n", "-i", "--index-path", str(self._indice), "--no-require-git"]
        if self._columnas:
            orden += ["-M", str(self._columnas), "--max-columns-preview"]
        proceso = self._correr([*orden, "--", patron, "pages"])
        if proceso.returncode == 2:
            return f"Invalid search: {(proceso.stderr or '').strip()[:200]}", "invalid pattern"
        lineas = [_con_ruta_normal(x) for x in (proceso.stdout or "").splitlines() if x.strip()]
        if not lineas:
            return "No lines match this pattern.", "no lines match"
        return "\n".join(lineas[: self._maximo]), f"{len(lineas)} lines"

    def herramienta(self) -> HerramientaExtra:
        return HerramientaExtra(
            "grep", "pattern", DESCRIPCION_TGREP, self.consultar, requiere_lectura=True
        )


# --- armado ------------------------------------------------------------------------------------
def nombre_del_brazo(tgrep: bool) -> str:
    return NOMBRE_GRAFO_TGREP if tgrep else NOMBRE_GRAFO


def crear_capas(
    wiki: Wiki,
    graphify: Path | str,
    trabajo: Path | str,
    *,
    tgrep: Path | str | None = None,
    ejecutor: Callable[..., Any] = subprocess.run,
) -> CapasDeConsulta:
    """Grafo y, si se indica el binario, tgrep como herramienta opcional detrás de la lectura."""
    herramientas: list[HerramientaExtra] = [
        GrafoDelWiki(wiki, graphify, trabajo, ejecutor=ejecutor).herramienta()
    ]
    if tgrep is not None:
        herramientas.append(BusquedaTgrep(wiki, tgrep, trabajo, ejecutor=ejecutor).herramienta())
    return CapasDeConsulta(tuple(herramientas))


def nombres_de(herramientas: Sequence[HerramientaExtra]) -> dict[str, str]:
    """Acción → clave del argumento, para analizar la respuesta del agente."""
    return {h.nombre: h.argumento for h in herramientas}
