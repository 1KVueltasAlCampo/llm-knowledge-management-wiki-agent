"""Regla fijada antes de ver resultados: preguntas T3 por id; para cada una, las páginas del wiki
que citan alguno de sus span_id de evidencia (orden alfabético), hasta 25 páginas; más 8
distractoras al azar del resto con semilla 20261117."""

import json
import random
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
WIKI = REPO / "data/wiki/construccion-1/pages"
OUT = Path(sys.argv[1])
N_T3, N_DIS, SEMILLA = 25, 8, 20261117


def main() -> None:
    pag = {p.stem: p.read_text(encoding="utf-8") for p in sorted(WIKI.glob("*.md"))}
    ruta = REPO / "data/preguntas/banco_100.jsonl"
    banco = [json.loads(x) for x in ruta.open(encoding="utf-8")]
    sel: list[str] = []
    for q in sorted((q for q in banco if q["tipo"] == "T3"), key=lambda q: q["id"]):
        for p, t in pag.items():
            if p not in sel and any(e["span_id"] in t for e in q["evidencia"]):
                sel.append(p)
    sel = sel[:N_T3]
    resto = [p for p in pag if p not in sel]
    dis = random.Random(SEMILLA).sample(resto, N_DIS)
    for sub in ("sem", "det"):
        d = OUT / sub / "pages"
        if d.parent.exists():
            shutil.rmtree(d.parent)
        d.mkdir(parents=True)
        for p in sel + dis:
            shutil.copy(WIKI / f"{p}.md", d)
    (OUT / "subconjunto.json").write_text(
        json.dumps({"t3": sel, "distractoras": dis}, indent=1), encoding="utf-8"
    )
    print(len(sel), len(dis), sum(len(pag[p]) for p in sel + dis) // 4, "tokens aprox.")


if __name__ == "__main__":
    main()
