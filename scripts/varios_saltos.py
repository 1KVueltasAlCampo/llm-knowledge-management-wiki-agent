"""Preguntas de varios saltos: el banco partido por cuántos papers exige cada pregunta.

No cambia ninguna pregunta ni llama a ningún modelo: reparte los resultados ya guardados
del paso 100.
Una pregunta es de **varios saltos** si su respuesta exige combinar dos o más papers
(``fuentes_requeridas``), y **encadenada** si alguno de esos papers cita a otro de ellos
(``referencias_en_corpus`` del manifiesto): el segundo paper se alcanza siguiendo una cita.
Uso:  python scripts/varios_saltos.py
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from wikillm.eval.estadistica import bootstrap_diferencia, mcnemar_exacto

PASO = 100
SALIDA = Path("results/varios-saltos")
BANCO = Path("data/preguntas/banco_100.jsonl")
MANIFEST = Path("data/corpus100/manifest.jsonl")
# nombre -> (corrida, sistema, filtro opcional por k no hace falta: cada corrida trae uno solo)
SISTEMAS = {
    "RAG k=5": ("ampliado-fases-1", "rag"),
    "RAG k=10": ("ampliado-rag-k10", "rag"),
    "RAG k=15": ("ampliado-rag-k15", "rag"),
    "RAG k=20": ("ampliado-rag-k20", "rag"),
    "Wiki 8 acc.": ("ampliado-fases-1", "wiki"),
    "Wiki 4 acc.": ("ampliado-wiki-tope4", "wiki"),
}


def leer_jsonl(ruta: Path) -> list[dict[str, Any]]:
    return [json.loads(x) for x in ruta.read_text("utf-8").splitlines() if x.strip()]


def encadenada(fuentes: list[str], referencias: dict[str, set[str]]) -> bool:
    return any(y in referencias.get(x, set()) for x in fuentes for y in fuentes if x != y)


def grupos(banco: list[dict[str, Any]], referencias: dict[str, set[str]]) -> dict[str, set[str]]:
    resp = [q for q in banco if q["fuentes_requeridas"]]
    multi = [q for q in resp if len(q["fuentes_requeridas"]) >= 2]
    return {
        "Un solo paper": {q["id"] for q in resp if len(q["fuentes_requeridas"]) == 1},
        "Varios papers": {q["id"] for q in multi},
        "  encadenados por citas": {
            q["id"] for q in multi if encadenada(q["fuentes_requeridas"], referencias)
        },
        "  sin cita entre ellos": {
            q["id"] for q in multi if not encadenada(q["fuentes_requeridas"], referencias)
        },
        "  T2 (combinar)": {q["id"] for q in multi if q["tipo"] == "T2"},
        "  T3 (comparar)": {q["id"] for q in multi if q["tipo"] == "T3"},
        "  T4 (actualizar)": {q["id"] for q in multi if q["tipo"] == "T4"},
    }


def cargar(corrida: str, sistema: str) -> dict[str, dict[str, Any]]:
    filas = leer_jsonl(Path("results") / corrida / "evaluados.jsonl")
    return {
        e["question_id"]: e for e in filas if e["system"] == sistema and e["ingest_step"] == PASO
    }


def fuentes_citadas(e: dict[str, Any]) -> set[str]:
    return {c.split("#", 1)[0] for c in e.get("citations", [])}


def main() -> None:
    banco = leer_jsonl(BANCO)
    por_id = {q["id"]: q for q in banco}
    referencias = {m["arxiv_id"]: set(m["referencias_en_corpus"]) for m in leer_jsonl(MANIFEST)}
    partes = grupos(banco, referencias)
    datos = {nombre: cargar(*origen) for nombre, origen in SISTEMAS.items()}

    resultado: dict[str, Any] = {"paso": PASO, "grupos": {}}
    print(f"{'Grupo':<26}{'n':>4} " + "".join(f"{s:>13}" for s in SISTEMAS))
    for nombre, ids in partes.items():
        fila: dict[str, Any] = {"n": len(ids), "cobertura": {}, "fuentes_completas": {}}
        celdas = []
        for sistema, evaluados in datos.items():
            correctas = sum(evaluados[q]["veredicto"] == "correcta" for q in ids)
            fila["cobertura"][sistema] = round(correctas / len(ids), 3) if ids else None
            fila.setdefault("correctas", {})[sistema] = correctas
            celdas.append(f"{correctas / len(ids):>13.2f}" if ids else f"{'-':>13}")
            citadas = [
                set(por_id[q]["fuentes_requeridas"]) <= fuentes_citadas(evaluados[q]) for q in ids
            ]
            fila["fuentes_completas"][sistema] = round(sum(citadas) / len(ids), 3) if ids else None
        resultado["grupos"][nombre.strip()] = fila
        print(f"{nombre:<26}{len(ids):>4} " + "".join(celdas))

    print("\nCita todos los papers que exige la pregunta (fracción de las preguntas del grupo)")
    for nombre in ("Un solo paper", "Varios papers", "  encadenados por citas"):
        fila = resultado["grupos"][nombre.strip()]
        print(
            f"{nombre:<26}{fila['n']:>4} "
            + "".join(f"{fila['fuentes_completas'][s]:>13.2f}" for s in SISTEMAS)
        )

    print("\nWiki (8 acciones) frente a cada RAG, en las preguntas de varios papers")
    comparaciones = []
    ids = sorted(partes["Varios papers"])
    for rag in ("RAG k=5", "RAG k=10", "RAG k=15", "RAG k=20"):
        r = [int(datos[rag][q]["veredicto"] == "correcta") for q in ids]
        w = [int(datos["Wiki 8 acc."][q]["veredicto"] == "correcta") for q in ids]
        solo_rag = sum(1 for a, b in zip(r, w, strict=True) if a and not b)
        solo_wiki = sum(1 for a, b in zip(r, w, strict=True) if b and not a)
        inf, sup = bootstrap_diferencia(r, w)
        fila = {
            "rag": rag,
            "n": len(ids),
            "diferencia": round((sum(w) - sum(r)) / len(ids), 3),
            "ic95": [round(inf, 3), round(sup, 3)],
            "solo_rag": solo_rag,
            "solo_wiki": solo_wiki,
            "p_mcnemar": round(mcnemar_exacto(solo_rag, solo_wiki), 4),
        }
        comparaciones.append(fila)
        print(
            f"  frente a {rag}: {fila['diferencia']:+.2f} [{inf:+.2f}, {sup:+.2f}] "
            f"solo RAG {solo_rag}, solo wiki {solo_wiki}, p = {fila['p_mcnemar']:.3f}"
        )
    resultado["wiki_frente_a_rag_varios_papers"] = comparaciones

    SALIDA.mkdir(parents=True, exist_ok=True)
    (SALIDA / "resumen.json").write_text(
        json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
