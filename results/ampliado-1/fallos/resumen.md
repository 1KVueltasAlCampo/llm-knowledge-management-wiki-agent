# Análisis de fallos de la corrida ampliado-1

Las categorías son una pista, no un diagnóstico: citar todas las fuentes requeridas no prueba que el modelo las haya leído bien, y una respuesta correcta que la clave no reconoce cae en `fuentes_completas_error`. `detalle.csv` permite revisar casos a mano.

Respuestas no correctas: 318 de 1760 (todos los pasos).

## Por sistema

| system | abstencion_erronea | sin_fuente | fuente_parcial | fuentes_completas_error | obsoleta | indeterminada | no_se_abstuvo | total |
|---|---|---|---|---|---|---|---|---|
| rag | 144 | 8 | 15 | 3 | 0 | 0 | 10 | 180 |
| wiki | 23 | 6 | 25 | 18 | 16 | 0 | 50 | 138 |

## Por sistema y tipo de pregunta

| system | tipo | abstencion_erronea | sin_fuente | fuente_parcial | fuentes_completas_error | obsoleta | indeterminada | no_se_abstuvo | total |
|---|---|---|---|---|---|---|---|---|---|
| rag | T1 | 60 | 8 | 0 | 2 | 0 | 0 | 1 | 71 |
| rag | T2 | 13 | 0 | 10 | 1 | 0 | 0 | 4 | 28 |
| rag | T3 | 37 | 0 | 5 | 0 | 0 | 0 | 5 | 47 |
| rag | T4 | 34 | 0 | 0 | 0 | 0 | 0 | 0 | 34 |
| wiki | T1 | 21 | 0 | 0 | 14 | 0 | 0 | 3 | 38 |
| wiki | T2 | 0 | 0 | 7 | 0 | 0 | 0 | 27 | 34 |
| wiki | T3 | 2 | 6 | 18 | 4 | 0 | 0 | 20 | 50 |
| wiki | T4 | 0 | 0 | 0 | 0 | 16 | 0 | 0 | 16 |
