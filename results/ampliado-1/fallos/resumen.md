# Análisis de fallos de la corrida ampliado-1

Las categorías son una pista, no un diagnóstico: citar todas las fuentes requeridas no prueba que el modelo las haya leído bien, y una respuesta correcta que la clave no reconoce cae en `fuentes_completas_error`. `detalle.csv` permite revisar casos a mano.

Respuestas no correctas: 172 de 600 (todos los pasos).

## Por sistema

| system | abstencion_erronea | sin_fuente | fuente_parcial | fuentes_completas_error | obsoleta | indeterminada | no_se_abstuvo | total |
|---|---|---|---|---|---|---|---|---|
| rag | 62 | 5 | 9 | 4 | 0 | 0 | 14 | 94 |
| wiki | 23 | 2 | 19 | 7 | 0 | 0 | 27 | 78 |

## Por sistema y tipo de pregunta

| system | tipo | abstencion_erronea | sin_fuente | fuente_parcial | fuentes_completas_error | obsoleta | indeterminada | no_se_abstuvo | total |
|---|---|---|---|---|---|---|---|---|---|
| rag | T1 | 31 | 3 | 0 | 4 | 0 | 0 | 0 | 38 |
| rag | T2 | 5 | 0 | 6 | 0 | 0 | 0 | 5 | 16 |
| rag | T3 | 16 | 2 | 3 | 0 | 0 | 0 | 9 | 30 |
| rag | T4 | 10 | 0 | 0 | 0 | 0 | 0 | 0 | 10 |
| wiki | T1 | 15 | 0 | 0 | 6 | 0 | 0 | 1 | 22 |
| wiki | T2 | 0 | 0 | 4 | 0 | 0 | 0 | 14 | 18 |
| wiki | T3 | 6 | 2 | 7 | 1 | 0 | 0 | 12 | 28 |
| wiki | T4 | 2 | 0 | 8 | 0 | 0 | 0 | 0 | 10 |
