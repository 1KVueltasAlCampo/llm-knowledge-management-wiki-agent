"""Capa Gold: encabezado de metadatos, archivos, manifiesto y validación del contrato.

El contrato está en specs/formato-gold.md.
"""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from bs4 import BeautifulSoup

CAMPOS_OBLIGATORIOS = (
    "type",
    "arxiv_id",
    "version",
    "titulo",
    "autores",
    "fecha_publicacion",
    "categoria",
    "sources",
    "extraccion",
    "fecha_captura",
    "hash",
    "tokens",
    "idioma",
)
MARGEN_TOKENS = 0.10
# Solo nombres de etiqueta HTML reales: los papers traen marcadores como `results/<name>/`.
ETIQUETAS_HTML = (
    "a|abbr|article|b|br|caption|cite|code|dd|div|dl|dt|em|figcaption|figure|h[1-6]|hr|i|img|"
    "li|math|mi|mn|mo|mrow|nav|ol|p|pre|section|small|span|strong|sub|sup|svg|table|tbody|td|"
    "tfoot|th|thead|tr|u|ul"
)
PATRON_HTML = re.compile(rf"</?(?:{ETIQUETAS_HTML})(?:\s[^>\n]*)?/?>", re.IGNORECASE)
PATRON_CODIGO = re.compile(r"```.*?```|`[^`\n]*`", re.DOTALL)
PATRON_MATEMATICA = re.compile(r"\$\$.*?\$\$|\$[^$\n]*\$", re.DOTALL)


@dataclass(frozen=True)
class Metadatos:
    titulo: str
    autores: list[str]
    fecha_publicacion: str
    fecha_version: str
    categoria: str


@dataclass(frozen=True)
class Problema:
    archivo: str
    motivo: str


def aproximar_tokens(texto: str) -> int:
    """Estimación del número de tokens: un token cada 4 caracteres. Es solo una aproximación."""
    return math.ceil(len(texto) / 4)


def _fecha(valor: str) -> str:
    return valor.strip().replace("/", "-")


def _nombre_natural(autor: str) -> str:
    """Convierte 'Apellido, Nombre' en 'Nombre Apellido'."""
    if "," in autor:
        apellido, _, nombre = autor.partition(",")
        return f"{nombre.strip()} {apellido.strip()}".strip()
    return autor.strip()


def parsear_abs(html: str) -> Metadatos:
    """Extrae los metadatos de la página de resumen de arXiv (etiquetas citation_*)."""
    sopa = BeautifulSoup(html, "lxml")

    def meta(nombre: str) -> list[str]:
        return [m.get("content", "").strip() for m in sopa.find_all("meta", attrs={"name": nombre})]

    titulo = (meta("citation_title") or [""])[0]
    autores = [_nombre_natural(a) for a in meta("citation_author") if a]
    fecha = (meta("citation_date") or [""])[0]
    en_linea = (meta("citation_online_date") or [fecha])[0]
    sujeto = sopa.select_one(".primary-subject")
    coincidencia = re.search(r"\(([^)]+)\)\s*$", sujeto.get_text().strip()) if sujeto else None
    categoria = coincidencia.group(1) if coincidencia else ""
    if not titulo or not autores or not fecha or not categoria:
        raise ValueError("La página de resumen no trae todos los metadatos esperados")
    return Metadatos(titulo, autores, _fecha(fecha), _fecha(en_linea), categoria)


def version_de_html(html: str, arxiv_id: str) -> str:
    """La versión capturada es la mayor que aparece junto al identificador en el HTML."""
    numeros = [int(n) for n in re.findall(re.escape(arxiv_id) + r"v(\d+)", html)]
    return f"v{max(numeros)}" if numeros else "v1"


def construir_encabezado(
    arxiv_id: str,
    version: str,
    meta: Metadatos,
    url: str,
    fecha_captura: str,
    huella: str,
    cuerpo: str,
    referencias: list[str],
    estado_publicacion: str = "desconocido",
) -> dict[str, Any]:
    return {
        "type": "paper",
        "arxiv_id": arxiv_id,
        "version": version,
        "titulo": meta.titulo,
        "autores": meta.autores,
        "fecha_publicacion": meta.fecha_publicacion,
        "fecha_version": meta.fecha_version,
        "categoria": meta.categoria,
        "estado_publicacion": estado_publicacion,
        "sources": [url],
        "extraccion": "html",
        "fecha_captura": fecha_captura,
        "hash": f"sha256:{huella}",
        "tokens": aproximar_tokens(cuerpo),
        "idioma": "en",
        "referencias_en_corpus": referencias,
    }


def escribir_gold(ruta: Path, encabezado: dict[str, Any], cuerpo: str) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    cabecera = yaml.safe_dump(
        encabezado, allow_unicode=True, sort_keys=False, default_flow_style=False, width=10_000
    )
    ruta.write_text(f"---\n{cabecera}---\n\n{cuerpo}", encoding="utf-8", newline="\n")


def leer_gold(ruta: Path) -> tuple[dict[str, Any], str]:
    texto = ruta.read_text(encoding="utf-8")
    if not texto.startswith("---\n"):
        raise ValueError("falta el encabezado YAML")
    cabecera, separador, cuerpo = texto[4:].partition("\n---\n")
    if not separador:
        raise ValueError("el encabezado YAML no se cierra")
    datos = yaml.safe_load(cabecera)
    if not isinstance(datos, dict):
        raise ValueError("el encabezado YAML no es un diccionario")
    return datos, cuerpo.lstrip("\n")


def escribir_manifiesto(carpeta_gold: Path, filas: list[dict[str, Any]]) -> None:
    lineas = [json.dumps(f, ensure_ascii=False) for f in filas]
    (carpeta_gold / "corpus.jsonl").write_text("\n".join(lineas) + "\n", encoding="utf-8")


def validar_gold(carpeta_gold: Path) -> list[Problema]:
    """Comprueba que cada archivo Gold cumple el contrato. Devuelve los problemas hallados."""
    problemas: list[Problema] = []
    vistos: dict[str, str] = {}
    for archivo in sorted(carpeta_gold.glob("*.md")):
        nombre = archivo.name
        try:
            encabezado, cuerpo = leer_gold(archivo)
        except ValueError as error:
            problemas.append(Problema(nombre, f"encabezado inválido: {error}"))
            continue
        for campo in CAMPOS_OBLIGATORIOS:
            if campo not in encabezado or encabezado[campo] in (None, "", []):
                problemas.append(Problema(nombre, f"falta el campo obligatorio '{campo}'"))
        identificador = str(encabezado.get("arxiv_id", ""))
        if identificador:
            if identificador in vistos:
                problemas.append(
                    Problema(nombre, f"arxiv_id repetido (también en {vistos[identificador]})")
                )
            vistos[identificador] = nombre
            if nombre != f"{identificador}.md":
                problemas.append(Problema(nombre, "el nombre del archivo no coincide con arxiv_id"))
        if not cuerpo.strip():
            problemas.append(Problema(nombre, "el cuerpo está vacío"))
            continue
        sin_matematica = PATRON_CODIGO.sub("", PATRON_MATEMATICA.sub("", cuerpo))
        if PATRON_HTML.search(sin_matematica):
            problemas.append(Problema(nombre, "quedan etiquetas HTML en el cuerpo"))
        declarado = encabezado.get("tokens")
        if isinstance(declarado, int):
            esperado = aproximar_tokens(cuerpo)
            if esperado and abs(declarado - esperado) / esperado > MARGEN_TOKENS:
                problemas.append(
                    Problema(nombre, f"tokens declarados {declarado}, esperados ~{esperado}")
                )
    return problemas
