"""Recuperación con el grafo de citas entre papers (nodos = papers, aristas = cita a)."""

import collections
import json
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
import grafos_eval as G  # noqa: E402
import recuperacion as R  # noqa: E402

CONS = json.load(open(R.S / "consultas_llm.json", encoding="utf-8"))
man = [json.loads(l) for l in open("data/corpus100/manifest.jsonl", encoding="utf-8")]
IDS = [m["arxiv_id"] for m in man]
TITULO = {m["arxiv_id"]: m["titulo"] for m in man}
FECHA = {m["arxiv_id"]: m["fecha_publicacion"] for m in man}
CITA = collections.defaultdict(set)  # a -> {b}: a cita a b
CITADO_POR = collections.defaultdict(set)
for m in man:
    for r in m.get("referencias_en_corpus") or []:
        CITA[m["arxiv_id"]].add(r)
        CITADO_POR[r].add(m["arxiv_id"])
VEC = {i: CITA[i] | CITADO_POR[i] for i in IDS}

# página «paper» de cada paper
PAG_PAPER = {}
RESUMEN = {}
for s in R.paginas:
    p = R.wiki.leer(s)
    if p.tipo == "paper" and len(p.fuentes) == 1:
        PAG_PAPER[p.fuentes[0]] = s
        RESUMEN[p.fuentes[0]] = p.resumen
print("papers con página:", len(PAG_PAPER), "de", len(IDS))


def norm(t):
    return re.sub(r"[^a-z0-9]", "", t.lower())


TOK_TITULO = {
    i: {norm(w) for w in re.findall(r"[A-Za-z0-9][A-Za-z0-9\-\.\+\^]*", TITULO[i])} for i in IDS
}
TOK_RES = {
    i: {norm(w) for w in re.findall(r"[A-Za-z0-9][A-Za-z0-9\-\.\+\^]*", RESUMEN.get(i, ""))}
    for i in IDS
}
DF_T = collections.Counter(w for s in TOK_TITULO.values() for w in s)
DF_R = collections.Counter(w for s in TOK_RES.values() for w in s)


def semillas(c):
    """Papers cuyo título (o resumen) nombra una de las entidades de la pregunta."""
    pts = collections.Counter()
    for e in c["entities"]:
        ne = norm(e)
        if len(ne) < 3:
            continue
        # entidad con varias palabras: todas las palabras en el título
        palabras = [
            norm(w) for w in re.findall(r"[A-Za-z0-9][A-Za-z0-9\-\.\+\^]*", e) if len(norm(w)) >= 3
        ]
        for i in IDS:
            en_titulo = ne in TOK_TITULO[i] or (
                palabras and all(w in TOK_TITULO[i] for w in palabras)
            )
            en_res = ne in TOK_RES[i] or (palabras and all(w in TOK_RES[i] for w in palabras))
            if en_titulo and DF_T.get(ne, 1) <= 3:
                pts[i] += 1.0
            elif en_res and DF_R.get(ne, 1) <= 3:
                pts[i] += 0.4
    return pts


def ranking_citas(c, texto_rank):
    sem = semillas(c)
    if not sem:
        return [], sem
    cand = collections.Counter()
    for s, w in sem.items():
        cand[s] += w  # el propio paper semilla
        for v in VEC[s]:
            cand[v] += w
    pos = {PAG_PAPER[i]: r for r, i in enumerate([None])} if False else {}
    rank_texto = {p: k for k, p in enumerate(texto_rank)}
    orden = sorted(
        cand, key=lambda i: (-cand[i], rank_texto.get(PAG_PAPER.get(i), 10**6), FECHA[i])
    )
    return [PAG_PAPER[i] for i in orden if i in PAG_PAPER], sem


def main():
    res = collections.defaultdict(list)
    cubiertas = 0
    for q in R.preguntas:
        c = CONS[q["id"]]
        todo = " ".join(c["entities"] + c["keywords"])
        rk = G.tfidf_paginas(todo)
        cit, sem = ranking_citas(c, rk)
        cubiertas += bool(sem)
        # texto + expansión por citas: semillas de texto (3) y el resto por citas, reordenado por texto
        exp = rk[:3] + [p for p in cit if p not in rk[:3]][:2]
        # los candidatos por cita que además coinciden con la consulta
        cit_texto = [p for p in rk[:40] if p in set(cit[:25])]
        v = {
            "texto p@3": rk[:3],
            "texto p@5": rk[:5],
            "citas p@3 (semillas por título)": cit[:3],
            "citas p@5": cit[:5],
            "citas p@8": cit[:8],
            "texto p@3 + citas 2": exp,
            "texto p@3 + 2 citas∩texto": rk[:3] + [p for p in cit_texto if p not in rk[:3]][:2],
            "texto p@5 + citas∩texto 2": rk[:5] + [p for p in cit_texto if p not in rk[:5]][:2],
        }
        for k, pags in v.items():
            res[k].append((q["tipo"],) + G.medir(q, G.texto_paginas(pags)))
    print(f"n={len(R.preguntas)} | preguntas con semilla en el grafo de citas: {cubiertas}")
    print(
        f"{'método':<36}{'frag':>7}{'claves':>8}{'todas':>7}{'T2 cl.':>8}{'T3 cl.':>8}{'T2 todas':>10}{'tokens':>8}"
    )
    for k, vv in res.items():

        def m(tipo, i):
            x = [r[i] for r in vv if tipo is None or r[0] == tipo]
            return sum(x) / len(x) if x else float("nan")

        todas = sum(r[2] == 1.0 for r in vv) / len(vv)
        t2 = [r for r in vv if r[0] == "T2"]
        t2t = sum(r[2] == 1.0 for r in t2) / len(t2)
        print(
            f"{k:<36}{m(None, 1):>7.2f}{m(None, 2):>8.2f}{todas:>7.2f}{m('T2', 2):>8.2f}{m('T3', 2):>8.2f}{t2t:>10.2f}{m(None, 3):>8.0f}"
        )


if __name__ == "__main__":
    main()
