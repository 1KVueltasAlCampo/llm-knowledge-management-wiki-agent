# Proposal

## Why

El RAG y el agente wiki los va a construir una persona y a iterar otra, y el arnés de comparación
tiene que poder llamar a los dos sin saber cómo funcionan por dentro. Si cada brazo devuelve las
cosas a su manera, las métricas no son comparables y el arnés se llena de casos especiales. Hace
falta fijar antes de escribir los brazos qué recibe y qué devuelve cada uno.

## What Changes

- Se define una interfaz común, `Brazo`: un objeto con un `nombre` y un método
  `responder(pregunta)` que devuelve siempre un `ResultadoBrazo`.
- `ResultadoBrazo` contiene la respuesta, las fuentes (identificadores de arXiv), los tokens de
  entrada y de salida, los segundos, el costo en dólares y el número de llamadas al modelo,
  sumados sobre todo lo que el brazo hizo para esa pregunta.
- El resultado se valida al crearse y se convierte en un diccionario listo para escribirse en el
  JSONL de resultados.
- Se documenta el contrato en `specs/interfaz-responder.md`, para que Juan Diego lo lea sin
  entrar a OpenSpec.

## Capabilities

### New Capabilities
- `arm-interface`: contrato común que cumplen el brazo RAG y el brazo wiki, y que consume el
  arnés de comparación.

### Modified Capabilities

## Impact

- Código nuevo en `src/wikillm/common/responder.py` y sus pruebas.
- Archivo nuevo `specs/interfaz-responder.md`.
- No llama al modelo ni a la red: no gasta saldo.
- No se implementa ningún brazo ni el arnés; solo el contrato que ellos van a cumplir.
