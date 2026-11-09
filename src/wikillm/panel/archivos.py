"""Archivos que el visor del panel puede mostrar: una lista blanca, nunca rutas libres.

Es la única entrada de rutas del servidor. Una ruta se acepta solo si, ya normalizada, coincide
con uno de los patrones declarados; nunca se sirve `.env`, `.git` ni nada fuera de la raíz.
"""

from __future__ import annotations

from fnmatch import fnmatchcase
from pathlib import Path, PurePosixPath
from typing import Any

LIMITE_BYTES = 600_000

GRUPOS: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "Wiki de la demostración",
        ("data/wiki/demo/index.md", "data/wiki/demo/log.md", "data/wiki/demo/pages/*.md"),
    ),
    (
        "Evidencia",
        (
            "results/demo/comparaciones.jsonl",
            "results/demo/ensayos/*.jsonl",
            "results/piloto-1/corrida.json",
            "results/piloto-1/respuestas.jsonl",
            "results/piloto-1/trazas.jsonl",
            "results/piloto-1/ingestas.jsonl",
            "results/piloto-1/metricas_por_paso.json",
            "results/piloto-1/evaluados.jsonl",
        ),
    ),
    ("Repositorio", ("README.md", "CONSTITUTION.md", "AGENTS.md", "pyproject.toml")),
    ("Documentos", ("docs/*.md", "docs/decisiones/*.md")),
    ("Especificaciones", ("specs/*.md", "openspec/specs/*/spec.md")),
    (
        "Código",
        (
            "src/wikillm/common/*.py",
            "src/wikillm/rag/*.py",
            "src/wikillm/wiki/*.py",
            "src/wikillm/arnes/*.py",
            "src/wikillm/eval/*.py",
            "src/wikillm/corpus/*.py",
            "src/wikillm/ingest/*.py",
        ),
    ),
    ("Datos", ("data/preguntas/banco.jsonl", "data/manifest_corpus.jsonl")),
)
TIPOS = {
    ".md": "markdown",
    ".json": "json",
    ".jsonl": "jsonl",
    ".py": "codigo",
    ".toml": "codigo",
}


class ArchivoNoPermitido(PermissionError):
    """La ruta pedida no está en la lista blanca o intenta salirse de la raíz."""


def normalizar(ruta: str) -> str:
    """Ruta relativa con barras normales, o ArchivoNoPermitido si es sospechosa."""
    texto = ruta.replace("\\", "/").strip()
    if not texto or "\x00" in texto or texto.startswith("/") or ":" in texto:
        raise ArchivoNoPermitido("Ruta no válida")
    partes = PurePosixPath(texto).parts
    for parte in partes:
        if parte in ("..", ".") or parte.startswith(".env") or parte.startswith(".git"):
            raise ArchivoNoPermitido("Ruta no permitida")
    return "/".join(partes)


def coincide(ruta: str) -> bool:
    """Si la ruta, exista o no, encaja con algún patrón de la lista blanca."""
    partes = ruta.split("/")
    return any(
        len(partes) == len(patron.split("/"))
        and all(fnmatchcase(p, q) for p, q in zip(partes, patron.split("/"), strict=True))
        for _, patrones in GRUPOS
        for patron in patrones
    )


class Archivos:
    def __init__(self, raiz: Path) -> None:
        self.raiz = raiz.resolve()

    def permitidos(self) -> dict[str, str]:
        """Ruta relativa -> grupo, para los archivos que existen ahora."""
        encontrados: dict[str, str] = {}
        for grupo, patrones in GRUPOS:
            for patron in patrones:
                for ruta in sorted(self.raiz.glob(patron)):
                    if ruta.is_file():
                        encontrados.setdefault(ruta.relative_to(self.raiz).as_posix(), grupo)
        return encontrados

    def listar(self) -> list[dict[str, str]]:
        return [
            {"grupo": grupo, "ruta": ruta, "nombre": ruta.rsplit("/", 1)[-1]}
            for ruta, grupo in self.permitidos().items()
        ]

    def leer(self, ruta: str) -> dict[str, Any]:
        relativa = normalizar(ruta)
        if relativa not in self.permitidos():
            raise ArchivoNoPermitido(
                "El archivo no está en la lista de archivos que se pueden mostrar"
            )
        destino = (self.raiz / relativa).resolve()
        if self.raiz not in destino.parents:
            raise ArchivoNoPermitido("Ruta fuera del repositorio")
        tamano = destino.stat().st_size
        with destino.open("rb") as archivo:
            contenido = archivo.read(LIMITE_BYTES)
        return {
            "ruta": relativa,
            "tipo": TIPOS.get(destino.suffix.lower(), "texto"),
            "texto": contenido.decode("utf-8", errors="replace"),
            "truncado": tamano > LIMITE_BYTES,
            "bytes": tamano,
        }
