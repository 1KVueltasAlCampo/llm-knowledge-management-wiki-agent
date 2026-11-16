# Tasks

## 1. Corte por tipo y tablas
- [x] 1.1 Escribir primero `tests/test_informe.py` con evaluados sintéticos: corte por tipo (T5 con cobertura vacía), CSV con columnas esperadas, `resumen.md` con denominadores, error sin `evaluados.jsonl`. Verificación: `uv run pytest tests/test_informe.py` en rojo.
- [x] 1.2 Implementar `src/wikillm/eval/informe.py` (`por_tipo`, `tabla_markdown`, `escribir_informe`) reutilizando `agregar`. Verificación: pruebas de 1.1 en verde.

## 2. Figuras
- [x] 2.1 Pruebas de SVG (válido con `xml.etree`, una polilínea por sistema, salida idéntica al repetir). Verificación: en rojo.
- [x] 2.2 Generador SVG de cobertura, contexto y costo acumulado. Verificación: en verde.

## 3. Comando
- [x] 3.1 Subcomando `informe` en `src/wikillm/eval/__main__.py` y ayuda actualizada. Verificación: `uv run python -m wikillm.eval informe --corrida results/piloto-2` crea `results/piloto-2/informe/` con los cinco archivos.

## 4. Cierre
- [ ] 4.1 Sincronizar el delta a `openspec/specs/informe/spec.md`, actualizar `AGENTS.md` (comandos) y la bitácora. Verificación: `uv run ruff check . && uv run ruff format --check . && uv run pytest`.
