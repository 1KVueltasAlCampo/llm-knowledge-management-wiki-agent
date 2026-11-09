"""Cliente del modelo que avisa de cada llamada, para ver el recorrido del agente en vivo."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

from wikillm.common.config import Settings
from wikillm.common.modelo import ClienteModelo, Respuesta

Emitir = Callable[[dict[str, Any]], None]
LARGO_TEXTO = 700


class ClienteObservado(ClienteModelo):
    """``ClienteModelo`` que emite un evento al empezar y otro al terminar cada llamada.

    No cambia la respuesta ni el registro de llamadas: solo observa. El texto devuelto de un turno
    del agente es su acción en JSON, así que los pasos del agente se ven al ocurrir.
    """

    def __init__(
        self, ajustes: Settings, *, emitir: Emitir, ruta_registro: Path | str, **kwargs: Any
    ) -> None:
        super().__init__(ajustes, ruta_registro=ruta_registro, **kwargs)
        self._emitir = emitir

    def generar(
        self,
        mensajes: Sequence[dict[str, str]],
        *,
        etiqueta: str = "",
        max_tokens: int | None = None,
    ) -> Respuesta:
        self._emitir({"t": "llamando", "etiqueta": etiqueta})
        try:
            respuesta = super().generar(mensajes, etiqueta=etiqueta, max_tokens=max_tokens)
        except Exception as error:
            self._emitir({"t": "llamada_fallida", "etiqueta": etiqueta, "motivo": str(error)[:300]})
            raise
        self._emitir(
            {
                "t": "llamada",
                "etiqueta": etiqueta,
                "tokens_entrada": respuesta.tokens_entrada_sin_cache
                + respuesta.tokens_entrada_cache,
                "tokens_cache": respuesta.tokens_entrada_cache,
                "tokens_salida": respuesta.tokens_salida,
                "segundos": round(respuesta.segundos, 2),
                "usd": respuesta.usd,
                "texto": respuesta.texto[:LARGO_TEXTO],
            }
        )
        return respuesta
