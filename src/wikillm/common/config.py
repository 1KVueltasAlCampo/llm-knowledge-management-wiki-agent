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
    temperature: float
    max_retries: int
    timeout_seconds: float
    price_input_cache_miss: float
    price_input_cache_hit: float
    price_output: float
    max_usd_per_run: float
    embedding_model: str
    embedding_device: str


def load_settings() -> Settings:
    """Lee el .env (si existe) y devuelve la configuración. La clave nunca se imprime."""
    load_dotenv()
    env = os.environ.get
    return Settings(
        api_key=env("DEEPSEEK_API_KEY", ""),
        base_url=env("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
        model=env("DEEPSEEK_MODEL", "deepseek-flash"),
        thinking=env("DEEPSEEK_THINKING", "disabled"),
        reasoning_effort=env("DEEPSEEK_REASONING_EFFORT", ""),
        temperature=float(env("MODEL_TEMPERATURE", "0")),
        max_retries=int(env("MODEL_MAX_RETRIES", "3")),
        timeout_seconds=float(env("MODEL_TIMEOUT_SECONDS", "120")),
        price_input_cache_miss=float(env("PRICE_INPUT_CACHE_MISS_USD_PER_M", "0.15")),
        price_input_cache_hit=float(env("PRICE_INPUT_CACHE_HIT_USD_PER_M", "0.003")),
        price_output=float(env("PRICE_OUTPUT_USD_PER_M", "0.60")),
        max_usd_per_run=float(env("MAX_USD_PER_RUN", "2.00")),
        embedding_model=env("EMBEDDING_MODEL", "") or "BAAI/bge-small-en-v1.5",
        embedding_device=env("EMBEDDING_DEVICE", "") or "cuda",
    )
