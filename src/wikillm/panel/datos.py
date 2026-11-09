"""Lectura de resultados ya guardados que muestra el panel: wiki, ingesta, comparación y piloto.

Solo lee archivos; no llama al modelo. Lo que devuelve es lo que las órdenes de consola dejan en
disco (`log.md`, `comparaciones.jsonl`, `results/piloto-1/`), de modo que la página muestra lo
mismo que se podría comprobar abriendo esos archivos.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from wikillm.arnes.comparar import DESCRIPCIONES, NOMBRES, Resolutor
from wikillm.arnes.registro import leer_lineas

PILOTO = "results/piloto-1"
EVIDENCIA = "results/demo/comparaciones.jsonl"
BANCO = "data/preguntas/banco.jsonl"
MANIFEST = "data/manifest_corpus.jsonl"
LARGO_CITA = 600
LARGO_RECUPERADO = 320
ENCABEZADO_DE_PASO = re.compile(r"^## Step (\d+): (\S+) — (.*)$")
CAMPO_DEL_REGISTRO = re.compile(
    r"^- (Created|Updated|Citations removed|Broken links|Uncited numeric lines): ?(.*)$"
)
CAMPOS_DE_LA_CORRIDA = (
    "corrida",
    "inicio",
    "commit",
    "modelo",
    "temperatura",
    "pasos",
    "valida_para_informe",
    "gasto_usd",
    "estimacion_usd",
)


def _json(ruta: Path) -> Any:
    try:
        return json.loads(ruta.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _recortar(texto: str, largo: int) -> str:
    plano = " ".join(texto.split())
    return plano if len(plano) <= largo else plano[: largo - 1].rstrip() + "…"


def _fragmento(resolutor: Resolutor, span_id: str, largo: int) -> str | None:
    texto = resolutor(span_id)
    return _recortar(texto, largo) if texto else None


def estado_del_wiki(raiz: Path, carpeta: str) -> dict[str, Any]:
    """Cuántos papers y páginas tiene un wiki, sin abrir su repositorio."""
    base = raiz / carpeta
    estado = _json(base / "estado.json") or {}
    ingeridos = [str(x) for x in estado.get("ingeridos", [])]
    paginas = base / "pages"
    return {
        "carpeta": carpeta,
        "existe": base.is_dir(),
        "ingeridos": len(ingeridos),
        "ids": ingeridos,
        "paginas": len(list(paginas.glob("*.md"))) if paginas.is_dir() else 0,
    }


def corpus(raiz: Path, ingeridos: list[str]) -> dict[str, Any]:
    """Cuántos papers tiene el corpus y cuál sigue en el orden de ingesta."""
    filas = sorted(leer_lineas(raiz / MANIFEST), key=lambda f: int(f.get("orden_ingesta", 0)))
    pendientes = [f for f in filas if f["arxiv_id"] not in ingeridos]
    siguiente = pendientes[0] if pendientes else None
    return {
        "total": len(filas),
        "siguiente": None
        if siguiente is None
        else {
            "paso": int(siguiente["orden_ingesta"]),
            "arxiv_id": siguiente["arxiv_id"],
            "titulo": siguiente.get("titulo", ""),
        },
    }


def _lista(valor: str) -> list[str]:
    return [x.strip() for x in valor.split(",") if x.strip() and x.strip() != "(none)"]


def _entero(valor: str) -> int:
    try:
        return int(valor)
    except ValueError:
        return 0


def ultima_ingesta(raiz: Path, carpeta: str) -> dict[str, Any] | None:
    """La última entrada del registro del wiki: paper, páginas tocadas y conteos de validación."""
    try:
        lineas = (raiz / carpeta / "log.md").read_text(encoding="utf-8").splitlines()
    except OSError:
        return None
    inicios = [i for i, linea in enumerate(lineas) if ENCABEZADO_DE_PASO.match(linea)]
    if not inicios:
        return None
    encabezado = ENCABEZADO_DE_PASO.match(lineas[inicios[-1]])
    assert encabezado is not None
    campos = {
        m.group(1): m.group(2)
        for linea in lineas[inicios[-1] + 1 :]
        if (m := CAMPO_DEL_REGISTRO.match(linea))
    }
    return {
        "paso": int(encabezado.group(1)),
        "arxiv_id": encabezado.group(2),
        "titulo": encabezado.group(3),
        "creadas": _lista(campos.get("Created", "")),
        "actualizadas": _lista(campos.get("Updated", "")),
        "citas_eliminadas": _entero(campos.get("Citations removed", "0")),
        "enlaces_rotos": _entero(campos.get("Broken links", "0")),
        "lineas_sin_cita": _entero(campos.get("Uncited numeric lines", "0")),
    }


def resultado_de_comparacion(raiz: Path, resolutor: Resolutor) -> dict[str, Any] | None:
    """La última comparación guardada, con el comienzo del fragmento de cada cita."""
    lineas = leer_lineas(raiz / EVIDENCIA)
    if not lineas:
        return None
    ultima = lineas[-1]
    sistemas = []
    for s in ultima.get("sistemas", []):
        citas = [str(c) for c in s.get("citas", [])]
        recuperados = s.get("recuperados")
        sistemas.append(
            {
                "sistema": s["sistema"],
                "nombre": NOMBRES.get(s["sistema"], s["sistema"]),
                "descripcion": DESCRIPCIONES.get(s["sistema"], ""),
                "respuesta": s["respuesta"],
                "abstuvo": bool(s["abstuvo"]),
                "citas": [
                    {"span_id": c, "texto": _fragmento(resolutor, c, LARGO_CITA)} for c in citas
                ],
                "llamadas": s["llamadas"],
                "tokens_entrada": s["tokens_entrada"],
                "tokens_contexto": s["tokens_contexto"],
                "tokens_salida": s["tokens_salida"],
                "segundos": s["segundos"],
                "usd": s["usd"],
                "traza": s.get("traza"),
                "recuperados": None
                if recuperados is None
                else [
                    {
                        "span_ids": r["span_ids"],
                        "distancia": r["distancia"],
                        "citado": bool(set(r["span_ids"]) & set(citas)),
                        "texto": _fragmento(resolutor, r["span_ids"][0], LARGO_RECUPERADO)
                        if r["span_ids"]
                        else None,
                    }
                    for r in recuperados
                ],
            }
        )
    return {
        "pregunta": ultima["pregunta"],
        "paso": ultima["paso"],
        "modelo": ultima["modelo"],
        "momento": ultima["timestamp"],
        "sistemas": sistemas,
    }


def leer_metricas(raiz: Path) -> dict[str, Any]:
    """Métricas por sistema y paso del piloto, y el veredicto de cada pregunta."""
    base = raiz / PILOTO
    corrida = _json(base / "corrida.json") or {}
    textos = {p["id"]: p.get("texto", "") for p in leer_lineas(raiz / BANCO)}
    preguntas = [
        {
            "id": e["question_id"],
            "texto": textos.get(e["question_id"], ""),
            "tipo": e.get("tipo"),
            "paso": e["ingest_step"],
            "sistema": e["system"],
            "respondible": e.get("respondible"),
            "veredicto": e.get("veredicto"),
            "abstuvo": e.get("abstained"),
            "obsoleta": e.get("obsoleta"),
            "respuesta": e.get("answer", ""),
            "citas": len(e.get("citations", [])),
            "costo_usd": e.get("cost_usd"),
            "segundos": round(float(e.get("latency_s", 0.0)), 2),
        }
        for e in leer_lineas(base / "evaluados.jsonl")
    ]
    return {
        "corrida": {k: corrida.get(k) for k in CAMPOS_DE_LA_CORRIDA}
        | {"preguntas": len((corrida.get("banco") or {}).get("preguntas", []))},
        "filas": _json(base / "metricas_por_paso.json") or [],
        "preguntas": preguntas,
    }
