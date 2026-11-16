"""Evaluación auxiliar: ítems ciegos para un segundo juez y acuerdo con el veredicto principal.

Decisión 0006. No llama a ningún modelo: `exportar` escribe los ítems y `importar` lee los
veredictos que el segundo juez dejó en `auxiliar/veredictos_claude.jsonl`.
"""

from __future__ import annotations

import json
import random
from collections import defaultdict
from pathlib import Path
from typing import Any

from wikillm.corpus.candidatos import escribir_jsonl
from wikillm.eval.acuerdo import kappa_cohen
from wikillm.eval.banco import esperado_en_paso
from wikillm.eval.correctitud import INDETERMINADA
from wikillm.eval.juez import VEREDICTOS

CARPETA = "auxiliar"
ITEMS = "items.jsonl"
CLAVES = "claves.jsonl"
VEREDICTOS_CLAUDE = "veredictos_claude.jsonl"


def _leer_jsonl(ruta: Path) -> list[dict[str, Any]]:
    return [
        json.loads(linea)
        for linea in ruta.read_text(encoding="utf-8").splitlines()
        if linea.strip()
    ]


def _clave(fila: dict[str, Any]) -> tuple[str, str, int]:
    return (fila["question_id"], fila["system"], int(fila["ingest_step"]))


def exportar(
    carpeta: Path, banco: list[dict[str, Any]], muestra: int = 40, semilla: int = 1
) -> int:
    """Escribe `items.jsonl` (ciego) y `claves.jsonl`; devuelve el número de ítems."""
    evaluados = sorted(_leer_jsonl(carpeta / "evaluados.jsonl"), key=_clave)
    por_id = {p["id"]: p for p in banco}
    indeterminadas = [e for e in evaluados if e["veredicto_capa1"] == INDETERMINADA]
    resto = [e for e in evaluados if e["respondible"] and e["veredicto_capa1"] != INDETERMINADA]
    azar = random.Random(semilla)
    elegidas = indeterminadas + azar.sample(resto, min(muestra, len(resto)))
    elegidas.sort(key=_clave)
    azar.shuffle(elegidas)

    items, claves = [], []
    for numero, e in enumerate(elegidas, start=1):
        pregunta = por_id[e["question_id"]]
        esperado = esperado_en_paso(pregunta, int(e["ingest_step"]))
        if esperado.respuesta_oraculo is None:
            continue
        item_id = f"i{numero:04d}"
        items.append(
            {
                "item_id": item_id,
                "question": pregunta["texto"],
                "reference_answer": esperado.respuesta_oraculo,
                "answer_to_grade": e["answer"],
            }
        )
        claves.append(
            {
                "item_id": item_id,
                **dict(zip(("question_id", "system", "ingest_step"), _clave(e), strict=True)),
            }
        )
    escribir_jsonl(carpeta / CARPETA / ITEMS, items)
    escribir_jsonl(carpeta / CARPETA / CLAVES, claves)
    return len(items)


def _leer_veredictos(ruta: Path) -> tuple[dict[str, str], dict[str, str]]:
    meta: dict[str, str] = {}
    veredictos: dict[str, str] = {}
    for fila in _leer_jsonl(ruta):
        if "meta" in fila:
            meta = {k: str(v) for k, v in fila["meta"].items()}
            continue
        veredicto = str(fila.get("veredicto", "")).strip().lower()
        if veredicto not in VEREDICTOS:
            raise ValueError(f"veredicto inválido {veredicto!r} en {fila.get('item_id')!r}")
        veredictos[str(fila["item_id"])] = veredicto
    return meta, veredictos


def _acuerdo(pares: list[tuple[str, str]]) -> dict[str, Any]:
    resultado = kappa_cohen([a for a, _ in pares], [b for _, b in pares])
    return {"n": resultado.n, "porcentaje": resultado.porcentaje, "kappa": resultado.kappa}


def _num(valor: float | None, formato: str) -> str:
    return "n/d" if valor is None else format(valor, formato)


def _markdown(resultado: dict[str, Any], meta: dict[str, str]) -> str:
    filas = [("Total", resultado["total"])]
    filas += [(f"Origen {k}", v) for k, v in sorted(resultado["por_origen"].items())]
    filas += [(f"Sistema {k}", v) for k, v in sorted(resultado["por_sistema"].items())]
    tabla = "\n".join(
        f"| {nombre} | {d['n']} | {_num(d['porcentaje'], '.1%')} | {_num(d['kappa'], '.3f')} |"
        for nombre, d in filas
    )
    return (
        "# Evaluación auxiliar: acuerdo con el veredicto principal\n\n"
        f"Segundo juez: {meta.get('modelo', 'modelo no declarado')} "
        f"({meta.get('fecha', 'fecha no declarada')}).\n\n"
        "Esta es una evaluación **auxiliar** (decisión 0006): no reemplaza el veredicto de las "
        "métricas principales ni el estado de ninguna pregunta, y su costo (cuota de suscripción) "
        "no está en `consumo.csv`. Los ítems se calificaron a ciegas.\n\n"
        "| Grupo | n | Acuerdo | Kappa |\n|---|---|---|---|\n"
        f"{tabla}\n"
    )


def importar(carpeta: Path) -> dict[str, Any]:
    """Calcula acuerdo y kappa y escribe `acuerdo.json` y `acuerdo.md`; falla sin escribir."""
    base = carpeta / CARPETA
    meta, veredictos = _leer_veredictos(base / VEREDICTOS_CLAUDE)
    claves = {c["item_id"]: c for c in _leer_jsonl(base / CLAVES)}
    desconocidos = sorted(set(veredictos) - set(claves))
    if desconocidos:
        raise ValueError(f"ítems desconocidos en los veredictos: {desconocidos}")
    principal = {_clave(e): e for e in _leer_jsonl(carpeta / "evaluados.jsonl")}

    todos: list[tuple[str, str]] = []
    por_origen: dict[str, list[tuple[str, str]]] = defaultdict(list)
    por_sistema: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for item_id, veredicto in sorted(veredictos.items()):
        evaluado = principal[_clave(claves[item_id])]
        par = (evaluado["veredicto"], veredicto)
        todos.append(par)
        por_origen[evaluado["origen_veredicto"]].append(par)
        por_sistema[evaluado["system"]].append(par)
    resultado = {
        "modelo": meta.get("modelo"),
        "fecha": meta.get("fecha"),
        "total": _acuerdo(todos),
        "por_origen": {k: _acuerdo(v) for k, v in sorted(por_origen.items())},
        "por_sistema": {k: _acuerdo(v) for k, v in sorted(por_sistema.items())},
    }
    (base / "acuerdo.json").write_text(
        json.dumps(resultado, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    (base / "acuerdo.md").write_text(_markdown(resultado, meta), encoding="utf-8")
    return resultado
