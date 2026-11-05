# Proposal

## Why

Toda la comparación RAG frente a wiki depende de medir tokens, tiempo y costo de cada llamada
al modelo, y de que ambos sistemas usen el mismo modelo con la misma configuración. Hoy no
existe ninguna función que llame a DeepSeek ni que registre esas métricas. Sin ella, cada
brazo (RAG, wiki) mediría por su cuenta y los resultados no serían comparables. Además hay
un saldo prepagado de 10 USD que no debe agotarse por error.

## What Changes

- Se añade un punto único de entrada para llamar al modelo (`deepseek-flash`) con mensajes de
  chat y obtener el texto y las métricas de uso.
- Cada llamada deja una línea en un registro JSONL con tokens, tiempo, costo en dólares y el
  texto completo de lo enviado y lo recibido (observabilidad). Esos registros no se versionan.
- Se impone un tope de gasto por corrida (`MAX_USD_PER_RUN`): al alcanzarlo, no se hacen más
  llamadas.
- El modo de razonamiento ("thinking") se controla desde la configuración y queda desactivado
  por defecto.
- Se añade un script de prueba manual que hace una llamada real mínima.
- Se amplía la configuración con reintentos y tiempo de espera.

## Capabilities

### New Capabilities
- `model-call`: llamar al modelo único del proyecto, con métricas de uso por llamada, registro,
  tope de gasto, control del razonamiento y manejo de errores.

### Modified Capabilities

## Impact

- Código nuevo en `src/wikillm/common/` (cliente del modelo y cálculo de costo).
- Dependencia nueva: `openai` (SDK compatible con la API de DeepSeek).
- Archivos modificados: `pyproject.toml`, `uv.lock`, `.env.example`, `.gitignore` (carpeta de
  registros de desarrollo) y `src/wikillm/common/config.py`.
- Un script nuevo en `scripts/` y pruebas nuevas en `tests/` que no llaman a la API real.
- Los brazos RAG y wiki, y el arnés de comparación, dependerán de este módulo.
