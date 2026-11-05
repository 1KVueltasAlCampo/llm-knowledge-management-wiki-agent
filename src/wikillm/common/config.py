"""Configuración del proyecto, leída de variables de entorno (archivo .env)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    api_key: str = field(repr=False)
    base_url: str
    model: str
    thinking: str
    reasoning_effort: str
    price_input_cache_miss: float
    price_input_cache_hit: float
    price_output: float
    max_usd_per_run: float


def load_settings() -> Settings:
    """Lee el .env (si existe) y devuelve la configuración. La clave nunca se imprime."""
    load_dotenv()
    return Settings(
        api_key=os.environ.get("DEEPSEEK_API_KEY", ""),
        base_url=os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
        model=os.environ.get("DEEPSEEK_MODEL", "deepseek-flash"),
        thinking=os.environ.get("DEEPSEEK_THINKING", "disabled"),
        reasoning_effort=os.environ.get("DEEPSEEK_REASONING_EFFORT", ""),
        price_input_cache_miss=float(os.environ.get("PRICE_INPUT_CACHE_MISS_USD_PER_M", "0.15")),
        price_input_cache_hit=float(os.environ.get("PRICE_INPUT_CACHE_HIT_USD_PER_M", "0.003")),
        price_output=float(os.environ.get("PRICE_OUTPUT_USD_PER_M", "0.60")),
        max_usd_per_run=float(os.environ.get("MAX_USD_PER_RUN", "2.00")),
    )
