"""Lanza graphify con la clave del proyecto en el entorno, sin imprimirla.

Uso: lanzar_graphify.py <graphify.exe> [--sin-thinking] -- <args de graphify>
"""

import os
import subprocess
import sys
import time

from wikillm.common.config import load_settings


def main() -> None:
    exe, resto = sys.argv[1], sys.argv[2:]
    sin_thinking = "--sin-thinking" in resto
    args = resto[resto.index("--") + 1 :]
    s = load_settings()
    env = dict(os.environ)
    env["DEEPSEEK_API_KEY"] = s.api_key
    env["GRAPHIFY_DEEPSEEK_MODEL"] = s.model
    env["PYTHONIOENCODING"] = "utf-8"
    env.pop("GRAPHIFY_DISABLE_THINKING", None)
    if sin_thinking:
        env["GRAPHIFY_DISABLE_THINKING"] = "1"
    print(f"modelo={s.model} precios in={s.price_input_cache_miss} out={s.price_output}")
    t = time.time()
    r = subprocess.run([exe, *args], env=env, capture_output=True, text=True, encoding="utf-8")
    salida = (r.stdout + r.stderr).replace(s.api_key, "***")
    print(salida[-4000:])
    print(f"código={r.returncode} segundos={time.time() - t:.0f}")


if __name__ == "__main__":
    main()
