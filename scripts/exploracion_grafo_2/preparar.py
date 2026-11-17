"""Copia el wiki (solo lectura) y añade una página-stub por paper con [[enlaces]] a las
páginas que lo usan como fuente y a los papers que cita dentro del corpus. También fija las
15 preguntas por una regla decidida antes de ver resultados."""

import json
import re
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
WIKI = REPO / "data/wiki/construccion-1/pages"
OUT = Path(sys.argv[1])


def fuentes(texto: str) -> list[str]:
    m = re.search(r"^fuentes:\n((?:- .*\n)+)", texto, re.M)
    return re.findall(r"'?([\d.]+)'?", m.group(1)) if m else []


def main() -> None:
    for sub in ("con_papers/pages", "solo_wiki/pages"):
        d = OUT / sub
        if d.exists():
            shutil.rmtree(d)
        shutil.copytree(WIKI, d)
    paginas = {p.stem: fuentes(p.read_text(encoding="utf-8")) for p in WIKI.glob("*.md")}
    usa: dict[str, list[str]] = {}
    for pag, fs in paginas.items():
        for f in fs:
            usa.setdefault(f, []).append(pag)
    man = [json.loads(x) for x in (REPO / "data/corpus100/manifest.jsonl").open(encoding="utf-8")]
    for m in man:
        a = m["arxiv_id"]
        lineas = [f"# paper {a}", "", f"Title: {m['titulo']}", ""]
        lineas += [f"Used by [[{p}]]" for p in usa.get(a, [])]
        lineas += [f"Cites [[paper-{c.replace('.', '-')}]]" for c in m["referencias_en_corpus"]]
        dest = OUT / "con_papers/pages" / f"paper-{a.replace('.', '-')}.md"
        dest.write_text("\n".join(lineas) + "\n", encoding="utf-8")

    ruta = REPO / "data/preguntas/banco_100.jsonl"
    banco = [json.loads(x) for x in ruta.open(encoding="utf-8")]
    banco.sort(key=lambda q: q["id"])
    multi = [q for q in banco if q["tipo"] != "T5" and len(q["fuentes_requeridas"]) >= 2][:12]
    t1 = [q for q in banco if q["tipo"] == "T1"][:3]
    sel = multi + t1
    (OUT / "preguntas.json").write_text(json.dumps(sel, ensure_ascii=False), encoding="utf-8")
    print(len(sel), [q["id"] for q in sel])


if __name__ == "__main__":
    main()
