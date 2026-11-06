"""Regla reproducible para elegir los N papers del corpus (ver `docs/corpus.md` §2).

1. Semillas obligatorias, si tienen HTML.
2. Referencias de 2026 del `.bib` con HTML.
3. Hasta completar N, preseleccionados de las búsquedas con HTML, ordenados por enlaces de
   citas con el resto del grupo (citas hechas + recibidas), luego por fecha.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from wikillm.corpus.manifest import FECHA_CORTE


def seleccionar(
    candidatos: dict[str, dict[str, Any]],
    semillas: list[str],
    preseleccion: list[str],
    referencias: dict[str, list[str]],
    tiene_html: Callable[[str], bool],
    n: int = 50,
) -> tuple[list[str], list[str]]:
    """Devuelve (elegidos, reservas). `referencias[id]` son los ids del grupo que cita."""
    elegidos = [s for s in semillas if tiene_html(s)]
    for arxiv_id, registro in sorted(candidatos.items()):
        if arxiv_id in elegidos or "bib" not in registro.get("origen", []):
            continue
        if registro["fecha_publicacion"] >= FECHA_CORTE and tiene_html(arxiv_id):
            elegidos.append(arxiv_id)
    if len(elegidos) > n:
        raise ValueError(f"{len(elegidos)} obligatorios superan el tamaño {n}")

    grupo = set(elegidos) | set(preseleccion)

    def enlaces(arxiv_id: str) -> int:
        hechas = sum(1 for r in referencias.get(arxiv_id, []) if r in grupo)
        recibidas = sum(1 for otro in grupo if arxiv_id in referencias.get(otro, []))
        return hechas + recibidas

    restantes = [p for p in preseleccion if p not in elegidos and tiene_html(p)]
    restantes.sort(key=lambda p: (-enlaces(p), candidatos[p]["fecha_publicacion"], p))
    faltan = n - len(elegidos)
    return elegidos + restantes[:faltan], restantes[faltan:]
