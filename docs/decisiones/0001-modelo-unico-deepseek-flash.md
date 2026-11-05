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
