# Tasks

## 1. Resultado del brazo

- [x] 1.1 Crear `common/responder.py` con la `dataclass` inmutable `ResultadoBrazo` (`respuesta`, `fuentes`, `tokens_entrada`, `tokens_salida`, `segundos`, `usd`, `llamadas`) y su validación al crearse. Verificación: pruebas con un resultado válido (con y sin fuentes) y uno por cada incumplimiento: respuesta en blanco, métrica negativa, fuente que no es identificador de arXiv y fuente repetida.
- [x] 1.2 Añadir `a_dict()` que devuelva solo tipos simples con los campos del contrato. Verificación: una prueba lo pasa por `json.dumps` y comprueba el conjunto exacto de claves.
- [x] 1.3 Añadir `desde_llamadas(respuesta, fuentes, llamadas, segundos)` que sume tokens (con y sin caché en la entrada), dólares y número de llamadas de las `Respuesta` del cliente del modelo. Verificación: pruebas con una llamada y con tres, comprobando cada suma.

## 2. Interfaz del brazo

- [x] 2.1 Añadir el `Protocol` `Brazo` (`nombre` y `responder(pregunta)`), comprobable en ejecución. Verificación: un brazo falso de prueba lo cumple; un objeto sin `nombre` o sin `responder` no.
- [x] 2.2 Probar que un brazo falso que usa un `ClienteModelo` con un cliente HTTP falso devuelve el resultado con las métricas sumadas, y que el error de tope de gasto se propaga sin resultado. Verificación: ambas pruebas pasan sin llamar a la API real.

## 3. Documentación del contrato

- [x] 3.1 Escribir `specs/interfaz-responder.md` para Juan Diego: firma, campos con su significado, ejemplo de brazo mínimo y reglas (fuentes, métricas sumadas, errores). Verificación: cada campo de `ResultadoBrazo` aparece descrito y el ejemplo del documento ejecuta sin error.

## 4. Cierre

- [x] 4.1 Ejecutar `uv run ruff check . && uv run ruff format --check . && uv run pytest` y `openspec validate interfaz-responder`. Verificación: todo termina sin errores.
