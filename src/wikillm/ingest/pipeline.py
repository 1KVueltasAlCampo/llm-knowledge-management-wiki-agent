"""Orquesta Bronze, Silver y Gold para una lista de identificadores de arXiv."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from wikillm.ingest.arxiv import (
    ClienteArxiv,
    descargar_paper,
    leer_ids,
    ultima_captura,
)
from wikillm.ingest.gold import (
    Metadatos,
    construir_encabezado,
    escribir_gold,
    escribir_manifiesto,
    parsear_abs,
    validar_gold,
    version_de_html,
)
from wikillm.ingest.markdown import ResultadoMarkdown, html_a_markdown, normalizar


@dataclass
class Resumen:
    arxiv_id: str
    titulo: str
    secciones: int
    tablas: int
    ecuaciones: int
    tokens: int
    referencias: list[str] = field(default_factory=list)


@dataclass
class Informe:
    resumenes: list[Resumen] = field(default_factory=list)
    fallos: list[str] = field(default_factory=list)
    problemas: list[str] = field(default_factory=list)

    @property
    def correcto(self) -> bool:
        return not self.fallos and not self.problemas


def construir_corpus(
    ruta_ids: Path | str,
    datos: Path | str = "data",
    *,
    cliente: ClienteArxiv | None = None,
    refrescar: bool = False,
    salida: Callable[[str], None] = print,
) -> Informe:
    """Descarga (Bronze), limpia (Silver) y enriquece (Gold) los papers de la lista."""
    datos = Path(datos)
    ids = leer_ids(ruta_ids)
    cliente = cliente or ClienteArxiv(avisar=salida)
    informe = Informe()
    procesados: dict[str, tuple[Metadatos, str, ResultadoMarkdown, str, str, str]] = {}

    for posicion, arxiv_id in enumerate(ids, start=1):
        salida(f"[{posicion}/{len(ids)}] {arxiv_id}")
        informe.fallos.extend(
            descargar_paper(cliente, arxiv_id, datos, refrescar=refrescar, avisar=salida)
        )
        carpeta = datos / "raw" / arxiv_id
        captura_html = ultima_captura(carpeta, "html")
        captura_abs = ultima_captura(carpeta, "abs")
        if not (carpeta / "page.html").exists() or captura_html is None:
            continue
        if not (carpeta / "abs.html").exists() or captura_abs is None:
            informe.fallos.append(f"{arxiv_id}: falta la página de resumen")
            continue
        html = (carpeta / "page.html").read_text(encoding="utf-8")
        try:
            convertido = html_a_markdown(html)
            meta = parsear_abs((carpeta / "abs.html").read_text(encoding="utf-8"))
        except ValueError as error:
            informe.fallos.append(f"{arxiv_id}: {error}")
            continue
        silver = datos / "processed" / f"{arxiv_id}.md"
        silver.parent.mkdir(parents=True, exist_ok=True)
        silver.write_text(convertido.markdown, encoding="utf-8", newline="\n")
        procesados[arxiv_id] = (
            meta,
            version_de_html(html, arxiv_id),
            convertido,
            str(captura_html["url"]),
            str(captura_html["fecha"]),
            str(captura_html["hash"]),
        )

    carpeta_gold = datos / "gold"
    filas = []
    for arxiv_id, (meta, version, convertido, url, fecha, huella) in procesados.items():
        referencias = _referencias_en_corpus(arxiv_id, convertido, procesados)
        encabezado = construir_encabezado(
            arxiv_id, version, meta, url, fecha, huella, convertido.markdown, referencias
        )
        escribir_gold(carpeta_gold / f"{arxiv_id}.md", encabezado, convertido.markdown)
        filas.append({**encabezado, "ruta": f"data/gold/{arxiv_id}.md"})
        informe.resumenes.append(
            Resumen(
                arxiv_id,
                meta.titulo,
                convertido.secciones,
                convertido.tablas,
                convertido.ecuaciones,
                encabezado["tokens"],
                referencias,
            )
        )
    if filas:
        escribir_manifiesto(carpeta_gold, filas)
    informe.problemas = [f"{p.archivo}: {p.motivo}" for p in validar_gold(carpeta_gold)]
    return informe


def _referencias_en_corpus(
    arxiv_id: str, convertido: ResultadoMarkdown, procesados: dict[str, tuple]
) -> list[str]:
    """Papers del corpus citados en la bibliografía, por identificador o por título completo."""
    citados = convertido.referencias_arxiv & set(procesados)
    for otro, (meta, *_resto) in procesados.items():
        if otro != arxiv_id and normalizar(meta.titulo) in convertido.texto_bibliografia:
            citados.add(otro)
    return sorted(citados - {arxiv_id})


def imprimir_informe(informe: Informe, salida: Callable[[str], None] = print) -> None:
    salida("\nResumen por paper")
    for r in informe.resumenes:
        salida(
            f"  {r.arxiv_id} | secciones {r.secciones} | tablas {r.tablas} | "
            f"ecuaciones {r.ecuaciones} | ~{r.tokens} tokens | cita a {r.referencias or '-'}"
        )
    for fallo in informe.fallos:
        salida(f"  FALLO: {fallo}")
    for problema in informe.problemas:
        salida(f"  INCUMPLE EL CONTRATO: {problema}")
    salida("Resultado: " + ("correcto" if informe.correcto else "con errores"))
