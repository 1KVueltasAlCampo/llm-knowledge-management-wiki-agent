"""Conversión del HTML de arXiv (LaTeXML) a Markdown limpio (capa Silver)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from bs4 import BeautifulSoup, NavigableString, Tag

RUIDO = ("script", "style", "nav", "header", "footer", "svg", "img", "noscript")
CLASES_RUIDO = ("ltx_page_navbar", "ltx_page_logo", "ltx_page_header", "ltx_page_footer")
ENCABEZADOS = {
    "ltx_title_section": "##",
    "ltx_title_subsection": "###",
    "ltx_title_subsubsection": "####",
    "ltx_title_paragraph": "#####",
    "ltx_title_appendix": "##",
    "ltx_title_acknowledgements": "##",
}
PATRONES_ARXIV = (
    re.compile(r"arxiv\.org/(?:abs|pdf|html)/(\d{4}\.\d{4,5})", re.IGNORECASE),
    re.compile(r"arXiv[:\s]+(\d{4}\.\d{4,5})", re.IGNORECASE),
)


@dataclass
class ResultadoMarkdown:
    markdown: str
    titulo: str
    secciones: int = 0
    tablas: int = 0
    ecuaciones: int = 0
    referencias_arxiv: set[str] = field(default_factory=set)
    texto_bibliografia: str = ""


def _clases(nodo: Tag) -> set[str]:
    return set(nodo.get("class") or [])


def _espacios(texto: str) -> str:
    return re.sub(r"\s+", " ", texto)


class _Conversor:
    def __init__(self) -> None:
        self.tablas = 0
        self.ecuaciones = 0

    # ---------------------------------------------------------------- en línea
    def en_linea(self, nodo: Tag | NavigableString) -> str:
        if isinstance(nodo, NavigableString):
            return _espacios(str(nodo))
        clases = _clases(nodo)
        if nodo.name == "math":
            self.ecuaciones += 1
            return f"${self._latex(nodo)}$"
        if "ltx_note" in clases:
            contenido = nodo.select_one(".ltx_note_content") or nodo
            texto = " ".join(self.en_linea(h) for h in contenido.children).strip()
            return f" (nota: {_espacios(texto).strip()})" if texto else ""
        if nodo.name in ("em", "i") or "ltx_emph" in clases:
            return self._envolver("*", self._hijos(nodo))
        if nodo.name in ("strong", "b") or "ltx_font_bold" in clases:
            return self._envolver("**", self._hijos(nodo))
        if nodo.name in ("code", "tt") or "ltx_font_typewriter" in clases:
            return self._envolver("`", self._hijos(nodo))
        if nodo.name == "br":
            return " "
        return self._hijos(nodo)

    def _hijos(self, nodo: Tag) -> str:
        return "".join(self.en_linea(hijo) for hijo in nodo.children)

    @staticmethod
    def _envolver(marca: str, texto: str) -> str:
        interior = texto.strip()
        if not interior:
            return texto
        izquierda = " " if texto[:1].isspace() else ""
        derecha = " " if texto[-1:].isspace() else ""
        return f"{izquierda}{marca}{interior}{marca}{derecha}"

    @staticmethod
    def _latex(nodo: Tag) -> str:
        anotacion = nodo.select_one('annotation[encoding="application/x-tex"]')
        latex = (anotacion.get_text() if anotacion else nodo.get("alttext", "")) or ""
        return _espacios(latex).strip()

    def parrafo(self, nodo: Tag) -> str:
        return _espacios(self._hijos(nodo)).strip()

    # ------------------------------------------------------------------ bloques
    def bloques(self, nodo: Tag) -> list[str]:
        salida: list[str] = []
        for hijo in nodo.children:
            if isinstance(hijo, NavigableString):
                texto = _espacios(str(hijo)).strip()
                if texto:
                    salida.append(texto)
                continue
            salida.extend(self.bloque(hijo))
        return salida

    def bloque(self, nodo: Tag) -> list[str]:
        clases = _clases(nodo)
        if nodo.name in RUIDO or clases & set(CLASES_RUIDO):
            return []
        if nodo.name in ("h1", "h2", "h3", "h4", "h5", "h6"):
            return self._encabezado(nodo)
        if nodo.name == "p" or "ltx_p" in clases and nodo.name != "div":
            texto = self.parrafo(nodo)
            return [texto] if texto else []
        if nodo.name == "math":
            return [f"$${self._latex(nodo)}$$"] if self._contar_ecuacion() else []
        if "ltx_equation" in clases or "ltx_eqn_table" in clases or "ltx_equationgroup" in clases:
            return self._ecuacion_en_bloque(nodo)
        if nodo.name in ("ul", "ol"):
            return self._lista(nodo, 0)
        if nodo.name == "figure":
            return self._figura(nodo)
        if nodo.name == "table":
            return self._tabla(nodo)
        if "ltx_listing" in clases:
            texto = nodo.get_text().strip("\n")
            return [f"```\n{texto}\n```"] if texto.strip() else []
        if nodo.name == "section" and "ltx_bibliography" in clases:
            return []
        if "ltx_abstract" in clases:
            return self._resumen(nodo)
        return self.bloques(nodo)

    def _contar_ecuacion(self) -> bool:
        self.ecuaciones += 1
        return True

    def _encabezado(self, nodo: Tag) -> list[str]:
        clases = _clases(nodo)
        marca = next((m for c, m in ENCABEZADOS.items() if c in clases), None)
        if marca is None:
            return []
        texto = _espacios(self._hijos(nodo)).strip()
        return [f"{marca} {texto}"] if texto else []

    def _resumen(self, nodo: Tag) -> list[str]:
        parrafos = [self.parrafo(p) for p in nodo.select("p.ltx_p")]
        parrafos = [p for p in parrafos if p]
        return ["## Abstract", *parrafos] if parrafos else []

    def _ecuacion_en_bloque(self, nodo: Tag) -> list[str]:
        ecuaciones = nodo.select("math")
        if not ecuaciones:
            return []
        self.ecuaciones += len(ecuaciones)
        return [f"$${self._latex(e)}$$" for e in ecuaciones]

    def _lista(self, nodo: Tag, nivel: int) -> list[str]:
        lineas: list[str] = []
        ordenada = nodo.name == "ol"
        elementos = nodo.find_all("li", recursive=False)
        for posicion, item in enumerate(elementos, start=1):
            partes: list[str] = []
            anidadas: list[str] = []
            for hijo in item.children:
                if isinstance(hijo, NavigableString):
                    continue
                if "ltx_tag" in _clases(hijo):
                    continue
                if hijo.name in ("ul", "ol"):
                    anidadas.extend(self._lista(hijo, nivel + 1))
                    continue
                for interno in hijo.find_all(["ul", "ol"], recursive=True):
                    anidadas.extend(self._lista(interno, nivel + 1))
                    interno.decompose()
                texto = self.parrafo(hijo) if hijo.name in ("p", "div") else self.en_linea(hijo)
                texto = _espacios(texto).strip()
                if texto:
                    partes.append(texto)
            marca = f"{posicion}." if ordenada else "-"
            lineas.append("  " * nivel + f"{marca} " + " ".join(partes))
            lineas.extend(anidadas)
        return ["\n".join(lineas)] if nivel == 0 and lineas else lineas

    def _figura(self, nodo: Tag) -> list[str]:
        salida: list[str] = []
        es_tabla = "ltx_table" in _clases(nodo)
        for pie in nodo.find_all("figcaption"):
            texto = _espacios(self._hijos(pie)).strip()
            if texto:
                salida.append(f"**{texto}**" if es_tabla else f"*{texto}*")
        for tabla in nodo.select("table.ltx_tabular"):
            if tabla.find_parent("table", class_="ltx_tabular") is None:
                salida.extend(self._tabla(tabla))
        return salida

    def _tabla(self, nodo: Tag) -> list[str]:
        if "ltx_tabular" not in _clases(nodo):
            return self.bloques(nodo)
        filas: list[list[str]] = []
        for fila in nodo.find_all("tr"):
            if fila.find_parent("table") is not nodo:
                continue
            celdas: list[str] = []
            for celda in fila.find_all(["td", "th"], recursive=False):
                texto = _espacios(self._hijos(celda)).strip().replace("|", "\\|")
                celdas.append(texto)
                celdas.extend([""] * (int(celda.get("colspan", 1) or 1) - 1))
            if any(celdas):
                filas.append(celdas)
        if not filas:
            return []
        self.tablas += 1
        ancho = max(len(f) for f in filas)
        filas = [f + [""] * (ancho - len(f)) for f in filas]
        lineas = ["| " + " | ".join(filas[0]) + " |", "|" + "---|" * ancho]
        lineas.extend("| " + " | ".join(f) + " |" for f in filas[1:])
        return ["\n".join(lineas)]


def normalizar(texto: str) -> str:
    """Minúsculas, sin signos y con espacios simples, para buscar títulos en la bibliografía."""
    return re.sub(r"[^a-z0-9]+", " ", texto.lower()).strip()


def extraer_referencias_arxiv(bibliografia: Tag) -> set[str]:
    """Identificadores de arXiv que aparecen en la bibliografía (en textos y enlaces)."""
    texto = (
        bibliografia.get_text(" ")
        + " "
        + " ".join(a.get("href", "") for a in bibliografia.find_all("a"))
    )
    return {m for patron in PATRONES_ARXIV for m in patron.findall(texto)}


def html_a_markdown(html: str) -> ResultadoMarkdown:
    """Convierte el HTML de un paper de arXiv en Markdown sin navegación ni bibliografía."""
    sopa = BeautifulSoup(html, "lxml")
    articulo = sopa.select_one("article.ltx_document")
    if articulo is None:
        raise ValueError("El HTML no es un documento de arXiv (falta article.ltx_document)")
    bibliografia = articulo.select_one("section.ltx_bibliography")
    referencias = extraer_referencias_arxiv(bibliografia) if bibliografia else set()
    texto_bibliografia = normalizar(bibliografia.get_text(" ")) if bibliografia else ""
    if bibliografia:
        bibliografia.decompose()
    for ruido in articulo.find_all(RUIDO):
        ruido.decompose()
    titulo_tag = articulo.select_one("h1.ltx_title_document")
    titulo = _espacios(titulo_tag.get_text(" ")).strip() if titulo_tag else ""

    conversor = _Conversor()
    partes: list[str] = [f"# {titulo}"] if titulo else []
    for hijo in articulo.children:
        if not isinstance(hijo, Tag) or hijo is titulo_tag:
            continue
        if "ltx_authors" in _clases(hijo):
            continue
        partes.extend(conversor.bloque(hijo))
    secciones = len(articulo.select("section.ltx_section"))
    cuerpo = "\n\n".join(p.strip() for p in partes if p.strip())
    cuerpo = re.sub(r"\n{3,}", "\n\n", cuerpo).strip() + "\n"
    return ResultadoMarkdown(
        markdown=cuerpo,
        titulo=titulo,
        secciones=secciones,
        tablas=conversor.tablas,
        ecuaciones=conversor.ecuaciones,
        referencias_arxiv=referencias,
        texto_bibliografia=texto_bibliografia,
    )
