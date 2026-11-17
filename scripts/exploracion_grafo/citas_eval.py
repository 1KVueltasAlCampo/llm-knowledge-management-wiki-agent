"""¿Las fuentes requeridas por cada pregunta están conectadas por citas entre papers del corpus?"""

import collections
import itertools
import json
import random
import sys

sys.stdout.reconfigure(encoding="utf-8")
man = [json.loads(l) for l in open("data/corpus100/manifest.jsonl", encoding="utf-8")]
ids = [m["arxiv_id"] for m in man]
fecha = {m["arxiv_id"]: m["fecha_publicacion"] for m in man}
cita = collections.defaultdict(set)  # a cita a b
for m in man:
    for r in m.get("referencias_en_corpus") or []:
        cita[m["arxiv_id"]].add(r)
aristas = {(a, b) for a, bs in cita.items() for b in bs}
print(
    "papers:",
    len(ids),
    "| aristas de cita dentro del corpus:",
    len(aristas),
    "| papers sin ninguna cita dentro:",
    sum(1 for i in ids if not cita[i] and not any(i in v for v in cita.values())),
)
no_dir = {frozenset(a) for a in aristas}
densidad = len(no_dir) / (len(ids) * (len(ids) - 1) / 2)
print(f"densidad (pares conectados / pares posibles): {densidad:.3f}")

banco = [json.loads(l) for l in open("data/preguntas/banco_100.jsonl", encoding="utf-8")]
print(
    f"\n{'tipo':<5}{'preguntas con ≥2 fuentes':>26}{'todas las fuentes conectadas':>31}{'pares conectados':>18}"
)
tot = collections.defaultdict(lambda: [0, 0, 0, 0])
for q in banco:
    f = [x for x in q.get("fuentes_requeridas", []) if x in fecha]
    if len(f) < 2:
        continue
    pares = list(itertools.combinations(f, 2))
    con = sum(frozenset(p) in no_dir for p in pares)
    # conectadas = el subgrafo de las fuentes es conexo
    comp = {x: x for x in f}

    def raiz(x):
        while comp[x] != x:
            x = comp[x]
        return x

    for a, b in pares:
        if frozenset((a, b)) in no_dir:
            comp[raiz(a)] = raiz(b)
    conexo = len({raiz(x) for x in f}) == 1
    t = tot[q["tipo"]]
    t[0] += 1
    t[1] += conexo
    t[2] += con
    t[3] += len(pares)
for tipo, (n, c, k, p) in sorted(tot.items()):
    print(f"{tipo:<5}{n:>26}{c:>31}{k:>12}/{p}")
n = sum(v[0] for v in tot.values())
c = sum(v[1] for v in tot.values())
k = sum(v[2] for v in tot.values())
p = sum(v[3] for v in tot.values())
print(f"{'todas':<5}{n:>26}{c:>31}{k:>12}/{p}  (aleatorio esperado: {densidad:.1%} de los pares)")

# ¿conectadas a distancia 2 (comparten un papel citado o citante)?
vec = collections.defaultdict(set)
for a, b in aristas:
    vec[a].add(b)
    vec[b].add(a)
d2 = tot2 = 0
for q in banco:
    f = [x for x in q.get("fuentes_requeridas", []) if x in fecha]
    for a, b in itertools.combinations(f, 2):
        tot2 += 1
        d2 += (b in vec[a]) or bool(vec[a] & vec[b])
print(f"pares de fuentes a distancia ≤2 en el grafo de citas: {d2}/{tot2} = {d2 / tot2:.2f}")
# línea base: pares aleatorios del corpus a distancia ≤2
rnd = random.Random(5)
bas = sum(
    1
    for _ in range(5000)
    if (lambda a, b: (b in vec[a]) or bool(vec[a] & vec[b]))(*rnd.sample(ids, 2))
)
print(f"pares aleatorios a distancia ≤2: {bas / 5000:.2f}")
