# 0006. Evaluación auxiliar con Claude (segundo juez y análisis de fallos)

**Fecha:** 15 de noviembre de 2026. **Estado:** propuesta (Juan Diego), pendiente de revisión de
Juan David. **Complementa:** la decisión 0003; no la cambia.

## Decisión

Se añade una **evaluación auxiliar**, siempre aparte de las métricas principales:

1. **Segundo juez de auditoría.** Claude (modelo de la sesión de Claude Code, id exacto
   registrado en cada archivo) emite veredictos ciegos sobre todas las respuestas que la capa
   determinista dejó indeterminadas y sobre una muestra aleatoria con semilla de las
   deterministas. Se reporta el acuerdo con el veredicto principal (porcentaje y kappa).
2. **Análisis de fallos.** Claude clasifica cada fallo de RAG y wiki leyendo `trazas.jsonl`
   (no recuperó, recuperó y se confundió, abstención errónea, respuesta obsoleta).

Los roles de 0003 no cambian: responde `deepseek-flash`, redacta `deepseek-v4-pro`, juzga
`gemini-3.1-flash-lite`. El veredicto de las métricas principales sigue siendo el de la capa
determinista y Gemini. Claude **nunca** reemplaza esos veredictos ni cambia el estado de una
pregunta del banco (constitución #11).

## Por qué

- Claude es distinto del que responde, del que redactó y del juez principal, así que respeta la
  regla 12 (nadie se evalúa a sí mismo).
- Un segundo juez de otro proveedor da una medida de acuerdo entre jueces, que defiende las
  cifras mejor que un solo juez sin calibrar.
- El análisis de fallos explica *por qué* un brazo supera al otro, no solo cuánto.

## Límites

- **No es una tercera arquitectura.** No hay brazo con Claude: se mantiene la regla 1 (mismo
  modelo en RAG y wiki) y la 4 (RAG simple).
- **Costo fuera de `consumo.csv`.** Se usa la cuota de suscripción de Claude Code, no la API, así
  que no hay dólares que registrar. Se anota el modelo, la fecha y el número de ítems en el
  encabezado de cada archivo auxiliar.
- **Menos reproducible.** Los veredictos son archivos guardados en `results/<corrida>/auxiliar/`;
  el informe cita esos archivos y rotula la sección "evaluación auxiliar".
- Los ítems se entregan **ciegos**: sin el veredicto del juez principal ni el sistema que los
  produjo.
