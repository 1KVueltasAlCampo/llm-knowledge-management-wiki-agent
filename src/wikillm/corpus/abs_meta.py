"""Metadatos de un paper a partir de su página `abs` de arXiv ya descargada (Bronze).

Sirve cuando la API de arXiv no responde (límite de peticiones): la página `abs` que la ingesta
guarda en `raw/<id>/abs.html` trae título, autores, fechas, versión y categorías. El resultado tiene
las mismas claves que un registro de la API, para que `construir_manifest` lo use sin cambios.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup

from wikillm.corpus.candidatos import escribir_jsonl, leer_jsonl

PATRON_CATEGORIA = re.compile(r"\(([a-z\-]+(?:\.[A-Za-z\-]+)?)\)")


def _meta(sopa: BeautifulSoup, nombre: str) -> str | None:
    etiqueta = sopa.find("meta", attrs={"name": nombre})
    contenido = etiqueta.get("content") if etiqueta else None
    return str(contenido) if contenido else None


def _fecha(valor: str | None) -> str:
    return (valor or "").replace("/", "-")


def _nombre(autor: str) -> str:
    apellido, coma, nombre = autor.partition(",")
    return f"{nombre.strip()} {apellido.strip()}" if coma else autor.strip()


def _celda(sopa: BeautifulSoup, clase: str) -> str | None:
    celda = sopa.find("td", class_=clase)
    texto = celda.get_text(" ", strip=True) if celda else ""
    return texto or None


def registro_desde_abs(html: str, arxiv_id: str) -> dict[str, Any]:
    """Registro con las claves de la API de arXiv, leído de la página `abs`."""
    sopa = BeautifulSoup(html, "lxml")
    historial = sopa.find("div", class_="submission-history")
    versiones = re.findall(r"\[v(\d+)\]", historial.get_text(" ") if historial else "")
    categorias = PATRON_CATEGORIA.findall(_celda(sopa, "subjects") or "")
    resumen = sopa.find("blockquote", class_="abstract")
    texto_resumen = resumen.get_text(" ", strip=True) if resumen else ""
    return {
        "arxiv_id": arxiv_id,
        "version": f"v{versiones[-1]}" if versiones else "v1",
        "titulo": _meta(sopa, "citation_title") or "",
        "autores": [
            _nombre(m["content"]) for m in sopa.find_all("meta", attrs={"name": "citation_author"})
        ],
        "fecha_publicacion": _fecha(_meta(sopa, "citation_date")),
        "fecha_version": _fecha(
            _meta(sopa, "citation_online_date") or _meta(sopa, "citation_date")
        ),
        "categoria": categorias[0] if categorias else "",
        "categorias": categorias,
        "journal_ref": _celda(sopa, "jref"),
        "doi": _meta(sopa, "citation_doi"),
        "comentario": _celda(sopa, "comments"),
        "resumen": re.sub(r"^Abstract:\s*", "", texto_resumen),
        "origen": ["abs"],
    }


def completar_candidatos(carpeta_raw: Path, ids: list[str]) -> list[str]:
    """Añade a `api/candidatos.jsonl` los ids sin metadatos y devuelve los que siguen sin ellos."""
    ruta = carpeta_raw / "api" / "candidatos.jsonl"
    filas = {f["arxiv_id"]: f for f in leer_jsonl(ruta)}
    faltan = []
    for arxiv_id in ids:
        if arxiv_id in filas:
            continue
        pagina = carpeta_raw / arxiv_id / "abs.html"
        if not pagina.is_file():
            faltan.append(arxiv_id)
            continue
        filas[arxiv_id] = registro_desde_abs(pagina.read_text(encoding="utf-8"), arxiv_id)
    escribir_jsonl(ruta, [filas[k] for k in sorted(filas)])
    return faltan
