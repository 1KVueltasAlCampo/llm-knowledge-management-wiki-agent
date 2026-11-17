"""Prueba sin modelo de grafos con otras aristas (entidades+PPR, hechos, citas) sobre el wiki de 100 papers.

Métricas por pregunta (84 respondibles): cobertura de fragmentos (span_id exactos de la evidencia que
aparecen en lo devuelto), cobertura de claves (la respuesta_clave está en lo devuelto) y tokens.
"""

import collections
import math
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
import recuperacion as R  # noqa: E402

from wikillm.eval.correctitud import clave_presente  # noqa: E402

SPAN = R.PATRON_SPAN
PARADAS = R.PARADAS | {
    "table",
    "figure",
    "section",
    "paper",
    "papers",
    "results",
    "result",
    "method",
}


def norm(t: str) -> str:
    return re.sub(r"[^a-z0-9]", "", t.lower())


# ------------------------------------------------------------------ hechos (frases con cita)
def frases(slug):
    cuerpo = R.wiki.leer(slug).cuerpo
    salida, seccion = [], ""
    for linea in cuerpo.splitlines():
        t = linea.strip()
        if not t:
            continue
        if t.startswith("#"):
            seccion = t.lstrip("# ").strip()
            continue
        for s in re.split(r"(?<=\.)\s+(?=[A-Z\[])", t):
            s = s.strip()
            if len(s) > 25:
                salida.append((slug, seccion, s))
    return salida


# ------------------------------------------------------------------ entidades
P_CAMEL = re.compile(r"\b[A-Z][a-z]+(?:[A-Z][A-Za-z0-9]*)+\b")
P_MIXTA = re.compile(r"\b[A-Za-z]*[A-Z][A-Za-z]*[0-9][A-Za-z0-9\.]*\b|\b[A-Z]{2,}[A-Za-z0-9]*\b")
P_GUION = re.compile(r"\b[A-Za-z0-9]+(?:-[A-Za-z0-9\.]+)+\b")
P_TITULO = re.compile(r"(?<=[a-z,;\(] )[A-Z][a-z]{2,}\b")


def entidades_de(texto: str) -> set[str]:
    texto = SPAN.sub(" ", texto)
    crudas = (
        set(P_CAMEL.findall(texto)) | set(P_MIXTA.findall(texto)) | set(P_TITULO.findall(texto))
    )
    crudas |= {t for t in P_GUION.findall(texto) if any(c.isupper() or c.isdigit() for c in t)}
    return {norm(t) for t in crudas if len(norm(t)) >= 2 and t.lower() not in PARADAS}


ALL_FRASES = [f for s in R.paginas for f in frases(s)]
ENT_FRASE = [entidades_de(f[2]) for f in ALL_FRASES]
ENT_PAG = collections.defaultdict(collections.Counter)
for f, es in zip(ALL_FRASES, ENT_FRASE):
    for e in es:
        ENT_PAG[f[0]][e] += 1
NP = len(R.paginas)
DF_E = collections.Counter(e for c in ENT_PAG.values() for e in c)
VOCAB = {e for e, d in DF_E.items() if d >= 1}
IDF_E = {e: math.log(1 + NP / d) for e, d in DF_E.items()}
# índice invertido entidad -> frases
POR_ENT = collections.defaultdict(list)
for i, es in enumerate(ENT_FRASE):
    for e in es:
        POR_ENT[e].append(i)


# texto completo por palabra (control sin grafo), a nivel de página y de frase
def palabras(t):
    return [
        w.lower()
        for w in re.findall(r"[A-Za-z0-9][A-Za-z0-9\-\.\+\^]*", t)
        if w.lower() not in PARADAS
    ]


DOC_P = {s: collections.Counter(palabras(R.wiki.leer(s).a_texto())) for s in R.paginas}
DF_P = collections.Counter(w for c in DOC_P.values() for w in c)
DOC_F = [collections.Counter(palabras(f[2])) for f in ALL_FRASES]
DF_F = collections.Counter(w for c in DOC_F for w in c)
NF = len(ALL_FRASES)


def tfidf_paginas(consulta):
    ws = palabras(consulta)
    pts = {
        s: sum((1 + math.log(c[w])) * math.log(1 + NP / DF_P[w]) for w in ws if c.get(w))
        for s, c in DOC_P.items()
    }
    return [s for s in sorted(pts, key=pts.get, reverse=True) if pts[s] > 0]


def tfidf_frases(consulta, n):
    ws = palabras(consulta)
    pts = []
    for i, c in enumerate(DOC_F):
        sc = sum(math.log(1 + NF / DF_F[w]) for w in ws if c.get(w))
        if sc > 0:
            pts.append((sc, i))
    pts.sort(reverse=True)
    return [i for _, i in pts[:n]]


def entidades_pregunta(texto: str) -> dict[str, float]:
    toks = {
        norm(t)
        for t in re.findall(r"[A-Za-z0-9][A-Za-z0-9\-\.\+\^]*", texto)
        if t.lower() not in PARADAS
    }
    return {e: IDF_E[e] for e in toks if e in VOCAB and DF_E[e] < 0.4 * NP}


# ------------------------------------------------------------------ PPR bipartito entidad-página (HippoRAG)
def ppr_paginas(consulta, restart=0.5, it=20):
    semillas = entidades_pregunta(consulta)
    if not semillas:
        return []
    paginas = list(R.paginas)
    ix = {p: i for i, p in enumerate(paginas)}
    # transición p -> e y e -> p
    suma_p = {p: sum(1 + math.log(v) for v in ENT_PAG[p].values()) or 1 for p in paginas}
    suma_e = collections.defaultdict(float)
    for p in paginas:
        for e, v in ENT_PAG[p].items():
            suma_e[e] += 1 + math.log(v)
    s_pers = {e: w for e, w in semillas.items()}
    z = sum(s_pers.values())
    pers = {e: w / z for e, w in s_pers.items()}
    ent = dict(pers)
    pag = {p: 0.0 for p in paginas}
    for _ in range(it):
        # e -> p
        nuevo_p = collections.defaultdict(float)
        for e, m in ent.items():
            if suma_e[e] == 0:
                continue
            for p in (pp for pp in paginas if e in ENT_PAG[pp]):
                nuevo_p[p] += m * (1 + math.log(ENT_PAG[p][e])) / suma_e[e]
        # p -> e
        nuevo_e = collections.defaultdict(float)
        for p, m in nuevo_p.items():
            for e, v in ENT_PAG[p].items():
                nuevo_e[e] += m * (1 + math.log(v)) / suma_p[p]
        ent = {
            e: restart * pers.get(e, 0.0) + (1 - restart) * nuevo_e.get(e, 0.0)
            for e in set(pers) | set(nuevo_e)
        }
        pag = {p: nuevo_p.get(p, 0.0) for p in paginas}
    return [p for p in sorted(pag, key=pag.get, reverse=True) if pag[p] > 0]


def rrf(*listas, k=60):
    pts = collections.Counter()
    for l in listas:
        for r, x in enumerate(l):
            pts[x] += 1 / (k + r + 1)
    return [x for x, _ in pts.most_common()]


# ------------------------------------------------------------------ hechos como aristas (entidad - hecho - entidad)
def hechos_por_entidades(consulta, n):
    q = entidades_pregunta(consulta)
    pts = collections.Counter()
    for e, w in q.items():
        for i in POR_ENT[e]:
            pts[i] += w
    # bono: las frases con más entidades de la pregunta y con una cita
    cand = []
    for i, sc in pts.items():
        cobertura = len([e for e in ENT_FRASE[i] if e in q]) / max(len(q), 1)
        cand.append((sc * (1 + cobertura) + (0.3 if SPAN.search(ALL_FRASES[i][2]) else 0), i))
    cand.sort(reverse=True)
    return [i for _, i in cand[:n]]


# ------------------------------------------------------------------ métricas
def texto_paginas(pags):
    return "\n".join(R.wiki.leer(p).a_texto() for p in pags)


def texto_frases(ids):
    return "\n".join(ALL_FRASES[i][2] for i in ids)


def medir(q, texto):
    ev = {e["span_id"] for e in q["evidencia"]}
    sp = set(SPAN.findall(texto))
    claves = q.get("respuesta_clave") or []
    if q.get("respuesta_por_paso"):
        claves = q["respuesta_por_paso"][-1]["respuesta_clave"]
    kc = sum(clave_presente(c, texto) for c in claves) / len(claves) if claves else 0.0
    return len(ev & sp) / len(ev), kc, len(texto) // 4


def main():
    preguntas = R.preguntas
    metodos = {}
    for q in preguntas:
        kw = R.palabras_clave(q["texto"])
        tc = tfidf_paginas(kw)
        bu = R.por_busqueda(kw)
        pp = ppr_paginas(q["texto"])
        res = {
            "busqueda p@5": texto_paginas(bu[:5]),
            "texto p@5": texto_paginas(tc[:5]),
            "PPR entidades p@5": texto_paginas(pp[:5]) if pp else "",
            "texto+PPR (RRF) p@5": texto_paginas(rrf(tc, pp)[:5]),
            "texto+PPR+búsq. (RRF) p@5": texto_paginas(rrf(tc, pp, bu)[:5]),
            "frases texto f@12": texto_frases(tfidf_frases(kw, 12)),
            "frases texto f@25": texto_frases(tfidf_frases(kw, 25)),
            "hechos entidades f@12": texto_frases(hechos_por_entidades(q["texto"], 12)),
            "hechos entidades f@25": texto_frases(hechos_por_entidades(q["texto"], 25)),
        }
        for k, t in res.items():
            metodos.setdefault(k, []).append((q["tipo"],) + medir(q, t))
    print(f"n={len(preguntas)} | páginas={NP} frases={NF} entidades={len(VOCAB)}")
    print(
        f"{'método':<30}{'frag':>7}{'claves':>8}{'todas':>7}{'T2 fr.':>8}{'T3 fr.':>8}{'T3 cl.':>8}{'tokens':>8}"
    )
    for k, v in metodos.items():

        def m(tipo, i):
            x = [r[i] for r in v if tipo is None or r[0] == tipo]
            return sum(x) / len(x) if x else float("nan")

        todas = sum(r[2] == 1.0 for r in v) / len(v)
        print(
            f"{k:<30}{m(None, 1):>7.2f}{m(None, 2):>8.2f}{todas:>7.2f}{m('T2', 1):>8.2f}{m('T3', 1):>8.2f}{m('T3', 2):>8.2f}{m(None, 3):>8.0f}"
        )


if __name__ == "__main__":
    main()
