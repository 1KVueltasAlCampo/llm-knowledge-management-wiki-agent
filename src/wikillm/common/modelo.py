"""Punto único de entrada para llamar al modelo del proyecto (DeepSeek V4.1 Flash).

Todo el código que necesite al modelo (RAG, wiki, juez) debe pasar por ClienteModelo, para que
las métricas, el registro y el tope de gasto sean los mismos en ambos sistemas.
"""

from __future__ import annotations

import hashlib
import json
import threading
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import openai

from wikillm.common.config import Settings, load_settings
from wikillm.common.costo import Tarifas, calcular_costo, es_hora_pico

RUTA_REGISTRO_POR_DEFECTO = Path("results/dev/llamadas.jsonl")
CODIGOS_TRANSITORIOS = {429, 500, 502, 503, 504}
MODOS_RAZONAMIENTO = {"enabled", "disabled"}


class TopeDeGastoError(RuntimeError):
    """Se alcanzó MAX_USD_PER_RUN: no se hacen más llamadas en esta corrida."""


class ErrorDeModelo(RuntimeError):
    """La llamada al modelo falló y no se pudo recuperar."""


@dataclass(frozen=True)
class Respuesta:
    texto: str
    tokens_entrada_sin_cache: int
    tokens_entrada_cache: int
    tokens_salida: int
    tokens_razonamiento: int
    segundos: float
    usd: float
    intentos: int


def _entero(objeto: Any, nombre: str) -> int:
    return int(getattr(objeto, nombre, 0) or 0)


class ClienteModelo:
    def __init__(
        self,
        ajustes: Settings | None = None,
        *,
        ruta_registro: Path | str = RUTA_REGISTRO_POR_DEFECTO,
        cliente: Any = None,
        dormir: Callable[[float], None] = time.sleep,
        ahora: Callable[[], datetime] | None = None,
    ) -> None:
        self._ajustes = ajustes or load_settings()
        if self._ajustes.thinking not in MODOS_RAZONAMIENTO:
            raise ValueError("DEEPSEEK_THINKING debe ser 'enabled' o 'disabled'")
        if cliente is None:
            if not self._ajustes.api_key:
                raise ErrorDeModelo("Falta DEEPSEEK_API_KEY en el entorno (.env)")
            cliente = openai.OpenAI(
                api_key=self._ajustes.api_key,
                base_url=self._ajustes.base_url,
                timeout=self._ajustes.timeout_seconds,
                max_retries=0,  # los reintentos los maneja este cliente
            )
        self._cliente = cliente
        self._ruta = Path(ruta_registro)
        self._dormir = dormir
        self._ahora = ahora or (lambda: datetime.now(UTC))
        self._tarifas = Tarifas(
            entrada_sin_cache=self._ajustes.price_input_cache_miss,
            entrada_con_cache=self._ajustes.price_input_cache_hit,
            salida=self._ajustes.price_output,
        )
        self._gasto = 0.0
        self._candado = threading.Lock()

    @property
    def gasto_acumulado(self) -> float:
        return self._gasto

    def generar(
        self,
        mensajes: Sequence[dict[str, str]],
        *,
        etiqueta: str = "",
        max_tokens: int | None = None,
    ) -> Respuesta:
        """Envía mensajes de chat al modelo y devuelve el texto con sus métricas."""
        with self._candado:
            if self._gasto >= self._ajustes.max_usd_per_run:
                raise TopeDeGastoError(
                    f"Tope de gasto alcanzado: {self._gasto:.4f} USD de "
                    f"{self._ajustes.max_usd_per_run:.2f} USD (MAX_USD_PER_RUN)"
                )
        argumentos = self._argumentos(mensajes, max_tokens)
        momento = self._ahora()
        intentos = 0
        while True:
            intentos += 1
            inicio = time.perf_counter()
            try:
                bruta = self._cliente.chat.completions.create(**argumentos)
            except Exception as error:
                if self._es_transitorio(error) and intentos <= self._ajustes.max_retries:
                    self._dormir(2 ** (intentos - 1))
                    continue
                descripcion = self._describir(error)
                self._escribir_registro(
                    {
                        **self._base_registro(momento, etiqueta, mensajes),
                        "resultado": "error",
                        "error": descripcion,
                        "intentos": intentos,
                    }
                )
                raise ErrorDeModelo(descripcion) from None
            segundos = time.perf_counter() - inicio
            break

        respuesta, texto = self._interpretar(bruta, momento, segundos, intentos)
        with self._candado:
            self._gasto += respuesta.usd
        self._escribir_registro(
            {
                **self._base_registro(momento, etiqueta, mensajes),
                "resultado": "ok",
                "intentos": intentos,
                "tokens_entrada_sin_cache": respuesta.tokens_entrada_sin_cache,
                "tokens_entrada_cache": respuesta.tokens_entrada_cache,
                "tokens_salida": respuesta.tokens_salida,
                "tokens_razonamiento": respuesta.tokens_razonamiento,
                "segundos": round(respuesta.segundos, 4),
                "usd": respuesta.usd,
                "hora_pico": es_hora_pico(momento),
                "respuesta": texto,
            }
        )
        return respuesta

    def _argumentos(self, mensajes: Sequence[dict[str, str]], max_tokens: int | None) -> dict:
        ajustes = self._ajustes
        extra: dict[str, Any] = {"thinking": {"type": ajustes.thinking}}
        argumentos: dict[str, Any] = {
            "model": ajustes.model,
            "messages": list(mensajes),
            "extra_body": extra,
        }
        if ajustes.thinking == "enabled":
            if ajustes.reasoning_effort:
                extra["reasoning_effort"] = ajustes.reasoning_effort
        else:
            argumentos["temperature"] = ajustes.temperature
        if max_tokens is not None:
            argumentos["max_tokens"] = max_tokens
        return argumentos

    @staticmethod
    def _es_transitorio(error: Exception) -> bool:
        if isinstance(error, openai.APIConnectionError):  # incluye los tiempos de espera
            return True
        return getattr(error, "status_code", None) in CODIGOS_TRANSITORIOS

    def _describir(self, error: Exception) -> str:
        codigo = getattr(error, "status_code", None)
        detalle = self._limpiar(str(error))[:300]
        etiqueta_codigo = f" [{codigo}]" if codigo else ""
        return f"{type(error).__name__}{etiqueta_codigo}: {detalle}"

    def _limpiar(self, texto: str) -> str:
        clave = self._ajustes.api_key
        return texto.replace(clave, "***") if clave else texto

    def _interpretar(
        self, bruta: Any, momento: datetime, segundos: float, intentos: int
    ) -> tuple[Respuesta, str]:
        uso = bruta.usage
        entrada = _entero(uso, "prompt_tokens")
        con_cache = _entero(uso, "prompt_cache_hit_tokens")
        sin_cache_bruto = getattr(uso, "prompt_cache_miss_tokens", None)
        sin_cache = (
            int(sin_cache_bruto) if sin_cache_bruto is not None else max(entrada - con_cache, 0)
        )
        salida = _entero(uso, "completion_tokens")
        detalles = getattr(uso, "completion_tokens_details", None)
        razonamiento = _entero(detalles, "reasoning_tokens") if detalles is not None else 0
        texto = bruta.choices[0].message.content or ""
        usd = calcular_costo(sin_cache, con_cache, salida, self._tarifas, es_hora_pico(momento))
        respuesta = Respuesta(
            texto=texto,
            tokens_entrada_sin_cache=sin_cache,
            tokens_entrada_cache=con_cache,
            tokens_salida=salida,
            tokens_razonamiento=razonamiento,
            segundos=segundos,
            usd=usd,
            intentos=intentos,
        )
        return respuesta, texto

    def _base_registro(
        self, momento: datetime, etiqueta: str, mensajes: Sequence[dict[str, str]]
    ) -> dict[str, Any]:
        contenido = json.dumps(list(mensajes), ensure_ascii=False, sort_keys=True)
        return {
            "momento": momento.astimezone(UTC).isoformat(),
            "etiqueta": etiqueta,
            "modelo": self._ajustes.model,
            "razonamiento": self._ajustes.thinking,
            "huella": hashlib.sha256(contenido.encode("utf-8")).hexdigest(),
            "mensajes": list(mensajes),
        }

    def _escribir_registro(self, linea: dict[str, Any]) -> None:
        texto = self._limpiar(json.dumps(linea, ensure_ascii=False))
        with self._candado:
            self._ruta.parent.mkdir(parents=True, exist_ok=True)
            with self._ruta.open("a", encoding="utf-8") as archivo:
                archivo.write(texto + "\n")
