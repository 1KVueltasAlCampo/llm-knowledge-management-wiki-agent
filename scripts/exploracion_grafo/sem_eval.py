"""Evalúa gratis el grafo semántico de 24 páginas frente a búsqueda, grafo determinista y texto completo."""

import collections
import math
import os
import re
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")
import recuperacion as R  # noqa: E402

SUB = {p[:-3] for p in os.listdir(R.S / "gsub/fuente/pages")}
GSEM = R.S / "gsub/fuente/graphify-out/graph.json"


def por_grafo_sem(consulta, prof=1):
    salida = subprocess.run(
        [
            str(R.GFY),
            "query",
            consulta,
            "--graph",
            str(GSEM),
            "--budget",
            "6000",
            "--depth",
            str(prof),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        env={**os.environ, "PYTHONUTF8": "1"},
    ).stdout
    ini = re.search(r"Start: \[(.*?)\]\s*\|", salida)
    et = set(re.findall(r"'((?:[^'\\]|\\.)*)'", ini.group(1))) if ini else set()
    dir_, vec = [], []
    for linea in salida.splitlines():
        m = re.match(r"^NODE (.+?) \[src=(\S+) loc=", linea)
        if not m:
            continue
        pg = re.match(r"^pages/(.+)\.md$", m.group(2))
        if not pg or pg.group(1) not in SUB:
            continue
        s = pg.group(1)
        d = dir_ if m.group(1) in et else vec
        if s not in dir_ and s not in vec:
            d.append(s)
        elif m.group(1) in et and s in vec:
            vec.remove(s)
            dir_.append(s)
    return dir_ + vec


docs = {
    s: collections.Counter(
        w.lower() for w in re.findall(r"[A-Za-z0-9][A-Za-z0-9\-\.\+\^]*", R.wiki.leer(s).a_texto())
    )
    for s in SUB
}
N = len(docs)
df = collections.Counter(w for c in docs.values() for w in c)


def texto_completo(consulta):
    ws = [w.lower() for w in consulta.split()]
    p = {
        s: sum((1 + math.log(c[w])) * math.log(1 + N / df[w]) for w in ws if c.get(w))
        for s, c in docs.items()
    }
    return [s for s in sorted(p, key=p.get, reverse=True) if p[s] > 0]


def cobertura(devueltas, disp, n):
    sp = set().union(*[R.paginas[s]["spans"] for s in devueltas[:n]]) if devueltas[:n] else set()
    return len(disp & sp) / len(disp)


qs = []
for q in R.preguntas:
    ev = {e["span_id"] for e in q["evidencia"]}
    disp = {s for s in ev if any(s in R.paginas[p]["spans"] for p in SUB)}
    if disp:
        qs.append((q, disp))
print(
    "preguntas con evidencia dentro del subconjunto:",
    len(qs),
    collections.Counter(q["tipo"] for q, _ in qs),
)
res = collections.defaultdict(list)
for q, disp in qs:
    kw = R.palabras_clave(q["texto"])
    m = {
        "busqueda": [s for s in R.por_busqueda(kw) if s in SUB],
        "grafo_determinista": [s for s in R.por_grafo(kw, R.GRAFO["sin_indice"]) if s in SUB],
        "grafo_semantico": por_grafo_sem(kw),
        "texto_completo": texto_completo(kw),
    }
    for k, v in m.items():
        res[k].append((q["tipo"], cobertura(v, disp, 3), cobertura(v, disp, 5), len(v)))
print(f"\n{'método':<20}{'frag@3':>8}{'frag@5':>8}{'págs. devueltas':>17}  | T3: frag@5")
for k, v in res.items():
    t3 = [x[2] for x in v if x[0] == "T3"]
    print(
        f"{k:<20}{sum(x[1] for x in v) / len(v):>8.2f}{sum(x[2] for x in v) / len(v):>8.2f}{sum(x[3] for x in v) / len(v):>17.1f}  | {sum(t3) / max(len(t3), 1):.2f} (n={len(t3)})"
    )
