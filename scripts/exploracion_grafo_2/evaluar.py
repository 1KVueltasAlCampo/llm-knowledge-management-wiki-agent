"""Recuperación sin modelo: control TF-IDF frente a tres usos de graphify (sin gasto)."""

import json
import math
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

W = Path(sys.argv[1])
GRAPHIFY = Path(sys.argv[2])
K = 5
pag = {p.stem: p.read_text(encoding="utf-8") for p in (W / "solo_wiki/pages").glob("*.md")}
tok = lambda s: re.findall(r"[a-z0-9]+", s.lower())  # noqa: E731
df = Counter(t for t in pag for t in set(tok(pag[t])))
tf = {p: Counter(tok(x)) for p, x in pag.items()}


def tfidf(q: str) -> list[tuple[float, str]]:
    qt = set(tok(q))
    out = []
    for p, c in tf.items():
        n = sum(c.values())
        s = sum(c[t] / n * math.log(len(pag) / df[t]) for t in qt if t in c)
        out.append((s, p))
    return sorted(out, reverse=True)


def gquery(q: str, carpeta: str) -> list[str]:
    r = subprocess.run(
        [str(GRAPHIFY), "query", q, "--graph", "graphify-out/graph.json", "--budget", "30000"],
        cwd=W / carpeta,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    orden = []
    for m in re.finditer(r"src=pages/([^ \]]+)\.md", r.stdout):
        s = m.group(1)
        if not s.startswith("paper-") and s not in orden:
            orden.append(s)
    return orden


g = json.loads((W / "con_papers/graphify-out/graph.json").read_text(encoding="utf-8"))
lab = {n["id"]: n["label"].removesuffix(".md") for n in g["nodes"]}
vec: dict[str, set[str]] = {}
for e in g.get("links") or g["edges"]:
    a, b = lab.get(e["source"]), lab.get(e["target"])
    if a and b:
        vec.setdefault(a, set()).add(b)
        vec.setdefault(b, set()).add(a)


def hibrido(q: str) -> list[str]:
    """Semillas de texto (3) + expansión por papers: página → paper → página / paper citado."""
    rank = tfidf(q)
    score = {p: s for s, p in rank}
    sem = [p for _, p in rank[:3]]
    cand = set()
    for p in sem:
        for pp in vec.get(p, ()):
            if pp.startswith("paper-"):
                for x in vec.get(pp, ()):
                    if x.startswith("paper-"):
                        cand |= {y for y in vec.get(x, ()) if not y.startswith("paper-")}
                    else:
                        cand.add(x)
    cand -= set(sem)
    return sem + sorted(cand, key=lambda x: -score.get(x, 0))[: K - 3]


def medir(paginas: list[str], q: dict) -> tuple[float, int, int]:
    texto = "".join(pag.get(p, "") for p in paginas[:K])
    spans = [e["span_id"] for e in q["evidencia"]]
    hit = sum(s in texto for s in spans)
    return hit / len(spans), int(hit == len(spans)), len(texto) // 4


preg = json.loads((W / "preguntas.json").read_text(encoding="utf-8"))
brazos = {
    "B0 texto completo (control)": lambda q: [p for _, p in tfidf(q)][:K],
    "G1 graphify query (wiki)": lambda q: gquery(q, "solo_wiki"),
    "G2 graphify query (wiki+papers)": lambda q: gquery(q, "con_papers"),
    "G3 semillas texto + vecinos por paper": hibrido,
}
filas = []
for q in preg:
    fila = {"id": q["id"], "tipo": q["tipo"]}
    for b, f in brazos.items():
        fila[b] = medir(f(q["texto"]), q)
    filas.append(fila)
(W / "resultados.json").write_text(json.dumps(filas, ensure_ascii=False, indent=1), "utf-8")
for b in brazos:
    v = [f[b] for f in filas]
    print(
        f"{b}: fragmentos {sum(x[0] for x in v) / len(v):.2f} | todos {sum(x[1] for x in v)}/15"
        f" | tokens {sum(x[2] for x in v) // len(v)}"
    )
for f in filas:
    print(f["id"], " ".join(f"{f[b][0]:.2f}" for b in brazos))
