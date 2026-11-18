# Preguntas de varios saltos y citas entre papers

Hecho el 18 de noviembre de 2026 sobre el banco de 100 preguntas, **sin cambiar ninguna** (cambio OpenSpec
`2026-11-18-preguntas-varios-saltos`). Una pregunta es de **varios saltos** si su respuesta exige combinar dos
o más papers (`fuentes_requeridas`): son 34 de las 84 respondibles (15 T2, 15 T3 y 4 T4). Es **encadenada**
si alguno de esos papers cita a otro de ellos (`referencias_en_corpus` del manifiesto): lo son 30 de las 34,
así que ahí el segundo paper se puede alcanzar siguiendo una cita, como sugirió el tutor.

## 1. Cómo les va a los sistemas (sin gasto)

`scripts/varios_saltos.py` reparte los resultados ya guardados del paso 100. Cobertura = fracción de
preguntas del grupo contestadas bien (`results/varios-saltos/resumen.json`).

| Grupo | n | RAG k=5 | RAG k=10 | RAG k=15 | RAG k=20 | Wiki 8 acc. | Wiki 4 acc. |
|---|--:|--:|--:|--:|--:|--:|--:|
| Un solo paper | 50 | 0,62 | 0,62 | 0,68 | 0,70 | **0,80** | 0,76 |
| **Varios papers** | **34** | **0,26** | 0,44 | 0,47 | 0,56 | **0,56** | 0,53 |
| encadenados por citas | 30 | 0,30 | 0,47 | 0,53 | 0,60 | 0,60 | 0,57 |
| sin cita entre ellos | 4 | 0,00 | 0,25 | 0,00 | 0,25 | 0,25 | 0,25 |
| T2 (combinar) | 15 | 0,40 | 0,60 | 0,67 | 0,73 | 0,80 | 0,80 |
| T3 (comparar) | 15 | 0,20 | 0,40 | 0,40 | 0,47 | 0,47 | 0,40 |
| T4 (actualizar) | 4 | 0,00 | 0,00 | 0,00 | 0,25 | 0,00 | 0,00 |

Fracción de preguntas en que el sistema **cita todos los papers que exige** la pregunta:

| Grupo | RAG k=5 | RAG k=10 | RAG k=15 | RAG k=20 | Wiki 8 | Wiki 4 |
|---|--:|--:|--:|--:|--:|--:|
| Un solo paper | 0,64 | 0,68 | 0,74 | 0,82 | 0,86 | 0,86 |
| Varios papers | 0,12 | 0,27 | 0,29 | 0,32 | **0,41** | 0,38 |

Wiki (8 acciones) frente a cada RAG en las 34 preguntas de varios papers (comparación pareada):

| RAG | Diferencia (IC 95 %) | Solo RAG / solo wiki | p (McNemar) |
|--:|---|--:|--:|
| k=5 | **+0,29 [+0,12, +0,50]** | 2 / 12 | 0,013 |
| k=10 | +0,12 [−0,03, +0,29] | 2 / 6 | 0,29 |
| k=15 | +0,09 [−0,06, +0,24] | 2 / 5 | 0,45 |
| k=20 | +0,00 [−0,15, +0,15] | 3 / 3 | 1,00 |

**Lectura.**
- **Las preguntas de varios papers son las difíciles para todos:** el RAG con 5 fragmentos acierta el 26 %
  (el 62 % en las de un solo paper) y el wiki el 56 % (el 80 %).
- **La ventaja del wiki en varios saltos es la misma de la comparación general:** grande con `k = 5` (+0,29,
  significativa) y **nula con `k = 20`** (0,56 frente a 0,56). Con un contexto como el del wiki, el RAG
  también combina papers. Varios saltos no es un terreno donde el wiki gane con independencia del contexto.
- **El wiki reúne mejor las fuentes, pero no del todo:** cita todos los papers exigidos en el 41 % de las
  preguntas (el RAG con `k = 5`, en el 12 %), así que en el 59 % le falta al menos uno. Ahí hay margen para
  ayudas de navegación como las citas.

## 2. ¿Ayuda una herramienta de citas de punta a punta?

Se añadió al script exploratorio `scripts/comparar_herramientas.py` la acción `cites`: dado un paper (página
o id de arXiv), devuelve los papers del corpus que cita y los que lo citan, con su página del wiki (grafo
de `referencias_en_corpus`). Se comparó el mismo agente con `search` y `read` **con** (`citas`) y **sin**
(`generico`) esa acción, en las 34 preguntas, un paso 100 y una repetición
(`results/herramientas/paso100-citas-herramienta/`; 0,054 USD en las 68 respuestas).

| | Sin `cites` | Con `cites` |
|---|--:|--:|
| Respuestas correctas (todas las claves presentes) | 11 de 34 | 9 de 34 |
| En las 30 encadenadas por citas | 10 | 8 |
| Cita todos los papers exigidos | 15 | 14 |
| Llamadas por pregunta | 3,85 | 3,94 |
| Tokens de entrada por pregunta | 10.839 | 13.375 |

**El agente no usó la herramienta ni una vez en 34 preguntas** (50 `search`, 44 `read`, 35 `answer`). Las
dos respuestas de diferencia (2 solo sin la herramienta, 0 solo con ella) son ruido de una corrida única y
no son significativas; el costo sube porque el protocolo es más largo. Estas cifras usan solo la capa
determinista (todas las claves presentes), por eso son menores que las de la tabla 1, que añade el juez: con
esa misma capa, el wiki de la corrida oficial acierta 11 de las 34 y el RAG con `k = 5`, 3.

Junto con la prueba previa de precargar las páginas conectadas por citas (`pipe_paginas_citas`, ver
`docs/evaluacion-grafo-100-papers.md`), son **dos formas de usar las citas y ninguna mejora los aciertos**.

## Qué se puede concluir y qué no

- Las citas entre papers existen y cubren casi todas las preguntas de varios saltos (30 de 34), pero el
  agente no las necesitó: encuentra los papers por búsqueda. Una explicación probable, **no probada**, es que
  muchas preguntas de síntesis nombran los papers o sus temas (ver los ejemplos de T2 y T3 en el README), así
  que no hace falta «saltar» para encontrarlos. El cuello de botella parece estar en lo que el wiki captó al
  ingerir y en leer la sección correcta, no en navegar.
- **Límites:** una repetición con temperatura 0; solo 34 preguntas (4 sin cita entre ellas); correctitud
  determinista en la prueba de la herramienta; y la herramienta es opcional, de modo que no se probó **obligar**
  al agente a seguir una cita, que sería otro diseño. No se creó ninguna pregunta nueva de varios saltos con
  encadenamiento forzado.

## Reproducir

```bash
uv run python scripts/varios_saltos.py     # sin gasto
uv run python scripts/comparar_herramientas.py --wiki data/wiki/construccion-1 --banco data/preguntas/banco_100.jsonl \
  --spans data/corpus100/gold/spans.jsonl --manifest data/corpus100/manifest.jsonl \
  --salida results/herramientas/paso100-citas-herramienta \
  --preguntas "$(cat results/herramientas/preguntas-varios-saltos.txt)" --variantes generico,citas
```
