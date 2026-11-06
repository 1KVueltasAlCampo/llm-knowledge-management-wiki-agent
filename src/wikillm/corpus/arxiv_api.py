"""Consulta de metadatos en la API de arXiv (export.arxiv.org/api/query).

La API se rige por sus términos de uso: una petición cada 3 segundos y una sola conexión.
Se usa para verificar metadatos (título, autores, fechas, versión, journal_ref, DOI) y buscar
candidatos, nunca para descargar texto.
"""

from __future__ import annotations

import time
import xml.etree.ElementTree as ET
from collections.abc import Callable, Iterable
from dataclasses import asdict, dataclass, field
from typing import Any

import requests

from wikillm.ingest.arxiv import USER_AGENT

URL_API = "https://export.arxiv.org/api/query"
ESPERA_API = 3.0
TIMEOUT_SEGUNDOS = 60.0
LOTE_IDS = 50
NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "arxiv": "http://arxiv.org/schemas/atom",
    "opensearch": "http://a9.com/-/spec/opensearch/1.1/",
}


class ErrorDeApi(RuntimeError):
    """La API de arXiv no respondió como se esperaba."""


@dataclass
class Registro:
    arxiv_id: str
    version: str
    titulo: str
    autores: list[str]
    fecha_publicacion: str
    fecha_version: str
    categoria: str
    categorias: list[str] = field(default_factory=list)
    journal_ref: str | None = None
    doi: str | None = None
    comentario: str | None = None
    resumen: str = ""

    def como_dict(self) -> dict[str, Any]:
        return asdict(self)


def _texto(nodo: ET.Element, ruta: str) -> str | None:
    hallado = nodo.find(ruta, NS)
    if hallado is None or hallado.text is None:
        return None
    return " ".join(hallado.text.split())


def _separar_version(id_con_version: str) -> tuple[str, str]:
    base, _, version = id_con_version.rpartition("v")
    if not base or not version.isdigit():
        return id_con_version, "v1"
    return base, f"v{version}"


def parsear_feed(xml: str) -> list[Registro]:
    """Convierte la respuesta Atom de la API en registros. Ignora las entradas de error."""
    raiz = ET.fromstring(xml)
    registros: list[Registro] = []
    for entrada in raiz.findall("atom:entry", NS):
        url_id = _texto(entrada, "atom:id") or ""
        if "/abs/" not in url_id:
            continue  # la API devuelve una entrada "Error" para identificadores inválidos
        arxiv_id, version = _separar_version(url_id.rsplit("/abs/", 1)[1])
        primaria = entrada.find("arxiv:primary_category", NS)
        registros.append(
            Registro(
                arxiv_id=arxiv_id,
                version=version,
                titulo=_texto(entrada, "atom:title") or "",
                autores=[
                    nombre
                    for autor in entrada.findall("atom:author", NS)
                    if (nombre := _texto(autor, "atom:name"))
                ],
                fecha_publicacion=(_texto(entrada, "atom:published") or "")[:10],
                fecha_version=(_texto(entrada, "atom:updated") or "")[:10],
                categoria=primaria.get("term", "") if primaria is not None else "",
                categorias=[c.get("term", "") for c in entrada.findall("atom:category", NS)],
                journal_ref=_texto(entrada, "arxiv:journal_ref"),
                doi=_texto(entrada, "arxiv:doi"),
                comentario=_texto(entrada, "arxiv:comment"),
                resumen=_texto(entrada, "atom:summary") or "",
            )
        )
    return registros


class ClienteApi:
    def __init__(
        self,
        sesion: Any = None,
        *,
        dormir: Callable[[float], None] = time.sleep,
        reloj: Callable[[], float] = time.monotonic,
        espera: float = ESPERA_API,
    ) -> None:
        self._sesion = sesion or requests.Session()
        self._dormir = dormir
        self._reloj = reloj
        self._espera = espera
        self._ultima: float | None = None

    def _pedir(self, parametros: dict[str, str]) -> str:
        if self._ultima is not None:
            falta = self._espera - (self._reloj() - self._ultima)
            if falta > 0:
                self._dormir(falta)
        try:
            respuesta = self._sesion.get(
                URL_API,
                params=parametros,
                headers={"User-Agent": USER_AGENT},
                timeout=TIMEOUT_SEGUNDOS,
            )
        except requests.RequestException as error:
            raise ErrorDeApi(type(error).__name__) from None
        finally:
            self._ultima = self._reloj()
        if respuesta.status_code != 200:
            raise ErrorDeApi(f"HTTP {respuesta.status_code}")
        return respuesta.text

    def por_ids(self, ids: Iterable[str]) -> list[Registro]:
        """Metadatos de la última versión de cada identificador, en lotes."""
        lista = list(dict.fromkeys(ids))
        registros: list[Registro] = []
        for inicio in range(0, len(lista), LOTE_IDS):
            lote = lista[inicio : inicio + LOTE_IDS]
            xml = self._pedir({"id_list": ",".join(lote), "max_results": str(len(lote))})
            registros.extend(parsear_feed(xml))
        return registros

    def buscar(self, consulta: str, maximo: int = 100) -> list[Registro]:
        """Búsqueda con la sintaxis de la API (p. ej. `abs:"LLM wiki"`), más recientes primero."""
        xml = self._pedir(
            {
                "search_query": consulta,
                "max_results": str(maximo),
                "sortBy": "submittedDate",
                "sortOrder": "descending",
            }
        )
        return parsear_feed(xml)
