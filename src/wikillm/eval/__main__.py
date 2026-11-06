"""Uso:
uv run python -m wikillm.eval validar-banco
uv run python -m wikillm.eval sinteticos --salida results/sintetico/respuestas.jsonl
uv run python -m wikillm.eval metricas --respuestas results/<corrida>/respuestas.jsonl [--juez]
uv run python -m wikillm.eval acuerdo --a hoja_a.csv --b hoja_b.csv [--columna veredicto]
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from pathlib import Path
from typing import Any

from wikillm.corpus.candidatos import escribir_jsonl, leer_jsonl
from wikillm.eval.acuerdo import acuerdo_de_hojas
from wikillm.eval.banco import leer_banco, validar_banco
from wikillm.eval.metricas import agregar, evaluar_resultados, leer_resultados
from wikillm.eval.sinteticos import generar

BANCO = "data/preguntas/banco.jsonl"
MANIFEST = "data/manifest_corpus.jsonl"
SPANS = "data/gold/spans.jsonl"


def _orden(ruta_manifest: str) -> dict[str, int]:
    return {f["arxiv_id"]: int(f["orden_ingesta"]) for f in leer_jsonl(Path(ruta_manifest))}


def _spans(ruta: str) -> dict[str, dict[str, Any]]:
    archivo = Path(ruta)
    return {s["span_id"]: s for s in leer_jsonl(archivo)} if archivo.exists() else {}


def _escribir_csv(ruta: Path, filas: list[dict[str, Any]]) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with ruta.open("w", encoding="utf-8", newline="") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=list(filas[0]))
        escritor.writeheader()
        escritor.writerows(filas)


def _borradores(args: argparse.Namespace) -> int:
    from dotenv import load_dotenv

    from wikillm.eval.plan_borradores import (
        TOPE_CONFIRMACION_USD,
        ejecutar,
        escribir_hoja,
        planear,
        precios_redactor,
    )

    load_dotenv()
    manifest = leer_jsonl(Path(args.manifest))
    plan = planear(manifest, args.autor)
    pedidas = sum(sum(t.pedidos.values()) for t in plan.tareas)
    print(
        f"Autor {args.autor}: {len(plan.tareas)} llamadas, {pedidas} preguntas pedidas, "
        f"~{plan.tokens_entrada:,} tokens de entrada y ~{plan.tokens_salida:,} de salida"
    )
    precios = precios_redactor()
    if precios is None:
        print("Sin tarifas del redactor en .env (DRAFT_PRICE_*): no se puede estimar el costo.")
        return 1
    costo = plan.costo(*precios)
    print(f"Costo estimado: {costo:.2f} USD (hora pico: hasta {2 * costo:.2f} USD)")
    if not args.ejecutar:
        return 0
    if 2 * costo > max(TOPE_CONFIRMACION_USD, args.confirmo_usd):
        print(f"Supera {TOPE_CONFIRMACION_USD} USD: repetir con --confirmo-usd {2 * costo:.2f}")
        return 1
    from wikillm.eval.modelos import crear_redactor

    datos = Path(args.datos)
    carpeta = datos / "preguntas"
    cliente = crear_redactor(Path("results/borradores") / f"llamadas_{args.autor}.jsonl")
    redactor = os.environ.get("DRAFT_MODEL", "deepseek-v4-pro")
    preguntas, citas, descartes = ejecutar(plan, manifest, datos / "gold", cliente, redactor)
    escribir_jsonl(carpeta / f"borradores_{args.autor}.jsonl", preguntas)
    escribir_jsonl(carpeta / "anotacion" / f"citas_{args.autor}.jsonl", citas)
    escribir_hoja(carpeta / "anotacion" / f"hoja_{args.autor}.csv", preguntas, citas)
    (carpeta / "anotacion" / f"descartes_{args.autor}.txt").write_text(
        "\n".join(descartes) + "\n", encoding="utf-8"
    )
    print(
        f"{len(preguntas)} borradores, {len(descartes)} descartes; "
        f"gasto real {cliente.gasto_acumulado:.4f} USD"
    )
    return 0


def _libro_cerrado(args: argparse.Namespace) -> int:
    from wikillm.common.config import load_settings
    from wikillm.common.modelo import ClienteModelo
    from wikillm.eval.libro_cerrado import correr, estimar

    banco = leer_banco(Path(args.banco))
    ajustes = load_settings()
    entrada, salida = estimar(banco)
    costo = (entrada * ajustes.price_input_cache_miss + salida * ajustes.price_output) / 1e6
    print(f"{len(banco)} preguntas, ~{entrada:,} + {salida:,} tokens, ~{2 * costo:.4f} USD máx.")
    if not args.ejecutar:
        return 0
    destino = Path(args.salida)
    cliente = ClienteModelo(ajustes, ruta_registro=destino.parent / "llamadas.jsonl")
    filas = correr(banco, cliente, ajustes.model, args.paso, destino.parent.name)
    escribir_jsonl(destino, filas)
    print(f"{len(filas)} respuestas en {destino}; gasto {cliente.gasto_acumulado:.4f} USD")
    return 0


def main() -> int:
    analizador = argparse.ArgumentParser(description="Banco de preguntas y métricas de calidad.")
    ordenes = analizador.add_subparsers(dest="orden", required=True)
    for nombre in ("validar-banco", "sinteticos", "metricas"):
        sub = ordenes.add_parser(nombre)
        sub.add_argument("--banco", default=BANCO)
        sub.add_argument("--manifest", default=MANIFEST)
        sub.add_argument("--spans", default=SPANS)
        if nombre == "sinteticos":
            sub.add_argument("--pasos", default="5,10,15,20,25,30,35,40,45,50")
            sub.add_argument("--salida", default="results/sintetico/respuestas.jsonl")
        if nombre == "metricas":
            sub.add_argument("--respuestas", required=True)
            sub.add_argument("--juez", action="store_true", help="capa 2 con Gemini (gasta)")
    borradores = ordenes.add_parser("borradores", help="plan y redacción de borradores")
    borradores.add_argument("--autor", required=True, choices=["A", "B"])
    borradores.add_argument("--manifest", default=MANIFEST)
    borradores.add_argument("--datos", default="data")
    borradores.add_argument("--ejecutar", action="store_true", help="llamar al redactor (gasta)")
    borradores.add_argument("--confirmo-usd", type=float, default=0.0, help="acepta gasto mayor")
    cerrado = ordenes.add_parser("libro-cerrado", help="control de contaminación (gasta)")
    cerrado.add_argument("--banco", default=BANCO)
    cerrado.add_argument("--paso", type=int, default=50, help="paso en que todo es respondible")
    cerrado.add_argument("--salida", default="results/libro_cerrado/respuestas.jsonl")
    cerrado.add_argument("--ejecutar", action="store_true")
    acuerdo = ordenes.add_parser("acuerdo")
    acuerdo.add_argument("--a", required=True)
    acuerdo.add_argument("--b", required=True)
    acuerdo.add_argument("--columna", default="veredicto")

    args = analizador.parse_args()
    if args.orden == "acuerdo":
        resultado = acuerdo_de_hojas(Path(args.a), Path(args.b), args.columna)
        kappa = "n/d" if resultado.kappa is None else f"{resultado.kappa:.3f}"
        print(f"n={resultado.n} acuerdo={resultado.porcentaje:.1%} kappa={kappa}")
        return 0

    if args.orden == "borradores":
        return _borradores(args)
    if args.orden == "libro-cerrado":
        return _libro_cerrado(args)

    banco = leer_banco(Path(args.banco))
    orden = _orden(args.manifest)
    if args.orden == "validar-banco":
        problemas = validar_banco(banco, orden)
        for problema in problemas:
            print(problema)
        estados: dict[str, int] = {}
        for p in banco:
            estados[p["estado_verificacion"]] = estados.get(p["estado_verificacion"], 0) + 1
        print(f"{len(banco)} preguntas, {len(problemas)} problemas, estados: {estados}")
        return 1 if problemas else 0

    spans = _spans(args.spans)
    if args.orden == "sinteticos":
        por_paper: dict[str, list[str]] = {}
        for span_id, span in spans.items():
            por_paper.setdefault(span["arxiv_id"], []).append(span_id)
        pasos = [int(p) for p in args.pasos.split(",")]
        filas = generar(banco, pasos, por_paper)
        escribir_jsonl(Path(args.salida), filas)
        print(f"{len(filas)} resultados sintéticos en {args.salida}")
        return 0

    juez = None
    if args.juez:
        from wikillm.eval.juez import Juez
        from wikillm.eval.modelos import crear_juez

        carpeta = Path(args.respuestas).parent
        juez = Juez(crear_juez(carpeta / "llamadas_juez.jsonl"))
    resultados = leer_resultados(Path(args.respuestas))
    evaluados = evaluar_resultados(resultados, {p["id"]: p for p in banco}, spans, orden, juez)
    carpeta = Path(args.respuestas).parent
    escribir_jsonl(carpeta / "evaluados.jsonl", evaluados)
    agregados = agregar(evaluados)
    _escribir_csv(carpeta / "metricas_por_paso.csv", agregados)
    (carpeta / "metricas_por_paso.json").write_text(
        json.dumps(agregados, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    for fila in agregados:
        cobertura = "n/d" if fila["cobertura"] is None else f"{fila['cobertura']:.2f}"
        print(
            f"{fila['system']:>4} paso {fila['ingest_step']:>2}: cobertura {cobertura}, "
            f"contexto medio {fila['context_tokens_media']:.0f}, "
            f"indeterminadas {fila['indeterminadas']}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
