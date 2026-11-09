"""Preguntas de ejemplo que ofrece el panel: cada una muestra algo distinto del experimento."""

from __future__ import annotations

from typing import Any

EJEMPLOS: tuple[dict[str, str], ...] = (
    {
        "pregunta": "What is the total number of sessions in the BeliefShift dataset?",
        "nota": "Su paper es el sexto en el orden de ingesta: antes de ingerirlo se abstienen.",
    },
    {
        "pregunta": "What does HippoRAG use Personalized PageRank for?",
        "nota": "La respuesta está en el primer paper del corpus.",
    },
    {
        "pregunta": (
            "What is the highest single-step passage Recall@5 on MuSiQue that the corpus reports "
            "for HippoRAG, leaving out combinations with iterative retrieval such as IRCoT?"
        ),
        "nota": "La cifra cambia al entrar un paper nuevo: pone a prueba las respuestas obsoletas.",
    },
)


def a_json() -> list[dict[str, Any]]:
    return [dict(e) for e in EJEMPLOS]
