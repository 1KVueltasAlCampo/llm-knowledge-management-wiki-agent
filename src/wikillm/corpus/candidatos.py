"""Reúne candidatos al corpus: referencias de arXiv del .bib y búsquedas en la API."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from wikillm.corpus.arxiv_api import ClienteApi, Registro

PATRON_ID_BIB = re.compile(r"\b(\d{4}\.\d{4,5})(?:v\d+)?\b")


def ids_de_bib(texto_bib: str) -> list[str]:
    """Identificadores de arXiv que aparecen en el .bib, en orden de aparición y sin repetir."""
    return list(dict.fromkeys(PATRON_ID_BIB.findall(texto_bib)))


def leer_consultas(ruta: Path) -> list[str]:
    consultas = []
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if linea and not linea.startswith("#"):
            consultas.append(linea)
    return consultas


def reunir(
    cliente: ClienteApi,
    ids_semilla: list[str],
    consultas: list[str],
    desde: str,
    maximo_por_consulta: int = 100,
) -> list[dict[str, Any]]:
    """Une semillas y resultados de búsqueda. `desde` (AAAA-MM-DD) filtra solo las búsquedas."""
    origen: dict[str, set[str]] = {}
    registros: dict[str, Registro] = {}
    for registro in cliente.por_ids(ids_semilla):
        registros[registro.arxiv_id] = registro
        origen.setdefault(registro.arxiv_id, set()).add("bib")
    for consulta in consultas:
        for registro in cliente.buscar(consulta, maximo_por_consulta):
            if registro.fecha_publicacion < desde:
                continue
            registros.setdefault(registro.arxiv_id, registro)
            origen.setdefault(registro.arxiv_id, set()).add(f"busqueda:{consulta}")
    filas = []
    for arxiv_id, registro in sorted(registros.items()):
        fila = registro.como_dict()
        fila["origen"] = sorted(origen[arxiv_id])
        filas.append(fila)
    return filas


def escribir_jsonl(ruta: Path, filas: list[dict[str, Any]]) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with ruta.open("w", encoding="utf-8") as archivo:
        for fila in filas:
            archivo.write(json.dumps(fila, ensure_ascii=False) + "\n")


def leer_jsonl(ruta: Path) -> list[dict[str, Any]]:
    return [
        json.loads(linea)
        for linea in ruta.read_text(encoding="utf-8").splitlines()
        if linea.strip()
    ]
