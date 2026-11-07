"""Divide los archivos Gold en fragmentos para el índice vectorial del RAG.

La primera frontera son los encabezados ``##`` (así lo fija el contrato del Gold). Si una sección
no cabe en el máximo de tokens del modelo de embeddings, se subdivide por párrafos. El conteo de
tokens se inyecta como función para poder probar sin descargar ningún modelo.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter

from wikillm.ingest.gold import leer_gold

Medidor = Callable[[str], int]

MAX_TOKENS_POR_DEFECTO = 400
SOLAPAMIENTO_POR_DEFECTO = 40
SEPARADORES = ["\n\n", "\n", ". ", " ", ""]
PATRON_SECCION = re.compile(r"(?m)^## +(.+?)\s*$")


@dataclass(frozen=True)
class Fragmento:
    texto: str
    arxiv_id: str
    titulo: str
    seccion: str
    posicion: int  # orden del fragmento dentro de su paper

    @property
    def id(self) -> str:
        return f"{self.arxiv_id}-{self.posicion}"


def _secciones(cuerpo: str) -> list[tuple[str, str]]:
    """Devuelve (nombre, texto) por cada encabezado ``##``; lo anterior al primero se descarta."""
    coincidencias = list(PATRON_SECCION.finditer(cuerpo))
    secciones = []
    for i, coincidencia in enumerate(coincidencias):
        fin = coincidencias[i + 1].start() if i + 1 < len(coincidencias) else len(cuerpo)
        secciones.append((coincidencia.group(1), cuerpo[coincidencia.end() : fin].strip()))
    return secciones


def dividir_paper(
    arxiv_id: str,
    titulo: str,
    cuerpo: str,
    *,
    medir: Medidor,
    max_tokens: int = MAX_TOKENS_POR_DEFECTO,
    solapamiento: int = SOLAPAMIENTO_POR_DEFECTO,
) -> list[Fragmento]:
    fragmentos: list[Fragmento] = []
    for seccion, texto in _secciones(cuerpo):
        if not texto:
            continue
        prefijo = f"{titulo} — {seccion}\n\n"
        presupuesto = max_tokens - medir(prefijo)
        if presupuesto <= solapamiento:
            raise ValueError(f"El título y la sección de {arxiv_id} no dejan espacio al texto")
        if medir(texto) <= presupuesto:
            trozos = [texto]
        else:
            divisor = RecursiveCharacterTextSplitter(
                chunk_size=presupuesto,
                chunk_overlap=solapamiento,
                length_function=medir,
                separators=SEPARADORES,
            )
            trozos = divisor.split_text(texto)
        for trozo in trozos:
            fragmentos.append(
                Fragmento(prefijo + trozo, arxiv_id, titulo, seccion, len(fragmentos))
            )
    return fragmentos


def leer_fragmentos(
    carpeta_gold: Path | str,
    *,
    medir: Medidor,
    max_tokens: int = MAX_TOKENS_POR_DEFECTO,
    solapamiento: int = SOLAPAMIENTO_POR_DEFECTO,
) -> list[Fragmento]:
    """Fragmentos de todos los ``.md`` de la carpeta Gold, en orden de identificador."""
    fragmentos: list[Fragmento] = []
    for ruta in sorted(Path(carpeta_gold).glob("*.md")):
        encabezado, cuerpo = leer_gold(ruta)
        fragmentos += dividir_paper(
            str(encabezado["arxiv_id"]),
            str(encabezado["titulo"]),
            cuerpo,
            medir=medir,
            max_tokens=max_tokens,
            solapamiento=solapamiento,
        )
    return fragmentos
