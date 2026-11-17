"""Deriva del wiki entre cargas: qué se conserva de lo que ya estaba al ingerir más papers.

Lee, solo en lectura, las copias `paso-N` del repositorio git del wiki construido (no toca el
wiki) y mide, sin llamar a ningún modelo:

- crecimiento y reescritura por paso (páginas nuevas, modificadas, líneas que desaparecen);
- supervivencia literal de las líneas de un paso en los pasos siguientes;
- retención de cifras (decimales) atribuidas a un paper en las líneas que solo lo citan a él;
- retención de las respuestas del banco: ¿las claves que estaban en el wiki siguen ahí después?;
- las preguntas de actualización (T4): claves viejas y nuevas en cada paso.

Uso: python scripts/exploracion_deriva/deriva_wiki.py [--wiki data/wiki/construccion-1]
"""

from __future__ import annotations

import argparse
import io
import json
import re
import subprocess
import tarfile
from collections import defaultdict
from pathlib import Path

from wikillm.eval.correctitud import clave_presente

PATRON_SPAN = re.compile(r"(\d{4}\.\d{4,5})#s\d+\.p\d+")
PATRON_DECIMAL = re.compile(r"(?<![\w.])\d+\.\d+(?![\w])")
CORTES = (33, 66, 100)


def paginas_en(wiki: Path, paso: int) -> dict[str, str]:
    """Texto de cada página en la copia `paso-N` (git archive, sin modificar el directorio)."""
    salida = subprocess.run(
        ["git", "-C", str(wiki), "archive", "--format=tar", f"paso-{paso}", "pages"],
        capture_output=True,
        check=True,
    ).stdout
    textos: dict[str, str] = {}
    with tarfile.open(fileobj=io.BytesIO(salida)) as tar:
        for miembro in tar.getmembers():
            if miembro.isfile() and miembro.name.endswith(".md"):
                datos = tar.extractfile(miembro)
                assert datos is not None
                textos[Path(miembro.name).stem] = datos.read().decode("utf-8")
    return textos


def lineas(textos: dict[str, str]) -> set[str]:
    return {ln.strip() for t in textos.values() for ln in t.splitlines() if len(ln.strip()) > 40}


def pares_cifra_paper(textos: dict[str, str]) -> dict[str, set[str]]:
    """paper -> cifras decimales de las líneas que citan fragmentos de ese único paper."""
    pares: dict[str, set[str]] = defaultdict(set)
    for texto in textos.values():
        for ln in texto.splitlines():
            papers = set(PATRON_SPAN.findall(ln))
            if len(papers) == 1:
                (paper,) = papers
                pares[paper].update(PATRON_DECIMAL.findall(PATRON_SPAN.sub("", ln)))
    return pares


def claves_de(pregunta: dict) -> list[str]:
    return list(pregunta.get("respuesta_clave") or [])


def main() -> None:
    analizador = argparse.ArgumentParser(description=__doc__)
    analizador.add_argument("--wiki", type=Path, default=Path("data/wiki/construccion-1"))
    analizador.add_argument("--manifest", type=Path, default=Path("data/corpus100/manifest.jsonl"))
    analizador.add_argument("--banco", type=Path, default=Path("data/preguntas/banco_100.jsonl"))
    analizador.add_argument("--salida", type=Path, default=Path("results/herramientas/deriva"))
    args = analizador.parse_args()

    manifest = [json.loads(x) for x in args.manifest.read_text("utf-8").splitlines() if x.strip()]
    paso_de = {m["arxiv_id"]: m["orden_ingesta"] for m in manifest}
    banco = [json.loads(x) for x in args.banco.read_text("utf-8").splitlines() if x.strip()]

    todas = {p: paginas_en(args.wiki, p) for p in range(1, 101)}
    resumen: dict[str, object] = {}

    # --- crecimiento y reescritura por paso
    filas = []
    for p in range(2, 101):
        antes, ahora = todas[p - 1], todas[p]
        ln_antes, ln_ahora = lineas(antes), lineas(ahora)
        modificadas = sum(1 for s, t in ahora.items() if s in antes and antes[s] != t)
        filas.append(
            {
                "paso": p,
                "paginas": len(ahora),
                "nuevas": sum(1 for s in ahora if s not in antes),
                "modificadas": modificadas,
                "lineas_perdidas": len(ln_antes - ln_ahora) / max(len(ln_antes), 1),
            }
        )
    resumen["por_paso"] = filas
    print("== Crecimiento y reescritura (medias por paso)")
    for nombre, (a, b) in {"1-33": (2, 33), "34-66": (34, 66), "67-100": (67, 100)}.items():
        f = [x for x in filas if a <= x["paso"] <= b]
        print(
            f"  pasos {nombre:<7} páginas al final={f[-1]['paginas']:>4} "
            f"nuevas/paso={sum(x['nuevas'] for x in f) / len(f):.1f} "
            f"modificadas/paso={sum(x['modificadas'] for x in f) / len(f):.1f} "
            f"líneas que desaparecen/paso="
            f"{100 * sum(x['lineas_perdidas'] for x in f) / len(f):.1f} %"
        )

    # --- supervivencia literal de líneas
    print("\n== Supervivencia literal de las líneas de un paso en pasos posteriores")
    supervivencia = {}
    for a, b in ((33, 66), (33, 100), (66, 100)):
        la, lb = lineas(todas[a]), lineas(todas[b])
        supervivencia[f"{a}->{b}"] = len(la & lb) / len(la)
        print(
            f"  paso {a} -> {b}: {100 * len(la & lb) / len(la):.1f} % de {len(la)} líneas idénticas"
        )
    resumen["supervivencia_lineas"] = supervivencia

    # --- retención de cifras por paper
    print(
        "\n== Retención de cifras decimales atribuidas a un paper (líneas con un solo paper citado)"
    )
    pares = {p: pares_cifra_paper(todas[p]) for p in CORTES}
    retencion = {}
    for grupo, (a, b) in {"papers 1-33": (1, 33), "papers 34-66": (34, 66)}.items():
        for corte in CORTES:
            if corte <= b:
                continue
            perdidas = total = 0
            for paper, k in paso_de.items():
                if not a <= k <= b:
                    continue
                # cifras del paper en el primer corte posterior a su ingesta
                base_corte = min(c for c in (33, 66) if c >= k)
                base = pares[base_corte].get(paper, set())
                total += len(base)
                perdidas += len(base - pares[corte].get(paper, set()))
            if total:
                retencion[f"{grupo} en corte {corte}"] = 1 - perdidas / total
                print(
                    f"  {grupo}: de {total} cifras vistas en su corte, se conservan "
                    f"{100 * (1 - perdidas / total):.1f} % en el paso {corte}"
                )
    resumen["retencion_cifras"] = retencion

    # --- retención de las respuestas del banco
    print("\n== Respuestas del banco (claves completas en el texto de todas las páginas)")
    textos = {p: "\n".join(todas[p].values()) for p in CORTES}
    respondibles = [
        q for q in banco if q["tipo"] != "T5" and claves_de(q) and q.get("ingesta_minima")
    ]
    detalle = {}
    for corte_base in (33, 66):
        grupo = [q for q in respondibles if q["ingesta_minima"] <= corte_base]
        presentes = [
            q for q in grupo if all(clave_presente(c, textos[corte_base]) for c in claves_de(q))
        ]
        print(
            f"  respondibles al paso {corte_base}: {len(grupo)}; con todas sus claves en el wiki: "
            f"{len(presentes)} ({100 * len(presentes) / len(grupo):.0f} %)"
        )
        for corte in CORTES:
            if corte <= corte_base:
                continue
            siguen = [
                q for q in presentes if all(clave_presente(c, textos[corte]) for c in claves_de(q))
            ]
            nuevas = [
                q
                for q in grupo
                if q not in presentes
                and all(clave_presente(c, textos[corte]) for c in claves_de(q))
            ]
            perdidas = [q["id"] for q in presentes if q not in siguen]
            print(
                f"    en el paso {corte}: siguen {len(siguen)}/{len(presentes)}; "
                f"se pierden {perdidas}; aparecen {len(nuevas)} que antes faltaban"
            )
            detalle[f"{corte_base}->{corte}"] = {
                "presentes": len(presentes),
                "siguen": len(siguen),
                "perdidas": perdidas,
                "aparecen": len(nuevas),
            }
    resumen["banco"] = detalle

    # --- actualizaciones (T4)
    print("\n== Preguntas de actualización: ¿qué clave hay en cada paso?")
    for q in banco:
        tramos = q.get("respuesta_por_paso") or []
        if not tramos:
            continue
        print(f"  {q['id']} ({q['texto'][:70]}...)")
        for corte in CORTES:
            vigente = claves_de(q)
            for tramo in tramos:
                if corte >= tramo["desde"]:
                    vigente = list(tramo["respuesta_clave"])
            viejas = [c for c in claves_de(q) if clave_presente(c, textos[corte])]
            nuevas = [
                c
                for tr in tramos
                for c in tr["respuesta_clave"]
                if clave_presente(c, textos[corte])
            ]
            print(
                f"    paso {corte}: vigente={vigente} | iniciales presentes={viejas} | "
                f"de tramos presentes={nuevas}"
            )

    args.salida.mkdir(parents=True, exist_ok=True)
    (args.salida / "deriva.json").write_text(
        json.dumps(resumen, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    print(f"\nDetalle en {args.salida / 'deriva.json'}")


if __name__ == "__main__":
    main()
