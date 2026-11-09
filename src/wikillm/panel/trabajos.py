"""Trabajos del panel: uno a la vez, en un hilo, con eventos ordenados, grabación y reproducción.

Un solo hilo ejecuta todos los trabajos: los clientes de Chroma y del modelo de embeddings se
crean y se usan en él, y dos operaciones no pueden pisarse el estado (el wiki cambia al ingerir).
Cada evento lleva su número de orden (`n`) y su tiempo relativo (`ts`). Al terminar, los eventos
se guardan; una reproducción los vuelve a emitir con esos tiempos y los marca como reproducidos.
"""

from __future__ import annotations

import contextlib
import json
import queue
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

Emitir = Callable[[dict[str, Any]], None]
Funcion = Callable[[Emitir], int | None]
Observador = Callable[["Trabajo", dict[str, Any]], None]
ESPERA_MAXIMA_REPRODUCCION = 3.0
EVENTOS_REGENERADOS = ("inicio", "fin")


class TrabajoEnCurso(RuntimeError):
    """Ya hay un trabajo ejecutándose o en cola."""


class SinGrabacion(LookupError):
    """No hay ninguna ejecución guardada de esa acción."""


@dataclass
class Trabajo:
    id: str
    accion: str
    titulo: str
    reproduccion: bool = False
    estado: str = "en_cola"  # en_cola | corriendo | terminado | error
    codigo: int | None = None
    inicio: float = 0.0
    eventos: list[dict[str, Any]] = field(default_factory=list)
    condicion: threading.Condition = field(default_factory=threading.Condition)

    @property
    def terminado(self) -> bool:
        return self.estado in ("terminado", "error")


class GestorDeTrabajos:
    def __init__(
        self,
        carpeta_grabaciones: Path,
        *,
        reloj: Callable[[], float] = time.monotonic,
        esperar: Callable[[float], None] = time.sleep,
        ahora: Callable[[], datetime] = lambda: datetime.now(UTC),
        observador: Observador | None = None,
    ) -> None:
        self._carpeta = carpeta_grabaciones
        self._reloj = reloj
        self._esperar = esperar
        self._ahora = ahora
        self._observador = observador
        self._cola: queue.Queue[tuple[Trabajo, Funcion, bool, dict[str, Any]]] = queue.Queue()
        self._trabajos: dict[str, Trabajo] = {}
        self._activo: Trabajo | None = None
        self._cerrojo = threading.Lock()
        self._contador = 0
        threading.Thread(target=self._bucle, daemon=True, name="panel-trabajos").start()

    # --- consulta ---------------------------------------------------------------------------
    def trabajo(self, identificador: str) -> Trabajo | None:
        return self._trabajos.get(identificador)

    @property
    def activo(self) -> Trabajo | None:
        activo = self._activo
        return activo if activo is not None and not activo.terminado else None

    def grabaciones(self) -> list[dict[str, Any]]:
        """Encabezados de las grabaciones, de la más antigua a la más reciente."""
        return [{"archivo": ruta.name, **self._encabezado(ruta)} for ruta in self._rutas()]

    def _rutas(self, accion: str = "*") -> list[Path]:
        return sorted(self._carpeta.glob(f"*-{accion}.jsonl"))

    @staticmethod
    def _encabezado(ruta: Path) -> dict[str, Any]:
        with ruta.open(encoding="utf-8") as archivo:
            primera = archivo.readline()
        try:
            meta = json.loads(primera) if primera.strip() else {}
        except json.JSONDecodeError:
            return {}
        return {k: v for k, v in meta.items() if k != "t"}

    def ultima_grabacion(
        self, accion: str, criterio: Callable[[dict[str, Any]], bool] | None = None
    ) -> Path | None:
        """La grabación más reciente de la acción cuyo encabezado cumple ``criterio``."""
        for ruta in reversed(self._rutas(accion)):
            if criterio is None or criterio(self._encabezado(ruta)):
                return ruta
        return None

    # --- lanzar -----------------------------------------------------------------------------
    def lanzar(
        self,
        accion: str,
        titulo: str,
        funcion: Funcion,
        *,
        grabar: bool = True,
        parametros: dict[str, Any] | None = None,
        reproduccion: bool = False,
    ) -> Trabajo:
        with self._cerrojo:
            if self.activo is not None:
                raise TrabajoEnCurso(f"Hay un trabajo en curso: {self.activo.titulo}")
            self._contador += 1
            trabajo = Trabajo(f"t{self._contador}", accion, titulo, reproduccion=reproduccion)
            self._trabajos[trabajo.id] = trabajo
            self._activo = trabajo
        self._cola.put((trabajo, funcion, grabar and not reproduccion, parametros or {}))
        return trabajo

    def reproducir(
        self,
        accion: str,
        titulo: str,
        criterio: Callable[[dict[str, Any]], bool] | None = None,
    ) -> Trabajo:
        ruta = self.ultima_grabacion(accion, criterio)
        if ruta is None:
            raise SinGrabacion(f"No hay ninguna ejecución guardada de «{accion}» que corresponda")
        lineas = [json.loads(x) for x in ruta.read_text("utf-8").splitlines() if x.strip()]
        meta = lineas[0] if lineas and lineas[0].get("t") == "meta" else {}
        eventos = [e for e in lineas if e.get("t") not in ("meta", *EVENTOS_REGENERADOS)]

        def funcion(emitir: Emitir) -> int:
            emitir({"t": "repro", "grabacion": ruta.name, "fecha": meta.get("fecha")})
            anterior = 0.0
            for evento in eventos:
                momento = float(evento.get("ts", 0.0))
                self._esperar(min(max(momento - anterior, 0.0), ESPERA_MAXIMA_REPRODUCCION))
                anterior = momento
                emitir({k: v for k, v in evento.items() if k not in ("n", "ts", "repro")})
            return int(meta.get("codigo", 0))

        return self.lanzar(accion, titulo, funcion, grabar=False, reproduccion=True)

    # --- ejecución --------------------------------------------------------------------------
    def _bucle(self) -> None:
        while True:
            trabajo, funcion, grabar, parametros = self._cola.get()
            try:
                self._ejecutar(trabajo, funcion, grabar, parametros)
            except Exception:  # un fallo del propio gestor no debe dejar el panel colgado
                with trabajo.condicion:
                    trabajo.codigo, trabajo.estado = 1, "error"
                    trabajo.condicion.notify_all()

    def _emisor(self, trabajo: Trabajo) -> Emitir:
        def emitir(evento: dict[str, Any]) -> None:
            with trabajo.condicion:
                completo = {
                    **evento,
                    "n": len(trabajo.eventos),
                    "ts": round(self._reloj() - trabajo.inicio, 2),
                }
                if trabajo.reproduccion:
                    completo["repro"] = True
                trabajo.eventos.append(completo)
                trabajo.condicion.notify_all()
            if self._observador is not None:
                with contextlib.suppress(Exception):  # observar nunca debe romper el trabajo
                    self._observador(trabajo, completo)

        return emitir

    def _ejecutar(
        self, trabajo: Trabajo, funcion: Funcion, grabar: bool, parametros: dict[str, Any]
    ) -> None:
        trabajo.estado = "corriendo"
        trabajo.inicio = self._reloj()
        emitir = self._emisor(trabajo)
        emitir(
            {
                "t": "inicio",
                "accion": trabajo.accion,
                "titulo": trabajo.titulo,
                "reproduccion": trabajo.reproduccion,
            }
        )
        try:
            codigo = funcion(emitir)
        except (Exception, SystemExit) as error:  # un fallo se informa y el servidor sigue
            emitir({"t": "error", "mensaje": f"{type(error).__name__}: {error}"})
            codigo = 1
        codigo = 0 if codigo is None else int(codigo)
        emitir({"t": "fin", "codigo": codigo, "segundos": round(self._reloj() - trabajo.inicio, 2)})
        trabajo.codigo = codigo
        if grabar:  # antes de anunciar el final: quien vea el trabajo terminado ya lo encuentra
            with contextlib.suppress(OSError):
                self._grabar(trabajo, parametros)
        with trabajo.condicion:
            trabajo.estado = "terminado" if codigo == 0 else "error"
            trabajo.condicion.notify_all()

    def _grabar(self, trabajo: Trabajo, parametros: dict[str, Any]) -> None:
        self._carpeta.mkdir(parents=True, exist_ok=True)
        momento = self._ahora()
        ruta = self._ruta_nueva(momento, trabajo.accion)
        meta = {
            "t": "meta",
            "accion": trabajo.accion,
            "titulo": trabajo.titulo,
            "parametros": parametros,
            "fecha": momento.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "codigo": trabajo.codigo,
        }
        with ruta.open("w", encoding="utf-8") as archivo:
            for evento in [meta, *trabajo.eventos]:
                archivo.write(json.dumps(evento, ensure_ascii=False) + "\n")

    def _ruta_nueva(self, momento: datetime, accion: str) -> Path:
        """Nombre ordenable por fecha (hasta el milisegundo) que no pisa otra grabación."""
        while True:
            ruta = self._carpeta / (
                f"{momento:%Y%m%d-%H%M%S}-{momento.microsecond // 1000:03d}-{accion}.jsonl"
            )
            if not ruta.exists():
                return ruta
            momento += timedelta(milliseconds=1)

    # --- lectura para SSE -------------------------------------------------------------------
    def esperar_eventos(
        self, trabajo: Trabajo, desde: int, espera: float = 15.0
    ) -> tuple[list[dict[str, Any]], bool]:
        """Eventos a partir de ``desde`` (espera hasta ``espera`` s) y si el trabajo ya terminó."""
        with trabajo.condicion:
            if desde >= len(trabajo.eventos) and not trabajo.terminado:
                trabajo.condicion.wait(timeout=espera)
            nuevos = trabajo.eventos[desde:]
            return nuevos, trabajo.terminado and desde + len(nuevos) >= len(trabajo.eventos)
