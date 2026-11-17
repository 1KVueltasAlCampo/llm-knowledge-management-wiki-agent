"""graph-expand: semillas por texto completo + vecinos por el grafo. ¿Importa cómo se eligen los vecinos?"""

import collections
import json
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
import grafos_eval as G  # noqa: E402
import recuperacion as R  # noqa: E402

CONS = json.load(open(R.S / "consultas_llm.json", encoding="utf-8"))
g = json.load(open(R.GRAFO["sin_indice"], encoding="utf-8"))
archivo = {n["id"]: n.get("source_file", "") for n in g["nodes"]}


def slug(i):
    m = re.match(r"^pages/(.+)\.md$", archivo.get(i, ""))
    return m.group(1) if m else None


ENLACES = collections.defaultdict(collections.Counter)  # enlaces [[..]] en ambos sentidos
SALIENTES = collections.defaultdict(set)
for e in g["links"]:
    if e.get("relation") != "references":
        continue
    a, b = slug(e["source"]), slug(e["target"])
    if a and b and a != b:
        ENLACES[a][b] += 1
        ENLACES[b][a] += 1
        SALIENTES[a].add(b)
TIPO = {s: R.wiki.leer(s).tipo for s in R.paginas}
FUENTES = {s: set(R.wiki.leer(s).fuentes) for s in R.paginas}


def expandir(semillas, ranking_texto, modo, n):
    vec = collections.Counter()
    for s in semillas:
        for v, c in ENLACES[s].items():
            if v not in semillas:
                vec[v] += c
    cand = list(vec)
    pos = {p: i for i, p in enumerate(ranking_texto)}
    if modo == "enlaces":
        orden = sorted(cand, key=lambda p: -vec[p])
    elif modo == "texto":  # el vecino que mejor coincide con la consulta
        orden = sorted(cand, key=lambda p: pos.get(p, 10**6))
    elif modo == "concepto":  # páginas de concepto primero (sintetizan varios papers)
        orden = sorted(cand, key=lambda p: (TIPO[p] != "concepto", pos.get(p, 10**6)))
    elif modo == "otro_paper":  # vecinos que añaden papers que las semillas no cubren
        cubiertos = set().union(*[FUENTES[s] for s in semillas]) if semillas else set()
        orden = sorted(cand, key=lambda p: (-len(FUENTES[p] - cubiertos), pos.get(p, 10**6)))
    else:
        orden = cand
    return semillas + orden[:n]


def main():
    res = collections.defaultdict(list)
    for q in R.preguntas:
        c = CONS[q["id"]]
        todo = " ".join(c["entities"] + c["keywords"])
        rk = G.tfidf_paginas(todo)
        v = {"texto p@3": rk[:3], "texto p@5": rk[:5], "texto p@7": rk[:7]}
        for modo in ("enlaces", "texto", "concepto", "otro_paper"):
            v[f"texto p@3 + 2 vecinos ({modo})"] = expandir(rk[:3], rk, modo, 2)
            v[f"texto p@3 + 4 vecinos ({modo})"] = expandir(rk[:3], rk, modo, 4)
        for k, pags in v.items():
            res[k].append((q["tipo"],) + G.medir(q, G.texto_paginas(pags)))
    print(f"n={len(R.preguntas)}")
    print(
        f"{'método':<40}{'frag':>7}{'claves':>8}{'todas':>7}{'T2 cl.':>8}{'T3 cl.':>8}{'tokens':>8}"
    )
    for k, vv in res.items():

        def m(tipo, i):
            x = [r[i] for r in vv if tipo is None or r[0] == tipo]
            return sum(x) / len(x) if x else float("nan")

        todas = sum(r[2] == 1.0 for r in vv) / len(vv)
        print(
            f"{k:<40}{m(None, 1):>7.2f}{m(None, 2):>8.2f}{todas:>7.2f}{m('T2', 2):>8.2f}{m('T3', 2):>8.2f}{m(None, 3):>8.0f}"
        )


if __name__ == "__main__":
    main()
