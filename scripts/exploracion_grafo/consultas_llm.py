"""El LLM (el mismo deepseek-flash) formula la consulta de búsqueda de cada pregunta: 1 llamada corta c/u."""

import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
from wikillm.common.config import load_settings  # noqa: E402
from wikillm.common.modelo import ClienteModelo  # noqa: E402
from wikillm.wiki.ingesta import extraer_json  # noqa: E402

S = Path(os.environ["S"])
SISTEMA = (
    "You help search a wiki of pages that summarize arXiv papers. Given a question, reply with exactly one "
    'JSON object: {"entities": [...], "keywords": [...], "queries": [...]}. "entities": the specific names '
    "of systems, datasets, benchmarks, models, metrics or numbers the question mentions or clearly implies, "
    'spelled as papers write them. "keywords": other important content words or short phrases. "queries": '
    "up to 3 short search queries (3 to 8 words each) that would find the pages needed to answer. Do not "
    "answer the question."
)


def una(q):
    modelo = ClienteModelo(load_settings(), ruta_registro=S / "consultas_llm_llamadas.jsonl")
    r = modelo.generar(
        [
            {"role": "system", "content": SISTEMA},
            {"role": "user", "content": f"Question: {q['texto']}"},
        ],
        etiqueta="consulta",
        max_tokens=300,
    )
    try:
        d = extraer_json(r.texto)
    except Exception:  # noqa: BLE001
        d = {"entities": [], "keywords": [], "queries": [q["texto"]]}
    return (
        q["id"],
        {k: [str(x) for x in d.get(k, [])] for k in ("entities", "keywords", "queries")},
        r.usd,
    )


if __name__ == "__main__":
    sys.path.insert(0, str(S))
    import recuperacion as R

    with ThreadPoolExecutor(4) as pool:
        res = list(pool.map(una, R.preguntas))
    json.dump(
        {i: d for i, d, _ in res},
        open(S / "consultas_llm.json", "w", encoding="utf-8"),
        ensure_ascii=False,
        indent=1,
    )
    print("preguntas:", len(res), "| costo USD:", round(sum(u for *_, u in res), 5))
    for i, d, _ in res[:5]:
        print(i, d)
