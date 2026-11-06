"""Uso: uv run python -m wikillm.corpus candidatos [--bib ...] [--consultas ...] [--salida ...]"""

import argparse
import sys
from pathlib import Path

from wikillm.corpus.arxiv_api import ClienteApi
from wikillm.corpus.candidatos import escribir_jsonl, ids_de_bib, leer_consultas, reunir

SALIDA_CANDIDATOS = "data/raw/api/candidatos.jsonl"


def main() -> int:
    analizador = argparse.ArgumentParser(description="Herramientas de selección del corpus.")
    ordenes = analizador.add_subparsers(dest="orden", required=True)

    candidatos = ordenes.add_parser("candidatos", help="reunir candidatos con la API de arXiv")
    candidatos.add_argument("--bib", default="docs/estado-del-arte/referencias.bib")
    candidatos.add_argument("--consultas", default="data/consultas_busqueda.txt")
    candidatos.add_argument("--desde", default="2026-01-01", help="fecha mínima (búsquedas)")
    candidatos.add_argument("--salida", default=SALIDA_CANDIDATOS)

    argumentos = analizador.parse_args()
    if argumentos.orden == "candidatos":
        ids = ids_de_bib(Path(argumentos.bib).read_text(encoding="utf-8"))
        consultas = leer_consultas(Path(argumentos.consultas))
        print(f"{len(ids)} ids del .bib, {len(consultas)} consultas", flush=True)
        filas = reunir(ClienteApi(), ids, consultas, argumentos.desde)
        escribir_jsonl(Path(argumentos.salida), filas)
        print(f"{len(filas)} candidatos en {argumentos.salida}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
