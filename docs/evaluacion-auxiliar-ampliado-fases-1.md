# Segundo juez sobre la corrida base `ampliado-fases-1`

Evaluación auxiliar de la [decisión 0006](decisiones/0006-evaluacion-auxiliar-con-claude.md), hecha el 17 de
noviembre de 2026. No reemplaza el veredicto de las métricas principales ni cambia el estado de ninguna
pregunta; sirve para medir cuánto se puede confiar en ese veredicto.

## Qué se hizo

- **Ítems:** 115 respuestas de `results/ampliado-fases-1`, exportadas con
  `uv run python -m wikillm.eval auxiliar exportar` y entregadas **a ciegas** (pregunta, respuesta de
  referencia y respuesta a calificar, sin el veredicto principal ni el sistema que respondió):
  las 75 respuestas que la capa determinista dejó indeterminadas (las resolvió el juez principal, Gemini) y
  40 respuestas decididas por la capa determinista, elegidas al azar con semilla 1.
- **Segundo juez:** Claude Sonnet 5.5 (`claude-sonnet-5-5`) en Claude Code, con la misma rúbrica del juez
  principal (`src/wikillm/eval/juez.py`): *correcta* si dice los mismos hechos, números y entidades que la
  referencia; *incorrecta* si los contradice, da otro número, omite el dato clave o responde cuando la
  referencia dice que el corpus no puede responder. Costo: 0 USD (cuota de suscripción).
- **Importación:** `auxiliar importar` calcula el acuerdo con el veredicto principal.

## Resultado

| Grupo | n | Acuerdo | Kappa |
|---|--:|--:|--:|
| **Total** | 115 | **94,8 %** | **0,893** |
| Capa determinista | 40 | 97,5 % | 0,950 |
| Juez principal (Gemini) | 75 | 93,3 % | 0,859 |
| RAG | 53 | 96,2 % | 0,920 |
| Wiki | 62 | 93,5 % | 0,871 |
| 60 preguntas originales | 51 | 94,1 % | 0,882 |
| 40 preguntas de borde | 64 | 95,3 % | 0,895 |

Un kappa por encima de 0,81 se considera acuerdo casi perfecto. En el total, el juez principal da 50
respuestas como correctas y Claude 48.

## Las 6 discrepancias

| Ítem | Pregunta | Principal | Claude | Por qué |
|---|---|---|---|---|
| i0005 | A003-T3-02 (wiki, paso 100) | incorrecta | correcta | Da 89,1 y «unos 20 puntos» y la limitación del survey; su línea base (69,1) difiere levemente de 68,2. Caso límite |
| i0020 | JD-27 (RAG, paso 66) | correcta | incorrecta | Falta el 60,20 de LiCoMemory; la capa determinista lo dio por bueno porque «60,2 %» aparece como línea base de contexto completo del propio paper de Zep |
| i0029 | JDi-37 (RAG, paso 66) | incorrecta | correcta | Identifica MemoryAgentBench por el título de su paper y su id; el juez principal no lo reconoció |
| i0036 | JD-31 (wiki, paso 100) | correcta | incorrecta | No da los 7.512 del paper de LoCoMo y declara la discrepancia sin resolver |
| i0044 | A013-T3-02 (wiki, paso 100) | correcta | incorrecta | Acierta el factor (estrategia de servicio) pero contrasta otro par de papers y omite los resultados de WiCER |
| i0052 | B011-T3-05 (wiki, paso 100) | correcta | incorrecta | El rango de MemStrata coincide, pero el del RAG llega a 0,43 y la referencia es 0,20 a 0,47 |

## Lectura

- **El veredicto principal es confiable:** el acuerdo es alto en ambos sistemas y en ambos grupos de
  preguntas, y las discrepancias van en los dos sentidos (en cuatro Claude es más estricto y en dos lo es el
  juez principal), así que no hay un sesgo sistemático a favor de un brazo.
- **Hallazgo sobre la capa determinista (i0020):** una clave numérica puede acreditarse por coincidencia con
  otro número del texto. Pasa con claves cortas o muy comunes (60,20 frente a un 60,2 % ajeno). Es un riesgo
  pequeño aquí (1 de 40 decididas por la capa), pero conviene mencionarlo.
- **Hallazgo sobre el juez principal:** tiende a ser indulgente con omisiones parciales en preguntas de
  lista o de rango (i0036, i0044, i0052).
- La diferencia neta en la muestra es de 2 respuestas de 115; no se puede extrapolar a las cifras completas
  porque la muestra no es aleatoria (incluye todas las indeterminadas).

## Límites

- **Independencia en las 40 preguntas de borde.** Claude redactó los borradores de esas preguntas
  (`redactado_por` en el banco), que luego verificaron los dos autores. Para ellas el segundo juez no es
  independiente de quien redactó la referencia (regla 12). El acuerdo en ese grupo (95,3 %, kappa 0,895) es
  igual al de las 60 originales (94,1 %, kappa 0,882), pero debe declararse.
- Un solo evaluador y un solo pase. Algunas respuestas largas se leyeron cortadas y se completaron las que
  eran decisivas (i0030, i0044, i0048, i0064, i0065, i0086, i0107).
- Es una evaluación auxiliar: el informe cita el veredicto principal y rotula esta sección como auxiliar.

## Archivos y cómo reproducir

`results/ampliado-fases-1/auxiliar/` contiene `items.jsonl` (ciegos), `claves.jsonl`,
`veredictos_claude.jsonl` (con el modelo y la fecha en el encabezado) y `acuerdo.md` y `acuerdo.json`.

```bash
uv run python -m wikillm.eval auxiliar exportar --corrida results/ampliado-fases-1 --banco data/preguntas/banco_100.jsonl
# el segundo juez escribe auxiliar/veredictos_claude.jsonl
uv run python -m wikillm.eval auxiliar importar --corrida results/ampliado-fases-1
```
