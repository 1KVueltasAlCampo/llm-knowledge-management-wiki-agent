"""Descarga cortés y capa Bronze, con una sesión HTTP y un reloj falsos (sin red)."""

import hashlib
import json
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from wikillm.ingest import arxiv
from wikillm.ingest.arxiv import (
    USER_AGENT,
    ClienteArxiv,
    ErrorDeDescarga,
    RutaProhibida,
    descargar_paper,
    leer_ids,
    ultima_captura,
)

ROBOTS = b"User-agent: *\nCrawl-delay: 15\nDisallow: /prohibido\nAllow: /html\nAllow: /abs\n"
AHORA = datetime(2026, 11, 5, 12, 0, tzinfo=UTC)


class Reloj:
    def __init__(self):
        self.t = 0.0
        self.esperas = []

    def __call__(self):
        return self.t

    def dormir(self, segundos):
        self.esperas.append(segundos)
        self.t += segundos


class SesionFalsa:
    def __init__(self, reloj, respuestas):
        self.reloj = reloj
        self.respuestas = respuestas
        self.llamadas = []  # (url, instante, encabezados)

    def get(self, url, headers=None, timeout=None, allow_redirects=True):
        self.llamadas.append((url, self.reloj(), headers))
        estado, contenido = self.respuestas.get(url, (404, b""))
        return SimpleNamespace(status_code=estado, content=contenido, url=url)


def crear(respuestas, espera_por_defecto=15.0):
    reloj = Reloj()
    sesion = SesionFalsa(reloj, {"https://arxiv.org/robots.txt": (200, ROBOTS), **respuestas})
    cliente = ClienteArxiv(
        sesion, dormir=reloj.dormir, reloj=reloj, espera_por_defecto=espera_por_defecto
    )
    return cliente, sesion, reloj


def test_leer_ids_ignora_comentarios_vacios_y_duplicados(tmp_path):
    archivo = tmp_path / "ids.txt"
    archivo.write_text(
        "# cabecera\n\n2405.14831  # HippoRAG\n2502.14802\n2405.14831\n  # otro\n", encoding="utf-8"
    )
    assert leer_ids(archivo) == ["2405.14831", "2502.14802"]


def test_leer_ids_rechaza_identificadores_invalidos(tmp_path):
    archivo = tmp_path / "ids.txt"
    archivo.write_text("hola\n", encoding="utf-8")
    with pytest.raises(ValueError, match="no válido"):
        leer_ids(archivo)


def test_espera_el_crawl_delay_entre_peticiones():
    cliente, sesion, _ = crear(
        {"https://arxiv.org/html/1": (200, b"a"), "https://arxiv.org/html/2": (200, b"b")}
    )
    cliente.descargar("https://arxiv.org/html/1")
    cliente.descargar("https://arxiv.org/html/2")
    instantes = [instante for _url, instante, _h in sesion.llamadas]
    assert len(instantes) == 3  # robots.txt y dos páginas
    assert all(b - a >= 15 for a, b in zip(instantes, instantes[1:], strict=False))
    assert cliente.espera == 15


def test_usa_el_crawl_delay_declarado_por_el_sitio():
    robots = b"User-agent: *\nCrawl-delay: 20\n"
    cliente, sesion, _ = crear(
        {"https://arxiv.org/robots.txt": (200, robots), "https://arxiv.org/html/1": (200, b"a")}
    )
    cliente.descargar("https://arxiv.org/html/1")
    assert cliente.espera == 20


def test_una_ruta_prohibida_no_se_descarga():
    cliente, sesion, _ = crear({"https://arxiv.org/prohibido/x": (200, b"secreto")})
    with pytest.raises(RutaProhibida):
        cliente.descargar("https://arxiv.org/prohibido/x")
    assert [url for url, _i, _h in sesion.llamadas] == ["https://arxiv.org/robots.txt"]


def test_si_robots_no_se_puede_leer_se_usa_la_espera_por_defecto():
    cliente, sesion, _ = crear(
        {"https://arxiv.org/robots.txt": (500, b""), "https://arxiv.org/html/1": (200, b"a")}
    )
    cliente.descargar("https://arxiv.org/html/1")
    assert cliente.espera == 15


def test_el_nombre_de_cliente_es_generico():
    cliente, sesion, _ = crear({"https://arxiv.org/html/1": (200, b"a")})
    cliente.descargar("https://arxiv.org/html/1")
    assert all(encabezados["User-Agent"] == USER_AGENT for _u, _i, encabezados in sesion.llamadas)
    assert "@" not in USER_AGENT
    assert "gmail" not in USER_AGENT.lower()


def test_descarga_correcta_guarda_bronze_y_registra_la_captura(tmp_path):
    html, resumen = b"<html>contenido</html>", b"<html>resumen</html>"
    cliente, _, _ = crear(
        {
            "https://arxiv.org/html/2401.00001": (200, html),
            "https://arxiv.org/abs/2401.00001": (200, resumen),
        }
    )
    fallos = descargar_paper(cliente, "2401.00001", tmp_path, ahora=lambda: AHORA)
    assert fallos == []
    carpeta = tmp_path / "raw" / "2401.00001"
    assert (carpeta / "page.html").read_bytes() == html
    assert (carpeta / "abs.html").read_bytes() == resumen
    capturas = [json.loads(c) for c in (carpeta / "capture.jsonl").read_text().splitlines()]
    assert [c["tipo"] for c in capturas] == ["html", "abs"]
    assert capturas[0]["estado"] == 200
    assert capturas[0]["hash"] == hashlib.sha256(html).hexdigest()
    assert ultima_captura(carpeta, "html")["url"] == "https://arxiv.org/html/2401.00001"


def test_un_404_se_registra_y_no_deja_archivo(tmp_path):
    cliente, _, _ = crear({"https://arxiv.org/abs/2401.00001": (200, b"resumen")})
    fallos = descargar_paper(cliente, "2401.00001", tmp_path, ahora=lambda: AHORA)
    carpeta = tmp_path / "raw" / "2401.00001"
    assert any("HTTP 404" in fallo for fallo in fallos)
    assert not (carpeta / "page.html").exists()
    assert ultima_captura(carpeta, "html") is None
    primera = json.loads((carpeta / "capture.jsonl").read_text().splitlines()[0])
    assert primera["estado"] == 404


def test_un_error_de_red_se_registra_como_fallo(tmp_path, monkeypatch):
    cliente, _, _ = crear({})
    monkeypatch.setattr(
        cliente, "descargar", lambda url: (_ for _ in ()).throw(ErrorDeDescarga("X"))
    )
    fallos = descargar_paper(cliente, "2401.00001", tmp_path, ahora=lambda: AHORA)
    assert len(fallos) == 2
    assert all("X" in fallo for fallo in fallos)


def test_segunda_ejecucion_no_vuelve_a_descargar(tmp_path):
    respuestas = {
        "https://arxiv.org/html/2401.00001": (200, b"a"),
        "https://arxiv.org/abs/2401.00001": (200, b"b"),
    }
    cliente, sesion, _ = crear(respuestas)
    descargar_paper(cliente, "2401.00001", tmp_path, ahora=lambda: AHORA)
    peticiones = len(sesion.llamadas)
    otro_cliente = ClienteArxiv(sesion, dormir=lambda _s: None, reloj=lambda: 0.0)
    descargar_paper(otro_cliente, "2401.00001", tmp_path, ahora=lambda: AHORA)
    assert len(sesion.llamadas) == peticiones


def test_refrescar_vuelve_a_descargar(tmp_path):
    respuestas = {
        "https://arxiv.org/html/2401.00001": (200, b"a"),
        "https://arxiv.org/abs/2401.00001": (200, b"b"),
    }
    cliente, sesion, _ = crear(respuestas)
    descargar_paper(cliente, "2401.00001", tmp_path, ahora=lambda: AHORA)
    antes = len(sesion.llamadas)
    descargar_paper(cliente, "2401.00001", tmp_path, refrescar=True, ahora=lambda: AHORA)
    assert len(sesion.llamadas) == antes + 2


def test_modulo_expone_la_espera_por_defecto_de_arxiv():
    assert arxiv.ESPERA_POR_DEFECTO == 15.0
