# model-call Specification

## Purpose
Define cómo el proyecto llama al modelo de lenguaje único (DeepSeek V4.1 Flash) y qué métricas, registros y límites de gasto acompañan a cada llamada, para que RAG y wiki sean comparables.

## Requirements

### Requirement: Single model entry point
El sistema SHALL ofrecer un único punto de entrada para enviar mensajes de chat al modelo configurado en `DEEPSEEK_MODEL` y devolver el texto de la respuesta junto con sus métricas de uso. Ninguna otra parte del código SHALL llamar a la API del modelo directamente.

#### Scenario: Llamada exitosa
- **WHEN** se envía una lista de mensajes de chat
- **THEN** se devuelve el texto generado y las métricas de la llamada (sección de métricas)

#### Scenario: Modelo tomado de la configuración
- **WHEN** `DEEPSEEK_MODEL` tiene un valor
- **THEN** la llamada usa exactamente ese modelo y el nombre queda en el registro

### Requirement: Usage metrics per call
Cada llamada SHALL reportar tokens de entrada con y sin caché, tokens de salida, tokens de razonamiento, segundos de duración y costo estimado en dólares, calculado con las tarifas configuradas.

#### Scenario: Cálculo del costo
- **WHEN** una llamada usa 1.000 tokens de entrada sin caché y 500 de salida a tarifa normal
- **THEN** el costo estimado es el producto de esos tokens por las tarifas por millón configuradas

#### Scenario: Tarifa de hora pico
- **WHEN** la llamada ocurre en horas pico (lunes a viernes, 01:00–04:00 y 06:00–10:00 UTC)
- **THEN** el costo estimado se calcula al doble de la tarifa normal

### Requirement: Call log
El sistema SHALL añadir una línea JSON por llamada a un archivo de registro, con marca de tiempo, etiqueta del llamador (por ejemplo `rag`, `wiki`, `juez`), modelo, modo de razonamiento, métricas, resultado (`ok` o error), el texto completo de los mensajes enviados y el texto completo de la respuesta recibida, para poder observar y depurar cada llamada. Como esos textos pueden contener fragmentos de papers, los registros de llamadas SHALL NOT versionarse en Git.

#### Scenario: Registro de una llamada exitosa
- **WHEN** termina una llamada correcta
- **THEN** se añade una línea con sus métricas, `ok`, los mensajes enviados y la respuesta recibida

#### Scenario: Registros fuera de Git
- **WHEN** se crea un registro de llamadas en cualquier carpeta de resultados
- **THEN** Git lo ignora

#### Scenario: Registro de una llamada fallida
- **WHEN** una llamada falla tras agotar los reintentos
- **THEN** se añade una línea con el tipo de error, los mensajes enviados y sin texto de respuesta

### Requirement: Spend cap
El sistema SHALL mantener el gasto acumulado de la corrida y SHALL negarse a hacer una nueva llamada cuando ese gasto alcance `MAX_USD_PER_RUN`, indicando el motivo.

#### Scenario: Tope alcanzado
- **WHEN** el gasto acumulado es igual o mayor que `MAX_USD_PER_RUN`
- **THEN** la siguiente llamada lanza un error de tope de gasto y no contacta a la API

### Requirement: Reasoning mode control
El modo de razonamiento SHALL controlarse con `DEEPSEEK_THINKING` (`enabled` o `disabled`) y `DEEPSEEK_REASONING_EFFORT`. Por defecto SHALL estar desactivado, y en ese caso la temperatura configurada SHALL aplicarse a la llamada.

#### Scenario: Razonamiento desactivado
- **WHEN** `DEEPSEEK_THINKING` es `disabled`
- **THEN** la llamada pide explícitamente desactivar el razonamiento y no se reportan tokens de razonamiento

### Requirement: Transient error handling
Ante errores transitorios (límite de solicitudes, errores del servidor o agotamiento de tiempo) el sistema SHALL reintentar con espera creciente hasta un máximo configurable. Ante errores no transitorios (por ejemplo, credencial inválida) SHALL fallar de inmediato.

#### Scenario: Error transitorio que se recupera
- **WHEN** la API responde con un error transitorio y el siguiente intento tiene éxito
- **THEN** se devuelve la respuesta y el registro refleja el número de intentos

#### Scenario: Credencial inválida
- **WHEN** la API rechaza la clave
- **THEN** se lanza un error inmediato sin reintentos

### Requirement: Secret protection
La clave de la API SHALL NOT aparecer en registros, mensajes de error ni representaciones de texto de ningún objeto del sistema.

#### Scenario: Error con clave configurada
- **WHEN** ocurre un error durante una llamada
- **THEN** ni el mensaje de error ni el registro contienen la clave
