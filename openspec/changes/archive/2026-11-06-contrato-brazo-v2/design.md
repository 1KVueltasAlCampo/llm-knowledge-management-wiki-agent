# Design

## Context

- `specs/contrato-resultados.md` (Juan Diego) fija una línea JSONL por (pregunta, sistema, paso) con `ingest_step`, `abstained`, `citations` como `span_id` y `context_tokens`. `wikillm.eval` calcula las métricas sobre ella.
- Verificado el 6-nov: el Gold local de los 50 papers es idéntico al de Juan Diego (hashes iguales y 8.387 de 8.387 fragmentos iguales), así que los `span_id` de `data/gold/spans.jsonl` valen para nuestro texto.
- Un `span` es un bloque de líneas no vacías del cuerpo (mediana de 361 caracteres; 8 de 8.387 pasan de 6.000, casi todos tablas). `calcular_spans` es determinista.
- Medido con el RAG v1 sobre los 102 borradores de A (k = 5): paper correcto en el top-5 en 78 % de las T1, pasaje exacto en 48 %; en las de dos fuentes, ambos papers solo en ~27 %. Es la línea base que se quiere iterar, no un defecto a esconder.
- La decisión 0004 fija el inglés para prompts, respuestas y wiki.

## Goals / Non-Goals

**Goals:**
- Una interfaz que sirva igual al RAG y al wiki y produzca sin traducciones las líneas que `wikillm.eval` ya sabe leer.
- Citas por `span_id` que la métrica de fundamentación acepte, sin que el RAG pueda inventarlas.

**Non-Goals:**
- Implementar el wiki ni el arnés (cambios aparte).
- Mejorar la recuperación (reordenamiento, `k` distinto, varias consultas): es lo que Juan Diego iterará.
- Cambiar `specs/contrato-resultados.md`; solo se propone `ingestas.jsonl` como añadido.

## Decisions

1. **`ingerir(arxiv_id)` en la interfaz, no un paso dentro de `responder`.** Así el costo de ingerir se mide aparte del de responder (el wiki gasta casi todo al ingerir; el RAG casi nada) y el arnés controla el orden. Alternativa descartada: `responder(pregunta, paso)`, porque obliga a cada brazo a reconstruir su estado en cada llamada.
2. **`ResultadoIngesta` para el costo por ingesta.** El contrato de Juan Diego mide el costo por respuesta pero no por ingesta, que el README promete medir. Se escribe en `results/<corrida>/ingestas.jsonl`; sus agregados los puede añadir `wikillm.eval` después.
3. **`citas` en lugar de `fuentes`, con `fuentes` derivada.** El contrato exige `span_id`. Los identificadores de arXiv se obtienen de las citas, así que no se guardan dos veces.
4. **`tokens_contexto` con `aproximar_tokens` (un token cada 4 caracteres).** Es la misma aproximación del campo `tokens` del Gold, por lo que se compara con la misma regla. La alternativa de usar los tokens reales del proveedor mezclaría el prompt fijo con el contexto.
5. **Una sola frase de abstención, comparada sin mayúsculas, espacios ni puntuación.** `abstained` lo decide un texto exacto y no una interpretación del modelo, igual para los dos brazos. Coincide con la respuesta de referencia de las T5.
6. **El RAG construye sus fragmentos desde los spans.** Así cada fragmento sabe qué `span_id` contiene y el modelo puede citar párrafos concretos. Los spans se agrupan por sección hasta 400 tokens de bge; el rótulo `[span_id]` de cada uno cuenta dentro del presupuesto (unos 12 tokens por span). Alternativa descartada: trocear como en v1 y mapear por posición, que obliga a un cálculo de solapes que puede fallar en silencio.
7. **Ingesta incremental con huella por paper.** `ingerir` añade los fragmentos de un paper y guarda el `hash` de su Gold; si cambia, reemplaza. Reingerir lo igual no cuesta nada. La recuperación filtra por los papers ingeridos en la corrida, así que un índice con los 50 construidos no se filtra a pasos anteriores. Alternativa descartada: construir el índice entero y filtrar por una fecha, porque no mide el costo de ingerir.
8. **Validar las citas contra lo recuperado y contra `spans.jsonl`.** Un `span_id` que el modelo recuerda de otro contexto o inventa se ignora; así la fundamentación mide solo citas verificables (regla 13 de la constitución).
9. **Comprobar el hash del Gold contra `corpus.jsonl` al ingerir.** Si el texto local difiere del que usó Juan Diego (por ejemplo, una versión nueva de arXiv), los `span_id` apuntarían a otro texto; es mejor fallar con un mensaje claro.
10. **Nombres.** En Python (`ResultadoBrazo`, `citas`, `abstuvo`) van en español, como el resto del módulo; las funciones de línea los traducen a los nombres en inglés del contrato (`citations`, `abstained`).

## Risks / Trade-offs

- **Spans muy largos** (tablas de hasta ~24.000 caracteres) se parten en varios trozos con el mismo `span_id`. El modelo puede citar una tabla entera aunque solo use una fila; la fundamentación lo acepta, pero la precisión de la cita es baja. Se acepta en esta versión.
- **Más tokens por fragmento** por los rótulos: baja un poco el texto útil dentro de los 400 tokens y sube el contexto enviado (unos 5 × 3 rótulos). Se mide en la corrida real.
- **El modelo puede citar con otro formato.** El prompt fija el formato y el analizador acepta uno o varios `span_id` por corchete; la corrida real lo comprueba.
- **Cambio incompatible en `ResultadoBrazo`.** Solo lo usa el RAG v1 y sus pruebas, que se actualizan aquí.
