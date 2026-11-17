"""Pipeline del tutor, sin modelo: texto completo (tgrep) -> grafo (vecinos) -> páginas para la WikiLLM."""

import collections
import json
import math
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
import recuperacion as R  # noqa: E402

g = json.load(open(R.GRAFO["sin_indice"], encoding="utf-8"))
archivo = {n["id"]: n.get("source_file", "") for n in g["nodes"]}


def slug(i):
    m = re.match(r"^pages/(.+)\.md$", archivo.get(i, ""))
    return m.group(1) if m else None


vecinos = collections.defaultdict(
    collections.Counter
)  # enlaces [[...]] entre páginas, en ambos sentidos
for e in g["links"]:
    if e.get("relation") != "references":
        continue
    a, b = slug(e["source"]), slug(e["target"])
    if a and b and a != b:
        vecinos[a][b] += 1
        vecinos[b][a] += 1

docs = {
    s: collections.Counter(
        w.lower() for w in re.findall(r"[A-Za-z0-9][A-Za-z0-9\-\.\+\^]*", R.wiki.leer(s).a_texto())
    )
    for s in R.paginas
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


def con_vecinos(base, k_semilla, total):
    """k_semilla páginas del texto completo + las más enlazadas con ellas, hasta `total`."""
    semilla = base[:k_semilla]
    pts = collections.Counter()
    for s in semilla:
        for v, c in vecinos[s].items():
            if v not in semilla:
                pts[v] += c
    return semilla + [v for v, _ in pts.most_common(total - len(semilla))]


def cobertura(q, devueltas):
    sp = set().union(*[R.paginas[s]["spans"] for s in devueltas]) if devueltas else set()
    ev = {e["span_id"] for e in q["evidencia"]}
    fu = set().union(*[R.paginas[s]["fuentes"] for s in devueltas]) if devueltas else set()
    req = set(q["fuentes_requeridas"])
    return (
        len(ev & sp) / len(ev),
        len(req & fu) / len(req),
        sum(R.paginas[s]["tokens"] for s in devueltas),
    )


filas = collections.defaultdict(list)
for q in R.preguntas:
    kw = R.palabras_clave(q["texto"])
    tc, bu = texto_completo(kw), R.por_busqueda(kw)
    for nombre, pags in {
        "busqueda@5": bu[:5],
        "texto@5": tc[:5],
        "texto@3 + 2 vecinos": con_vecinos(tc, 3, 5),
        "texto@2 + 3 vecinos": con_vecinos(tc, 2, 5),
        "texto@8": tc[:8],
        "texto@5 + 3 vecinos": con_vecinos(tc, 5, 8),
        "busqueda@5 + 3 vecinos": con_vecinos(bu, 5, 8),
    }.items():
        filas[nombre].append((q["tipo"],) + cobertura(q, pags))
print(f"n={len(R.preguntas)} preguntas respondibles (paso 100)")
print(f"{'método':<26}{'frag.':>7}{'fuentes':>9}{'T2 frag.':>10}{'T3 frag.':>10}{'tokens':>9}")
for k, v in filas.items():

    def m(tipo, i):
        x = [r[i] for r in v if tipo is None or r[0] == tipo]
        return sum(x) / len(x)

    print(
        f"{k:<26}{m(None, 1):>7.2f}{m(None, 2):>9.2f}{m('T2', 1):>10.2f}{m('T3', 1):>10.2f}{m(None, 3):>9.0f}"
    )
