"""Informe de una corrida: tablas por sistema, paso y tipo, y figuras SVG sin dependencias.

Solo lee `evaluados.jsonl` (lo escribe `wikillm.eval metricas`); no llama a ningún modelo.
"""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

from wikillm.eval.estadistica import comparar_pareado
from wikillm.eval.metricas import agregar

COLORES = {"rag": "#1f77b4", "wiki": "#d62728"}
COLOR_POR_DEFECTO = "#555555"
ANCHO, ALTO = 640, 360
MARGEN_IZQ, MARGEN_DER, MARGEN_SUP, MARGEN_INF = 64, 24, 40, 56

COLUMNAS_RESUMEN = (
    "n",
    "n_respondibles",
    "cobertura",
    "abstencion_correcta",
    "tasa_obsoleta",
    "context_tokens_media",
    "tokens_por_correcta",
    "costo_usd_total",
)


def leer_evaluados(carpeta: Path) -> list[dict[str, Any]]:
    ruta = carpeta / "evaluados.jsonl"
    return [
        json.loads(linea)
        for linea in ruta.read_text(encoding="utf-8").splitlines()
        if linea.strip()
    ]


def por_tipo(evaluados: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Una fila por (sistema, tipo, paso), con el mismo cálculo que `agregar`."""
    grupos: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for e in evaluados:
        grupos[e["tipo"]].append(e)
    filas = []
    for tipo in sorted(grupos):
        for fila in agregar(grupos[tipo]):
            filas.append({"system": fila["system"], "tipo": tipo, **_sin_sistema(fila)})
    return sorted(filas, key=lambda f: (f["system"], f["tipo"], f["ingest_step"]))


def _sin_sistema(fila: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in fila.items() if k != "system"}


def _celda(valor: Any) -> str:
    if valor is None:
        return ""
    if isinstance(valor, float):
        return f"{valor:.6g}"
    return str(valor)


def _escribir_csv(ruta: Path, filas: list[dict[str, Any]]) -> None:
    with ruta.open("w", encoding="utf-8", newline="") as f:
        if not filas:
            return
        escritor = csv.writer(f, lineterminator="\n")
        columnas = list(filas[0])
        escritor.writerow(columnas)
        for fila in filas:
            escritor.writerow([_celda(fila[c]) for c in columnas])


def _tabla_markdown(filas: list[dict[str, Any]], claves: tuple[str, ...]) -> str:
    columnas = (*claves, *COLUMNAS_RESUMEN)
    lineas = ["| " + " | ".join(columnas) + " |", "|" + "|".join(["---"] * len(columnas)) + "|"]
    for fila in filas:
        celdas = [_celda(fila[c]) if c in fila else "" for c in columnas]
        lineas.append("| " + " | ".join(celdas) + " |")
    return "\n".join(lineas)


def _tabla_pareada(filas: list[dict[str, Any]]) -> str:
    """Tabla por paso (sin el corte por tipo) con el intervalo en una sola celda."""
    columnas = (
        "ingest_step",
        "n",
        "cobertura_rag",
        "cobertura_wiki",
        "diferencia",
        "IC95",
        "solo_rag",
        "solo_wiki",
        "p_mcnemar",
    )
    lineas = ["| " + " | ".join(columnas) + " |", "|" + "|".join(["---"] * len(columnas)) + "|"]
    for f in (f for f in filas if f["tipo"] == ""):
        ic = f"[{_celda(f['ic95_inf'])}, {_celda(f['ic95_sup'])}]"
        celdas = [_celda(f[c]) if c != "IC95" else ic for c in columnas]
        lineas.append("| " + " | ".join(celdas) + " |")
    return "\n".join(lineas)


NOTA_PAREADA = (
    "Pares: preguntas respondibles en ese paso con respuesta de ambos brazos; acierta quien "
    "tiene veredicto `correcta`. `diferencia` = cobertura del wiki menos la de RAG. El IC95 sale "
    "de 2.000 remuestreos de las preguntas (semilla fija) y `p_mcnemar` es la prueba exacta sobre "
    "los pares discordantes (`solo_rag`, `solo_wiki`). Los intervalos suponen preguntas "
    "independientes y no hay corrección por comparaciones múltiples: con pocas preguntas por "
    "paso o por tipo conviene leerlos como orientativos."
)


def _resumen_markdown(
    nombre: str,
    general: list[dict[str, Any]],
    tipos: list[dict[str, Any]],
    pareada: list[dict[str, Any]],
) -> str:
    return (
        f"# Resumen de la corrida {nombre}\n\n"
        "Cifras calculadas solo de los resultados guardados de esta corrida. "
        "Una celda vacía significa que no hay denominador (no es cero). "
        "`n_respondibles` es el denominador de la cobertura.\n\n"
        "## Por sistema y paso\n\n"
        f"{_tabla_markdown(general, ('system', 'ingest_step'))}\n\n"
        "## Por sistema, tipo y paso\n\n"
        f"{_tabla_markdown(tipos, ('system', 'tipo', 'ingest_step'))}\n\n"
        "## Comparación pareada (wiki frente a RAG)\n\n"
        f"{NOTA_PAREADA}\n\n"
        f"{_tabla_pareada(pareada)}\n"
    )


def _figura(
    titulo: str,
    etiqueta_y: str,
    series: dict[str, list[tuple[int, float | None]]],
    y_max: float | None = None,
) -> str:
    puntos_validos = [(x, y) for serie in series.values() for x, y in serie if y is not None]
    xs = sorted({x for x, _ in puntos_validos})
    techo = y_max if y_max is not None else max((y for _, y in puntos_validos), default=0.0)
    techo = techo if techo > 0 else 1.0
    x_min, x_max = (xs[0], xs[-1]) if xs else (0, 1)
    ancho_util = ANCHO - MARGEN_IZQ - MARGEN_DER
    alto_util = ALTO - MARGEN_SUP - MARGEN_INF

    def pos_x(x: int) -> float:
        if x_max == x_min:
            return MARGEN_IZQ + ancho_util / 2
        return MARGEN_IZQ + (x - x_min) / (x_max - x_min) * ancho_util

    def pos_y(y: float) -> float:
        return MARGEN_SUP + alto_util - y / techo * alto_util

    partes = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {ANCHO} {ALTO}" '
        f'width="{ANCHO}" height="{ALTO}" font-family="sans-serif" font-size="12">',
        f"<title>{escape(titulo)}</title>",
        f'<rect width="{ANCHO}" height="{ALTO}" fill="#ffffff"/>',
        f'<text x="{ANCHO / 2:.1f}" y="22" text-anchor="middle" font-size="14">'
        f"{escape(titulo)}</text>",
        f'<line x1="{MARGEN_IZQ}" y1="{MARGEN_SUP}" x2="{MARGEN_IZQ}" '
        f'y2="{MARGEN_SUP + alto_util}" stroke="#333333"/>',
        f'<line x1="{MARGEN_IZQ}" y1="{MARGEN_SUP + alto_util}" '
        f'x2="{MARGEN_IZQ + ancho_util}" y2="{MARGEN_SUP + alto_util}" stroke="#333333"/>',
    ]
    for i in range(5):
        valor = techo * i / 4
        y = pos_y(valor)
        partes.append(
            f'<line x1="{MARGEN_IZQ}" y1="{y:.1f}" x2="{MARGEN_IZQ + ancho_util}" '
            f'y2="{y:.1f}" stroke="#dddddd"/>'
        )
        partes.append(
            f'<text x="{MARGEN_IZQ - 6}" y="{y + 4:.1f}" text-anchor="end">{valor:.3g}</text>'
        )
    for x in xs:
        partes.append(
            f'<text x="{pos_x(x):.1f}" y="{MARGEN_SUP + alto_util + 16}" '
            f'text-anchor="middle">{x}</text>'
        )
    partes.append(
        f'<text x="{MARGEN_IZQ + ancho_util / 2:.1f}" y="{ALTO - 22}" '
        'text-anchor="middle">Paso de ingesta (papers ingeridos)</text>'
    )
    partes.append(
        f'<text x="16" y="{MARGEN_SUP + alto_util / 2:.1f}" text-anchor="middle" '
        f'transform="rotate(-90 16 {MARGEN_SUP + alto_util / 2:.1f})">{escape(etiqueta_y)}</text>'
    )
    for indice, (nombre, serie) in enumerate(sorted(series.items())):
        color = COLORES.get(nombre, COLOR_POR_DEFECTO)
        validos = sorted((x, y) for x, y in serie if y is not None)
        if validos:
            trazo = " ".join(f"{pos_x(x):.1f},{pos_y(y):.1f}" for x, y in validos)
            partes.append(
                f'<polyline fill="none" stroke="{color}" stroke-width="2" points="{trazo}"/>'
            )
            for x, y in validos:
                partes.append(
                    f'<circle cx="{pos_x(x):.1f}" cy="{pos_y(y):.1f}" r="3" fill="{color}"/>'
                )
        leyenda_x = MARGEN_IZQ + 12 + indice * 90
        partes.append(
            f'<rect x="{leyenda_x}" y="{MARGEN_SUP + 6}" width="12" height="12" fill="{color}"/>'
        )
        partes.append(f'<text x="{leyenda_x + 18}" y="{MARGEN_SUP + 16}">{escape(nombre)}</text>')
    partes.append("</svg>")
    return "\n".join(partes) + "\n"


def _series(filas: list[dict[str, Any]], campo: str) -> dict[str, list[tuple[int, float | None]]]:
    series: dict[str, list[tuple[int, float | None]]] = defaultdict(list)
    for fila in filas:
        series[fila["system"]].append((int(fila["ingest_step"]), fila[campo]))
    return dict(series)


def _costo_acumulado(filas: list[dict[str, Any]]) -> dict[str, list[tuple[int, float | None]]]:
    series: dict[str, list[tuple[int, float | None]]] = {}
    for sistema, puntos in _series(filas, "costo_usd_total").items():
        total = 0.0
        acumulada: list[tuple[int, float | None]] = []
        for paso, costo in sorted(puntos):
            total += costo or 0.0
            acumulada.append((paso, total))
        series[sistema] = acumulada
    return series


def escribir_informe(carpeta: Path) -> Path:
    """Escribe tablas, resumen y figuras en `<carpeta>/informe/` y devuelve esa ruta."""
    evaluados = leer_evaluados(carpeta)
    general = agregar(evaluados)
    tipos = por_tipo(evaluados)
    pareada = comparar_pareado(evaluados)
    destino = carpeta / "informe"
    destino.mkdir(exist_ok=True)
    nombre = carpeta.name
    _escribir_csv(destino / "por_sistema_paso.csv", general)
    _escribir_csv(destino / "por_tipo.csv", tipos)
    _escribir_csv(destino / "comparacion_pareada.csv", pareada)
    (destino / "resumen.md").write_text(
        _resumen_markdown(nombre, general, tipos, pareada), encoding="utf-8"
    )
    figuras = {
        "cobertura_por_paso.svg": _figura(
            f"Cobertura por paso de ingesta ({nombre})",
            "Cobertura (respondibles correctas)",
            _series(general, "cobertura"),
            y_max=1.0,
        ),
        "contexto_por_paso.svg": _figura(
            f"Tokens de contexto medios por paso ({nombre})",
            "Tokens de contexto (media)",
            _series(general, "context_tokens_media"),
        ),
        "costo_acumulado.svg": _figura(
            f"Costo acumulado por sistema ({nombre})",
            "USD acumulados",
            _costo_acumulado(general),
        ),
    }
    for archivo, contenido in figuras.items():
        (destino / archivo).write_text(contenido, encoding="utf-8")
    return destino
