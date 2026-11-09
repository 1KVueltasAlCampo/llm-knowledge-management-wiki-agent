"""Panel local de la demostración: preguntar, ingerir, explorar el wiki y ver resultados.

    uv run python -m wikillm.panel
    uv run python -m wikillm.panel --puerto 8800 --tope-usd 0.5 --no-abrir

Abre una página en http://127.0.0.1:8765/ que ejecuta las mismas órdenes que la consola y muestra
su salida, las llamadas al modelo y el costo mientras ocurren. Solo escucha en esta máquina. Las
acciones que llaman al modelo piden confirmación y la sesión tiene un tope de gasto.
"""

from __future__ import annotations

import argparse
import os
import sys
import webbrowser
from collections.abc import Sequence
from pathlib import Path

from wikillm.panel.acciones import POR_ID
from wikillm.panel.servidor import Panel, crear_servidor

PUERTO_POR_DEFECTO = 8765
TOPE_POR_DEFECTO_USD = 0.25


def encontrar_raiz() -> Path:
    """La carpeta del repositorio: la más cercana hacia arriba con pyproject.toml y src/wikillm."""
    for carpeta in (Path.cwd(), *Path.cwd().parents):
        if (carpeta / "pyproject.toml").exists() and (carpeta / "src" / "wikillm").is_dir():
            return carpeta
    return Path(__file__).resolve().parents[3]


def principal(argv: Sequence[str] | None = None) -> int:
    analizador = argparse.ArgumentParser(prog="python -m wikillm.panel", description=__doc__)
    analizador.add_argument(
        "--puerto", type=int, default=PUERTO_POR_DEFECTO, help="0 elige uno libre"
    )
    analizador.add_argument(
        "--tope-usd",
        type=float,
        default=TOPE_POR_DEFECTO_USD,
        help="gasto máximo de esta sesión en llamadas al modelo",
    )
    analizador.add_argument("--no-abrir", action="store_true", help="no abrir el navegador")
    analizador.add_argument(
        "--sin-calentar", action="store_true", help="no cargar el índice del RAG al arrancar"
    )
    argumentos = analizador.parse_args(argv)

    raiz = encontrar_raiz()
    os.chdir(raiz)
    panel = Panel(raiz, tope_usd=argumentos.tope_usd)
    try:
        servidor = crear_servidor(panel, argumentos.puerto)
    except OSError as error:
        print(
            f"No se pudo abrir el puerto {argumentos.puerto}: {error}. "
            "Prueba con --puerto 0 para elegir uno libre.",
            file=sys.stderr,
        )
        return 1
    url = f"http://127.0.0.1:{servidor.server_port}/"
    print(f"Panel de la demostración en {url}  (Ctrl+C para detenerlo)")
    print(f"Tope de gasto de la sesión: {argumentos.tope_usd:.2f} USD · raíz: {raiz}")
    if not argumentos.sin_calentar:
        accion = POR_ID["calentar"]
        panel.gestor.lanzar(
            accion.id, accion.titulo, panel.ejecutor.funcion(accion, {}), grabar=False
        )
    if not argumentos.no_abrir:
        webbrowser.open(url)
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nPanel detenido.")
    finally:
        servidor.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(principal())
