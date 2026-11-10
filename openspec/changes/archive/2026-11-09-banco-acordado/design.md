# Design

## Context

Cada mitad del banco la revisan los dos autores con la página de revisión, que exporta una decisión por pregunta (aceptar, corregir o descartar). `aplicar-revision` ya transcribe la revisión del autor de la mitad y deja `verificado_a` o `verificado_b`; el estado `acordado` quedaba para una persona (regla 11: el código crea borradores y nunca cambia su estado).

## Decisions

1. **La orden informa por defecto y escribe solo con `--ejecutar`.** El paso a `acordado` es una decisión de los autores; el código la transcribe y deja su fecha y la medida del acuerdo.
2. **Acuerdo en «aceptar o ajustar».** Se compara si cada autor aceptó la pregunta tal cual o pidió un cambio (corregir y descartar cuentan igual), sobre las preguntas que ambos decidieron. Cohen kappa corrige el azar; con pocas correcciones puede ser bajo aunque el porcentaje sea alto.
3. **Versiones distintas del texto.** Cada autor decide sobre la versión que tiene delante, y la revisión del segundo suele ser posterior a las correcciones del primero. Por eso la cifra se acompaña de una nota en el resumen, y las discrepancias de fondo se documentan en la bitácora.
4. **Pendientes explícitos.** Una pregunta que un autor no ha leído se pasa con `--pendientes` y no se acuerda; así la corrida por defecto solo usa preguntas acordadas por ambos.

## Risks / Trade-offs

- El kappa sobre pocas categorías y pocos desacuerdos es inestable: se reporta junto al porcentaje y a la lista de discrepancias, no solo.
- `--pendientes` depende de que la persona los nombre: la orden no puede saber quién leyó qué fuera de las revisiones.
