"""Brazo WikiLLM: ingiere papers en un wiki de páginas y responde con un agente que lo consulta."""

from __future__ import annotations

import time
from collections.abc import Callable, Collection
from pathlib import Path

from wikillm.common.modelo import ClienteModelo
from wikillm.common.responder import ResultadoBrazo, ResultadoIngesta
from wikillm.wiki.almacen import Wiki
from wikillm.wiki.consulta import MAX_ACCIONES_POR_DEFECTO, PACIENCIA_POR_DEFECTO, ConsultaWiki
from wikillm.wiki.ingesta import Ingestor


class BrazoWiki:
    nombre = "wiki"

    def __init__(
        self,
        modelo: ClienteModelo,
        wiki: Wiki,
        carpeta_gold: Path | str,
        *,
        max_acciones: int = MAX_ACCIONES_POR_DEFECTO,
        paciencia: int = PACIENCIA_POR_DEFECTO,
        spans_validos: Collection[str] | None = None,
        reloj: Callable[[], float] = time.perf_counter,
    ) -> None:
        self.wiki = wiki
        self.ingestor = Ingestor(
            modelo, wiki, carpeta_gold, spans_validos=spans_validos, reloj=reloj
        )
        self.consulta = ConsultaWiki(
            modelo,
            wiki,
            max_acciones=max_acciones,
            paciencia=paciencia,
            spans_validos=spans_validos,
            reloj=reloj,
        )

    def ingerir(self, arxiv_id: str) -> ResultadoIngesta:
        return self.ingestor.ingerir(arxiv_id)

    def responder(self, pregunta: str) -> ResultadoBrazo:
        return self.consulta.responder(pregunta)

    @property
    def ingeridos(self) -> list[str]:
        return list(self.wiki.ingeridos)

    def traza(self) -> dict[str, object]:
        """Qué hizo el agente en la última pregunta (vacía antes de la primera)."""
        traza = self.consulta.traza
        return {
            "acciones": traza.acciones,
            "busquedas": traza.busquedas,
            "lecturas": traza.lecturas,
            "paginas_leidas": list(traza.paginas_leidas),
            "incidencias": list(traza.incidencias),
            "detalle": [dict(paso) for paso in traza.detalle],
        }
