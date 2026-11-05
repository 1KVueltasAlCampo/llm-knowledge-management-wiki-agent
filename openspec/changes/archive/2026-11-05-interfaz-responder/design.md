# Design

## Context

- El plan de trabajo fijó el contrato así: `responder(pregunta) → {respuesta, fuentes,
  tokens_entrada, tokens_salida, segundos}`.
- `ClienteModelo.generar` ya devuelve una `Respuesta` con tokens (con y sin caché, de salida y de
  razonamiento), segundos, dólares e intentos. Un brazo puede hacer una o varias llamadas por
  pregunta; el wiki probablemente haga varias.
- Las fuentes son lo que permitirá medir fundamentación: se comparan con la fuente esperada de
  cada pregunta, que también es un identificador de arXiv.

## Goals / Non-Goals

**Goals:**
- Un contrato pequeño que el RAG y el wiki cumplan sin esfuerzo y que el arnés pueda leer sin
  conocer el brazo.
- Que el costo de una pregunta incluya todas las llamadas que se hicieron para ella.

**Non-Goals:**
- No se implementa ningún brazo ni el arnés.
- No se define el formato del JSONL de resultados completo (pregunta, juez, métricas de calidad):
  eso pertenece al cambio del arnés. Aquí solo se garantiza que la parte del brazo es
  serializable.
- No se registran fragmentos ni secciones dentro de las fuentes. Si hace falta más detalle para
  medir fundamentación, se añade después como campo nuevo.

## Decisions

1. **`Protocol` en lugar de clase base.** Un `Protocol` con `nombre` y `responder` obliga a lo
   mínimo y no ata a los brazos a una jerarquía. Alternativa descartada: clase abstracta, porque
   exigiría que Juan Diego herede de ella al iterar los brazos.
2. **`ResultadoBrazo` como `dataclass` inmutable y validada en `__post_init__`.** Así un resultado
   inválido no llega al arnés. Alternativa descartada: diccionario libre, porque los errores de
   un campo se descubrirían al calcular métricas, lejos de donde se originan.
3. **`tokens_entrada` suma los tokens con y sin caché.** Para comparar contexto leído por
   pregunta importa el total; el costo en dólares ya refleja la diferencia de precio. Los
   tokens de razonamiento no se separan: con el razonamiento desactivado por defecto son cero y,
   si se activan, ya van incluidos en los de salida que cobra la API.
4. **Se añaden `usd` y `llamadas` a los cinco campos del plan.** El costo es una de las métricas
   comparadas y la constitución exige registrarlo; el número de llamadas distingue un brazo de
   una llamada de uno de varias.
5. **Constructor auxiliar `desde_llamadas`.** Recibe la respuesta, las fuentes, las `Respuesta`
   del cliente del modelo y los segundos, y hace la suma. Así RAG y wiki no repiten la
   aritmética.
6. **Las fuentes son identificadores de arXiv sin versión.** El corpus identifica cada paper por
   su identificador; la versión ya está dentro del Gold.

## Risks / Trade-offs

- **Si el wiki necesita citar páginas del wiki y no papers**, la lista de identificadores de
  arXiv quedaría corta. Mitigación: el wiki debe rastrear cada afirmación hasta el paper
  (procedencia por afirmación, ya prometida en el anteproyecto); si no, se amplía el contrato
  con un cambio nuevo.
- **Segundos medidos por el propio brazo.** Cada brazo debe cronometrar de principio a fin. Se
  deja `desde_llamadas` recibiendo los segundos para que el arnés pueda medirlos por fuera si
  prefiere.
