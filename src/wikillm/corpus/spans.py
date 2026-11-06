"""Fragmentos citables del cuerpo Gold (propuesta Gold v1, §2).

Un fragmento es un bloque de líneas no vacías del cuerpo (párrafo, tabla, ecuación, lista o
pie de figura). Se guarda su posición y la huella de su texto, nunca el texto: así las citas
se pueden versionar sin copiar contenido de arXiv (regla 8 de la constitución).
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

PATRON_ENCABEZADO = re.compile(r"^(#{1,6})\s+(.*)$")
PATRON_LISTA = re.compile(r"^\s*(?:[-*+]|\d+\.)\s")


@dataclass
class Span:
    span_id: str
    arxiv_id: str
    version: str
    seccion: str
    tipo: str
    inicio: int
    fin: int
    sha256: str

    def como_dict(self) -> dict[str, Any]:
        return asdict(self)


def huella(texto: str) -> str:
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def _tipo(bloque: str) -> str:
    primera = bloque.lstrip()
    if primera.startswith("|"):
        return "tabla"
    if primera.startswith("$$"):
        return "ecuacion"
    if primera.startswith("**") and bloque.rstrip().endswith("**"):
        return "pie_tabla"
    if primera.startswith("*") and not primera.startswith("* ") and bloque.rstrip().endswith("*"):
        return "pie_figura"
    if PATRON_LISTA.match(primera):
        return "lista"
    return "parrafo"


def _bloques(cuerpo: str) -> list[tuple[int, int]]:
    """Posiciones [inicio, fin) de cada bloque de líneas no vacías."""
    bloques: list[tuple[int, int]] = []
    inicio: int | None = None
    fin = 0
    posicion = 0
    for linea in cuerpo.splitlines(keepends=True):
        contenido = linea.rstrip("\r\n")
        if contenido.strip():
            if inicio is None:
                inicio = posicion
            fin = posicion + len(contenido)
        elif inicio is not None:
            bloques.append((inicio, fin))
            inicio = None
        posicion += len(linea)
    if inicio is not None:
        bloques.append((inicio, fin))
    return bloques


def calcular_spans(arxiv_id: str, version: str, cuerpo: str) -> list[Span]:
    spans: list[Span] = []
    seccion = ""
    numero_seccion = 0
    numero_bloque = 0
    for inicio, fin in _bloques(cuerpo):
        texto = cuerpo[inicio:fin]
        encabezado = PATRON_ENCABEZADO.match(texto)
        if encabezado and "\n" not in texto:
            if len(encabezado.group(1)) >= 2:  # el título (#) no abre sección
                numero_seccion += 1
                numero_bloque = 0
                seccion = encabezado.group(2).strip()
            continue
        numero_bloque += 1
        spans.append(
            Span(
                span_id=f"{arxiv_id}#s{numero_seccion}.p{numero_bloque}",
                arxiv_id=arxiv_id,
                version=version,
                seccion=seccion,
                tipo=_tipo(texto),
                inicio=inicio,
                fin=fin,
                sha256=huella(texto),
            )
        )
    return spans


class SpanInvalido(ValueError):
    """La cita no resuelve a un fragmento existente con la misma huella."""


def resolver(span: dict[str, Any], cuerpo: str) -> str:
    """Devuelve el texto del fragmento si su huella coincide con el cuerpo Gold local."""
    inicio, fin = int(span["inicio"]), int(span["fin"])
    if not 0 <= inicio < fin <= len(cuerpo):
        raise SpanInvalido(f"{span['span_id']}: posición fuera del cuerpo")
    texto = cuerpo[inicio:fin]
    if huella(texto) != span["sha256"]:
        raise SpanInvalido(f"{span['span_id']}: la huella no coincide (¿cambió el Gold?)")
    return texto


def spans_de_carpeta(carpeta_gold: Path, ids: list[str]) -> list[dict[str, Any]]:
    from wikillm.ingest.gold import leer_gold

    filas: list[dict[str, Any]] = []
    for arxiv_id in ids:
        ruta = carpeta_gold / f"{arxiv_id}.md"
        if not ruta.exists():
            continue
        encabezado, cuerpo = leer_gold(ruta)
        filas.extend(s.como_dict() for s in calcular_spans(arxiv_id, encabezado["version"], cuerpo))
    return filas
