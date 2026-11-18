# Eficiencia: calidad frente a costo y tiempo

Análisis del 18 de noviembre de 2026 (rúbrica R.6.2 Cr6 y R.7.2 Cr5). Todas las cifras salen de resultados
guardados; el único gasto nuevo fue una corrida de 0,068 USD (apartado 5). Se reproduce con
`uv run python scripts/costo_calidad.py` (sin gasto). Salidas en `results/costo-calidad/`.

## 1. Construir el wiki cuesta una sola vez

Procedencia: `results/construccion-1/ingesta.log` (100 papers, 461 páginas).

| | Wiki | RAG |
|---|--:|--:|
| Costo de construir con 100 papers | **1,60 USD** | 0 USD (embeddings locales) |
| Tiempo de construir | **1,8 h** | 2 a 4 min |
| Papers 1–10 | 0,008 USD y 28 s por paper | |
| Papers 11–33 | 0,012 USD y 46 s por paper | |
| Papers 34–66 | 0,017 USD y 58 s por paper | |
| Papers 67–100 | 0,020 USD y 58 s por paper | |

El costo por paper crece al hacerlo el wiki, porque cada ingesta lee y reescribe páginas ya existentes (de
0,0045 a 0,0254 USD entre el primero y el último). Curvas acumuladas:
`results/costo-calidad/ingesta_usd_acumulado.svg` y `ingesta_minutos_acumulados.svg`. La corrida de Juan Diego
(`ampliado-1`, otra construcción del mismo wiki) registró 2,89 USD y 1,8 h, así que el costo de construir
queda **entre 1,6 y 2,9 USD** según la corrida (precio de la hora, aciertos de caché).

## 2. Responder una pregunta (paso 100, 100 preguntas)

Procedencia: `results/ampliado-fases-1` (la misma corrida de las métricas principales).

| | RAG | Wiki |
|---|--:|--:|
| Respuestas correctas (de 100, con abstenciones) | 56 | **75** |
| Costo por consulta | 0,000135 USD | 0,000962 USD (**7,2×**) |
| Tiempo medio (mediana) | 1,5 s (1,4) | 6,1 s (4,8) (**4,1×**) |
| Tokens de entrada por consulta | 1.420 | 10.595 |
| Costo por respuesta correcta | 0,00024 USD | 0,00128 USD |

El wiki acierta 19 respuestas más de cada 100. Atender esas 100 preguntas cuesta 0,083 USD más que con el
RAG: unos **0,004 USD por respuesta correcta adicional**, sin contar la construcción. El sobrecosto viene
de leer páginas completas (10.595 tokens frente a 1.420) y de dar varias vueltas al agente.

En los pasos 33 y 66 el RAG acierta más o parecido (0,83 y 0,67 frente a 0,77 y 0,70) porque entonces la
mayoría de las preguntas no se pueden responder aún y ambos se abstienen; la ventaja del wiki aparece cuando
el corpus completo está cargado y crece con él.

## 3. Cuántas consultas hacen falta

Con el corpus completo, sumando la construcción al wiki (1,60 USD y 1,8 h):

| Consultas atendidas | RAG: USD total / por correcta | Wiki: USD total / por correcta |
|--:|--:|--:|
| 100 | 0,01 / 0,00024 | 1,70 / 0,0227 |
| 1.000 | 0,13 / 0,00024 | 2,57 / 0,0034 |
| 10.000 | 1,35 / 0,00024 | 11,22 / 0,0015 |

**El wiki nunca empata con el RAG en costo**, porque cada consulta suya cuesta más (`scripts/punto_de_equilibrio.py`
da «nunca» en todos los pasos). Lo que sí ocurre es que la construcción deja de pesar: el costo por
respuesta correcta baja de 0,023 a 0,0015 USD, unas **6 veces el del RAG** con 10.000 consultas. La eficiencia
se debe presentar como una decisión de calidad frente a costo: 19 puntos más de aciertos por unas 6 a 7 veces
el costo por respuesta.

## 4. Dónde se gasta en una consulta del wiki

Procedencia: `results/ampliado-fases-1/trazas.jsonl` y `evaluados.jsonl`, 300 consultas del wiki.

| Acciones del agente | Consultas | Parte del costo | Respuestas correctas |
|---|--:|--:|--:|
| 2 | 131 (44 %) | 28 % | 90 de 131 (69 %) |
| 3 | 33 | 10 % | 23 de 33 (70 %) |
| 4 | 21 | 9 % | 10 de 21 (48 %) |
| 5 a 8 | 114 (38 %) | 53 % | 99 de 114 (87 %) |

Las consultas largas cuestan más y son las que más aciertan: recortar el número de acciones debería
costar exactitud. Se comprobó con una corrida real (apartado 5).

## 5. Experimento: tope de 4 acciones en lugar de 8

Corrida `ampliado-wiki-tope4` (wiki del paso 100, mismas 100 preguntas, mismo modelo y wiki reutilizado de
`construccion-1`; `--max-acciones 4`). Costo: 0,068 USD (el juez no hizo falta: la capa determinista decidió
todo).

| | Wiki, 8 acciones | Wiki, 4 acciones | RAG |
|---|--:|--:|--:|
| Respuestas correctas | 75 | **72** | 56 |
| Costo en 100 consultas | 0,0962 USD | **0,0682 USD (−29 %)** | 0,0135 USD |
| Costo por respuesta correcta | 0,00128 USD | **0,00095 USD (−26 %)** | 0,00024 USD |
| Tiempo medio | 6,1 s | 5,7 s | 1,5 s |
| Tokens de entrada | 10.595 | 6.888 | 1.420 |

Con 4 acciones se pierden 3 respuestas (y no se gana ninguna): con 3 contra 0 discordantes la diferencia no es
significativa (prueba exacta de McNemar, p = 0,25), pero tampoco hay evidencia de que sea gratis. El wiki con
tope sigue 16 respuestas por encima del RAG y baja su sobrecosto de 7,2× a 5,1×. Ese recorte no cierra la
brecha: el costo grueso está en leer páginas enteras, no en el número de vueltas.

## Límites

- **Una repetición, temperatura 0 y 100 preguntas:** las diferencias de 3 respuestas no son concluyentes.
- **Costos en dólares:** el precio sale de la tarifa declarada (0,15 / 0,003 / 0,60 USD por millón de
  tokens) y la caché de prefijos de DeepSeek los distorsiona; los tokens y el tiempo son más estables.
  No se aplicó el recargo de hora pico.
- **La construcción viene de otra corrida** que las consultas (1,60 USD de `construccion-1`, 2,89 USD de
  `ampliado-1`); por eso se da un rango.
- **Tiempo:** depende de la carga de la API ese día (una ingesta tardó 688 s por un reintento).
- **Exactitud** cuenta como correctas las abstenciones debidas, por eso mezcla pasos con distintas
  preguntas respondibles.
