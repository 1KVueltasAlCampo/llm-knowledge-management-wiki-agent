# Proposal

## Why

Las tablas de `informe` dan la cobertura de cada brazo, pero con 60 preguntas (y solo 4 de T4) una
diferencia de 0,1 puede ser ruido. Para concluir que un brazo supera al otro hace falta saber cuánto
varía la diferencia y si es mayor que el azar. Como ambos brazos responden las mismas preguntas, la
comparación correcta es **pareada**.

## What Changes

- `wikillm.eval informe` escribe además `comparacion_pareada.csv` y una sección en `resumen.md` con,
  por paso de ingesta (y por tipo de pregunta): la cobertura de cada brazo, la diferencia
  wiki − RAG, su intervalo de confianza al 95 % por bootstrap sobre las preguntas y el valor p de la
  prueba exacta de McNemar sobre los pares discordantes.
- Cálculo en Python puro (`src/wikillm/eval/estadistica.py`), sin dependencias nuevas y con semilla
  fija, de modo que repetir el informe da archivos idénticos.

## Impact

- Código nuevo en `eval/`; `informe` pasa a escribir dos productos más. Sin llamadas a API.
- Los intervalos asumen preguntas independientes y no corrigen por comparaciones múltiples: el
  resumen lo declara.
