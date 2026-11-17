# Sensibilidad del RAG al `k` y deriva del wiki entre cargas

Dos análisis complementarios del experimento base (corrida `ampliado-fases-1`: 100 papers, 100 preguntas,
pasos 33, 66 y 100, `deepseek-flash`). Se hicieron el 17 de noviembre de 2026. Gasto: ≈ 0,5 USD
(≈ 0,22 las tres corridas RAG, 0,26 la prueba con texto original y centavos del juez); el análisis de
deriva no gasta.

## 1. ¿La ventaja del wiki depende de que el RAG recupere solo 5 fragmentos?

La corrida oficial usa `k = 5` (decisión 0008). Para ver si «el wiki gana» se debe a un RAG con poco
contexto, se repitió **solo el brazo RAG** con `k = 10` y `k = 20` (opción nueva `--brazos`, cambio
OpenSpec `2026-11-17-brazos-seleccionables`), con las mismas preguntas y pasos, y se comparó cada una
contra el wiki de `ampliado-fases-1` con la comparación pareada del proyecto (`scripts/sensibilidad_rag.py`).
Cobertura = fracción de respondibles con veredicto correcto (juez de Gemini solo para lo indeterminado).

| k | Paso | RAG | Wiki | Diferencia (IC 95 %) | Solo RAG | Solo wiki | p (McNemar) |
|--:|--:|--:|--:|---|--:|--:|--:|
| 5 | 33 | 0,53 | 0,68 | +0,16 [−0,05, +0,42] | 1 | 4 | 0,38 |
| 5 | 66 | 0,47 | 0,61 | +0,14 [−0,02, +0,31] | 6 | 13 | 0,17 |
| 5 | 100 | 0,48 | 0,70 | **+0,23 [+0,11, +0,35]** | 7 | 26 | **0,001** |
| 10 | 33 | 0,63 | 0,68 | +0,05 [−0,11, +0,26] | 1 | 2 | 1,00 |
| 10 | 66 | 0,47 | 0,61 | +0,14 [0,00, +0,27] | 4 | 11 | 0,12 |
| 10 | 100 | 0,55 | 0,70 | +0,15 [+0,05, +0,26] | 6 | 19 | 0,015 |
| 15 | 33 | 0,68 | 0,68 | 0,00 [−0,16, +0,16] | 1 | 1 | 1,00 |
| 15 | 66 | 0,57 | 0,61 | +0,04 [−0,10, +0,18] | 5 | 7 | 0,77 |
| 15 | 100 | 0,60 | 0,70 | +0,11 [+0,01, +0,21] | 6 | 15 | 0,078 |
| 20 | 33 | 0,68 | 0,68 | 0,00 [−0,16, +0,16] | 1 | 1 | 1,00 |
| 20 | 66 | 0,59 | 0,61 | +0,02 [−0,12, +0,16] | 6 | 7 | 1,00 |
| 20 | 100 | 0,64 | 0,70 | **+0,06 [−0,05, +0,17]** | 8 | 13 | **0,38** |

Paso 100 por tipo (RAG / wiki): T1 0,64 / 0,79 con `k = 5` y 0,70 / 0,79 con `k = 20`; T2 0,40 / 0,80
y 0,73 / 0,80; T3 0,22 / 0,56 y 0,50 / 0,56. La abstención correcta (T5) es 1,00 en todos los `k`.

| k | Contexto medio del RAG | Tokens de entrada de las 300 respuestas |
|--:|--:|--:|
| 5 | 1.282 | 0,43 M |
| 10 | 2.532 | 0,82 M |
| 15 | 3.810 | 1,22 M |
| 20 | 5.087 | 1,61 M |

(El wiki, en la misma corrida base: contexto medio 4.800 y 4,30 M de tokens de entrada, porque su agente
hace varias llamadas por pregunta.) **No se comparan los dólares entre `k`**: DeepSeek cachea los
prefijos repetidos y los contextos de `k = 10` y `k = 15` son prefijo del de `k = 20`, que corrió al
mismo tiempo o justo antes, así que su costo salió artificialmente bajo (0,022 USD con `k = 15`).

**Lectura.**
- La conclusión «el wiki gana» **depende de `k`**: la diferencia al paso 100 baja de forma continua
  (+0,23, +0,15, +0,11, +0,06 con 5, 10, 15 y 20 fragmentos). Es significativa con 5 y 10, queda en el
  límite con 15 (p = 0,078) y deja de serlo con 20, que usa un contexto del tamaño del que usa el wiki.
  En los pasos 33 y 66 ya no hay diferencia clara desde `k = 15`.
- Lo que se mantiene en todos los `k` es el gasto de tokens: el RAG con 20 fragmentos usa 1,6 M de tokens
  de entrada frente a 4,3 M del wiki.
- El wiki sigue por delante en los tres tipos con `k = 20`, pero sin significancia con estas muestras.
- Es una sola corrida por `k` (temperatura 0) y 84 pares al paso 100: no es evidencia de que el RAG
  iguale al wiki, sino de que el resultado no es robusto a ese parámetro.

**Qué implica para la tesis.** Con `k = 5` la comparación está fijada de antemano y sale a favor del wiki;
conviene declarar el análisis de sensibilidad y la salvedad (a igual contexto, la diferencia deja de ser
significativa). Esta no es una prueba de RAG híbrido (BM25 más vectores), que la constitución deja fuera
del RAG simple; sería una decisión aparte.

## 2. ¿Se degrada el wiki al ingerir más papers? (deriva entre cargas)

Medido sin llamar al modelo, leyendo las copias `paso-N` del repositorio git del wiki
(`scripts/exploracion_deriva/deriva_wiki.py`, sin modificar el wiki).

- **Crecimiento:** entre 4 y 5 páginas nuevas y 5 o 6 modificadas por paper. Las líneas que desaparecen
  por paso son el 2,8 % en los pasos 1–33, el 0,4 % en 34–66 y el 0,2 % en 67–100.
- **Supervivencia literal:** el 87,5 % de las líneas del paso 33 siguen idénticas en el 66 y el 85,9 % en
  el 100; del paso 66 al 100, el 94,6 %.
- **Cifras:** de las cifras decimales atribuidas a un paper (líneas que citan solo ese paper), se conserva el
  97,3 % del paso 33 al 66 y el 96,9 % al 100 (papers 1–33), y el 99,3 % del 66 al 100 (papers 34–66).
- **Respuestas del banco:** de las 19 preguntas respondibles al paso 33, el wiki tiene todas las claves en
  12 (63 %), y esas 12 siguen en los pasos 66 y 100; de las 51 respondibles al 66, en 41 (80 %), y siguen las
  41 al 100. **No se pierde lo ya aprendido; lo que falta es lo que no entró al ingerir.**
- **Actualizaciones (T4):** el valor viejo **no se retira** cuando llega el nuevo. En A016-T4-03 conviven
  `71.0` y `0.831` al paso 100; en A039-T4-03 el valor vigente (`52.94`) nunca llegó al wiki y sigue el
  viejo (`74.7`). Es un hallazgo sobre el mantenimiento incremental, tema que el estado del arte marca como
  vacío de investigación.

**Lectura.** El cuello de botella del wiki es la **captura en la ingesta** (el 20 % al 37 % de las preguntas
respondibles no tiene sus claves en las páginas), no la deriva posterior; la ingesta tampoco actualiza ni
retira lo obsoleto, lo que penaliza a las preguntas de actualización.

**Límites.** La retención de cifras agrupa por corte (33 y 66), no por el paso exacto de cada paper, y
asigna cada cifra a un paper solo si la línea cita uno; es una aproximación. El banco tiene 4 preguntas T4.

## 3. ¿Ayuda dar al wiki acceso al texto original de los papers?

El wiki resume, y una parte de sus fallos son detalles que el resumen perdió. En `ampliado-fases-1`, al paso 100,
el wiki acierta 59 de 84 respondibles, el RAG con `k = 5` acierta 40 y un enrutador perfecto entre los dos
acertaría 66: el RAG solo añade 7 preguntas (+8 puntos) sobre el wiki, y el wiki añade 26 sobre el RAG.

Se probó, con `scripts/comparar_herramientas.py`, el wiki en el paso 100 con respaldo en el texto original
(el índice vectorial de `ampliado-fases-1`, recuperación de 5 o 3 pasajes), sobre **las 100 preguntas** y con la
base en la misma sesión (una repetición; acierto por presencia de claves, no por el juez, así que las
cifras no son comparables con las del juez de `ampliado-fases-1`):

| Variante | Respondibles (84) | T5 (16) | Total (100) | Llamadas | Tokens de entrada |
|---|--:|--:|--:|--:|--:|
| Base (`search` y `read`) | 46 | 15 | 61 | 4,3 | 11.200 |
| Herramienta opcional `raw` (texto original, 5 pasajes) | 47 | 16 | 63 | 4,6 | 13.400 |
| Precarga de 3 pasajes originales junto a las páginas del wiki | **50** | 15 | **65** | 4,4 | 14.100 |

- La herramienta opcional se usó en el 38 % de las corridas (el grafo de graphify, en el 3–12 %).
- Frente a la base: +2 (herramienta, p = 0,75) y +4 (precarga, p = 0,39), con 4 y 6 preguntas que
  cambian en cada sentido. **No es significativo**; la dirección es favorable y el margen total posible
  era de +7.
- El costo es un 20 % a 26 % más de tokens de entrada, con las mismas llamadas.
- En T5 (abstención) no empeora (15, 16 y 15 de 16).

**Lectura.** Dar acceso al texto original recupera una parte del margen que el RAG tiene sobre el wiki, a
cambio de más contexto; con una repetición y 100 preguntas no se puede afirmar que mejore. Es un brazo
distinto del diseño (el WikiLLM deja de ser «solo wiki») y habría que decidirlo y registrarlo.

## Reproducir

```bash
uv run python -m wikillm.arnes correr --corrida ampliado-rag-k10 --brazos rag --k 10 \
    --pasos 33,66,100 --banco data/preguntas/banco_100.jsonl --manifest data/corpus100/manifest.jsonl \
    --gold data/corpus100/gold --spans data/corpus100/gold/spans.jsonl
uv run python -m wikillm.eval metricas --respuestas results/ampliado-rag-k10/respuestas.jsonl --juez \
    --banco data/preguntas/banco_100.jsonl --manifest data/corpus100/manifest.jsonl \
    --spans data/corpus100/gold/spans.jsonl
uv run python scripts/sensibilidad_rag.py
uv run python scripts/exploracion_deriva/deriva_wiki.py
```
