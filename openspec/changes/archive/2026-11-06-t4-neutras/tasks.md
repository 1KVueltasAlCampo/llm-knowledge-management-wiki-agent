# Tasks

## 1. Redactor y validación

- [x] 1.1 Añadir `PATRON_ORDEN` a `banco.py` y hacer que `validar_banco` marque las T4 con `respuesta_por_paso` que mencionen el orden o tengan `respuesta_clave` vacía. Verificación: pruebas con una T4 válida, una con `earlier` y una sin claves.
- [x] 1.2 Cambiar la instrucción de T4 en `redaccion.py` (un solo dato, redacción neutra, `answer_before_keys`) y hacer que `interpretar` descarte las T4 que mencionen el orden o no traigan la respuesta previa con claves, y use esas claves como `respuesta_clave`. Verificación: pruebas con un borrador completo y con uno por cada motivo de descarte; el T4 completo pasa `validar_banco`.

## 2. Métrica de obsolescencia

- [x] 2.1 Marcar `obsoleta` y `tras_cambio` en `evaluar_resultados` y añadir `obsoletas` y `tasa_obsoleta` a `agregar`. Verificación: pruebas con el valor viejo en el paso del cambio, el mismo antes del cambio y el valor nuevo.

## 3. Aviso y cierre

- [x] 3.1 Anotar el cambio en `docs/bitacora-datos.md`. Verificación: la entrada nombra los archivos tocados y por qué.
- [x] 3.2 Ejecutar `uv run ruff check . && uv run ruff format --check . && uv run pytest` y `openspec validate t4-neutras`. Verificación: todo termina sin errores.
