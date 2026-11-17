"""Sensibilidad del RAG al número de fragmentos (k) frente al wiki de la corrida base.

Une las respuestas del RAG de cada corrida `--brazos rag --k K` con las del wiki de
`ampliado-fases-1`
(mismas preguntas y pasos) y calcula, con la comparación pareada del proyecto, si el wiki sigue
ganando. Uso:
  python scripts/sensibilidad_rag.py ampliado-fases-1:5 ampliado-rag-k10:10 ampliado-rag-k20:20
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from wikillm.eval.estadistica import comparar_pareado


def leer(corrida: str) -> list[dict]:
    ruta = Path("results") / corrida / "evaluados.jsonl"
    return [json.loads(x) for x in ruta.read_text("utf-8").splitlines() if x.strip()]


def main() -> None:
    corridas = [a.split(":") for a in sys.argv[1:]] or [
        ["ampliado-fases-1", "5"],
        ["ampliado-rag-k10", "10"],
        ["ampliado-rag-k20", "20"],
    ]
    wiki = [e for e in leer("ampliado-fases-1") if e["system"] == "wiki"]
    print(
        f"{'k':>3} {'paso':>5} {'RAG':>6} {'wiki':>6} {'dif.':>7} {'IC95':>17} "
        f"{'solo RAG':>9} {'solo wiki':>10} {'p':>7}"
    )
    for corrida, k in corridas:
        rag = [e for e in leer(corrida) if e["system"] == "rag"]
        for fila in comparar_pareado(rag + wiki):
            if fila["tipo"]:
                continue
            ic = f"[{fila['ic95_inf']:+.2f}, {fila['ic95_sup']:+.2f}]"
            print(
                f"{k:>3} {fila['ingest_step']:>5} {fila['cobertura_rag']:>6.2f} "
                f"{fila['cobertura_wiki']:>6.2f} {fila['diferencia']:>+7.2f} {ic:>17} "
                f"{fila['solo_rag']:>9} {fila['solo_wiki']:>10} {fila['p_mcnemar']:>7.3f}"
            )
    print("\nPor tipo en el paso 100 (RAG / wiki), abstención correcta (T5) y contexto medio")
    for corrida, k in corridas:
        rag = [e for e in leer(corrida) if e["system"] == "rag"]
        partes = []
        for fila in comparar_pareado(rag + wiki):
            if fila["tipo"] and fila["ingest_step"] == 100:
                partes.append(
                    f"{fila['tipo']} {fila['cobertura_rag']:.2f}/{fila['cobertura_wiki']:.2f}"
                )
        t5 = [e for e in rag if e["ingest_step"] == 100 and e["tipo"] == "T5"]
        abst = sum(e["veredicto"] == "correcta" for e in t5) / len(t5)
        ctx = sum(e["context_tokens"] for e in rag) / len(rag)
        print(f"  k={k:>2}: {'  '.join(partes)} | T5 {abst:.2f} | contexto {ctx:.0f} tokens")


if __name__ == "__main__":
    main()
