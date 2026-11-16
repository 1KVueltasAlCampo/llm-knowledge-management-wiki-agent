# Design

## Context

`eval/metricas.py` ya produce `evaluados.jsonl` (un registro por respuesta, con `tipo`, `veredicto`,
`context_tokens`, `cost_usd`) y `agregar()` (una fila por sistema y paso). La función `_escribir_csv`
en `eval/__main__.py` escribe esos agregados. Falta el corte por tipo y la presentación.

## Decisions

1. **Reutilizar `agregar`.** El corte por tipo agrupa `evaluados` por `tipo` y llama a `agregar`
   por grupo; así las definiciones de cobertura, obsolescencia y costo no se duplican.
2. **SVG a mano.** Una polilínea por sistema con una escala lineal simple. Evita añadir
   matplotlib (cambio de dependencias = riesgo de entorno) y da archivos diminutos, determinísticos
   y versionables. Orden y formato de números fijos para que la salida sea idéntica entre corridas.
3. **Costo acumulado.** Se acumula `costo_usd_total` por sistema sobre los pasos ordenados.
4. **Sin juez ni red.** El informe solo lee archivos; el veredicto ya viene en `evaluados.jsonl`.

## Risks

- Con pocas preguntas por tipo (T4 tiene 4) las tasas son ruidosas: `por_tipo.csv` incluye `n` y
  `n_respondibles` para que se vea el denominador, y `resumen.md` lo imprime junto a cada cifra.
