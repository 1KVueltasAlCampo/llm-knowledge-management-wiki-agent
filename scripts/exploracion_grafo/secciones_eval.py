"""Arista = co-ocurrencia de entidades en una misma sección. ¿Recupera mejor que páginas o frases?"""

import collections
import math
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
import grafos_eval as G  # noqa: E402
import recuperacion as R  # noqa: E402


def secciones(slug):
    p = R.wiki.leer(slug)
    partes = [("", [])]
    for linea in p.cuerpo.splitlines():
        m = re.match(r"^(#{1,6})\s+(.*)$", linea)
        if m:
            partes.append((m.group(2).strip(), [linea]))
        else:
            partes[-1][1].append(linea)
    return [(slug, t, "\n".join(ls).strip(), p.titulo) for t, ls in partes if "".join(ls).strip()]


SEC = [s for slug in R.paginas for s in secciones(slug)]
NS = len(SEC)
ENT_S = [G.entidades_de(f"{t}. {x}") for _, t, x, _ in SEC]
DF_ES = collections.Counter(e for es in ENT_S for e in es)
IDF_ES = {e: math.log(1 + NS / d) for e, d in DF_ES.items()}
PAL_S = [collections.Counter(G.palabras(f"{t} {x}")) for _, t, x, _ in SEC]
DF_WS = collections.Counter(w for c in PAL_S for w in c)
TOK_S = [len(x) // 4 for _, _, x, _ in SEC]


def ent_pregunta(texto):
    toks = {
        G.norm(t)
        for t in re.findall(r"[A-Za-z0-9][A-Za-z0-9\-\.\+\^]*", texto)
        if t.lower() not in G.PARADAS
    }
    return {e for e in toks if e in DF_ES and DF_ES[e] < 0.3 * NS}


def rank_entidades(q, k, lam=2.0):
    Q = ent_pregunta(q)
    if not Q:
        return []
    pts = []
    for i, es in enumerate(ENT_S):
        inter = Q & es
        if inter:
            cov = len(inter) / len(Q)
            pts.append((sum(IDF_ES[e] for e in inter) * (1 + lam * cov), i))
    pts.sort(reverse=True)
    return [i for _, i in pts[:k]]


def rank_lexico(kw, k, lam=2.0):
    ws = set(G.palabras(kw))
    pts = []
    for i, c in enumerate(PAL_S):
        inter = [w for w in ws if c.get(w)]
        if inter:
            cov = len(inter) / len(ws)
            pts.append((sum(math.log(1 + NS / DF_WS[w]) for w in inter) * (1 + lam * cov), i))
    pts.sort(reverse=True)
    return [i for _, i in pts[:k]]


def texto_sec(ids):
    return "\n".join(f"[{SEC[i][3]} / {SEC[i][1]}]\n{SEC[i][2]}" for i in ids)


def main():
    res = collections.defaultdict(list)
    for q in R.preguntas:
        kw = R.palabras_clave(q["texto"])
        tc = G.tfidf_paginas(kw)
        bu = R.por_busqueda(kw)
        variantes = {
            "búsqueda p@5": G.texto_paginas(bu[:5]),
            "texto p@5": G.texto_paginas(tc[:5]),
            "frases texto f@25": G.texto_frases(G.tfidf_frases(kw, 25)),
            "secciones entidades s@3": texto_sec(rank_entidades(q["texto"], 3)),
            "secciones entidades s@5": texto_sec(rank_entidades(q["texto"], 5)),
            "secciones entidades s@8": texto_sec(rank_entidades(q["texto"], 8)),
            "secciones léxico s@3": texto_sec(rank_lexico(kw, 3)),
            "secciones léxico s@5": texto_sec(rank_lexico(kw, 5)),
            "secciones léxico s@8": texto_sec(rank_lexico(kw, 8)),
            "secc.léxico s@5 + p@2 texto": texto_sec(rank_lexico(kw, 5))
            + "\n"
            + G.texto_paginas(tc[:2]),
        }
        for k, t in variantes.items():
            res[k].append((q["tipo"],) + G.medir(q, t))
    print(f"n={len(R.preguntas)} | secciones={NS}")
    print(
        f"{'método':<30}{'frag':>7}{'claves':>8}{'todas':>7}{'T1 cl.':>8}{'T2 cl.':>8}{'T3 cl.':>8}{'tokens':>8}"
    )
    for k, v in res.items():

        def m(tipo, i):
            x = [r[i] for r in v if tipo is None or r[0] == tipo]
            return sum(x) / len(x) if x else float("nan")

        todas = sum(r[2] == 1.0 for r in v) / len(v)
        print(
            f"{k:<30}{m(None, 1):>7.2f}{m(None, 2):>8.2f}{todas:>7.2f}{m('T1', 2):>8.2f}{m('T2', 2):>8.2f}{m('T3', 2):>8.2f}{m(None, 3):>8.0f}"
        )


if __name__ == "__main__":
    main()
