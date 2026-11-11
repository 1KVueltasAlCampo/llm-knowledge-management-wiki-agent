"""Resume las corridas de ``comparar_herramientas.py`` por variante, pregunta y herramienta.

Une varios ``corridas.jsonl`` y trata ``actual`` y ``generico`` como una sola línea base (son la
misma implementación: el control de equivalencia las deja iguales), lo que duplica sus corridas.

Uso:  uv run python scripts/analizar_herramientas.py results/herramientas/paso15 [más carpetas]
"""

from __future__ import annotations

import json
import random
import statistics
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

BASE = "actual+generico"
ORDEN = (
    BASE,
    "grep",
    "secciones",
    "esquema",
    "graphify",
    "fragmentos",
    "gist",
    "vecinos",
    "combinado",
    "opcional",
    "tras_grafo",
    "tras_lectura",
)


def cargar(carpetas: list[Path]) -> list[dict[str, Any]]:
    filas = []
    for carpeta in carpetas:
        for linea in (carpeta / "corridas.jsonl").read_text("utf-8").splitlines():
            fila = json.loads(linea)
            if "error" in fila:
                continue
            if fila["variante"] in ("actual", "generico"):
                fila["variante"] = BASE
            filas.append(fila)
    return filas


def media(valores: list[float]) -> float:
    return sum(valores) / len(valores) if valores else float("nan")


def tabla_global(filas: list[dict[str, Any]]) -> None:
    print("\n== Por variante (todas las corridas)")
    print(
        f"{'variante':<17}{'n':>4}{'ok':>5}{'llam.':>7}{'t.entrada':>11}{'mediana':>9}"
        f"{'t.ctx':>8}{'t.sal':>7}{'USD':>10}{'seg':>7}"
    )
    for v in ORDEN:
        f = [x for x in filas if x["variante"] == v]
        if not f:
            continue
        print(
            f"{v:<17}{len(f):>4}{sum(x['correcta'] for x in f):>5}"
            f"{media([x['llamadas'] for x in f]):>7.1f}"
            f"{media([x['tokens_entrada'] for x in f]):>11.0f}"
            f"{statistics.median(x['tokens_entrada'] for x in f):>9.0f}"
            f"{media([x['tokens_contexto'] for x in f]):>8.0f}"
            f"{media([x['tokens_salida'] for x in f]):>7.0f}"
            f"{media([x['usd'] for x in f]):>10.6f}{media([x['segundos'] for x in f]):>7.1f}"
        )


def tabla_por_pregunta(filas: list[dict[str, Any]]) -> None:
    preguntas = sorted({x["pregunta"] for x in filas})
    print("\n== Mediana de tokens de entrada por pregunta (y aciertos / corridas)")
    print(f"{'pregunta':<12}" + "".join(f"{v:>22}" for v in ORDEN))
    for q in preguntas:
        linea = f"{q:<12}"
        for v in ORDEN:
            f = [x for x in filas if x["pregunta"] == q and x["variante"] == v]
            if not f:
                linea += f"{'-':>22}"
                continue
            mediana = statistics.median(x["tokens_entrada"] for x in f)
            linea += f"{mediana:>13.0f} {sum(x['correcta'] for x in f):>2}/{len(f):<2}   "
        print(linea)


def tabla_solo_aciertos(filas: list[dict[str, Any]]) -> None:
    """Preguntas que todas las variantes aciertan siempre: la comparación sin el ruido del fallo."""
    por_pregunta = defaultdict(list)
    for x in filas:
        por_pregunta[x["pregunta"]].append(x)
    fiables = [q for q, f in por_pregunta.items() if all(x["correcta"] for x in f)]
    print(f"\n== Preguntas que todas las variantes aciertan siempre: {', '.join(sorted(fiables))}")
    print(f"{'variante':<17}{'n':>4}{'llam.':>7}{'t.entrada':>11}{'t.ctx':>8}{'USD':>10}")
    base = None
    for v in ORDEN:
        f = [x for x in filas if x["variante"] == v and x["pregunta"] in fiables]
        if not f:
            continue
        entrada = media([x["tokens_entrada"] for x in f])
        base = entrada if base is None else base
        print(
            f"{v:<17}{len(f):>4}{media([x['llamadas'] for x in f]):>7.1f}{entrada:>11.0f}"
            f"{media([x['tokens_contexto'] for x in f]):>8.0f}"
            f"{media([x['usd'] for x in f]):>10.6f}   ({entrada / base - 1:+.0%} frente a la base)"
        )


def tabla_herramientas(filas: list[dict[str, Any]]) -> None:
    print("\n== Tokens que devuelve cada herramienta por llamada (media)")
    por_herramienta = defaultdict(list)
    for x in filas:
        for paso in x["pasos"]:
            if "tokens_devueltos" in paso:
                por_herramienta[(x["variante"], paso["accion"])].append(paso["tokens_devueltos"])
    print(f"{'variante':<17}{'herramienta':<10}{'llamadas':>9}{'tokens/llamada':>16}")
    for (v, h), t in sorted(por_herramienta.items(), key=lambda k: (ORDEN.index(k[0][0]), k[0][1])):
        print(f"{v:<17}{h:<10}{len(t):>9}{media(t):>16.0f}")


def tabla_intervalos(filas: list[dict[str, Any]], remuestreos: int = 5000) -> None:
    """Diferencia de la media por pregunta frente a la base, con IC 95 % por remuestreo."""
    preguntas = sorted({x["pregunta"] for x in filas})
    azar = random.Random(0)

    def macro(variante: str, campo: str, muestra: bool) -> float:
        medias = []
        for q in preguntas:
            f = [x[campo] for x in filas if x["pregunta"] == q and x["variante"] == variante]
            if muestra:
                f = azar.choices(f, k=len(f))
            medias.append(media(f))
        return media(medias)

    print("\n== Diferencia frente a la base de la media por pregunta (IC 95 % por remuestreo)")
    print(f"{'variante':<17}{'t.entrada':>26}{'USD (x1000)':>30}")
    for v in ORDEN[1:]:
        if not any(x["variante"] == v for x in filas):
            continue
        celdas = []
        for campo, escala in (("tokens_entrada", 1), ("usd", 1000)):
            punto = macro(v, campo, False) - macro(BASE, campo, False)
            dif = sorted(
                macro(v, campo, True) - macro(BASE, campo, True) for _ in range(remuestreos)
            )
            bajo, alto = dif[int(0.025 * remuestreos)], dif[int(0.975 * remuestreos)]
            celdas.append(f"{punto * escala:+9.1f} [{bajo * escala:+.1f}, {alto * escala:+.1f}]")
        print(f"{v:<17}{celdas[0]:>26}{celdas[1]:>30}")


def tabla_facturacion(filas: list[dict[str, Any]], carpetas: list[Path]) -> None:
    """Lo que se factura: entrada sin caché, entrada en caché, salida y dólares por corrida.

    Sale de ``llamadas.jsonl`` (una línea por llamada al modelo, con la etiqueta de la variante;
    la variante ``actual`` se registra como ``wiki``) y se divide por el número de corridas.
    """
    etiqueta = {"wiki": BASE, "generico": BASE}
    totales: dict[str, list[float]] = defaultdict(lambda: [0.0, 0.0, 0.0, 0.0, 0.0])
    for carpeta in carpetas:
        ruta = carpeta / "llamadas.jsonl"
        if not ruta.exists():
            continue
        for linea in ruta.read_text("utf-8").splitlines():
            r = json.loads(linea)
            t = totales[etiqueta.get(r["etiqueta"], r["etiqueta"])]
            t[0] += 1
            t[1] += r["tokens_entrada_sin_cache"]
            t[2] += r["tokens_entrada_cache"]
            t[3] += r["tokens_salida"]
            t[4] += r["usd"]
    print("\n== Facturación por corrida (de llamadas.jsonl)")
    print(
        f"{'variante':<17}{'corr.':>6}{'llam.':>7}{'sin caché':>11}{'en caché':>10}"
        f"{'% caché':>9}{'salida':>8}{'USD':>10}"
    )
    for v in ORDEN:
        corridas = sum(1 for x in filas if x["variante"] == v)
        t = totales.get(v)
        if not t or not corridas:
            continue
        entrada = t[1] + t[2]
        print(
            f"{v:<17}{corridas:>6}{t[0] / corridas:>7.1f}{t[1] / corridas:>11.0f}"
            f"{t[2] / corridas:>10.0f}{t[2] / entrada:>9.0%}{t[3] / corridas:>8.0f}"
            f"{t[4] / corridas:>10.6f}"
        )


def main() -> int:
    carpetas = [Path(a) for a in sys.argv[1:]]
    if not carpetas:
        print(__doc__)
        return 1
    filas = cargar(carpetas)
    print(f"{len(filas)} corridas de {', '.join(str(c) for c in carpetas)}")
    tabla_global(filas)
    tabla_por_pregunta(filas)
    tabla_solo_aciertos(filas)
    tabla_herramientas(filas)
    tabla_facturacion(filas, carpetas)
    tabla_intervalos(filas)
    return 0


if __name__ == "__main__":
    sys.exit(main())
