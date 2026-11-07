"""Lectura de un paper para ingerirlo: su cuerpo Gold con cada fragmento citable rotulado.

Los rótulos son los `span_id` que calcula `calcular_spans`, los mismos de `spans.jsonl`, así que
cualquier cita que el modelo copie de aquí se puede verificar contra el Gold.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from wikillm.corpus.spans import calcular_spans
from wikillm.ingest.gold import leer_gold


@dataclass(frozen=True)
class PaperLeido:
    arxiv_id: str
    titulo: str
    version: str
    texto: str  # el cuerpo con "[span_id] " delante de cada fragmento
    span_ids: frozenset[str]


def rotular(cuerpo: str, arxiv_id: str, version: str) -> tuple[str, frozenset[str]]:
    """Inserta el `span_id` delante de cada fragmento; encabezados y espacios no cambian."""
    spans = calcular_spans(arxiv_id, version, cuerpo)
    partes: list[str] = []
    cursor = 0
    for span in spans:
        partes.append(cuerpo[cursor : span.inicio])
        partes.append(f"[{span.span_id}] ")
        cursor = span.inicio
    partes.append(cuerpo[cursor:])
    return "".join(partes), frozenset(s.span_id for s in spans)


def leer_paper(arxiv_id: str, carpeta_gold: Path | str) -> PaperLeido:
    ruta = Path(carpeta_gold) / f"{arxiv_id}.md"
    if not ruta.exists():
        raise FileNotFoundError(f"No hay Gold de {arxiv_id}; ejecuta wikillm.ingest")
    encabezado, cuerpo = leer_gold(ruta)
    version = str(encabezado["version"])
    texto, span_ids = rotular(cuerpo, arxiv_id, version)
    return PaperLeido(arxiv_id, str(encabezado["titulo"]), version, texto, span_ids)
