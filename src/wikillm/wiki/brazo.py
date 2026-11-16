"""Brazo WikiLLM: ingiere papers en un wiki de páginas y responde con un agente que lo consulta."""

from __future__ import annotations

import time
from collections.abc import Callable, Collection
from pathlib import Path

from wikillm.common.modelo import ClienteModelo
from wikillm.common.responder import ResultadoBrazo, ResultadoIngesta
from wikillm.wiki.almacen import Wiki
from wikillm.wiki.capas import CapasDeConsulta
from wikillm.wiki.consulta import (
    MAX_ACCIONES_POR_DEFECTO,
    PACIENCIA_POR_DEFECTO,
    ConsultaWiki,
    Traza,
)
from wikillm.wiki.ingesta import Ingestor


def _resumen_de_traza(traza: Traza) -> dict[str, object]:
    return {
        "acciones": traza.acciones,
        "busquedas": traza.busquedas,
        "lecturas": traza.lecturas,
        "paginas_leidas": list(traza.paginas_leidas),
        "incidencias": list(traza.incidencias),
        "detalle": [dict(paso) for paso in traza.detalle],
    }


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
        return _resumen_de_traza(self.consulta.traza)


class BrazoWikiPrestado:
    """El brazo ``wiki`` sobre un wiki que otra corrida ya construyó: no ingiere, lo sitúa.

    Cada llamada a ``ingerir`` avanza un paper y deja la copia ``paso-N`` del wiki prestado, así
    que el brazo ve exactamente lo que vio en la corrida que lo construyó. Su costo de ingesta es
    cero porque esa corrida ya lo pagó. Sirve para probar otras formas de consulta (por ejemplo
    las capas con grafo) sin reconstruir el conocimiento.
    """

    nombre = "wiki"

    def __init__(
        self,
        modelo: ClienteModelo,
        wiki: Wiki,
        *,
        max_acciones: int = MAX_ACCIONES_POR_DEFECTO,
        paciencia: int = PACIENCIA_POR_DEFECTO,
        spans_validos: Collection[str] | None = None,
        reloj: Callable[[], float] = time.perf_counter,
    ) -> None:
        self.wiki = wiki
        self._paso = 0  # el arnés llama a ingerir desde el primer paper también al reanudar
        self.consulta = ConsultaWiki(
            modelo,
            wiki,
            max_acciones=max_acciones,
            paciencia=paciencia,
            spans_validos=spans_validos,
            reloj=reloj,
        )

    def ingerir(self, arxiv_id: str) -> ResultadoIngesta:
        self._paso += 1
        self.wiki.situar_en_paso(self._paso)
        if arxiv_id not in self.wiki.ingeridos:
            raise ValueError(
                f"El wiki prestado en el paso {self._paso} no contiene {arxiv_id}: "
                "no se construyó con el mismo orden"
            )
        return ResultadoIngesta(
            tokens_entrada=0, tokens_salida=0, segundos=0.0, usd=0.0, llamadas=0
        )

    def responder(self, pregunta: str) -> ResultadoBrazo:
        return self.consulta.responder(pregunta)

    @property
    def ingeridos(self) -> list[str]:
        return list(self.wiki.ingeridos)

    def traza(self) -> dict[str, object]:
        return _resumen_de_traza(self.consulta.traza)


class BrazoWikiCapas:
    """Brazo adicional: el mismo wiki del brazo ``wiki``, consultado con las capas opcionales.

    No ingiere nada (el wiki ya lo escribió el brazo ``wiki``, y su costo se cuenta allí), así
    que añadirlo no obliga a reingerir. Debe ir después del brazo ``wiki`` en la lista de brazos.
    """

    def __init__(
        self,
        nombre: str,
        modelo: ClienteModelo,
        wiki: Wiki,
        capas: CapasDeConsulta,
        *,
        max_acciones: int = MAX_ACCIONES_POR_DEFECTO,
        paciencia: int = PACIENCIA_POR_DEFECTO,
        spans_validos: Collection[str] | None = None,
        reloj: Callable[[], float] = time.perf_counter,
    ) -> None:
        self.nombre = nombre
        self.wiki = wiki
        self.consulta = ConsultaWiki(
            modelo,
            wiki,
            max_acciones=max_acciones,
            paciencia=paciencia,
            spans_validos=spans_validos,
            reloj=reloj,
            capas=capas,
        )

    def ingerir(self, arxiv_id: str) -> ResultadoIngesta:
        return ResultadoIngesta(
            tokens_entrada=0, tokens_salida=0, segundos=0.0, usd=0.0, llamadas=0
        )

    def responder(self, pregunta: str) -> ResultadoBrazo:
        return self.consulta.responder(pregunta)

    @property
    def ingeridos(self) -> list[str]:
        return list(self.wiki.ingeridos)

    def traza(self) -> dict[str, object]:
        return _resumen_de_traza(self.consulta.traza)
