"""Descarga cortés de papers de arXiv (capa Bronze).

Respeta robots.txt (Disallow y Crawl-delay), espera entre peticiones y se identifica con un
nombre de cliente genérico, sin datos personales.
"""

from __future__ import annotations

import hashlib
import json
import re
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib import robotparser

import requests

USER_AGENT = "wikillm-tesis-icesi/0.1 (proyecto academico)"
BASE_ARXIV = "https://arxiv.org"
ESPERA_POR_DEFECTO = 15.0
TIMEOUT_SEGUNDOS = 30.0
PATRON_ID = re.compile(r"^\d{4}\.\d{4,5}$")


class RutaProhibida(RuntimeError):
    """robots.txt prohíbe descargar esa ruta."""


class ErrorDeDescarga(RuntimeError):
    """No se pudo completar la petición."""


@dataclass(frozen=True)
class Descarga:
    url: str
    url_final: str
    estado: int
    contenido: bytes


def leer_ids(ruta: Path | str) -> list[str]:
    """Lee identificadores de arXiv, uno por línea. Ignora vacías y comentarios con #."""
    ids: list[str] = []
    for linea in Path(ruta).read_text(encoding="utf-8").splitlines():
        identificador = linea.split("#", 1)[0].strip()
        if not identificador:
            continue
        if not PATRON_ID.match(identificador):
            raise ValueError(f"Identificador de arXiv no válido: {identificador!r}")
        if identificador not in ids:
            ids.append(identificador)
    return ids


class ClienteArxiv:
    def __init__(
        self,
        sesion: Any = None,
        *,
        dormir: Callable[[float], None] = time.sleep,
        reloj: Callable[[], float] = time.monotonic,
        espera_por_defecto: float = ESPERA_POR_DEFECTO,
        base: str = BASE_ARXIV,
        avisar: Callable[[str], None] | None = None,
    ) -> None:
        self._sesion = sesion or requests.Session()
        self._dormir = dormir
        self._reloj = reloj
        self._base = base.rstrip("/")
        self._avisar = avisar or (lambda _mensaje: None)
        self._espera = espera_por_defecto
        self._espera_por_defecto = espera_por_defecto
        self._ultima: float | None = None
        self._robots: robotparser.RobotFileParser | None = None

    @property
    def espera(self) -> float:
        return self._espera

    def descargar(self, url: str) -> Descarga:
        """Descarga una URL tras consultar robots.txt y esperar el Crawl-delay."""
        if self._robots is None:
            self._robots = self._cargar_robots()
        if not self._robots.can_fetch(USER_AGENT, url):
            raise RutaProhibida(f"robots.txt prohíbe descargar {url}")
        respuesta = self._pedir(url)
        return Descarga(url, str(respuesta.url), int(respuesta.status_code), respuesta.content)

    def _cargar_robots(self) -> robotparser.RobotFileParser:
        reglas = robotparser.RobotFileParser()
        try:
            respuesta = self._pedir(f"{self._base}/robots.txt")
        except ErrorDeDescarga:
            self._avisar("  no se pudo leer robots.txt: se usa la espera por defecto")
            reglas.allow_all = True
            return reglas
        if respuesta.status_code == 200:
            reglas.parse(respuesta.content.decode("utf-8", errors="replace").splitlines())
            reglas.modified()  # sin esto can_fetch() siempre responde False
            retraso = reglas.crawl_delay("*")
            self._espera = float(retraso) if retraso is not None else self._espera_por_defecto
        else:
            reglas.allow_all = True
        return reglas

    def _pedir(self, url: str) -> Any:
        self._esperar()
        try:
            respuesta = self._sesion.get(
                url,
                headers={"User-Agent": USER_AGENT},
                timeout=TIMEOUT_SEGUNDOS,
                allow_redirects=True,
            )
        except requests.RequestException as error:
            raise ErrorDeDescarga(type(error).__name__) from None
        self._ultima = self._reloj()
        return respuesta

    def _esperar(self) -> None:
        if self._ultima is None:
            return
        falta = self._espera - (self._reloj() - self._ultima)
        if falta > 0:
            self._avisar(f"  esperando {falta:.0f} s (Crawl-delay del sitio)")
            self._dormir(falta)


def ahora_utc() -> datetime:
    return datetime.now(UTC)


def leer_capturas(carpeta: Path) -> list[dict[str, Any]]:
    archivo = carpeta / "capture.jsonl"
    if not archivo.exists():
        return []
    lineas = archivo.read_text(encoding="utf-8").splitlines()
    return [json.loads(linea) for linea in lineas if linea.strip()]


def ultima_captura(carpeta: Path, tipo: str) -> dict[str, Any] | None:
    """Última captura correcta (estado 200) del tipo pedido: 'html' o 'abs'."""
    correctas = [c for c in leer_capturas(carpeta) if c["tipo"] == tipo and c["estado"] == 200]
    return correctas[-1] if correctas else None


def _registrar(carpeta: Path, linea: dict[str, Any]) -> None:
    carpeta.mkdir(parents=True, exist_ok=True)
    with (carpeta / "capture.jsonl").open("a", encoding="utf-8") as archivo:
        archivo.write(json.dumps(linea, ensure_ascii=False) + "\n")


def descargar_paper(
    cliente: ClienteArxiv,
    arxiv_id: str,
    datos: Path,
    *,
    refrescar: bool = False,
    ahora: Callable[[], datetime] = ahora_utc,
    avisar: Callable[[str], None] | None = None,
) -> list[str]:
    """Guarda en Bronze el HTML y la página de resumen de un paper. Devuelve los fallos."""
    avisar = avisar or (lambda _mensaje: None)
    carpeta = datos / "raw" / arxiv_id
    fallos: list[str] = []
    destinos = (
        ("html", f"{BASE_ARXIV}/html/{arxiv_id}", "page.html"),
        ("abs", f"{BASE_ARXIV}/abs/{arxiv_id}", "abs.html"),
    )
    for tipo, url, nombre in destinos:
        if (carpeta / nombre).exists() and not refrescar:
            avisar(f"  {nombre} ya está en Bronze: no se descarga")
            continue
        avisar(f"  descargando {url}")
        linea: dict[str, Any] = {
            "tipo": tipo,
            "arxiv_id": arxiv_id,
            "url": url,
            "fecha": ahora().astimezone(UTC).isoformat(),
        }
        try:
            descarga = cliente.descargar(url)
        except (RutaProhibida, ErrorDeDescarga) as error:
            _registrar(carpeta, {**linea, "url_final": None, "estado": 0, "hash": None})
            fallos.append(f"{arxiv_id} ({tipo}): {error}")
            continue
        huella = hashlib.sha256(descarga.contenido).hexdigest() if descarga.contenido else None
        _registrar(
            carpeta,
            {**linea, "url_final": descarga.url_final, "estado": descarga.estado, "hash": huella},
        )
        if descarga.estado != 200:
            fallos.append(f"{arxiv_id} ({tipo}): HTTP {descarga.estado}")
            continue
        (carpeta / nombre).write_bytes(descarga.contenido)
    return fallos
