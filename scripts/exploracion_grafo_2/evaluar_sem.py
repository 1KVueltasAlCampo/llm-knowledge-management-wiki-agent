"""Evaluación sin modelo sobre el subconjunto: texto, búsqueda, grafos y mejoras (a) y (b)."""

import collections
import json
import math
import re
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
REPO = Path(__file__).resolve().parents[2]
W, GRAPHIFY = Path(sys.argv[1]), sys.argv[2]
PAG = {p.stem: p.read_text(encoding="utf-8") for p in (W / "det/pages").glob("*.md")}
CONS = json.loads(
    (REPO / "results/herramientas/paso100-consultas/consultas_llm.json").read_text("utf-8")
)


def tok(s: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", s.lower())


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


def resumen(t: str) -> str:
    m = re.search(r"^(titulo|resumen):(.*)$", t, re.M)
    return " ".join(re.findall(r"^(?:titulo|resumen):(.*)$", t, re.M)) if m else ""


def indice(textos: dict[str, str]):
    tf = {p: collections.Counter(tok(x)) for p, x in textos.items()}
    df = collections.Counter(t for c in tf.values() for t in c)

    def rank(q: str) -> list[str]:
        qt = set(tok(q))
        sc = {
            p: sum(c[t] / max(1, sum(c.values())) * math.log(len(tf) / df[t]) for t in qt if t in c)
            for p, c in tf.items()
        }
        return sorted(sc, key=lambda p: -sc[p])

    return rank


texto = indice(PAG)
busqueda = indice({p: resumen(t) for p, t in PAG.items()})


def gquery(q: str, carpeta: str) -> list[str]:
    r = subprocess.run(
        [GRAPHIFY, "query", q, "--graph", "graphify-out/graph.json", "--budget", "30000"],
        cwd=W / carpeta,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    orden: list[str] = []
    for m in re.finditer(r"src=pages/([^ \]]+)\.md", r.stdout):
        if m.group(1) not in orden:
            orden.append(m.group(1))
    return orden


G = json.loads((W / "sem/graphify-out/graph.json").read_text(encoding="utf-8"))
PAGINA = {}
POR_ETIQUETA = collections.defaultdict(set)
for n in G["nodes"]:
    m = re.match(r"^pages/(.+)\.md$", (n.get("source_file") or "").replace("\\", "/"))
    if m:
        PAGINA[n["id"]] = m.group(1)
        POR_ETIQUETA[norm(n["label"])].add(m.group(1))
VECINOS = collections.defaultdict(set)
RELACIONES = collections.Counter()
for e in G.get("links") or G["edges"]:
    RELACIONES[e["relation"]] += 1
    if e["relation"] in ("conceptually_related_to", "references"):
        VECINOS[e["source"]].add(e["target"])
        VECINOS[e["target"]].add(e["source"])


def unificado(entidades: list[str]) -> list[str]:
    """(a) Etiquetas normalizadas iguales = un solo nodo; páginas puntuadas por IDF de entidad."""
    pts: collections.Counter = collections.Counter()
    for e in entidades:
        ne = norm(e)
        if len(ne) < 3:
            continue
        pags = set()
        for et, ps in POR_ETIQUETA.items():
            if et == ne or (len(ne) >= 4 and ne in et):
                pags |= ps
        for p in pags:
            pts[p] += math.log(1 + len(PAG) / len(pags))
    return [p for p, _ in pts.most_common()]


def rrf(*listas: list[str]) -> list[str]:
    pts: collections.Counter = collections.Counter()
    for lista in listas:
        for r, x in enumerate(lista):
            pts[x] += 1 / (61 + r)
    return [x for x, _ in pts.most_common()]


def expandir(q: str) -> list[str]:
    """(b) 3 páginas de texto + vecinas por aristas semánticas, ordenadas por texto."""
    rank = texto(q)
    sem = rank[:3]
    cand = (
        {PAGINA.get(v) for nid, p in PAGINA.items() if p in sem for v in VECINOS[nid]}
        - set(sem)
        - {None}
    )
    return sem + sorted(cand, key=rank.index)[:2]


def medir(pags: list[str], q: dict, k: int) -> tuple[float, float, int]:
    t = "".join(PAG.get(p, "") for p in pags[:k])
    sp = [e["span_id"] for e in q["evidencia"]]
    cl = q["respuesta_clave"]
    return (
        sum(s in t for s in sp) / len(sp),
        sum(c.lower() in t.lower() for c in cl) / len(cl),
        len(t) // 4,
    )


banco = [json.loads(x) for x in (REPO / "data/preguntas/banco_100.jsonl").open(encoding="utf-8")]
todo = "".join(PAG.values())
qs = [
    q
    for q in banco
    if q["tipo"] != "T5" and q["id"] in CONS and all(e["span_id"] in todo for e in q["evidencia"])
]
res = collections.defaultdict(list)
for q in qs:
    c = CONS[q["id"]]
    consulta = " ".join(c["entities"] + c["keywords"])
    tx = texto(consulta)
    brazos = {
        "búsqueda (resúmenes)": busqueda(consulta),
        "texto completo": tx,
        "grafo determinista (query)": gquery(consulta, "det"),
        "grafo semántico (query)": gquery(consulta, "sem"),
        "(a) semántico unificado": unificado(c["entities"]),
        "(a) + texto (RRF)": rrf(unificado(c["entities"]), tx),
        "(b) texto 3 + vecinos sem.": expandir(consulta),
    }
    for b, pags in brazos.items():
        res[b].append((q["id"], medir(pags, q, 3), medir(pags, q, 5)))
print(f"n = {len(qs)} preguntas; tipos {collections.Counter(q['tipo'] for q in qs)}")
print(f"nodos {len(G['nodes'])}, páginas con nodos {len(set(PAGINA.values()))}/{len(PAG)}")
print(f"relaciones {RELACIONES.most_common(6)}")
print(
    f"etiquetas distintas {len(POR_ETIQUETA)}; en 2+ páginas "
    f"{sum(len(v) > 1 for v in POR_ETIQUETA.values())}"
)
print(f"{'método':<30}{'frag@3':>7}{'clav@3':>7}{'frag@5':>7}{'clav@5':>7}{'tok@5':>7}")
for b, v in res.items():
    n = len(v)
    print(
        f"{b:<30}{sum(x[1][0] for x in v) / n:>7.2f}{sum(x[1][1] for x in v) / n:>7.2f}"
        f"{sum(x[2][0] for x in v) / n:>7.2f}{sum(x[2][1] for x in v) / n:>7.2f}"
        f"{sum(x[2][2] for x in v) // n:>7}"
    )
tx5 = {i: m5[0] for i, _, m5 in res["texto completo"]}
for b in res:
    d = [m5[0] - tx5[i] for i, _, m5 in res[b]]
    print(f"{b:<30} gana {sum(x > 0 for x in d)} pierde {sum(x < 0 for x in d)} (frag@5 vs texto)")
(W / "resultados_sem.json").write_text(json.dumps(res, ensure_ascii=False), encoding="utf-8")
