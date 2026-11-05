# Design

## Context

El esqueleto ya carga la configuración desde `.env` (`common/config.py`). La API de DeepSeek es
compatible con el protocolo de OpenAI. Datos verificados el 4 de noviembre de 2026 en la
documentación oficial y con `GET /models`:

- Modelos disponibles: `deepseek-flash` y `deepseek-v4-pro`. Se usa solo `deepseek-flash`.
- El razonamiento está activado por defecto. Se desactiva enviando `thinking: {"type": "disabled"}`.
  `reasoning_effort` acepta `none`, `low`, `high` y `max`.
- `temperature` no tiene efecto con el razonamiento activado.
- La respuesta trae `usage` con `prompt_cache_hit_tokens`, `prompt_cache_miss_tokens`,
  `completion_tokens` y `completion_tokens_details.reasoning_tokens`.
- Tarifas (USD por millón, fuera de pico): entrada sin caché 0,15; con caché 0,003; salida 0,60.
  En hora pico cuestan el doble.
- Saldo prepagado de 10 USD: no se puede gastar más de lo recargado, pero el tope por corrida
  evita agotarlo por un error del código.

## Goals / Non-Goals

**Goals:**
- Que RAG y wiki llamen al modelo por el mismo camino y con la misma configuración.
- Medir cada llamada de forma consistente y dejar un registro auditable.
- Poder probar toda la lógica sin gastar saldo.

**Non-Goals:**
- No se implementa recuperación, agente ni evaluación.
- No se soporta otro proveedor ni se elige el modelo por etapa (regla del proyecto: un solo modelo).
- No hay *streaming*, llamadas a herramientas ni caché propia de respuestas.

## Decisions

**1. SDK `openai` con `base_url` de DeepSeek, en lugar de HTTP directo.**
El SDK ya maneja conexiones, tiempos de espera y errores tipados, y LangChain lo usará después
para el RAG. Alternativa descartada: `httpx` manual, que obliga a reimplementar esos errores.
`thinking` se envía en `extra_body`, porque no es un parámetro estándar de OpenAI.

**2. Cliente inyectable.**
La clase del cliente recibe opcionalmente el objeto del SDK. Las pruebas pasan uno falso y
nunca tocan la red.

**3. El costo se calcula con las tarifas de `.env`, con ajuste de hora pico.**
Es una estimación local; no hay un endpoint que devuelva el costo por llamada. La hora pico se
detecta por la hora UTC y no distingue los festivos chinos, así que el valor es una cota
superior. El saldo real puede verificarse con `GET /user/balance`.

**4. Registro JSONL con el texto completo, fuera de Git.**
Por decisión del usuario se guardan siempre los mensajes enviados y la respuesta, para tener
observabilidad total de cada llamada (qué fragmentos recibió el modelo y qué contestó). Se añade
además una huella (SHA-256) del contenido para detectar repeticiones. Como el texto puede incluir
fragmentos de papers de arXiv (licencias propias), los registros de llamadas no se versionan:
`.gitignore` ignora `results/**/llamadas*.jsonl`. El registro de desarrollo va en
`results/dev/`; los resultados derivados (tablas de métricas) sí se versionan.

**5. Reintentos propios, sin librería adicional.**
Un bucle con espera exponencial (1 s, 2 s, 4 s…) sobre los errores 429, 5xx y de tiempo. Es
poco código y fácil de probar. Alternativa descartada: `tenacity`, por añadir una dependencia
para un caso simple.

**6. El tope de gasto vive en el cliente, no en quien lo llama.**
Así ningún brazo puede olvidarlo. El gasto acumulado es por instancia del cliente, es decir, por
corrida.

## Risks / Trade-offs

- [El costo estimado difiere del cobrado] → Contrastar con `GET /user/balance` en la primera
  corrida real y ajustar si hace falta.
- [Nombres de campos de `usage` que cambian] → Leerlos con valores por defecto y registrar un
  aviso si faltan, en lugar de fallar.
- [Las llamadas concurrentes comparten el gasto acumulado] → De momento el uso es secuencial;
  se protege el acumulado con un candado simple.
- [Reintentos que gastan saldo] → Solo se reintentan errores transitorios y se cuentan en el
  registro.
- [Los registros con texto crecen rápido] → Un archivo por corrida y fuera de Git; se pueden
  borrar sin perder resultados, que se derivan a tablas aparte.
