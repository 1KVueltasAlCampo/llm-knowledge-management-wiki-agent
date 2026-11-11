# 0001. Modelo único: DeepSeek V4.1 Flash

**Fecha:** 4 de noviembre de 2026. **Estado:** vigente.

## Decisión
RAG, wiki y juez usan `deepseek-flash` (DeepSeek-V4.1-Flash) por la API de DeepSeek, con el modo
de razonamiento desactivado por defecto.

## Por qué
- El tutor pidió el mismo modelo en ambos sistemas para que la comparación sea justa, y
  recomendó este.
- **No hay uno más barato dentro de DeepSeek.** `GET /models`, consultado con la clave real el
  4-nov-2026, devuelve solo `deepseek-flash` y `deepseek-v4-pro`. Pro cuesta más de tres veces
  más. Los nombres antiguos de Flash están retirados y se cobran al precio de Flash.
- Tarifas oficiales (USD por millón de tokens, fuera de pico): entrada sin caché 0,15; con
  caché 0,003; salida 0,60. En hora pico cuestan el doble. Hora pico: lunes a viernes,
  01:00–04:00 y 06:00–10:00 UTC (en Colombia: 8–11 pm y 1–5 am).
- Contexto de 1.048.576 tokens y hasta 393.216 de salida.

## Razonamiento desactivado
La API activa el razonamiento por defecto, lo que aumenta tokens de salida, costo y latencia, y
anula la temperatura. Se envía `thinking: {"type": "disabled"}`.

## Primera llamada real (4-nov-2026)
Respuesta correcta en 1,5 s con 14 tokens de entrada y 1 de salida: costo estimado 0,0000054
USD. El saldo (10,00 USD) no cambió visiblemente porque la API lo informa con dos decimales;
la comparación entre costo estimado y saldo se hará en la primera corrida mayor.

## Consecuencias
- Las llamadas pasan siempre por `wikillm.common.modelo.ClienteModelo`.
- El gasto de cada corrida se limita con `MAX_USD_PER_RUN`.

## Alternativas consideradas (añadido el 10-nov-2026)

La decisión nació de la petición del tutor (mismo modelo en ambos sistemas, el que él
recomendó). Esta tabla deja por escrito por qué las alternativas disponibles no la cambian. Las
tarifas son las consultadas en las decisiones 0001 y 0003; no se consultaron tarifas de otros
proveedores porque no se evaluaron como respondedores.

Criterios: (1) un solo modelo para los dos sistemas, (2) contexto amplio, porque la ingesta lee
un paper y revisa varias páginas del wiki, (3) obedecer el formato JSON de salida, (4) costo
predecible, con descuento por caché (el agente del wiki reenvía su historial en cada turno) y
(5) que la corrida completa quepa en el saldo.

| Alternativa | Entrada / salida (USD por millón) | Veredicto |
|---|---|---|
| `deepseek-flash` (elegida) | 0,15 (0,003 con caché) / 0,60 | Contexto de 1.048.576 tokens, JSON estable en las pruebas y descuento de caché que en las mediciones cubre el 72–87 % de la entrada. Corrida estimada en 1–2,5 USD, con cota alta de 4,67 USD. |
| `deepseek-v4-pro` | más de 3 veces Flash | Descartada como respondedora: la cota alta pasaría de 14 USD, más que el saldo. Se usa solo para redactar borradores (decisión 0003). |
| `gemini-3.1-flash-lite` | 0,25 / 1,50 | Es el juez. Como respondedora costaría más por token y rompería la independencia entre quien responde y quien juzga (decisión 0003). |
| `gemini-3.8-flash` | 0,75 / 3,75 | Descartada: el 6-nov devolvió errores 500 y cortó el JSON (decisión 0003). |
| Modelos comerciales grandes (Claude, GPT) | no consultadas | No evaluados: exigirían rehacer la ingesta y no caben en el saldo con margen para repetir. |
| Modelo abierto local (Qwen, Llama) | sin costo por token | No evaluado: ventana de contexto menor y menos garantías de formato, a cambio de privacidad. Queda como trabajo futuro. |

**Límite.** El experimento mide arquitecturas con un modelo, no modelos. No se comparó la
calidad de otros modelos como respondedores, y la conclusión no se extrapola a ellos.
