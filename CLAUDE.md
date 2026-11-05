# Instrucciones para el asistente

Proyecto de maestría: comparación experimental RAG frente a WikiLLM sobre un corpus de arXiv.
Reglas del proyecto: @CONSTITUTION.md

Este archivo es corto a propósito. Se edita a medida que se afinan las preferencias.

## Estilo
- Responder y documentar en español. Los nombres de funciones y variables pueden ir en español
  o en inglés, pero no mezclados dentro de un mismo módulo.
- Python 3.12 con anotaciones de tipo. Líneas de hasta 100 caracteres.
- Comentarios solo cuando expliquen el porqué, no el qué.
- Hacer solo lo que se pidió; no añadir funciones de más.

## Flujo
- Antes de un cambio nuevo, proponerlo con OpenSpec (`/opsx:propose`).
- Antes de dar algo por terminado, ejecutar:
  `uv run ruff check . && uv run ruff format --check . && uv run pytest`
- No hacer commits ni push sin que se pida. Mensajes con prefijo semántico (`feat:`, `fix:`…).

## Seguridad
- No leer, imprimir ni copiar el contenido de `.env`.
- No ejecutar llamadas que gasten saldo de la API sin avisar antes.
