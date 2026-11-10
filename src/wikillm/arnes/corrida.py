"""Bucle del arnés: ingiere por pasos y hace cada pregunta a cada brazo, con reanudación.

En cada paso de evaluación, los brazos ingieren primero lo que falta y luego se hace cada
pregunta a todos los brazos, uno tras otro, antes de pasar a la siguiente pregunta: los dos ven
la misma hora, la misma carga de la API y la misma tarifa. Las líneas se escriben una a una, de
modo que una corrida cortada se reanuda saltando lo que ya consta.
"""

from __future__ import annotations

import json
import statistics
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from wikillm.arnes.registro import anexar_linea, claves_escritas, leer_lineas
from wikillm.common.responder import Brazo, a_linea_ingesta, a_linea_resultado

RESPUESTAS = "respuestas.jsonl"
INGESTAS = "ingestas.jsonl"
TRAZAS = "trazas.jsonl"
CORRIDA = "corrida.json"
PASOS_POR_DEFECTO = tuple(range(0, 51, 5))


class ErrorDeCorrida(RuntimeError):
    """La corrida no puede continuar de forma fiel: se detiene con un mensaje."""


@dataclass(frozen=True)
class Configuracion:
    corrida: str
    carpeta: Path  # results/<corrida>
    pasos: tuple[int, ...]
    orden: tuple[str, ...]  # arxiv_id en orden_ingesta
    preguntas: tuple[dict[str, Any], ...]
    modelo: str
    temperatura: float


def leer_orden(manifest: Path) -> tuple[str, ...]:
    lineas = manifest.read_text(encoding="utf-8").splitlines()
    filas = sorted(
        (json.loads(linea) for linea in lineas if linea.strip()),
        key=lambda fila: int(fila["orden_ingesta"]),
    )
    return tuple(fila["arxiv_id"] for fila in filas)


def _ahora_utc() -> datetime:
    return datetime.now(UTC)


def validar_pasos(pasos: Sequence[int], total_papers: int) -> tuple[int, ...]:
    ordenados = tuple(sorted(set(pasos)))
    fuera = [p for p in ordenados if p < 0 or p > total_papers]
    if not ordenados or fuera:
        raise ErrorDeCorrida(f"Pasos no válidos {fuera or list(pasos)}: usa de 0 a {total_papers}")
    return ordenados


def comprobar_estado(brazos: Sequence[Brazo], esperados: Sequence[str], paso: int) -> None:
    for brazo in brazos:
        ingeridos = getattr(brazo, "ingeridos", None)
        if ingeridos is not None and list(ingeridos) != list(esperados):
            raise ErrorDeCorrida(
                f"El brazo {brazo.nombre} tiene {len(ingeridos)} papers ingeridos y en el paso "
                f"{paso} deben ser exactamente los primeros {paso} del orden. Usa otra "
                "--corrida o borra el estado de esta (data/wiki/<corrida>, data/qdrant/<corrida>)."
            )


def ejecutar(
    brazos: Sequence[Brazo],
    config: Configuracion,
    *,
    ahora: Callable[[], datetime] = _ahora_utc,
    salida: Callable[[str], None] = print,
) -> None:
    carpeta = config.carpeta
    respuestas, ingestas, trazas = carpeta / RESPUESTAS, carpeta / INGESTAS, carpeta / TRAZAS
    respondidas = claves_escritas(respuestas, ("question_id", "system", "ingest_step"))
    ingeridas = claves_escritas(ingestas, ("system", "arxiv_id"))
    validar_pasos(config.pasos, len(config.orden))

    def marca() -> str:
        return ahora().strftime("%Y-%m-%dT%H:%M:%SZ")

    hechos = 0
    for paso in config.pasos:
        for posicion in range(hechos, paso):
            arxiv_id = config.orden[posicion]
            for brazo in brazos:
                resultado = brazo.ingerir(arxiv_id)
                if (brazo.nombre, arxiv_id) in ingeridas:
                    continue  # reanudación: el costo de esta ingesta ya consta
                anexar_linea(
                    ingestas,
                    a_linea_ingesta(
                        resultado,
                        run_id=config.corrida,
                        system=brazo.nombre,
                        ingest_step=posicion + 1,
                        arxiv_id=arxiv_id,
                        model=config.modelo,
                        timestamp=marca(),
                    ),
                )
                ingeridas.add((brazo.nombre, arxiv_id))
        hechos = paso

        pendientes = [
            (pregunta, brazo)
            for pregunta in config.preguntas
            for brazo in brazos
            if (pregunta["id"], brazo.nombre, paso) not in respondidas
        ]
        total = len(config.preguntas) * len(brazos)
        if not pendientes:
            salida(f"Paso {paso}: ya estaba completo ({total} respuestas)")
            continue
        comprobar_estado(brazos, config.orden[:paso], paso)
        salida(f"Paso {paso}: {len(pendientes)} respuestas por hacer de {total}")
        for pregunta, brazo in pendientes:
            resultado = brazo.responder(pregunta["texto"])
            anexar_linea(
                respuestas,
                a_linea_resultado(
                    resultado,
                    run_id=config.corrida,
                    question_id=pregunta["id"],
                    system=brazo.nombre,
                    ingest_step=paso,
                    model=config.modelo,
                    temperature=config.temperatura,
                    timestamp=marca(),
                ),
            )
            respondidas.add((pregunta["id"], brazo.nombre, paso))
            traza = getattr(brazo, "traza", None)
            if callable(traza):
                anexar_linea(
                    trazas,
                    {
                        "run_id": config.corrida,
                        "question_id": pregunta["id"],
                        "system": brazo.nombre,
                        "ingest_step": paso,
                        **traza(),
                    },
                )


def resumir(carpeta: Path) -> list[dict[str, Any]]:
    """Una fila por sistema con lo escrito en la corrida (suma todas las reanudaciones)."""
    respuestas = leer_lineas(carpeta / RESPUESTAS)
    ingestas = leer_lineas(carpeta / INGESTAS)
    sistemas = sorted({f["system"] for f in respuestas} | {f["system"] for f in ingestas})
    filas = []
    for sistema in sistemas:
        r = [f for f in respuestas if f["system"] == sistema]
        i = [f for f in ingestas if f["system"] == sistema]
        filas.append(
            {
                "sistema": sistema,
                "respuestas": len(r),
                "abstenciones": sum(1 for f in r if f["abstained"]),
                "usd_ingesta": sum(f["cost_usd"] for f in i),
                "usd_preguntas": sum(f["cost_usd"] for f in r),
                "contexto_mediano": statistics.median(f["context_tokens"] for f in r) if r else 0,
                "seg_ingesta": sum(f["latency_s"] for f in i),
                "seg_respuestas": sum(f["latency_s"] for f in r),
            }
        )
    return filas


def formatear_resumen(filas: list[dict[str, Any]], corrida: str) -> list[str]:
    lineas = ["", f"Resumen de {corrida}:"]
    for f in filas:
        lineas.append(
            f"  {f['sistema']}: {f['respuestas']} respuestas ({f['abstenciones']} abstenciones) · "
            f"ingesta {f['usd_ingesta']:.4f} USD y {f['seg_ingesta']:.0f} s · "
            f"preguntas {f['usd_preguntas']:.4f} USD y {f['seg_respuestas']:.0f} s · "
            f"contexto mediano {f['contexto_mediano']:.0f} tokens"
        )
    total = sum(f["usd_ingesta"] + f["usd_preguntas"] for f in filas)
    lineas.append(f"  Gasto total registrado: {total:.4f} USD")
    lineas.append(
        f"Métricas: uv run python -m wikillm.eval metricas --respuestas "
        f"results/{corrida}/{RESPUESTAS}"
    )
    return lineas
