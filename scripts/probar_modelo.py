"""Prueba manual: una llamada real mínima al modelo. Cuesta bastante menos de un centavo.

Uso: uv run python scripts/probar_modelo.py
"""

import json
import urllib.request

from wikillm.common.config import Settings, load_settings
from wikillm.common.modelo import ClienteModelo


def consultar_saldo(ajustes: Settings) -> float:
    """Saldo total en USD según GET /user/balance (la API lo informa con dos decimales)."""
    peticion = urllib.request.Request(
        f"{ajustes.base_url}/user/balance",
        headers={"Authorization": f"Bearer {ajustes.api_key}"},
    )
    with urllib.request.urlopen(peticion, timeout=30) as respuesta:
        datos = json.load(respuesta)
    return float(datos["balance_infos"][0]["total_balance"])


def main() -> None:
    ajustes = load_settings()
    cliente = ClienteModelo(ajustes)
    print(f"Modelo: {ajustes.model} | razonamiento: {ajustes.thinking}")
    print(f"Saldo antes: {consultar_saldo(ajustes):.2f} USD")
    respuesta = cliente.generar(
        [{"role": "user", "content": "Responde únicamente con la palabra: ok"}],
        etiqueta="prueba",
        max_tokens=16,
    )
    print(f"Respuesta: {respuesta.texto!r}")
    print(
        f"Tokens entrada (sin caché / con caché): "
        f"{respuesta.tokens_entrada_sin_cache} / {respuesta.tokens_entrada_cache}"
    )
    print(
        f"Tokens salida: {respuesta.tokens_salida} (razonamiento: {respuesta.tokens_razonamiento})"
    )
    print(f"Tiempo: {respuesta.segundos:.2f} s | intentos: {respuesta.intentos}")
    print(f"Costo estimado: {respuesta.usd:.6f} USD")
    print(f"Saldo después: {consultar_saldo(ajustes):.2f} USD")


if __name__ == "__main__":
    main()
