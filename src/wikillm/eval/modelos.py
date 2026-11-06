"""Clientes del redactor y del juez (decisión 0003), sobre `ClienteModelo`.

No se toca el camino de `deepseek-flash`: se reutiliza `ClienteModelo` con otros ajustes. Para
Gemini se usa su endpoint compatible con OpenAI y se quita `extra_body`, que lleva la opción
`thinking` propia de DeepSeek.
"""

from __future__ import annotations

import os
from dataclasses import replace
from pathlib import Path
from typing import Any

import openai
from dotenv import load_dotenv

from wikillm.common.config import Settings, load_settings
from wikillm.common.modelo import ClienteModelo, ErrorDeModelo

URL_GEMINI_OPENAI = "https://generativelanguage.googleapis.com/v1beta/openai/"
# Tarifas de gemini-3.8-flash, USD por millón, vigentes hasta el 31-dic-2026.
# Fuente: https://aistudio.google.com/docs/pricing (consultado el 6-nov-2026).
PRECIOS_JUEZ_POR_DEFECTO = (0.75, 0.75, 3.75)
# deepseek-v4-pro no tiene tarifa verificada. Cota superior: 4 veces las tarifas de Flash
# (decisión 0001 y .env.example: "3-4 veces más caro"; Flash verificado el 4-nov-2026).
FACTOR_PRO_SOBRE_FLASH = 4.0


class _SinExtraBody:
    """Envuelve un cliente OpenAI y descarta `extra_body` (Gemini no conoce `thinking`)."""

    def __init__(self, cliente: Any) -> None:
        self._cliente = cliente
        self.chat = self
        self.completions = self

    def create(self, **argumentos: Any) -> Any:
        argumentos.pop("extra_body", None)
        return self._cliente.chat.completions.create(**argumentos)


def _precio(nombre: str, por_defecto: float) -> float:
    valor = os.environ.get(nombre, "")
    return float(valor) if valor else por_defecto


def precios_redactor(base: Settings | None = None) -> tuple[float, float, float]:
    """(entrada sin caché, entrada con caché, salida) en USD por millón.

    Usa las tarifas de .env si existen; si no, la cota superior de 4 veces Flash.
    """
    load_dotenv()
    base = base or load_settings()
    return (
        _precio(
            "DRAFT_PRICE_INPUT_CACHE_MISS_USD_PER_M",
            base.price_input_cache_miss * FACTOR_PRO_SOBRE_FLASH,
        ),
        _precio(
            "DRAFT_PRICE_INPUT_CACHE_HIT_USD_PER_M",
            base.price_input_cache_hit * FACTOR_PRO_SOBRE_FLASH,
        ),
        _precio("DRAFT_PRICE_OUTPUT_USD_PER_M", base.price_output * FACTOR_PRO_SOBRE_FLASH),
    )


def crear_redactor(ruta_registro: Path | str, cliente: Any = None) -> ClienteModelo:
    """`deepseek-v4-pro` (o DRAFT_MODEL), con tarifas de .env o la cota superior."""
    load_dotenv()
    base = load_settings()
    entrada, cache, salida = precios_redactor(base)
    ajustes = replace(
        base,
        model=os.environ.get("DRAFT_MODEL", "deepseek-v4-pro"),
        price_input_cache_miss=entrada,
        price_input_cache_hit=cache,
        price_output=salida,
    )
    return ClienteModelo(ajustes, ruta_registro=ruta_registro, cliente=cliente)


def crear_juez(ruta_registro: Path | str, cliente: Any = None) -> ClienteModelo:
    """Gemini (JUDGE_MODEL, por defecto gemini-3.8-flash) con temperatura 0."""
    load_dotenv()
    base = load_settings()
    entrada, cache, salida = PRECIOS_JUEZ_POR_DEFECTO
    ajustes = replace(
        base,
        api_key=os.environ.get("GEMINI_API_KEY", ""),
        base_url=URL_GEMINI_OPENAI,
        model=os.environ.get("JUDGE_MODEL", "gemini-3.8-flash"),
        thinking="disabled",
        temperature=0.0,
        price_input_cache_miss=_precio("JUDGE_PRICE_INPUT_USD_PER_M", entrada),
        price_input_cache_hit=_precio("JUDGE_PRICE_INPUT_CACHE_HIT_USD_PER_M", cache),
        price_output=_precio("JUDGE_PRICE_OUTPUT_USD_PER_M", salida),
    )
    if cliente is None:
        if not ajustes.api_key:
            raise ErrorDeModelo("Falta GEMINI_API_KEY en el entorno (.env)")
        cliente = _SinExtraBody(
            openai.OpenAI(
                api_key=ajustes.api_key,
                base_url=ajustes.base_url,
                timeout=ajustes.timeout_seconds,
                max_retries=0,
            )
        )
    return ClienteModelo(ajustes, ruta_registro=ruta_registro, cliente=cliente)
