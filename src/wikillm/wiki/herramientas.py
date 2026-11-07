"""Las dos herramientas del agente que consulta el wiki: buscar páginas y leerlas.

La búsqueda es léxica y determinista (sin embeddings): puntúa por palabras clave, con más peso
en el título y el resumen, y devuelve resúmenes de una línea. Es lo que el estudio de progressive
disclosure (2607.04576) encontró que reduce el costo, y evita que el wiki dependa del mismo
modelo de embeddings que usa el RAG.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass

from wikillm.wiki.almacen import Pagina, Wiki

MAXIMO_RESULTADOS = 8
MAXIMO_PAGINAS_POR_LECTURA = 3
PESO_TITULO = 3.0
PESO_RESUMEN = 2.0
TOPE_FRECUENCIA_CUERPO = 5
PATRON_PALABRA = re.compile(r"[a-z0-9]+")
PATRON_CITA = re.compile(r"\[[^\[\]]*#s\d+\.p\d+[^\[\]]*\]")
PAGINA_INDICE = "index"
PALABRAS_VACIAS = frozenset(
    "a an and are as at be by do does for from has have how in is it its of on or that the "
    "their this to was were what which who with".split()
)


def palabras(texto: str) -> list[str]:
    """Palabras clave en minúscula, sin las citas `[span_id]` ni palabras vacías."""
    sin_citas = PATRON_CITA.sub(" ", texto).lower()
    return [
        p for p in PATRON_PALABRA.findall(sin_citas) if len(p) >= 2 and p not in PALABRAS_VACIAS
    ]


@dataclass(frozen=True)
class Resumen:
    slug: str
    tipo: str
    titulo: str
    resumen: str

    def a_texto(self) -> str:
        return f"- {self.slug} [{self.tipo}] {self.titulo}: {self.resumen}"


def _puntuar(consulta: set[str], pagina: Pagina, idf: dict[str, float]) -> float:
    titulo = set(palabras(f"{pagina.titulo} {pagina.slug.replace('-', ' ')}"))
    resumen = set(palabras(pagina.resumen))
    cuerpo = Counter(palabras(pagina.cuerpo))
    puntos = 0.0
    for palabra in consulta:
        peso = (
            PESO_TITULO * (palabra in titulo)
            + PESO_RESUMEN * (palabra in resumen)
            + min(cuerpo[palabra], TOPE_FRECUENCIA_CUERPO) / TOPE_FRECUENCIA_CUERPO
        )
        puntos += idf[palabra] * peso
    return puntos


def wiki_search(wiki: Wiki, consulta: str, maximo: int = MAXIMO_RESULTADOS) -> list[Resumen]:
    """Hasta ``maximo`` páginas ordenadas por coincidencia; vacío si nada coincide."""
    palabras_consulta = set(palabras(consulta))
    paginas = wiki.paginas()
    if not palabras_consulta or not paginas:
        return []
    presentes: Counter[str] = Counter()
    for pagina in paginas:
        texto = f"{pagina.titulo} {pagina.slug} {pagina.resumen} {pagina.cuerpo}"
        presentes.update(set(palabras(texto)) & palabras_consulta)
    idf = {p: math.log(1 + len(paginas) / (1 + presentes[p])) for p in palabras_consulta}
    puntuadas = sorted(
        ((_puntuar(palabras_consulta, p, idf), p) for p in paginas),
        key=lambda par: (-par[0], par[1].slug),
    )
    return [Resumen(p.slug, p.tipo, p.titulo, p.resumen) for puntos, p in puntuadas if puntos > 0][
        :maximo
    ]


def texto_de_busqueda(resultados: list[Resumen]) -> str:
    if not resultados:
        return "No pages match this search."
    return "\n".join(r.a_texto() for r in resultados)


@dataclass(frozen=True)
class Lectura:
    texto: str
    leidas: list[str]
    no_encontradas: list[str]
    no_leidas: list[str]


def wiki_read(wiki: Wiki, slugs: list[str], maximo: int = MAXIMO_PAGINAS_POR_LECTURA) -> Lectura:
    """Contenido de hasta ``maximo`` páginas; informa de las que no existen o quedaron sin leer."""
    pedidas = list(dict.fromkeys(s.strip().strip("[]") for s in slugs if s.strip()))
    leidas: list[str] = []
    no_encontradas: list[str] = []
    no_leidas: list[str] = []
    bloques: list[str] = []
    for slug in pedidas:
        existe = slug == PAGINA_INDICE or wiki.existe(slug)
        if not existe:
            no_encontradas.append(slug)
        elif len(leidas) >= maximo:
            no_leidas.append(slug)
        else:
            contenido = (
                wiki.texto_del_indice() if slug == PAGINA_INDICE else wiki.leer(slug).a_texto()
            )
            bloques.append(f"=== Page {slug} ===\n{contenido.strip()}")
            leidas.append(slug)
    if no_encontradas:
        bloques.append(f"Not found: {', '.join(no_encontradas)}.")
    if no_leidas:
        bloques.append(
            f"Not read (at most {maximo} pages per read): {', '.join(no_leidas)}. Ask again."
        )
    return Lectura("\n\n".join(bloques) or "No pages requested.", leidas, no_encontradas, no_leidas)
