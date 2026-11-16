"""Comparación pareada: McNemar exacto, bootstrap con semilla y tabla por paso y tipo."""

from __future__ import annotations

from typing import Any

import pytest

from wikillm.eval.estadistica import bootstrap_diferencia, comparar_pareado, mcnemar_exacto


def test_mcnemar_exacto_todo_a_favor_de_un_brazo():
    assert mcnemar_exacto(0, 5) == pytest.approx(0.0625)
    assert mcnemar_exacto(5, 0) == pytest.approx(0.0625)


def test_mcnemar_empate_y_sin_discordantes_valen_uno():
    assert mcnemar_exacto(3, 3) == 1.0
    assert mcnemar_exacto(0, 0) == 1.0


def test_bootstrap_es_reproducible_y_contiene_la_diferencia_observada():
    rag = [1, 0, 0, 0, 1, 0, 0, 1, 0, 0]
    wiki = [1, 1, 1, 0, 1, 1, 1, 1, 0, 1]
    a = bootstrap_diferencia(rag, wiki, remuestreos=500, semilla=1)
    b = bootstrap_diferencia(rag, wiki, remuestreos=500, semilla=1)
    assert a == b
    inf, sup = a
    diferencia = sum(wiki) / 10 - sum(rag) / 10
    assert inf <= diferencia <= sup and inf > 0  # el wiki gana claramente


def _fila(q: str, sistema: str, paso: int, ok: bool, tipo="T1", respondible=True) -> dict[str, Any]:
    return {
        "question_id": q,
        "system": sistema,
        "ingest_step": paso,
        "tipo": tipo,
        "respondible": respondible,
        "veredicto": "correcta" if ok else "incorrecta",
    }


def _datos() -> list[dict[str, Any]]:
    filas = []
    # paso 5, 10 preguntas T1 respondibles: solo wiki acierta 5, solo RAG 1, ambos 4
    for i in range(10):
        filas.append(_fila(f"Q{i}", "rag", 5, i in (5, 6, 7, 8, 9)))
        filas.append(_fila(f"Q{i}", "wiki", 5, i in (0, 1, 2, 3, 4, 5, 6, 7, 8)))
    # una T5 no respondible: no entra
    filas.append(_fila("N1", "rag", 5, True, tipo="T5", respondible=False))
    filas.append(_fila("N1", "wiki", 5, True, tipo="T5", respondible=False))
    # una pregunta con respuesta solo de un brazo: se excluye de los pares
    filas.append(_fila("X1", "wiki", 5, True))
    return filas


def test_pares_solo_respondibles_con_ambos_brazos_y_discordantes_correctos():
    filas = comparar_pareado(_datos())
    paso5 = next(f for f in filas if f["ingest_step"] == 5 and f["tipo"] == "")
    assert paso5["n"] == 10
    assert paso5["solo_wiki"] == 5 and paso5["solo_rag"] == 1
    assert paso5["cobertura_rag"] == pytest.approx(0.5)
    assert paso5["cobertura_wiki"] == pytest.approx(0.9)
    assert paso5["diferencia"] == pytest.approx(0.4)
    assert paso5["p_mcnemar"] == pytest.approx(0.21875)  # 2 * P(X<=1), n=6


def test_hay_fila_por_tipo_y_por_paso():
    filas = comparar_pareado(_datos())
    claves = {(f["ingest_step"], f["tipo"]) for f in filas}
    assert (5, "") in claves and (5, "T1") in claves
    assert (5, "T5") not in claves  # sin preguntas respondibles
