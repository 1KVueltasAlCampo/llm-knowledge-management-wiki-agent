"""Servidor local del panel: una página, una API pequeña y un flujo SSE por trabajo.

Escucha solo en 127.0.0.1, rechaza peticiones cuyo ``Host`` u ``Origin`` no sean locales y solo
ejecuta acciones del catálogo con parámetros validados. Un trabajo a la vez; sus eventos se
transmiten en orden desde el principio y se guardan para poder reproducirlos.
"""

from __future__ import annotations

import json
import threading
from datetime import UTC, datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit

from wikillm.common.config import load_settings
from wikillm.common.costo import es_hora_pico
from wikillm.panel import datos, ejemplos
from wikillm.panel.acciones import (
    CATALOGO,
    POR_ID,
    WIKI_DEMO,
    AccionDesconocida,
    ConfirmacionRequerida,
    Ejecutor,
    GastoDeSesion,
    ParametroInvalido,
    TopeDeSesion,
)
from wikillm.panel.archivos import ArchivoNoPermitido, Archivos
from wikillm.panel.trabajos import GestorDeTrabajos, SinGrabacion, Trabajo, TrabajoEnCurso

PAGINA = Path(__file__).parent / "static" / "index.html"
HOSTS_LOCALES = {"127.0.0.1", "localhost", "::1"}
LIMITE_DEL_CUERPO = 20_000
LIMITE_DE_LECTURA = 1_000_000
ESPERA_DEL_FLUJO = 15.0
CABECERAS_DE_SEGURIDAD = {
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "Cache-Control": "no-store",
    "Content-Security-Policy": (
        "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; "
        "connect-src 'self'; img-src data:; base-uri 'none'; form-action 'none'"
    ),
}


class Panel:
    """Estado compartido del servidor: archivos, ejecutor, trabajos y gasto de la sesión."""

    def __init__(
        self,
        raiz: Path,
        *,
        tope_usd: float = 0.25,
        ejecutor: Ejecutor | None = None,
        espera_del_flujo: float = ESPERA_DEL_FLUJO,
        gestor: GestorDeTrabajos | None = None,
    ) -> None:
        self.raiz = raiz.resolve()
        self.archivos = Archivos(self.raiz)
        self.ejecutor = ejecutor or Ejecutor(self.raiz, GastoDeSesion(tope_usd))
        self.gasto = self.ejecutor.gasto
        self.gestor = gestor or GestorDeTrabajos(
            self.raiz / "results" / "demo" / "grabaciones", observador=self._observar
        )
        self.espera_del_flujo = espera_del_flujo
        self.ajustes = load_settings()
        self.inicio = datetime.now(UTC)

    def _observar(self, trabajo: Trabajo, evento: dict[str, Any]) -> None:
        if evento.get("t") == "llamada" and not evento.get("repro"):
            self.gasto.sumar(float(evento.get("usd", 0.0)))

    def estado(self) -> dict[str, Any]:
        activo = self.gestor.activo
        wiki = datos.estado_del_wiki(self.raiz, WIKI_DEMO)
        return {
            "ocupado": None
            if activo is None
            else {"id": activo.id, "accion": activo.accion, "titulo": activo.titulo},
            "gasto": {
                "sesion_usd": round(self.gasto.total, 6),
                "tope_usd": self.gasto.tope,
                "agotado": self.gasto.agotado,
            },
            "rag_listo": self.ejecutor.rag_listo,
            "modelo": self.ajustes.model,
            "clave_presente": bool(self.ajustes.api_key),
            "hora_pico": es_hora_pico(datetime.now(UTC)),
            "wiki": wiki,
            "corpus": datos.corpus(self.raiz, wiki["ids"]),
            "grabaciones": self.gestor.grabaciones(),
        }


def _criterio(coincide: dict[str, Any] | None) -> Any:
    if not coincide:
        return None

    def criterio(encabezado: dict[str, Any]) -> bool:
        parametros = encabezado.get("parametros") or {}
        return all(parametros.get(k) == v for k, v in coincide.items())

    return criterio


class ServidorPanel(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, direccion: tuple[str, int], panel: Panel) -> None:
        super().__init__(direccion, ManejadorPanel)
        self.panel = panel

    def handle_error(self, request: Any, client_address: Any) -> None:
        pass  # no escribir en stderr: allí se captura la salida de la acción en curso


class ManejadorPanel(BaseHTTPRequestHandler):
    server: ServidorPanel
    server_version = "PanelWikiLLM"

    # --- utilidades -------------------------------------------------------------------------
    def log_message(self, formato: str, *argumentos: Any) -> None:
        pass

    @property
    def panel(self) -> Panel:
        return self.server.panel

    def _enviar(
        self, codigo: int, cuerpo: bytes, tipo: str, extra: dict[str, str] | None = None
    ) -> None:
        self.send_response(codigo)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(cuerpo)))
        for nombre, valor in (CABECERAS_DE_SEGURIDAD | (extra or {})).items():
            self.send_header(nombre, valor)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(cuerpo)

    def _json(self, codigo: int, objeto: Any) -> None:
        cuerpo = json.dumps(objeto, ensure_ascii=False).encode("utf-8")
        self._enviar(codigo, cuerpo, "application/json; charset=utf-8")

    def _error(self, codigo: int, mensaje: str) -> None:
        self._json(codigo, {"error": mensaje})

    def _host_local(self) -> bool:
        host = urlsplit("//" + (self.headers.get("Host") or "")).hostname or ""
        return host.lower() in HOSTS_LOCALES

    def _origen_local(self) -> bool:
        """Sin ``Origin`` (órdenes directas) o con el de esta misma página; nunca de otra."""
        origen = self.headers.get("Origin")
        if origen is None:
            return True
        try:
            partes = urlsplit(origen)
            return (
                partes.scheme == "http"
                and (partes.hostname or "") in HOSTS_LOCALES
                and partes.port == self.server.server_port
            )
        except ValueError:
            return False

    def _desde(self, consulta: dict[str, list[str]]) -> int:
        """Primer evento que pide el cliente: tras el último recibido o desde ``?desde=``."""
        ultimo = self.headers.get("Last-Event-ID")
        if ultimo is not None and ultimo.isdigit():
            return int(ultimo) + 1
        texto = (consulta.get("desde") or ["0"])[0]
        return int(texto) if texto.isdigit() else 0

    def _permitido(self, *, escritura: bool) -> bool:
        if not self._host_local():
            self._error(HTTPStatus.FORBIDDEN, "Solo se atiende desde esta máquina")
            return False
        if escritura and not self._origen_local():
            self._error(HTTPStatus.FORBIDDEN, "Origen no permitido")
            return False
        return True

    def _leer_cuerpo(self) -> bytes | None:
        """Lee y descarta siempre el cuerpo enviado: si no, al rechazar se corta la conexión."""
        try:
            largo = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            largo = -1
        if not 0 <= largo <= LIMITE_DE_LECTURA:
            self._error(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, "Cuerpo demasiado grande")
            self.close_connection = True
            return None
        return self.rfile.read(largo)

    def _cuerpo_json(self, bruto: bytes) -> dict[str, Any] | None:
        if not (self.headers.get("Content-Type") or "").startswith("application/json"):
            self._error(HTTPStatus.UNSUPPORTED_MEDIA_TYPE, "Se espera application/json")
            return None
        if len(bruto) > LIMITE_DEL_CUERPO:
            self._error(HTTPStatus.BAD_REQUEST, "Cuerpo demasiado grande")
            return None
        try:
            cuerpo = json.loads(bruto or b"{}")
        except json.JSONDecodeError:
            self._error(HTTPStatus.BAD_REQUEST, "JSON no válido")
            return None
        if not isinstance(cuerpo, dict):
            self._error(HTTPStatus.BAD_REQUEST, "Se espera un objeto JSON")
            return None
        return cuerpo

    # --- GET --------------------------------------------------------------------------------
    def do_GET(self) -> None:
        if not self._permitido(escritura=False):
            return
        url = urlsplit(self.path)
        consulta = parse_qs(url.query)
        ruta = url.path
        if ruta == "/":
            self._pagina()
        elif ruta == "/api/estado":
            self._json(HTTPStatus.OK, self.panel.estado())
        elif ruta == "/api/acciones":
            self._json(HTTPStatus.OK, [a.a_json() for a in CATALOGO])
        elif ruta == "/api/ejemplos":
            self._json(HTTPStatus.OK, ejemplos.a_json())
        elif ruta == "/api/archivos":
            self._json(HTTPStatus.OK, self.panel.archivos.listar())
        elif ruta == "/api/archivo":
            self._archivo(consulta.get("ruta", [""])[0])
        elif ruta == "/api/metricas":
            self._json(HTTPStatus.OK, datos.leer_metricas(self.panel.raiz))
        elif ruta.startswith("/api/eventos/"):
            self._flujo(ruta.rsplit("/", 1)[-1], consulta)
        else:
            self._error(HTTPStatus.NOT_FOUND, "No existe")

    def _pagina(self) -> None:
        try:
            cuerpo = PAGINA.read_bytes()
        except OSError:
            self._error(HTTPStatus.INTERNAL_SERVER_ERROR, "Falta panel/static/index.html")
            return
        self._enviar(HTTPStatus.OK, cuerpo, "text/html; charset=utf-8")

    def _archivo(self, ruta: str) -> None:
        try:
            self._json(HTTPStatus.OK, self.panel.archivos.leer(ruta))
        except ArchivoNoPermitido as error:
            self._error(HTTPStatus.FORBIDDEN, str(error))
        except OSError:
            self._error(HTTPStatus.NOT_FOUND, "No se pudo leer el archivo")

    def _flujo(self, identificador: str, consulta: dict[str, list[str]]) -> None:
        trabajo = self.panel.gestor.trabajo(identificador)
        if trabajo is None:
            self._error(HTTPStatus.NOT_FOUND, "No existe ese trabajo")
            return
        desde = self._desde(consulta)
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Connection", "close")
        self.send_header("X-Accel-Buffering", "no")
        for nombre, valor in CABECERAS_DE_SEGURIDAD.items():
            self.send_header(nombre, valor)
        self.end_headers()
        self.close_connection = True
        try:
            while True:
                nuevos, terminado = self.panel.gestor.esperar_eventos(
                    trabajo, desde, self.panel.espera_del_flujo
                )
                for evento in nuevos:
                    texto = json.dumps(evento, ensure_ascii=False)
                    self.wfile.write(f"id: {evento['n']}\ndata: {texto}\n\n".encode())
                    desde = evento["n"] + 1
                if not nuevos:
                    self.wfile.write(b": ping\n\n")
                self.wfile.flush()
                if terminado:
                    return
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError, OSError):
            return

    # --- POST -------------------------------------------------------------------------------
    def do_POST(self) -> None:
        bruto = self._leer_cuerpo()
        if bruto is None or not self._permitido(escritura=True):
            return
        ruta = urlsplit(self.path).path
        if ruta not in ("/api/ejecutar", "/api/reproducir"):
            self._error(HTTPStatus.NOT_FOUND, "No existe")
            return
        cuerpo = self._cuerpo_json(bruto)
        if cuerpo is None:
            return
        if ruta == "/api/ejecutar":
            self._ejecutar(cuerpo)
        else:
            self._reproducir(cuerpo)

    def _ejecutar(self, cuerpo: dict[str, Any]) -> None:
        panel = self.panel
        try:
            accion, valores = panel.ejecutor.preparar(
                cuerpo.get("accion"), cuerpo.get("parametros"), cuerpo.get("confirmo") is True
            )
        except (AccionDesconocida, ParametroInvalido, ConfirmacionRequerida) as error:
            self._error(HTTPStatus.BAD_REQUEST, str(error))
            return
        except TopeDeSesion as error:
            self._error(HTTPStatus.FORBIDDEN, str(error))
            return
        try:
            trabajo = panel.gestor.lanzar(
                accion.id,
                accion.titulo,
                panel.ejecutor.funcion(accion, valores),
                grabar=accion.grabar,
                parametros=panel.ejecutor.parametros_grabados(accion, valores),
            )
        except TrabajoEnCurso as error:
            self._error(HTTPStatus.CONFLICT, str(error))
            return
        self._json(HTTPStatus.ACCEPTED, {"trabajo": trabajo.id, "accion": accion.id})

    def _reproducir(self, cuerpo: dict[str, Any]) -> None:
        accion = POR_ID.get(cuerpo.get("accion")) if isinstance(cuerpo.get("accion"), str) else None
        coincide = cuerpo.get("coincide")
        if accion is None or not accion.grabar or not isinstance(coincide, dict | None):
            self._error(HTTPStatus.BAD_REQUEST, "Acción no reproducible")
            return
        try:
            trabajo = self.panel.gestor.reproducir(
                accion.id, f"Reproducción · {accion.titulo}", _criterio(coincide)
            )
        except SinGrabacion as error:
            self._error(HTTPStatus.NOT_FOUND, str(error))
        except TrabajoEnCurso as error:
            self._error(HTTPStatus.CONFLICT, str(error))
        else:
            self._json(HTTPStatus.ACCEPTED, {"trabajo": trabajo.id, "accion": accion.id})


def crear_servidor(panel: Panel, puerto: int = 8765) -> ServidorPanel:
    return ServidorPanel(("127.0.0.1", puerto), panel)


def servir_en_hilo(servidor: ServidorPanel) -> threading.Thread:
    hilo = threading.Thread(target=servidor.serve_forever, daemon=True, name="panel-http")
    hilo.start()
    return hilo
