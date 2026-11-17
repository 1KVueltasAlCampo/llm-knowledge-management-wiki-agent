# Resumen de la corrida ampliado-fases-1

Cifras calculadas solo de los resultados guardados de esta corrida. Una celda vacía significa que no hay denominador (no es cero). `n_respondibles` es el denominador de la cobertura.

## Por sistema y paso

| system | ingest_step | n | n_respondibles | cobertura | abstencion_correcta | tasa_obsoleta | context_tokens_media | tokens_por_correcta | costo_usd_total |
|---|---|---|---|---|---|---|---|---|---|
| rag | 33 | 100 | 19 | 0.526316 | 0.901235 |  | 1273.56 | 12735.6 | 0.0225421 |
| rag | 66 | 100 | 51 | 0.470588 | 0.877551 | 0 | 1306.42 | 5443.42 | 0.0192463 |
| rag | 100 | 100 | 84 | 0.47619 | 1 | 0 | 1264.92 | 3162.3 | 0.0134554 |
| wiki | 33 | 100 | 19 | 0.684211 | 0.790123 |  | 5120.8 | 39390.8 | 0.103071 |
| wiki | 66 | 100 | 51 | 0.607843 | 0.795918 | 0 | 5179.99 | 16709.6 | 0.103441 |
| wiki | 100 | 100 | 84 | 0.702381 | 1 | 0 | 4800.67 | 8136.73 | 0.0961623 |

## Por sistema, tipo y paso

| system | tipo | ingest_step | n | n_respondibles | cobertura | abstencion_correcta | tasa_obsoleta | context_tokens_media | tokens_por_correcta | costo_usd_total |
|---|---|---|---|---|---|---|---|---|---|---|
| rag | T1 | 33 | 47 | 17 | 0.588235 | 1 |  | 1313.21 | 6172.1 | 0.0106669 |
| rag | T1 | 66 | 47 | 33 | 0.575758 | 1 |  | 1371.62 | 3392.95 | 0.00884842 |
| rag | T1 | 100 | 47 | 47 | 0.638298 |  |  | 1300.53 | 2037.5 | 0.00683668 |
| rag | T2 | 33 | 15 | 0 |  | 0.866667 |  | 1352.13 |  | 0.00337759 |
| rag | T2 | 66 | 15 | 3 | 0.333333 | 0.75 |  | 1161.87 | 17428 | 0.00246778 |
| rag | T2 | 100 | 15 | 15 | 0.4 |  |  | 1197.8 | 2994.5 | 0.00287541 |
| rag | T3 | 33 | 18 | 0 |  | 0.666667 |  | 1197 |  | 0.00412769 |
| rag | T3 | 66 | 18 | 11 | 0.363636 | 0.571429 |  | 1300.61 | 5852.75 | 0.00395932 |
| rag | T3 | 100 | 18 | 18 | 0.222222 |  |  | 1253.39 | 5640.25 | 0.00229779 |
| rag | T4 | 33 | 4 | 2 | 0 | 1 |  | 1090 |  | 0.000844968 |
| rag | T4 | 66 | 4 | 4 | 0 |  | 0 | 1197 |  | 0.000651792 |
| rag | T4 | 100 | 4 | 4 | 0 |  | 0 | 1197 |  | 0.00014376 |
| rag | T5 | 33 | 16 | 0 |  | 1 |  | 1215.44 |  | 0.00352497 |
| rag | T5 | 66 | 16 | 0 |  | 1 |  | 1284.31 |  | 0.00331897 |
| rag | T5 | 100 | 16 | 0 |  | 1 |  | 1253.19 |  | 0.00130174 |
| wiki | T1 | 33 | 47 | 17 | 0.764706 | 0.966667 |  | 4642.45 | 16784.2 | 0.0433841 |
| wiki | T1 | 66 | 47 | 33 | 0.787879 | 1 |  | 4557.19 | 8238 | 0.0412923 |
| wiki | T1 | 100 | 47 | 47 | 0.787234 |  |  | 4354.83 | 5531.81 | 0.0383001 |
| wiki | T2 | 33 | 15 | 0 |  | 0.533333 |  | 6045.87 |  | 0.0186383 |
| wiki | T2 | 66 | 15 | 3 | 0.666667 | 0.416667 |  | 6360.67 | 47705 | 0.0192398 |
| wiki | T2 | 100 | 15 | 15 | 0.8 |  |  | 5022.47 | 6278.08 | 0.0172794 |
| wiki | T3 | 33 | 18 | 0 |  | 0.5 |  | 5526.33 |  | 0.0209909 |
| wiki | T3 | 66 | 18 | 11 | 0.272727 | 0.571429 |  | 5236 | 31416 | 0.0212037 |
| wiki | T3 | 100 | 18 | 18 | 0.555556 |  |  | 4579.39 | 8242.9 | 0.0180186 |
| wiki | T4 | 33 | 4 | 2 | 0 | 1 |  | 3056.25 |  | 0.00281135 |
| wiki | T4 | 66 | 4 | 4 | 0 |  | 0 | 2582.75 |  | 0.00258892 |
| wiki | T4 | 100 | 4 | 4 | 0 |  | 0 | 2584.75 |  | 0.00242634 |
| wiki | T5 | 33 | 16 | 0 |  | 1 |  | 5718.62 |  | 0.0172467 |
| wiki | T5 | 66 | 16 | 0 |  | 1 |  | 6488.88 |  | 0.0191164 |
| wiki | T5 | 100 | 16 | 0 |  | 1 |  | 6705.31 |  | 0.0201379 |

## Comparación pareada (wiki frente a RAG)

Pares: preguntas respondibles en ese paso con respuesta de ambos brazos; acierta quien tiene veredicto `correcta`. `diferencia` = cobertura del wiki menos la de RAG. El IC95 sale de 2.000 remuestreos de las preguntas (semilla fija) y `p_mcnemar` es la prueba exacta sobre los pares discordantes (`solo_rag`, `solo_wiki`). Los intervalos suponen preguntas independientes y no hay corrección por comparaciones múltiples: con pocas preguntas por paso o por tipo conviene leerlos como orientativos.

| ingest_step | n | cobertura_rag | cobertura_wiki | diferencia | IC95 | solo_rag | solo_wiki | p_mcnemar |
|---|---|---|---|---|---|---|---|---|
| 33 | 19 | 0.526316 | 0.684211 | 0.157895 | [-0.0526316, 0.421053] | 1 | 4 | 0.375 |
| 66 | 51 | 0.470588 | 0.607843 | 0.137255 | [-0.0196078, 0.313725] | 6 | 13 | 0.167068 |
| 100 | 84 | 0.47619 | 0.702381 | 0.22619 | [0.107143, 0.345238] | 7 | 26 | 0.00131873 |
