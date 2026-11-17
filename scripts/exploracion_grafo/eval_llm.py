"""Recuperación con las consultas que escribe el LLM (entidades, palabras clave y 3 consultas)."""

import collections
import json
import sys

sys.stdout.reconfigure(encoding="utf-8")
import grafos_eval as G  # noqa: E402
import recuperacion as R  # noqa: E402
import secciones_eval as SE  # noqa: E402

CONS = json.load(open(R.S / "consultas_llm.json", encoding="utf-8"))


def rrf(*listas, k=60):
    pts = collections.Counter()
    for l in listas:
        for r, x in enumerate(l):
            pts[x] += 1 / (k + r + 1)
    return [x for x, _ in pts.most_common()]


def main():
    res = collections.defaultdict(list)
    for q in R.preguntas:
        c = CONS[q["id"]]
        ents = " ".join(c["entities"])
        todo = " ".join(c["entities"] + c["keywords"])
        qs = c["queries"] or [q["texto"]]
        busq = [R.por_busqueda(x) for x in qs]
        busq_union = R.intercalar(*busq)
        tf_todo = G.tfidf_paginas(todo)
        tf_qs = rrf(*[G.tfidf_paginas(x) for x in qs])
        graf_e = R.por_grafo(ents or qs[0], R.GRAFO["sin_indice"])
        graf_q = R.intercalar(*[R.por_grafo(x, R.GRAFO["sin_indice"]) for x in qs])
        # graph-expand a la Graphify: semillas de texto + vecinos del grafo
        graf_exp = tf_todo[:3] + [p for p in R.intercalar(graf_q) if p not in tf_todo[:3]][:2]
        v = {
            "búsqueda 1.ª consulta p@5": G.texto_paginas(busq[0][:5]),
            "búsqueda 3 consultas p@5": G.texto_paginas(busq_union[:5]),
            "texto (ents+kw) p@5": G.texto_paginas(tf_todo[:5]),
            "texto 3 consultas RRF p@5": G.texto_paginas(tf_qs[:5]),
            "grafo (entidades) p@5": G.texto_paginas(graf_e[:5]),
            "grafo 3 consultas p@5": G.texto_paginas(graf_q[:5]),
            "texto p@3 + grafo 2 vecinos": G.texto_paginas(graf_exp),
            "búsq.+texto+grafo RRF p@5": G.texto_paginas(rrf(busq_union, tf_qs, graf_q)[:5]),
            "texto+grafo RRF p@5": G.texto_paginas(rrf(tf_qs, graf_q)[:5]),
            "secciones léxico s@5 (ents+kw)": SE.texto_sec(SE.rank_lexico(todo, 5)),
            "secciones léxico s@8 (ents+kw)": SE.texto_sec(SE.rank_lexico(todo, 8)),
            "frases f@25 (ents+kw)": G.texto_frases(G.tfidf_frases(todo, 25)),
        }
        for k, t in v.items():
            res[k].append((q["tipo"],) + G.medir(q, t))
    print(f"n={len(R.preguntas)} (consultas del LLM)")
    print(
        f"{'método':<34}{'frag':>7}{'claves':>8}{'todas':>7}{'T1 cl.':>8}{'T2 cl.':>8}{'T3 cl.':>8}{'tokens':>8}"
    )
    for k, vv in res.items():

        def m(tipo, i):
            x = [r[i] for r in vv if tipo is None or r[0] == tipo]
            return sum(x) / len(x) if x else float("nan")

        todas = sum(r[2] == 1.0 for r in vv) / len(vv)
        print(
            f"{k:<34}{m(None, 1):>7.2f}{m(None, 2):>8.2f}{todas:>7.2f}{m('T1', 2):>8.2f}{m('T2', 2):>8.2f}{m('T3', 2):>8.2f}{m(None, 3):>8.0f}"
        )


if __name__ == "__main__":
    main()
