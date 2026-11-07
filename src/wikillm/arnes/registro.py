"""Archivos de una corrida: líneas JSONL que se escriben una a una y `corrida.json`.

Cada línea se vacía a disco al escribirla, así que un corte pierde como mucho la pregunta en
curso, y las claves ya escritas permiten reanudar sin repetir.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections.abc import Iterable
from pathlib import Path
from typing import Any


def anexar_linea(ruta: Path, fila: dict[str, Any]) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with ruta.open("a", encoding="utf-8") as archivo:
        archivo.write(json.dumps(fila, ensure_ascii=False) + "\n")
        archivo.flush()


def leer_lineas(ruta: Path) -> list[dict[str, Any]]:
    if not ruta.exists():
        return []
    texto = ruta.read_text(encoding="utf-8")
    return [json.loads(linea) for linea in texto.splitlines() if linea.strip()]


def claves_escritas(ruta: Path, campos: Iterable[str]) -> set[tuple[Any, ...]]:
    campos = tuple(campos)
    return {tuple(fila[c] for c in campos) for fila in leer_lineas(ruta)}


def huella_archivo(ruta: Path) -> str:
    return hashlib.sha256(ruta.read_bytes()).hexdigest()


def info_git(carpeta: Path | None = None) -> dict[str, Any]:
    """Commit actual y si hay cambios sin guardar (sin contar `results/`); None si no hay Git."""

    def git(*argumentos: str) -> str:
        return subprocess.run(
            ["git", *argumentos],
            cwd=carpeta,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True,
        ).stdout.strip()

    try:
        commit = git("rev-parse", "HEAD")
        sucio = bool(git("status", "--porcelain", "--", ".", ":(exclude)results"))
    except (OSError, subprocess.CalledProcessError):
        return {"commit": None, "arbol_con_cambios": None}
    return {"commit": commit, "arbol_con_cambios": sucio}


def leer_corrida(ruta: Path) -> dict[str, Any] | None:
    if not ruta.exists():
        return None
    return json.loads(ruta.read_text(encoding="utf-8"))


def escribir_corrida(ruta: Path, datos: dict[str, Any]) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(datos, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def actualizar_corrida(ruta: Path, **cambios: Any) -> dict[str, Any]:
    datos = leer_corrida(ruta) or {}
    datos.update(cambios)
    escribir_corrida(ruta, datos)
    return datos
