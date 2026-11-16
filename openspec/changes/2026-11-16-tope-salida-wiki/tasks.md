# Tasks

## 1. Tope
- [x] 1.1 Subir `MAX_TOKENS_ESCRITURA` a 32.000 y comprobar que ninguna prueba lo fija. Verificación: `uv run ruff check . && uv run ruff format --check . && uv run pytest`.

## 2. Reanudar
- [ ] 2.1 Reanudar `oficial-1` con `MAX_USD_PER_RUN=10` y `--confirmo-usd 10`. Verificación: la corrida termina con 1.320 respuestas únicas y el costo total sigue bajo el tope.
