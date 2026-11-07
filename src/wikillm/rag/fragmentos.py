"""Fragmentos del RAG, construidos a partir de los fragmentos citables (spans) del Gold.

Cada fragmento agrupa spans consecutivos de una misma sección hasta el máximo de tokens del
modelo de embeddings, y rotula cada span con su ``span_id`` para que el modelo pueda citarlo.
Un span que por sí solo no cabe (por ejemplo una tabla enorme) se parte en trozos que conservan
su ``span_id``. El conteo de tokens se inyecta como función para probar sin descargar modelos.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter

from wikillm.corpus.spans import calcular_spans
from wikillm.ingest.gold import leer_gold

Medidor = Callable[[str], int]

MAX_TOKENS_POR_DEFECTO = 400
SOLAPAMIENTO_POR_DEFECTO = 40
SEPARADORES = ["\n\n", "\n", ". ", " ", ""]
TOKENS_POR_UNION = 2  # los dos saltos de línea que unen un span con el siguiente
PATRON_SECCION = re.compile(r"#s(\d+)\.p")


@dataclass(frozen=True)
class Fragmento:
    texto: str
    arxiv_id: str
    titulo: str
    seccion: str
    posicion: int  # orden del fragmento dentro de su paper
    span_ids: tuple[str, ...]

    @property
    def id(self) -> str:
        return f"{self.arxiv_id}-{self.posicion}"


def _unidades(
    texto: str, span_id: str, presupuesto: int, medir: Medidor, solapamiento: int
) -> list[str]:
    """El span rotulado, o sus trozos rotulados si no cabe en un fragmento."""
    rotulo = f"[{span_id}] "
    if medir(rotulo + texto) <= presupuesto:
        return [rotulo + texto]
    hueco = presupuesto - medir(rotulo)
    if hueco <= solapamiento:
        raise ValueError(f"El rótulo de {span_id} no deja espacio al texto")
    divisor = RecursiveCharacterTextSplitter(
        chunk_size=hueco,
        chunk_overlap=solapamiento,
        length_function=medir,
        separators=SEPARADORES,
    )
    return [rotulo + trozo for trozo in divisor.split_text(texto)]


def dividir_paper(
    arxiv_id: str,
    titulo: str,
    version: str,
    cuerpo: str,
    *,
    medir: Medidor,
    max_tokens: int = MAX_TOKENS_POR_DEFECTO,
    solapamiento: int = SOLAPAMIENTO_POR_DEFECTO,
) -> list[Fragmento]:
    secciones: dict[str, list] = {}
    for span in calcular_spans(arxiv_id, version, cuerpo):
        secciones.setdefault(PATRON_SECCION.search(span.span_id).group(1), []).append(span)

    fragmentos: list[Fragmento] = []
    for spans in secciones.values():
        seccion = spans[0].seccion or "Front matter"
        prefijo = f"{titulo} — {seccion}\n\n"
        presupuesto = max_tokens - medir(prefijo)
        if presupuesto <= solapamiento:
            raise ValueError(f"El título y la sección de {arxiv_id} no dejan espacio al texto")
        unidades: list[tuple[str, str]] = []
        for span in spans:
            texto = cuerpo[span.inicio : span.fin]
            for unidad in _unidades(texto, span.span_id, presupuesto, medir, solapamiento):
                unidades.append((span.span_id, unidad))

        lote: list[tuple[str, str]] = []
        gastado = 0
        for unidad in [*unidades, None]:
            coste = 0 if unidad is None else medir(unidad[1]) + TOKENS_POR_UNION
            if lote and (unidad is None or gastado + coste > presupuesto):
                fragmentos.append(
                    Fragmento(
                        texto=prefijo + "\n\n".join(texto for _, texto in lote),
                        arxiv_id=arxiv_id,
                        titulo=titulo,
                        seccion=seccion,
                        posicion=len(fragmentos),
                        span_ids=tuple(dict.fromkeys(span_id for span_id, _ in lote)),
                    )
                )
                lote, gastado = [], 0
            if unidad is not None:
                lote.append(unidad)
                gastado += coste
    return fragmentos


def fragmentos_de_gold(
    ruta_gold: Path | str,
    *,
    medir: Medidor,
    max_tokens: int = MAX_TOKENS_POR_DEFECTO,
    solapamiento: int = SOLAPAMIENTO_POR_DEFECTO,
) -> list[Fragmento]:
    """Fragmentos de un archivo Gold."""
    encabezado, cuerpo = leer_gold(Path(ruta_gold))
    return dividir_paper(
        str(encabezado["arxiv_id"]),
        str(encabezado["titulo"]),
        str(encabezado["version"]),
        cuerpo,
        medir=medir,
        max_tokens=max_tokens,
        solapamiento=solapamiento,
    )
