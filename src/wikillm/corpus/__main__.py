"""Uso:
uv run python -m wikillm.corpus candidatos   # metadatos de la API de arXiv (.bib + búsquedas)
uv run python -m wikillm.corpus manifest     # data/manifest_corpus.jsonl a partir del Gold
uv run python -m wikillm.corpus spans        # data/gold/spans.jsonl (fragmentos citables)
"""

import argparse
import sys
from pathlib import Path

from wikillm.corpus.arxiv_api import ClienteApi
from wikillm.corpus.candidatos import (
    escribir_jsonl,
    ids_de_bib,
    leer_consultas,
    leer_jsonl,
    reunir,
)
from wikillm.corpus.manifest import construir_manifest
from wikillm.corpus.seleccion import seleccionar
from wikillm.corpus.spans import spans_de_carpeta
from wikillm.ingest.arxiv import leer_ids

SALIDA_CANDIDATOS = "data/raw/api/candidatos.jsonl"
SEMILLAS = ["2405.14831", "2502.14802", "2605.25480", "2605.18490", "2607.04576"]


def main() -> int:
    analizador = argparse.ArgumentParser(description="Herramientas de selección del corpus.")
    ordenes = analizador.add_subparsers(dest="orden", required=True)

    candidatos = ordenes.add_parser("candidatos", help="reunir candidatos con la API de arXiv")
    candidatos.add_argument("--bib", default="docs/estado-del-arte/referencias.bib")
    candidatos.add_argument("--consultas", default="data/consultas_busqueda.txt")
    candidatos.add_argument("--desde", default="2026-01-01", help="fecha mínima (búsquedas)")
    candidatos.add_argument("--extra", nargs="*", default=[], help="ids adicionales")
    candidatos.add_argument("--salida", default=SALIDA_CANDIDATOS)

    manifest = ordenes.add_parser("manifest", help="construir el manifest del corpus")
    manifest.add_argument("--ids", default="data/corpus_ids.txt")
    manifest.add_argument("--candidatos", default=SALIDA_CANDIDATOS)
    manifest.add_argument("--datos", default="data")
    manifest.add_argument("--salida", default="data/manifest_corpus.jsonl")

    spans = ordenes.add_parser("spans", help="calcular los fragmentos citables del Gold")
    spans.add_argument("--ids", default="data/corpus_ids.txt")
    spans.add_argument("--datos", default="data")
    spans.add_argument("--salida", default="data/gold/spans.jsonl")

    seleccion = ordenes.add_parser("seleccionar", help="elegir los N papers y escribir la lista")
    seleccion.add_argument("--candidatos", default=SALIDA_CANDIDATOS)
    seleccion.add_argument("--semillas", nargs="+", default=SEMILLAS)
    seleccion.add_argument("--preseleccion", default="data/preseleccion_busqueda.txt")
    seleccion.add_argument("--datos", default="data")
    seleccion.add_argument("--n", type=int, default=50)
    seleccion.add_argument("--salida", default="data/corpus_ids.txt")

    argumentos = analizador.parse_args()
    if argumentos.orden == "candidatos":
        ids = ids_de_bib(Path(argumentos.bib).read_text(encoding="utf-8")) + argumentos.extra
        consultas = leer_consultas(Path(argumentos.consultas))
        print(f"{len(ids)} ids semilla, {len(consultas)} consultas", flush=True)
        filas = reunir(ClienteApi(), ids, consultas, argumentos.desde)
        escribir_jsonl(Path(argumentos.salida), filas)
        print(f"{len(filas)} candidatos en {argumentos.salida}", flush=True)
    elif argumentos.orden == "manifest":
        datos = Path(argumentos.datos)
        por_id = {f["arxiv_id"]: f for f in leer_jsonl(Path(argumentos.candidatos))}
        filas = construir_manifest(leer_ids(argumentos.ids), por_id, datos / "raw", datos / "gold")
        escribir_jsonl(Path(argumentos.salida), filas)
        sin_html = [f["arxiv_id"] for f in filas if not f["html_available"]]
        print(f"{len(filas)} papers en {argumentos.salida}; sin HTML: {sin_html or 'ninguno'}")
        return 1 if sin_html else 0
    elif argumentos.orden == "spans":
        datos = Path(argumentos.datos)
        filas = spans_de_carpeta(datos / "gold", leer_ids(argumentos.ids))
        escribir_jsonl(Path(argumentos.salida), filas)
        print(f"{len(filas)} fragmentos en {argumentos.salida}")
    elif argumentos.orden == "seleccionar":
        return _seleccionar(argumentos)
    return 0


def _seleccionar(argumentos: argparse.Namespace) -> int:
    from wikillm.corpus.manifest import html_disponible
    from wikillm.ingest.gold import leer_gold

    datos = Path(argumentos.datos)
    candidatos = {f["arxiv_id"]: f for f in leer_jsonl(Path(argumentos.candidatos))}
    preseleccion = leer_ids(argumentos.preseleccion)
    referencias: dict[str, list[str]] = {}
    for arxiv_id in candidatos:
        ruta = datos / "gold" / f"{arxiv_id}.md"
        if ruta.exists():
            referencias[arxiv_id] = leer_gold(ruta)[0].get("referencias_en_corpus") or []
    elegidos, reservas = seleccionar(
        candidatos,
        argumentos.semillas,
        preseleccion,
        referencias,
        lambda i: html_disponible(datos / "raw", i),
        argumentos.n,
    )
    lineas = [
        f"# Corpus de {len(elegidos)} papers. Generado con `uv run python -m wikillm.corpus "
        "seleccionar`; criterios en docs/corpus.md.",
        "# Un identificador de arXiv por línea. Las líneas que empiezan con # se ignoran.",
    ]
    for arxiv_id in sorted(elegidos, key=lambda i: (candidatos[i]["fecha_publicacion"], i)):
        registro = candidatos[arxiv_id]
        lineas.append(f"{arxiv_id}  # {registro['fecha_publicacion']} {registro['titulo'][:80]}")
    Path(argumentos.salida).write_text("\n".join(lineas) + "\n", encoding="utf-8")
    print(f"{len(elegidos)} elegidos en {argumentos.salida}; reservas: {reservas or 'ninguna'}")
    return 0 if len(elegidos) == argumentos.n else 1


if __name__ == "__main__":
    sys.exit(main())
