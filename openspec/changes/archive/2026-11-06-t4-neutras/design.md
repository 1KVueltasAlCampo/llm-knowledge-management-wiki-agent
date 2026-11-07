# Design

## Context

- `redaccion.py` pide a T4 que `answer` sea el valor del paper posterior y `answer_before` el del anterior, y en `interpretar` borra `respuesta_clave` del tramo inicial (línea 174). La instrucción no prohíbe nombrar al paper posterior.
- `esperado_en_paso` ya devuelve la respuesta y las claves correctas por paso con `respuesta_por_paso`.
- Medido el 6-nov sobre los 102 borradores de A: 13 de 18 T4 mencionan el orden; las 18 tienen las claves previas vacías; una (A010) tiene un «antes» de otra métrica.

## Decisions

1. **Una lista de palabras de orden compartida.** `PATRON_ORDEN` vive en `banco.py` y la usan el redactor (descarta) y `validar-banco` (señala). Se excluyen «update/updated» a propósito: en este corpus son palabras normales («memory update»).
2. **Las claves previas reemplazan al borrado.** El redactor devuelve `answer_before_keys`; si falta, el borrador se descarta en vez de entrar con claves vacías.
3. **«Obsoleta» se calcula con las claves previas.** Es obsoleta si, desde el primer cambio, el veredicto no es `correcta` y están todas las claves previas. Si la respuesta contiene también el valor nuevo, la capa 1 la da por correcta y no cuenta como obsoleta.
4. **No se regeneran los borradores de A.** Hacerlo costaría ~0,8 USD del saldo de Juan Diego; los T4 defectuosos se arreglan con «Corregir» en la página de revisión.

## Risks / Trade-offs

- **Palabras como «prior» o «original» pueden aparecer en una pregunta legítima.** Se acepta: un falso descarte cuesta una pregunta, y el humano puede corregirla.
- **Sin juez, la obsolescencia solo se detecta por claves.** Una respuesta obsoleta parafraseada sin las cifras exactas no se marca.
