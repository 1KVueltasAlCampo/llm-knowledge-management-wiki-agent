# Análisis de fallos de la corrida oficial-1

Las categorías son una pista, no un diagnóstico: citar todas las fuentes requeridas no prueba que el modelo las haya leído bien, y una respuesta correcta que la clave no reconoce cae en `fuentes_completas_error`. `detalle.csv` permite revisar casos a mano.

Respuestas no correctas: 293 de 1320 (todos los pasos).

## Por sistema

| system | abstencion_erronea | sin_fuente | fuente_parcial | fuentes_completas_error | obsoleta | indeterminada | no_se_abstuvo | total |
|---|---|---|---|---|---|---|---|---|
| rag | 157 | 5 | 4 | 2 | 0 | 0 | 1 | 169 |
| wiki | 24 | 1 | 26 | 15 | 18 | 0 | 40 | 124 |

## Por sistema y tipo de pregunta

| system | tipo | abstencion_erronea | sin_fuente | fuente_parcial | fuentes_completas_error | obsoleta | indeterminada | no_se_abstuvo | total |
|---|---|---|---|---|---|---|---|---|---|
| rag | T1 | 49 | 5 | 0 | 0 | 0 | 0 | 0 | 54 |
| rag | T2 | 29 | 0 | 4 | 2 | 0 | 0 | 1 | 36 |
| rag | T3 | 39 | 0 | 0 | 0 | 0 | 0 | 0 | 39 |
| rag | T4 | 40 | 0 | 0 | 0 | 0 | 0 | 0 | 40 |
| wiki | T1 | 23 | 0 | 0 | 8 | 0 | 0 | 1 | 32 |
| wiki | T2 | 0 | 0 | 0 | 0 | 0 | 0 | 29 | 29 |
| wiki | T3 | 0 | 1 | 15 | 7 | 0 | 0 | 6 | 29 |
| wiki | T4 | 1 | 0 | 11 | 0 | 18 | 0 | 0 | 30 |
| wiki | T5 | 0 | 0 | 0 | 0 | 0 | 0 | 4 | 4 |
