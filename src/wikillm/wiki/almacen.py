"""El wiki en disco: páginas Markdown con encabezado, índice y registro, y copias versionadas.

El índice (`index.md`) y el registro (`log.md`) los escribe el código, no el modelo. Cada copia
tras una ingesta es un commit con la etiqueta `paso-N` en un repositorio Git propio del wiki
(la carpeta no pertenece al repositorio del proyecto: son textos derivados de arXiv).
"""

from __future__ import annotations

import json
import re
import subprocess
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

TIPOS = ("paper", "concepto")
PATRON_SLUG = re.compile(r"^[a-z0-9][a-z0-9-]{0,79}$")
INDICE_VACIO = "# Wiki index\n\n(no pages yet)\n"
REGISTRO_INICIAL = "# Ingestion log\n"


class ErrorDeAlmacen(RuntimeError):
    """El wiki en disco no se pudo leer, escribir o versionar."""


def slug_de(texto: str) -> str:
    """Nombre de archivo seguro y legible a partir de un título."""
    ascii_ = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_.lower()).strip("-")[:80].strip("-")
    return slug or "pagina"


@dataclass
class Pagina:
    slug: str
    titulo: str
    tipo: str
    resumen: str
    fuentes: list[str]
    actualizada_en_paso: int
    cuerpo: str

    def __post_init__(self) -> None:
        if not PATRON_SLUG.match(self.slug):
            raise ErrorDeAlmacen(f"Nombre de página no válido: {self.slug!r}")
        if self.tipo not in TIPOS:
            raise ErrorDeAlmacen(f"Tipo de página no válido: {self.tipo!r} (usa {TIPOS})")

    def a_texto(self) -> str:
        encabezado = yaml.safe_dump(
            {
                "titulo": self.titulo,
                "tipo": self.tipo,
                "resumen": self.resumen,
                "fuentes": list(self.fuentes),
                "actualizada_en_paso": self.actualizada_en_paso,
            },
            sort_keys=False,
            allow_unicode=True,
        )
        return f"---\n{encabezado}---\n\n{self.cuerpo.strip()}\n"

    @classmethod
    def desde_texto(cls, slug: str, texto: str) -> Pagina:
        if not texto.startswith("---\n"):
            raise ErrorDeAlmacen(f"La página {slug} no tiene encabezado")
        cabecera, separador, cuerpo = texto[4:].partition("\n---\n")
        if not separador:
            raise ErrorDeAlmacen(f"El encabezado de la página {slug} no se cierra")
        datos: dict[str, Any] = yaml.safe_load(cabecera) or {}
        return cls(
            slug=slug,
            titulo=str(datos.get("titulo", slug)),
            tipo=str(datos.get("tipo", "")),
            resumen=str(datos.get("resumen", "")),
            fuentes=[str(f) for f in datos.get("fuentes") or []],
            actualizada_en_paso=int(datos.get("actualizada_en_paso", 0)),
            cuerpo=cuerpo.strip(),
        )


class Wiki:
    def __init__(self, carpeta: Path | str) -> None:
        self.carpeta = Path(carpeta)
        self._paginas = self.carpeta / "pages"
        self._paginas.mkdir(parents=True, exist_ok=True)
        for nombre, inicial in (("index.md", INDICE_VACIO), ("log.md", REGISTRO_INICIAL)):
            if not (self.carpeta / nombre).exists():
                (self.carpeta / nombre).write_text(inicial, encoding="utf-8")
        if not (self.carpeta / ".git").exists():
            self._git("init", "-q")

    # --- estado de la ingesta -------------------------------------------------------------
    @property
    def _ruta_estado(self) -> Path:
        return self.carpeta / "estado.json"

    @property
    def ingeridos(self) -> list[str]:
        if not self._ruta_estado.exists():
            return []
        return list(json.loads(self._ruta_estado.read_text(encoding="utf-8"))["ingeridos"])

    @property
    def paso(self) -> int:
        return len(self.ingeridos)

    def marcar_ingerido(self, arxiv_id: str) -> None:
        ingeridos = self.ingeridos
        if arxiv_id not in ingeridos:
            ingeridos.append(arxiv_id)
        self._ruta_estado.write_text(
            json.dumps({"ingeridos": ingeridos}, ensure_ascii=False, indent=1), encoding="utf-8"
        )

    # --- páginas --------------------------------------------------------------------------
    def slugs(self) -> list[str]:
        return sorted(ruta.stem for ruta in self._paginas.glob("*.md"))

    def existe(self, slug: str) -> bool:
        return (self._paginas / f"{slug}.md").exists()

    def leer(self, slug: str) -> Pagina:
        ruta = self._paginas / f"{slug}.md"
        if not PATRON_SLUG.match(slug) or not ruta.exists():
            raise ErrorDeAlmacen(f"No existe la página {slug!r}")
        return Pagina.desde_texto(slug, ruta.read_text(encoding="utf-8"))

    def escribir(self, pagina: Pagina) -> None:
        (self._paginas / f"{pagina.slug}.md").write_text(pagina.a_texto(), encoding="utf-8")

    def paginas(self) -> list[Pagina]:
        return [self.leer(slug) for slug in self.slugs()]

    # --- índice y registro (los escribe el código) ----------------------------------------
    def regenerar_indice(self) -> None:
        paginas = self.paginas()
        if not paginas:
            (self.carpeta / "index.md").write_text(INDICE_VACIO, encoding="utf-8")
            return
        lineas = [
            "# Wiki index",
            "",
            f"Papers ingested: {len(self.ingeridos)}. Pages: {len(paginas)}.",
        ]
        for tipo, titulo in (("paper", "Papers"), ("concepto", "Concepts")):
            seleccion = [p for p in paginas if p.tipo == tipo]
            if seleccion:
                lineas += ["", f"## {titulo}"]
                lineas += [f"- [[{p.slug}]] **{p.titulo}**: {p.resumen}" for p in seleccion]
        (self.carpeta / "index.md").write_text("\n".join(lineas) + "\n", encoding="utf-8")

    def texto_del_indice(self) -> str:
        return (self.carpeta / "index.md").read_text(encoding="utf-8")

    def anotar(self, entrada: str) -> None:
        with (self.carpeta / "log.md").open("a", encoding="utf-8") as archivo:
            archivo.write("\n" + entrada.strip() + "\n")

    # --- copias versionadas ---------------------------------------------------------------
    def _git(self, *argumentos: str) -> str:
        resultado = subprocess.run(
            [
                "git",
                "-C",
                str(self.carpeta),
                "-c",
                "user.name=wikillm",
                "-c",
                "user.email=wikillm@localhost",
                "-c",
                "core.autocrlf=false",
                "-c",
                "commit.gpgsign=false",
                *argumentos,
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        if resultado.returncode != 0:
            raise ErrorDeAlmacen(f"git {' '.join(argumentos)}: {resultado.stderr.strip()}")
        return resultado.stdout.strip()

    def guardar_copia(self, paso: int, mensaje: str) -> str:
        """Commit de todo el wiki con la etiqueta `paso-N`; devuelve el identificador."""
        self._git("add", "-A")
        self._git("commit", "-q", "--allow-empty", "-m", mensaje)
        self._git("tag", "-f", f"paso-{paso}")
        return self._git("rev-parse", "HEAD")

    def etiquetas(self) -> list[str]:
        salida = self._git("tag", "--list", "paso-*")
        return sorted(salida.splitlines(), key=lambda e: int(e.split("-")[1]))
