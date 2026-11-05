"""Uso: uv run python -m wikillm.ingest [--ids data/corpus_ids.txt] [--datos data] [--refrescar]"""

import argparse
import sys

from wikillm.ingest.pipeline import construir_corpus, imprimir_informe


def main() -> int:
    analizador = argparse.ArgumentParser(description="Construye el corpus Bronze, Silver y Gold.")
    analizador.add_argument("--ids", default="data/corpus_ids.txt", help="lista de identificadores")
    analizador.add_argument("--datos", default="data", help="carpeta de datos")
    analizador.add_argument("--refrescar", action="store_true", help="volver a descargar")
    argumentos = analizador.parse_args()

    informe = construir_corpus(
        argumentos.ids,
        argumentos.datos,
        refrescar=argumentos.refrescar,
        salida=lambda mensaje: print(mensaje, flush=True),
    )
    imprimir_informe(informe, lambda mensaje: print(mensaje, flush=True))
    return 0 if informe.correcto else 1


if __name__ == "__main__":
    sys.exit(main())
