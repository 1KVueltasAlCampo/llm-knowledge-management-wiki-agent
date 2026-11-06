"""Correctitud, capa 1: comparación determinista de cifras y entidades.

Devuelve `correcta`, `incorrecta` o `indeterminada`. Solo las indeterminadas pasan al juez
(capa 2), lo que ahorra llamadas y deja la mayoría de veredictos sin LLM.
"""

from __future__ import annotations

import re
import unicodedata

from wikillm.eval.banco import Esperado

CORRECTA, INCORRECTA, INDETERMINADA = "correcta", "incorrecta", "indeterminada"
PATRON_NUMERO = re.compile(r"(?<![\w.,])[-−]?\d+(?:[.,]\d+)*(?:\s?%)?")
PATRON_MILES = re.compile(r"^\d{1,3}(?:,\d{3})+(?:\.\d+)?$")
PATRON_MILES_PUNTO = re.compile(r"^\d{1,3}(?:\.\d{3})+(?:,\d+)?$")
TOLERANCIA_RELATIVA = 1e-6


def normalizar_texto(texto: str) -> str:
    sin_tildes = "".join(
        c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c)
    )
    return re.sub(r"[\s\-_‐–—]+", " ", sin_tildes.casefold()).strip()


def _a_float(literal: str) -> float | None:
    literal = literal.replace("−", "-").replace(" ", "")
    signo = -1.0 if literal.startswith("-") else 1.0
    literal = literal.lstrip("-")
    if PATRON_MILES.match(literal):
        literal = literal.replace(",", "")
    elif PATRON_MILES_PUNTO.match(literal) and literal.count(".") > 1:
        literal = literal.replace(".", "").replace(",", ".")
    else:
        literal = literal.replace(",", ".")
    if literal.count(".") > 1:
        return None
    try:
        return signo * float(literal)
    except ValueError:
        return None


def extraer_numeros(texto: str) -> list[float]:
    """Números del texto. Un porcentaje aporta su valor y su fracción (71 % → 71 y 0,71)."""
    valores: list[float] = []
    for literal in PATRON_NUMERO.findall(texto):
        es_porcentaje = literal.rstrip().endswith("%")
        valor = _a_float(literal.rstrip("% "))
        if valor is None:
            continue
        valores.append(valor)
        if es_porcentaje:
            valores.append(valor / 100)
    return valores


def _es_numerica(clave: str) -> bool:
    return bool(re.fullmatch(r"\s*" + PATRON_NUMERO.pattern + r"\s*", clave))


def _coincide_numero(objetivo: float, valores: list[float]) -> bool:
    escala = max(abs(objetivo), 1e-12)
    return any(abs(v - objetivo) / escala <= TOLERANCIA_RELATIVA for v in valores)


def clave_presente(clave: str, respuesta: str) -> bool:
    if _es_numerica(clave):
        objetivos = extraer_numeros(clave)
        valores = extraer_numeros(respuesta)
        return bool(objetivos) and _coincide_numero(objetivos[0], valores)
    return normalizar_texto(clave) in normalizar_texto(respuesta)


def evaluar(esperado: Esperado, respuesta: str, abstuvo: bool) -> str:
    if not esperado.respondible:
        return CORRECTA if abstuvo else INCORRECTA  # responder aquí es alucinar
    if abstuvo:
        return INCORRECTA
    if not esperado.respuesta_clave:
        return INDETERMINADA
    if all(clave_presente(c, respuesta) for c in esperado.respuesta_clave):
        return CORRECTA
    return INDETERMINADA
