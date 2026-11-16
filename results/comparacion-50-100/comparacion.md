# Comparación entre corridas: `oficial-1` (paso 50) y `ampliado-1` (paso 100)

Pares: preguntas respondibles en ambos pasos y presentes en las dos corridas, por sistema. `diferencia` = cobertura de la ampliada menos la de la base; `solo_base` y `solo_ampliada` son los pares discordantes.

Las dos corridas difieren en el **orden** de ingesta y en el **tamaño** del corpus, así que el efecto de añadir papers se mezcla con el del cambio de orden. Los intervalos suponen preguntas independientes y no hay corrección por comparaciones múltiples; con pocas preguntas por tipo son orientativos. El wiki no es determinista y cada corrida es una sola ejecución.

## Por sistema

| sistema | tipo | n | cobertura_base | cobertura_ampliada | diferencia | ic95_inf | ic95_sup | solo_base | solo_ampliada | p_mcnemar |
|---|---|---|---|---|---|---|---|---|---|---|
| rag |  | 50 | 0.54 | 0.56 | 0.02 | 0 | 0.06 | 0 | 1 | 1 |
| wiki |  | 50 | 0.78 | 0.78 | 0 | -0.1 | 0.1 | 3 | 3 | 1 |

## Por sistema y tipo de pregunta

| sistema | tipo | n | cobertura_base | cobertura_ampliada | diferencia | ic95_inf | ic95_sup | solo_base | solo_ampliada | p_mcnemar |
|---|---|---|---|---|---|---|---|---|---|---|
| rag | T1 | 26 | 0.769231 | 0.769231 | 0 | 0 | 0 | 0 | 0 | 1 |
| rag | T2 | 12 | 0.416667 | 0.5 | 0.0833333 | 0 | 0.25 | 0 | 1 | 1 |
| rag | T3 | 8 | 0.25 | 0.25 | 0 | 0 | 0 | 0 | 0 | 1 |
| rag | T4 | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| wiki | T1 | 26 | 0.807692 | 0.769231 | -0.0384615 | -0.192308 | 0.115385 | 3 | 2 | 1 |
| wiki | T2 | 12 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 1 |
| wiki | T3 | 8 | 0.625 | 0.625 | 0 | 0 | 0 | 0 | 0 | 1 |
| wiki | T4 | 4 | 0.25 | 0.5 | 0.25 | 0 | 0.75 | 0 | 1 | 1 |

## Preguntas nuevas (preliminares)

Son 17 preguntas que solo están en `ampliado-1`, sin revisión cruzada del otro autor, así que sus resultados son preliminares.

| n | cobertura_rag | cobertura_wiki | diferencia | ic95_inf | ic95_sup | solo_rag | solo_wiki | p_mcnemar |
|---|---|---|---|---|---|---|---|---|
| 17 | 0.411765 | 0.588235 | 0.176471 | -0.117647 | 0.470588 | 2 | 5 | 0.453125 |

## Contexto y costo

| corrida | sistema | paso | contexto_medio | costo_por_respuesta | costo_preguntas_total | costo_ingesta_total |
|---|---|---|---|---|---|---|
| oficial-1 | rag | 50 | 1240.95 | 8.20262e-05 | 0.11671 | 0 |
| oficial-1 | wiki | 50 | 4650.03 | 0.00081262 | 0.991351 | 1.4076 |
| ampliado-1 | rag | 100 | 1291.49 | 0.000165193 | 0.157045 | 0 |
| ampliado-1 | wiki | 100 | 5562.5 | 0.00203178 | 1.47714 | 2.88646 |
