# Design

## Context

Medido el 5 de noviembre de 2026 sobre los 5 archivos Gold:

- Hay 84 secciones `##`. Su tamaño (aproximado, caracteres entre 4) tiene mediana de entre 500 y
  1.100 tokens según el paper, percentil 90 de unos 2.300 y máximo de unos 6.400.
- `BAAI/bge-small-en-v1.5` lee como máximo **512 tokens** por texto y trunca el resto en
  silencio. Si se indexara cada sección entera, buena parte de cada sección larga (y las
  ecuaciones de HippoRAG 2) no influiría en la búsqueda.
- La decisión 0002 midió 46 fragmentos por segundo en la GPU de 4 GB con fragmentos de unos 500
  tokens, y fijó `EMBEDDING_DEVICE=cuda` por defecto.
- El tutor pidió: RAG simple, LangChain, base de datos vectorial, mismo modelo que el wiki.
- El contrato `Brazo` y el cliente único del modelo ya existen.

## Goals / Non-Goals

**Goals:**
- Un RAG que se pueda leer de principio a fin en una tarde y que Juan Diego pueda modificar pieza
  por pieza (fragmentación, `k`, prompt).
- Que ninguna parte del texto indexado se pierda por truncamiento.
- Que todo el comportamiento se pueda probar sin red, sin GPU y sin descargar modelos.

**Non-Goals:**
- Reordenamiento, búsqueda híbrida, reescritura de preguntas, memoria entre preguntas.
- Afinar `k`, el tamaño de fragmento o el prompt: son los valores de partida para iterar.
- Generar el archivo de preguntas o el arnés.

## Decisions

1. **Fragmentos de hasta 400 tokens del propio modelo de embeddings.** Se mide con el tokenizador
   de bge, no con la aproximación de caracteres, porque las ecuaciones en LaTeX gastan muchos más
   tokens por carácter que la prosa. 400 deja margen bajo el límite de 512 para el título y la
   sección que se anteponen. El máximo y el solapamiento son parámetros.
2. **Primero `##`, luego párrafos.** Respeta la frontera que el contrato del Gold ya declara y solo
   subdivide lo que no cabe. Se usa `RecursiveCharacterTextSplitter` de `langchain-text-splitters`
   con separadores `\n\n`, `\n`, `. ` y espacio, y como medida de longitud el tokenizador de bge.
   Alternativa descartada: partir todo el texto por tamaño fijo, que ignoraría las secciones.
3. **Cada fragmento empieza con «Título — Sección».** Un fragmento de la mitad de una sección larga
   queda así autocontenido, que es lo que pide el contrato del Gold. Ese prefijo cuenta dentro de
   los 400 tokens.
4. **Chroma en disco (`data/chroma/`) con huella del Gold.** Es la base vectorial más sencilla de
   LangChain y no exige un servicio. Se guarda en los metadatos de la colección una huella del
   contenido de todos los Gold; si coincide, se reutiliza el índice; si no, se borra la colección
   y se reconstruye. Reconstruir 5 papers tarda segundos, así que no se complica con
   actualizaciones parciales. Alternativas descartadas: FAISS (no guarda metadatos con la misma
   facilidad) y una base en memoria (haría reindexar en cada ejecución).
5. **Similitud coseno.** Los embeddings de bge se normalizan y la colección usa distancia coseno.
6. **`k = 5` por defecto.** Con fragmentos de hasta 400 tokens son unos 2.000 tokens de contexto,
   lo bastante para una respuesta y barato. Es el primer valor que Juan Diego puede mover.
7. **Una sola llamada, prompt en español, pregunta y fragmentos en su idioma.** El sistema indica:
   responder solo con el contexto, citar con `[id]`, y decir «El corpus no contiene esta
   información» si no la encuentra. Esto implementa la regla 3 de la constitución (la respuesta
   correcta sale del corpus, no del mundo).
8. **Las fuentes son las citadas, no las recuperadas.** Con `k = 5` casi siempre se recuperan 2 o
   3 papers aunque la respuesta solo use uno; contarlos todos haría que el RAG pareciera citar
   más de lo que usó y no mediría fundamentación. Se extraen con la expresión `\[(\d{4}\.\d{4,5})\]`
   y se filtran contra los recuperados para ignorar identificadores inventados. Alternativa
   descartada: devolver siempre los recuperados, que es más simple pero infla las fuentes.
9. **El embedding de la pregunta no lleva instrucción de consulta.** La versión 1.5 de bge rinde
   bien sin el prefijo de instrucción; se prueba más adelante si hace falta.
10. **PyTorch CUDA desde el índice `cu126` solo en Windows y Linux.** El mismo paquete funciona en
    CPU, así que quien no tenga GPU instala lo mismo y pone `EMBEDDING_DEVICE=cpu`. En macOS se
    usa el paquete por defecto.

## Risks / Trade-offs

- **Descarga de unos 3 GB de PyTorch.** Está aceptado en la decisión 0002. Se mide en la primera
  instalación.
- **La API de `langchain-huggingface` y `langchain-chroma` cambia entre versiones.** Se fijan las
  versiones resueltas en `uv.lock`, y las pruebas con embeddings falsos detectan roturas pronto.
- **Chroma 1.x arrastra muchas dependencias.** Se acepta por simplicidad; si molestara, la
  interfaz de índice es lo bastante pequeña para cambiarla.
- **Filtro de citas frágil.** Si el modelo cita con otro formato (`(2405.14831)`), las fuentes
  quedarían vacías. El prompt fija el formato y la verificación real lo comprueba; si falla con
  frecuencia se endurece el prompt o el analizador.
- **Fragmentos que mezclan tablas.** Una tabla grande se parte por filas y pierde su encabezado.
  Se acepta en esta versión y se anota para iterar.
