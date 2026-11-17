"""Grafo semántico (LLM) de 24 páginas, bien usado: puntuar páginas por entidades de la pregunta."""

import collections
import json
import math
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
import recuperacion as R  # noqa: E402
import sem_eval as SE  # noqa: E402  (reutiliza SUB, texto_completo, cobertura)

CONS = json.load(open(R.S / "consultas_llm.json", encoding="utf-8"))
g = json.load(open(SE.GSEM, encoding="utf-8"))


def norm(t):
    return re.sub(r"[^a-z0-9]", "", t.lower())


# etiqueta normalizada -> páginas donde hay un nodo con esa etiqueta (concepto o documento)
POR_ETIQUETA = collections.defaultdict(set)
for n in g["nodes"]:
    m = re.match(r"^pages/(.+)\.md$", n.get("source_file") or "")
    if m and m.group(1) in SE.SUB:
        POR_ETIQUETA[norm(n["label"])].add(m.group(1))
NP = len(SE.SUB)
ETIQUETAS = list(POR_ETIQUETA)


def paginas_por_entidades(entidades):
    pts = collections.Counter()
    usadas = 0
    for e in entidades:
        ne = norm(e)
        if len(ne) < 3:
            continue
        # la entidad coincide con una etiqueta (igual, o contenida en ella)
        pag = set()
        for et in ETIQUETAS:
            if et == ne or (len(ne) >= 4 and ne in et):
                pag |= POR_ETIQUETA[et]
        if pag:
            usadas += 1
            idf = math.log(1 + NP / len(pag))
            for p in pag:
                pts[p] += idf
    return [p for p, _ in pts.most_common()], usadas


def rrf(*listas, k=60):
    pts = collections.Counter()
    for l in listas:
        for r, x in enumerate(l):
            pts[x] += 1 / (k + r + 1)
    return [x for x, _ in pts.most_common()]


res = collections.defaultdict(list)
sin_entidades = 0
for q, disp in SE.qs:
    c = CONS[q["id"]]
    todo = " ".join(c["entities"] + c["keywords"])
    sem, usadas = paginas_por_entidades(c["entities"])
    sin_entidades += usadas == 0
    tx = SE.texto_completo(todo)
    bu = [s for s in R.por_busqueda(todo) if s in SE.SUB]
    gd = [
        s
        for s in R.por_grafo(" ".join(c["entities"]) or todo, R.GRAFO["sin_indice"])
        if s in SE.SUB
    ]
    v = {
        "búsqueda": bu,
        "grafo determinista": gd,
        "texto completo": tx,
        "grafo semántico (entidades)": sem,
        "semántico + texto (RRF)": rrf(sem, tx),
    }
    for k, pags in v.items():
        res[k].append(
            (q["tipo"], SE.cobertura(pags, disp, 3), SE.cobertura(pags, disp, 5), len(pags))
        )
print(
    f"{len(SE.qs)} preguntas con evidencia en las 24 páginas; sin ninguna entidad enlazada al grafo: {sin_entidades}"
)
print(f"{'método':<30}{'frag@3':>8}{'frag@5':>8}{'págs.':>7}")
for k, v in res.items():
    print(
        f"{k:<30}{sum(x[1] for x in v) / len(v):>8.2f}{sum(x[2] for x in v) / len(v):>8.2f}{sum(x[3] for x in v) / len(v):>7.1f}"
    )
