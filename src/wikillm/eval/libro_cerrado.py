"""Control de contaminación: el modelo que responde, sin contexto, frente al banco.

Si acierta preguntas sin leer el corpus, las sabe de memoria (el paper es anterior a su corte
o se filtró). Escribe resultados con el contrato del arnés (`system = "libro_cerrado"`,
`ingest_step` = último paso) para que `metricas` dé directamente la tasa de aciertos.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

SISTEMA = (
    "Answer the question from your own knowledge only. If you do not know the answer, reply "
    "exactly: I DON'T KNOW. Be brief and include the key number or name."
)
TOKENS_SALIDA = 120
NO_SE = "i don't know"


def estimar(banco: list[dict[str, Any]]) -> tuple[int, int]:
    entrada = sum(len(p["texto"]) // 4 + 60 for p in banco)
    return entrada, TOKENS_SALIDA * len(banco)


def correr(
    banco: list[dict[str, Any]], cliente: Any, modelo: str, paso: int, run_id: str
) -> list[dict[str, Any]]:
    filas = []
    for pregunta in banco:
        if pregunta["tipo"] == "T5":
            continue
        mensajes = [
            {"role": "system", "content": SISTEMA},
            {"role": "user", "content": pregunta["texto"]},
        ]
        r = cliente.generar(
            mensajes, etiqueta=f"cerrado:{pregunta['id']}", max_tokens=TOKENS_SALIDA
        )
        filas.append(
            {
                "run_id": run_id,
                "question_id": pregunta["id"],
                "system": "libro_cerrado",
                "ingest_step": paso,
                "answer": r.texto,
                "abstained": NO_SE in r.texto.casefold().replace("’", "'"),
                "citations": [],
                "context_tokens": 0,
                "input_tokens": r.tokens_entrada_sin_cache + r.tokens_entrada_cache,
                "output_tokens": r.tokens_salida,
                "latency_s": r.segundos,
                "cost_usd": r.usd,
                "model": modelo,
                "temperature": 0,
                "timestamp": datetime.now(UTC).isoformat(),
            }
        )
    return filas
