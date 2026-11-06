"""Plan, estimación de costo y ejecución de los borradores de un autor.

Nada se ejecuta sin una estimación previa: `planear` no llama a la API, `ejecutar` exige que la
estimación quede por debajo del tope o una confirmación explícita.
"""

from __future__ import annotations

import csv
import os
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from wikillm.eval.redaccion import Fuente, construir_mensajes, interpretar
from wikillm.ingest.gold import leer_gold

TOKENS_SALIDA_POR_PREGUNTA = 350
TOKENS_INSTRUCCIONES = 700
TOPE_CONFIRMACION_USD = 5.0


@dataclass
class Tarea:
    fuentes: list[str]
    pedidos: dict[str, int]
    tokens_entrada: int = 0
    tokens_salida: int = 0
    etiqueta: str = ""


@dataclass
class Plan:
    autor: str
    tareas: list[Tarea] = field(default_factory=list)

    @property
    def tokens_entrada(self) -> int:
        return sum(t.tokens_entrada for t in self.tareas)

    @property
    def tokens_salida(self) -> int:
        return sum(t.tokens_salida for t in self.tareas)

    def costo(self, precio_entrada: float, precio_salida: float) -> float:
        return (self.tokens_entrada * precio_entrada + self.tokens_salida * precio_salida) / 1e6


def planear(manifest: list[dict[str, Any]], autor: str, por_par: int = 1) -> Plan:
    """T1 por cada paper del autor; T2, T3 y T4 por cada par citado→citante.

    Un par pertenece al autor del paper que entra más tarde, porque ese fija `ingesta_minima`.
    """
    por_id = {f["arxiv_id"]: f for f in manifest}
    plan = Plan(autor)
    for fila in manifest:
        if fila["mitad"] != autor or not fila.get("en_gold"):
            continue
        plan.tareas.append(Tarea([fila["arxiv_id"]], {"T1": 2}, etiqueta=f"T1:{fila['arxiv_id']}"))
        for citado in fila.get("referencias_en_corpus") or []:
            anterior = por_id.get(citado)
            if anterior is None or not anterior.get("en_gold"):
                continue
            if anterior["orden_ingesta"] >= fila["orden_ingesta"]:
                continue
            plan.tareas.append(
                Tarea(
                    [citado, fila["arxiv_id"]],
                    {"T2": por_par, "T3": por_par, "T4": por_par},
                    etiqueta=f"par:{citado}>{fila['arxiv_id']}",
                )
            )
    for tarea in plan.tareas:
        tokens = sum(int(por_id[i].get("tokens") or 0) for i in tarea.fuentes)
        tarea.tokens_entrada = tokens + TOKENS_INSTRUCCIONES
        tarea.tokens_salida = TOKENS_SALIDA_POR_PREGUNTA * sum(tarea.pedidos.values())
    return plan


def precios_redactor() -> tuple[float, float] | None:
    entrada = os.environ.get("DRAFT_PRICE_INPUT_CACHE_MISS_USD_PER_M", "")
    salida = os.environ.get("DRAFT_PRICE_OUTPUT_USD_PER_M", "")
    if not entrada or not salida:
        return None
    return float(entrada), float(salida)


def ejecutar(
    plan: Plan,
    manifest: list[dict[str, Any]],
    carpeta_gold: Path,
    cliente: Any,
    redactor: str,
    avisar: Callable[[str], None] = print,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    por_id = {f["arxiv_id"]: f for f in manifest}
    preguntas: list[dict[str, Any]] = []
    citas: list[dict[str, Any]] = []
    descartes: list[str] = []
    for numero, tarea in enumerate(plan.tareas, start=1):
        fuentes = []
        for arxiv_id in tarea.fuentes:
            encabezado, cuerpo = leer_gold(carpeta_gold / f"{arxiv_id}.md")
            fuentes.append(
                Fuente(arxiv_id, por_id[arxiv_id]["orden_ingesta"], cuerpo, encabezado["version"])
            )
        mensajes = construir_mensajes(fuentes, tarea.pedidos)
        respuesta = cliente.generar(mensajes, etiqueta=f"borrador:{tarea.etiqueta}")
        nuevas, literales, rechazos = interpretar(
            respuesta.texto,
            set(tarea.pedidos),
            fuentes,
            plan.autor,
            redactor,
            prefijo_id=f"{plan.autor}{numero:03d}",
        )
        preguntas.extend(nuevas)
        citas.extend(literales)
        descartes.extend(rechazos)
        avisar(
            f"[{numero}/{len(plan.tareas)}] {tarea.etiqueta}: {len(nuevas)} borradores, "
            f"{len(rechazos)} descartes, {respuesta.usd:.4f} USD"
        )
    return preguntas, citas, descartes


COLUMNAS_HOJA = (
    "question_id",
    "tipo",
    "ingesta_minima",
    "pregunta",
    "respuesta_borrador",
    "respuesta_clave",
    "evidencia",
    "cita_literal",
    "decision",
    "respuesta_revisor",
    "notas",
)


def escribir_hoja(ruta: Path, preguntas: list[dict[str, Any]], citas: list[dict[str, Any]]) -> None:
    """Hoja de anotación local (contiene citas literales: no se versiona).

    `decision` la llena una persona: aceptar | corregir | descartar.
    """
    por_pregunta: dict[str, list[str]] = {}
    for cita in citas:
        por_pregunta.setdefault(cita["question_id"], []).append(
            f"[{cita['span_id']}] {cita['cita']}"
        )
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with ruta.open("w", encoding="utf-8", newline="") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=COLUMNAS_HOJA)
        escritor.writeheader()
        for p in preguntas:
            escritor.writerow(
                {
                    "question_id": p["id"],
                    "tipo": p["tipo"],
                    "ingesta_minima": p["ingesta_minima"],
                    "pregunta": p["texto"],
                    "respuesta_borrador": p["respuesta_oraculo"],
                    "respuesta_clave": " | ".join(p.get("respuesta_clave") or []),
                    "evidencia": " ".join(e["span_id"] for e in p["evidencia"]),
                    "cita_literal": "\n".join(por_pregunta.get(p["id"], [])),
                    "decision": "",
                    "respuesta_revisor": "",
                    "notas": "",
                }
            )
