"""Elige las preguntas de la prueba de punta a punta por su recuperación (no por lo que falló la base)."""

import json
import random
import sys

sys.stdout.reconfigure(encoding="utf-8")
import grafos_eval as G  # noqa: E402
import recuperacion as R  # noqa: E402

from wikillm.eval.correctitud import clave_presente  # noqa: E402

CONS = json.load(open(R.S / "consultas_llm.json", encoding="utf-8"))
TEXTOS = {p: R.wiki.leer(p).a_texto() for p in R.paginas}


def claves(q):
    c = q.get("respuesta_clave") or []
    if q.get("respuesta_por_paso"):
        c = q["respuesta_por_paso"][-1]["respuesta_clave"]
    return c


def cobertura(q, pags):
    t = "\n".join(TEXTOS[p] for p in pags)
    c = claves(q)
    return sum(clave_presente(x, t) for x in c) / len(c) if c else 0.0


mejora, ambas = [], []
for q in R.preguntas:
    if not claves(q):
        continue
    c = CONS[q["id"]]
    qs = c["queries"] or [q["texto"]]
    bu = R.intercalar(*[R.por_busqueda(x) for x in qs])[:5]
    tx = G.tfidf_paginas(" ".join(c["entities"] + c["keywords"]))[:5]
    a, b = cobertura(q, bu), cobertura(q, tx)
    if b > a:
        mejora.append(q["id"])
    elif a == 1.0 and b == 1.0:
        ambas.append(q["id"])
rnd = random.Random(11)
controles = rnd.sample(sorted(ambas), min(8, len(ambas)))
print("mejora con texto completo:", len(mejora), mejora)
print("controles (ambos completos):", controles, "de", len(ambas))
open(R.S / "pipe_preguntas.txt", "w").write(",".join(mejora + controles))
