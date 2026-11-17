"""Etapa A (sin modelo): ¿qué métodos devuelven las páginas del wiki que tienen la evidencia?

Para cada pregunta respondible del banco mide, sobre las N primeras páginas que devuelve cada
método: cobertura de fuentes (fuentes_requeridas cubiertas por el `fuentes` de las páginas) y
cobertura de fragmentos (span_id de la evidencia citados literalmente en esas páginas).
"""

import json
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
S = Path(os.environ["S"])
WIKI = Path("data/wiki/construccion-1")
GRAFO = {
    "con_indice": S / "g100/fuente/graphify-out/graph.json",
    "sin_indice": S / "g100/fuente_sin_indice/graphify-out/graph.json",
}
GFY = S / "gfy-venv/Scripts/graphify.exe"
PATRON_SPAN = re.compile(r"\d{4}\.\d{4,5}#s\d+\.p\d+")
PARADAS = set(
    "a an the of in on for to and or is are was were be been what which who whom how many much does do "
    "did has have had that this these those with by from as at it its into than then their there "
    "about according reported report paper papers collection corpus score reach reaches get gets".split()
)

from wikillm.wiki.almacen import Wiki  # noqa: E402
from wikillm.wiki.herramientas import wiki_search  # noqa: E402

wiki = Wiki(WIKI)
paginas = {}
for slug in wiki.slugs():
    p = wiki.leer(slug)
    paginas[slug] = {
        "fuentes": set(p.fuentes),
        "spans": set(PATRON_SPAN.findall(p.cuerpo)),
        "tokens": len(p.a_texto()) // 4,
    }
banco = [json.loads(x) for x in open("data/preguntas/banco_100.jsonl", encoding="utf-8")]
preguntas = [q for q in banco if q["tipo"] != "T5" and q.get("fuentes_requeridas")]


def palabras_clave(texto: str) -> str:
    toks = re.findall(r"[A-Za-z0-9][A-Za-z0-9\-\.\+\^]*", texto)
    return " ".join(t for t in toks if t.lower() not in PARADAS and len(t) > 1)


def por_busqueda(consulta: str) -> list[str]:
    return [r.slug for r in wiki_search(wiki, consulta, 40)]


def por_grafo(consulta: str, grafo: Path, profundidad: int = 1) -> list[str]:
    salida = subprocess.run(
        [
            str(GFY),
            "query",
            consulta,
            "--graph",
            str(grafo),
            "--budget",
            "6000",
            "--depth",
            str(profundidad),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        env={**os.environ, "PYTHONUTF8": "1"},
    ).stdout
    inicio = re.search(r"Start: \[(.*?)\]", salida)
    etiquetas_inicio = set(re.findall(r"'((?:[^'\\]|\\.)*)'", inicio.group(1))) if inicio else set()
    directas, vecinas = [], []
    for linea in salida.splitlines():
        m = re.match(r"^NODE (.+?) \[src=(\S+) loc=(L\d+)", linea)
        if not m:
            continue
        etiqueta, fuente, _ = m.groups()
        pg = re.match(r"^pages/(.+)\.md$", fuente)
        if not pg or pg.group(1) not in paginas:
            continue
        slug = pg.group(1)
        destino = directas if etiqueta in etiquetas_inicio else vecinas
        if slug not in directas and slug not in vecinas:
            destino.append(slug)
        elif etiqueta in etiquetas_inicio and slug in vecinas:
            vecinas.remove(slug)
            directas.append(slug)
    return directas + vecinas


def intercalar(*listas: list[str]) -> list[str]:
    salida: list[str] = []
    for i in range(max((len(x) for x in listas), default=0)):
        for x in listas:
            if i < len(x) and x[i] not in salida:
                salida.append(x[i])
    return salida


def metricas(q, devueltas: list[str], n: int):
    top = devueltas[:n]
    fuentes = set().union(*[paginas[s]["fuentes"] for s in top]) if top else set()
    spans = set().union(*[paginas[s]["spans"] for s in top]) if top else set()
    req = set(q["fuentes_requeridas"])
    ev = {e["span_id"] for e in q["evidencia"]}
    return (
        len(req & fuentes) / len(req),
        len(ev & spans) / len(ev) if ev else 0.0,
        sum(paginas[s]["tokens"] for s in top),
    )


def evaluar(q):
    texto = q["texto"]
    kw = palabras_clave(texto)
    r = {
        "busqueda": por_busqueda(kw),
        "grafo": por_grafo(kw, GRAFO["con_indice"]),
        "grafo_sin_indice": por_grafo(kw, GRAFO["sin_indice"]),
        "grafo_prof2": por_grafo(kw, GRAFO["sin_indice"], 2),
    }
    r["busqueda+grafo"] = intercalar(r["busqueda"], r["grafo_sin_indice"])
    return q, r


if __name__ == "__main__":
    with ThreadPoolExecutor(4) as pool:
        res = list(pool.map(evaluar, preguntas))
    json.dump(
        {q["id"]: r for q, r in res}, open(S / "recuperacion_paginas.json", "w", encoding="utf-8")
    )
    metodos = ["busqueda", "grafo", "grafo_sin_indice", "grafo_prof2", "busqueda+grafo"]
    for n in (3, 5, 8):
        print(f"\n== primeras {n} páginas | n={len(res)} preguntas")
        print(
            f"{'método':<18}{'fuentes':>9}{'todas':>8}{'frag.':>8}{'ningún frag.':>14}{'tokens':>9}"
        )
        for m in metodos:
            f = e = t = todas = cero = 0
            for q, r in res:
                a, b, c = metricas(q, r[m], n)
                f += a
                e += b
                t += c
                todas += a == 1.0
                cero += b == 0
            k = len(res)
            print(
                f"{m:<18}{f / k:>9.2f}{todas / k:>8.2f}{e / k:>8.2f}{cero / k:>14.2f}{t / k:>9.0f}"
            )
    print("\npor tipo (primeras 5, cobertura de fragmentos)")
    for tipo in ("T1", "T2", "T3", "T4"):
        sub = [(q, r) for q, r in res if q["tipo"] == tipo]
        if not sub:
            continue
        print(
            f"  {tipo} (n={len(sub)}): "
            + "  ".join(
                f"{m}={sum(metricas(q, r[m], 5)[1] for q, r in sub) / len(sub):.2f}"
                for m in metodos
            )
        )
