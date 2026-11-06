"""Resultados sintéticos con el formato del contrato, para probar las métricas sin el arnés."""

from __future__ import annotations

import random
from typing import Any

from wikillm.eval.banco import esperado_en_paso


def generar(
    banco: list[dict[str, Any]],
    pasos: list[int],
    spans_por_paper: dict[str, list[str]],
    semilla: int = 0,
) -> list[dict[str, Any]]:
    """Simula un `wiki` que acierta más y lee menos contexto que un `rag`. Solo para pruebas."""
    azar = random.Random(semilla)
    perfiles = {"wiki": (0.75, 1500), "rag": (0.6, 4000)}
    filas = []
    for sistema, (acierto, contexto) in perfiles.items():
        for paso in pasos:
            for pregunta in banco:
                esperado = esperado_en_paso(pregunta, paso)
                acierta = azar.random() < acierto
                if not esperado.respondible:
                    respuesta, abstuvo = (
                        ("No consta en el corpus.", True) if acierta else ("42", False)
                    )
                elif acierta:
                    respuesta, abstuvo = " ".join(esperado.respuesta_clave) or "sí", False
                else:
                    respuesta, abstuvo = "Respuesta sin las cifras esperadas.", False
                fuentes = pregunta.get("fuentes_requeridas") or []
                citas = [spans_por_paper[f][0] for f in fuentes if spans_por_paper.get(f)]
                tokens = int(contexto * azar.uniform(0.7, 1.3))
                filas.append(
                    {
                        "run_id": "sintetico",
                        "question_id": pregunta["id"],
                        "system": sistema,
                        "ingest_step": paso,
                        "answer": respuesta,
                        "abstained": abstuvo,
                        "citations": citas if acierta else [],
                        "context_tokens": tokens,
                        "input_tokens": tokens + 200,
                        "output_tokens": 60,
                        "latency_s": round(azar.uniform(0.5, 3.0), 2),
                        "cost_usd": round((tokens + 200) * 0.15e-6 + 60 * 0.6e-6, 8),
                        "model": "sintetico",
                        "temperature": 0,
                        "timestamp": "2026-11-06T00:00:00Z",
                    }
                )
    return filas
