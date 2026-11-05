# Tasks

## 1. Configuración y dependencias

- [x] 1.1 Añadir `openai` a las dependencias con `uv add openai`. Verificación: `uv run python -c "import openai"` termina sin error y `uv.lock` cambia.
- [x] 1.2 Ampliar `common/config.py` con `MODEL_MAX_RETRIES` (por defecto 3), `MODEL_TIMEOUT_SECONDS` (por defecto 120) y `MODEL_TEMPERATURE` (por defecto 0). Añadir también `EMBEDDING_MODEL` (por defecto `BAAI/bge-small-en-v1.5`) y `EMBEDDING_DEVICE` (por defecto `cuda`; se cambia a `cpu` si la máquina no tiene GPU), que usará el RAG más adelante. Verificación: una prueba comprueba los valores por defecto y la lectura desde el entorno.
- [x] 1.3 Actualizar `.env.example` y `.env` con esas variables y con el valor `none` de `DEEPSEEK_REASONING_EFFORT`, y añadir `results/**/llamadas*.jsonl` a `.gitignore`. Verificación: `git check-ignore results/dev/llamadas.jsonl` y `git check-ignore results/corrida1/llamadas.jsonl` los reportan como ignorados y la prueba de `.env.example` sigue pasando.

## 2. Cálculo de costo

- [x] 2.1 Crear `common/costo.py` con el cálculo de costo a partir de tokens y tarifas, y la detección de hora pico por fecha UTC. Verificación: pruebas con ejemplos numéricos fijos (incluida una llamada dentro y otra fuera de hora pico, y el lunes frente al domingo).

## 3. Cliente del modelo

- [x] 3.1 Crear `common/modelo.py` con el cliente: envío de mensajes, `extra_body` para el razonamiento, lectura de `usage` con valores por defecto y objeto de respuesta con las métricas. Verificación: pruebas con un cliente falso que devuelve una respuesta fija y comprueban texto, tokens, segundos y costo.
- [x] 3.2 Añadir el registro JSONL con los mensajes enviados, la respuesta recibida y una huella del contenido. Verificación: una prueba lee el archivo creado, comprueba una línea por llamada y que contiene los mensajes y la respuesta tal cual.
- [x] 3.3 Añadir el tope de gasto acumulado. Verificación: una prueba con tope pequeño comprueba que la llamada que lo supera lanza el error y que el cliente falso no recibe esa llamada.
- [x] 3.4 Añadir reintentos con espera creciente para errores transitorios y falla inmediata para los demás. Verificación: pruebas con un cliente falso que falla una vez con 429 y luego responde, y otro que devuelve 401 y no reintenta (la espera se sustituye en la prueba para que no tarde).
- [x] 3.5 Garantizar que la clave no aparece en errores, registros ni `repr`. Verificación: una prueba provoca un error con una clave conocida y comprueba que no aparece en el mensaje ni en el archivo de registro.

## 4. Prueba real manual

- [x] 4.1 Crear `scripts/probar_modelo.py`, que hace una llamada real mínima y muestra las métricas. Verificación: tras la aprobación del usuario, se ejecuta una vez, devuelve respuesta y el costo estimado es menor que 0,01 USD.

## 5. Cierre

- [x] 5.1 Ejecutar `uv run ruff check . && uv run ruff format --check . && uv run pytest`. Verificación: sin errores y con todas las pruebas en verde.

## Workflow follow-up

- Contrastar el costo estimado con `GET /user/balance` antes y después de la primera corrida mayor (costo estimado de al menos 0,05 USD), porque la API informa el saldo con dos decimales y una llamada mínima no lo mueve. Anotar el resultado en `docs/decisiones/0001-modelo-unico-deepseek-flash.md`.
