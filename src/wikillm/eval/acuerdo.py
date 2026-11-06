"""Acuerdo entre dos anotadores: porcentaje y kappa de Cohen."""

from __future__ import annotations

import csv
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Acuerdo:
    n: int
    porcentaje: float
    kappa: float | None


def kappa_cohen(a: Sequence[str], b: Sequence[str]) -> Acuerdo:
    if len(a) != len(b):
        raise ValueError("las dos listas de etiquetas deben tener el mismo largo")
    n = len(a)
    if n == 0:
        return Acuerdo(0, 0.0, None)
    observado = sum(x == y for x, y in zip(a, b, strict=True)) / n
    cuenta_a, cuenta_b = Counter(a), Counter(b)
    esperado = sum(cuenta_a[e] * cuenta_b[e] for e in set(a) | set(b)) / (n * n)
    kappa = None if esperado == 1 else (observado - esperado) / (1 - esperado)
    return Acuerdo(n, observado, kappa)


def acuerdo_de_hojas(hoja_a: Path, hoja_b: Path, columna: str) -> Acuerdo:
    """Compara dos hojas CSV por `question_id`; ignora filas sin etiqueta en alguna de ellas."""

    def leer(ruta: Path) -> dict[str, str]:
        with ruta.open(encoding="utf-8", newline="") as archivo:
            return {
                fila["question_id"]: fila[columna].strip()
                for fila in csv.DictReader(archivo)
                if fila.get(columna, "").strip()
            }

    etiquetas_a, etiquetas_b = leer(hoja_a), leer(hoja_b)
    comunes = sorted(set(etiquetas_a) & set(etiquetas_b))
    return kappa_cohen([etiquetas_a[i] for i in comunes], [etiquetas_b[i] for i in comunes])
