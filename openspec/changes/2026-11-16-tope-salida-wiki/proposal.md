# Proposal

## Why

La corrida oficial `oficial-1` se detuvo en el paso 20: la escritura del wiki de `2606.06240` llegó
al tope de 16.000 tokens de salida y el JSON quedó cortado en los dos intentos. Sin un tope mayor la
corrida no puede completarse con los papers grandes del corpus. Ver decisión 0007.

## What Changes

- `MAX_TOKENS_ESCRITURA` en `src/wikillm/wiki/ingesta.py` pasa de 16.000 a 32.000.
- ADR 0007 con el motivo, el costo máximo por llamada y el riesgo.
- Se reanuda `oficial-1` con la misma orden y el mismo nombre; los pasos 0–15 no se repiten.

## Impact

- Código: una constante. Sin cambio de contrato ni de formato de resultados. RAG no cambia.
- Aviso a Juan David (dueño de `src/wikillm/wiki/`) en el PR.
