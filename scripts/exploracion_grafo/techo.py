"""Techo de recuperación y preguntas recuperables pero perdidas por el mejor recuperador de texto."""

import sys

sys.stdout.reconfigure(encoding="utf-8")
import grafos_eval as G  # noqa: E402
import recuperacion as R  # noqa: E402

from wikillm.eval.correctitud import clave_presente  # noqa: E402

TODO = "\n".join(R.wiki.leer(p).a_texto() for p in R.paginas)
TEXTOS = {p: R.wiki.leer(p).a_texto() for p in R.paginas}


def claves_de(q):
    c = q.get("respuesta_clave") or []
    if q.get("respuesta_por_paso"):
        c = q["respuesta_por_paso"][-1]["respuesta_clave"]
    return c


filas = []
for q in R.preguntas:
    claves = claves_de(q)
    if not claves:
        continue
    techo = [c for c in claves if clave_presente(c, TODO)]
    kw = R.palabras_clave(q["texto"])
    rank_texto = G.tfidf_paginas(kw)
    top5 = "\n".join(TEXTOS[p] for p in rank_texto[:5])
    top10 = "\n".join(TEXTOS[p] for p in rank_texto[:10])
    bu = R.por_busqueda(kw)
    top5b = "\n".join(TEXTOS[p] for p in bu[:5])
    ok5 = [c for c in claves if clave_presente(c, top5)]
    ok10 = [c for c in claves if clave_presente(c, top10)]
    ok5b = [c for c in claves if clave_presente(c, top5b)]
    filas.append((q, claves, techo, ok5, ok10, ok5b, rank_texto, bu))

print(f"{'tipo':<5}{'n':>4}{'techo(todas)':>14}{'texto@5':>9}{'texto@10':>10}{'búsqueda@5':>12}")
for tipo in ("T1", "T2", "T3", "T4", None):
    f = [x for x in filas if tipo is None or x[0]["tipo"] == tipo]
    n = len(f)
    print(
        f"{tipo or 'todas':<5}{n:>4}{sum(len(x[2]) == len(x[1]) for x in f) / n:>14.2f}"
        f"{sum(len(x[3]) == len(x[1]) for x in f) / n:>9.2f}{sum(len(x[4]) == len(x[1]) for x in f) / n:>10.2f}"
        f"{sum(len(x[5]) == len(x[1]) for x in f) / n:>12.2f}"
    )

print("\nRecuperables (techo completo) pero que el mejor recuperador de texto@5 NO completa:")
for q, claves, techo, ok5, ok10, ok5b, rank, bu in filas:
    if len(techo) == len(claves) and len(ok5) < len(claves):
        faltan = [c for c in claves if c not in ok5]
        donde = {}
        for c in faltan:
            pos = [i for i, p in enumerate(rank) if clave_presente(c, TEXTOS[p])]
            donde[c] = (len(pos), pos[:3])
        print(f"- {q['id']} [{q['tipo']}] {q['texto'][:95]}")
        print(
            f"    faltan {faltan} | (nº de páginas que la contienen, sus posiciones en el ranking de texto) {donde}"
        )
