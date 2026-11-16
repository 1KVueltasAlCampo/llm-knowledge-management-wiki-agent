# Tasks

## 1. Fases
- [x] 1.1 `aplicar_fases` en `corpus/manifest.py` y la orden `wikillm.corpus fases`. Verificación: `uv run pytest tests/test_corpus_manifest.py`.
- [x] 1.2 `data/corpus100/fases.json` con las 10 excepciones y su motivo. Verificación: 33, 33 y 34 papers por fase.
- [x] 1.3 Reordenar `data/corpus100/manifest.jsonl` y regenerar `banco_100.jsonl`. Verificación: `validar-banco` sin problemas y 138 evidencias que coinciden con el Gold.

## 2. Decisión
- [x] 2.1 ADR 0009 con las razones de cada carga y los límites que el informe debe declarar.
