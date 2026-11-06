"""Manifest del corpus: orden de ingesta, mitad asignada y señales de selección.

Se versiona solo con metadatos (sin texto de arXiv). Complementa `data/gold/corpus.jsonl`
según `specs/propuesta-gold-v1.md` §3.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from wikillm.ingest.arxiv import leer_capturas
from wikillm.ingest.gold import leer_gold

FECHA_CORTE = "2026-01-01"
PATRON_CODIGO = re.compile(
    r"github\.com/[\w.-]+/[\w.-]+|gitlab\.com/[\w.-]+/[\w.-]+|"
    r"huggingface\.co/(?:datasets/|spaces/)?[\w.-]+/[\w.-]+|"
    r"\bcode (?:is |will be )?(?:publicly )?(?:available|released)\b",
    re.IGNORECASE,
)
AUTORES = {"A": "Juan Diego Ramírez", "B": "Juan David Cruz"}


def html_disponible(carpeta_raw: Path, arxiv_id: str) -> bool:
    capturas = [c for c in leer_capturas(carpeta_raw / arxiv_id) if c["tipo"] == "html"]
    return bool(capturas) and capturas[-1]["estado"] == 200


def ordenar(registros: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Orden de ingesta: fecha de la primera versión; empate por identificador."""
    return sorted(registros, key=lambda r: (r["fecha_publicacion"], r["arxiv_id"]))


def mitad(orden_ingesta: int) -> str:
    """Impar → A, par → B: cada autor cubre toda la línea de tiempo y cualquier prefijo."""
    return "A" if orden_ingesta % 2 == 1 else "B"


def construir_manifest(
    ids: list[str],
    candidatos: dict[str, dict[str, Any]],
    carpeta_raw: Path,
    carpeta_gold: Path,
) -> list[dict[str, Any]]:
    faltan = [i for i in ids if i not in candidatos]
    if faltan:
        raise KeyError(f"sin metadatos de la API para: {', '.join(faltan)}")
    gold: dict[str, tuple[dict[str, Any], str]] = {}
    for arxiv_id in ids:
        ruta = carpeta_gold / f"{arxiv_id}.md"
        if ruta.exists():
            gold[arxiv_id] = leer_gold(ruta)
    citado_por: dict[str, int] = dict.fromkeys(ids, 0)
    for encabezado, _ in gold.values():
        for citado in encabezado.get("referencias_en_corpus") or []:
            if citado in citado_por:
                citado_por[citado] += 1

    filas = []
    for posicion, registro in enumerate(ordenar([candidatos[i] for i in ids]), start=1):
        arxiv_id = registro["arxiv_id"]
        encabezado, cuerpo = gold.get(arxiv_id, ({}, ""))
        texto_codigo = " ".join(
            filter(None, [registro.get("resumen"), registro.get("comentario"), cuerpo])
        )
        revisado = bool(registro.get("journal_ref") or registro.get("doi"))
        referencias = [r for r in encabezado.get("referencias_en_corpus") or [] if r in citado_por]
        filas.append(
            {
                "orden_ingesta": posicion,
                "arxiv_id": arxiv_id,
                "version": encabezado.get("version") or registro["version"],
                "fecha_publicacion": registro["fecha_publicacion"],
                "fecha_version": registro["fecha_version"],
                "titulo": registro["titulo"],
                "autores": registro["autores"],
                "categoria": registro["categoria"],
                "estado_publicacion": "revisado" if revisado else "preprint",
                "journal_ref": registro.get("journal_ref"),
                "doi": registro.get("doi"),
                "html_available": html_disponible(carpeta_raw, arxiv_id),
                "en_gold": arxiv_id in gold,
                "tokens": encabezado.get("tokens"),
                "pre_corte": registro["fecha_publicacion"] < FECHA_CORTE,
                "senal_codigo": bool(PATRON_CODIGO.search(texto_codigo)),
                "referencias_en_corpus": referencias,
                "citado_por_en_corpus": citado_por[arxiv_id],
                "mitad": mitad(posicion),
                "autor_preguntas": AUTORES[mitad(posicion)],
                "origen": registro.get("origen", []),
            }
        )
    return filas
