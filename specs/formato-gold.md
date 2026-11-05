# Especificación: formato del corpus (capas Bronze, Silver y Gold)

**Estado:** propuesta v0, para revisión de ambos. Si nadie la objeta, es el contrato.

**Para qué sirve:** que el scraper, el RAG y la wiki se construyan por separado y se
conecten sin tocarse. Todo lo que entra al RAG y a la wiki sale de la capa Gold.

Basada en la arquitectura medallion de la Clase 2 del tutor (págs. 210–218 y 269–276) y en
los campos obligatorios y de procedencia del Open Knowledge Format v0.2 (`type`, `sources`).

---

## 1. Las tres capas

| Capa | Carpeta | Qué contiene | Regla |
|---|---|---|---|
| **Bronze** (crudo) | `data/raw/<arxiv_id>/` | `page.html` tal como lo devolvió arXiv y una línea en `capture.jsonl` con `url`, `fecha`, `status`, `hash`. También se guardan los errores (404, fallos). | Nunca se edita a mano. Si algo sale mal, se reconstruye todo desde aquí. |
| **Silver** (limpio) | `data/processed/<arxiv_id>.md` | Solo el contenido útil del paper en Markdown: sin menús, sin barra de navegación ni bibliografía. | Se puede regenerar desde Bronze sin volver a la web. |
| **Gold** (enriquecido) | `data/gold/<arxiv_id>.md` + `data/gold/corpus.jsonl` | El Silver más un encabezado de metadatos (sección 2). Un archivo por paper. | **Es lo único que leen el RAG y la wiki.** |

Las carpetas `data/raw`, `data/processed` y `data/gold` van en `.gitignore`: los textos
completos de arXiv tienen licencias propias. Se versionan solo `data/corpus_ids.txt` (lista
de identificadores) y `data/gold/corpus.jsonl` (los metadatos, sin el texto).

---

## 2. Encabezado de cada archivo Gold

```yaml
---
type: paper
arxiv_id: "2605.18490"
version: v2
titulo: "Single-Round Vector RAG vs an LLM-Compiled Wiki: A Preregistered Comparison on a Small Multi-Domain Research Corpus"
autores: ["Theodore O. Cochran"]
fecha_publicacion: 2026-05-18
fecha_version: 2026-08-16
categoria: cs.CL
estado_publicacion: desconocido
sources: ["https://arxiv.org/html/2605.18490v2"]
extraccion: html
fecha_captura: 2026-11-10
hash: "sha256:<huella del page.html de Bronze>"
tokens: 14250
idioma: en
referencias_en_corpus: []
---
```

Los valores de `hash` y `tokens` son ejemplos; el scraper los calcula.

| Campo | Obligatorio | Qué significa | Para qué sirve |
|---|---|---|---|
| `type` | Sí | Tipo de documento; aquí siempre `paper`. | Lo exige OKF; permite que la wiki distinga papers de otras páginas. |
| `arxiv_id` | Sí | Identificador del paper. | Clave única: evita duplicados y da nombre al archivo. |
| `version` | Sí | Versión de arXiv que se capturó (`v1`, `v2`…). | Reproducibilidad: dos capturas del mismo paper pueden diferir. |
| `titulo`, `autores` | Sí | Datos bibliográficos. | Citar y mostrar la fuente en las respuestas. |
| `fecha_publicacion` | Sí | Fecha de la primera versión. | **Ordena la ingesta cronológica** y define qué paper es "más reciente" en las preguntas de recencia. |
| `fecha_version` | No | Fecha de la versión capturada. | Distinguir un paper actualizado. |
| `categoria` | Sí | Categoría principal de arXiv. | Filtrar el corpus por tema. |
| `estado_publicacion` | No | `preprint`, `revisado` o `desconocido` (por defecto: arXiv no lo informa de forma fiable). | Señal ligera de respaldo; no entra al ranking. |
| `sources` | Sí | URL exacta de donde sale el texto. | **Trazabilidad:** la métrica de fundamentación comprueba que cada afirmación llegue a una fuente. |
| `extraccion` | Sí | `html` o `pdf`. | Control de calidad: los PDF son el plan B y salen peor. |
| `fecha_captura` | Sí | Día en que se descargó. | Saber qué volver a descargar si arXiv actualiza el paper. |
| `hash` | Sí | Huella del archivo crudo. | Hace la ingesta **idempotente**: si el hash no cambió, no se reprocesa. |
| `tokens` | Sí | Tamaño aproximado del texto en tokens. | Métrica de **eficiencia de contexto** y control de costo. |
| `idioma` | Sí | Idioma del texto. | Filtrar y detectar errores de extracción. |
| `referencias_en_corpus` | No | Identificadores de otros papers del corpus que este cita. | Enlazar páginas en la wiki y comprobar que el corpus está conectado. |

---

## 3. Cuerpo del archivo

- El título va como `#`; las secciones del paper, como `##`. **Los encabezados `##` son las
  fronteras de los fragmentos** que usa el RAG: cada trozo queda autocontenido.
- Las tablas se conservan como tablas de Markdown; las ecuaciones, como LaTeX entre `$…$`.
- Se eliminan: navegación, pie de página, bibliografía y marcadores de figuras sin texto.
  Los pies de figura se conservan.
- Sin HTML dentro del Markdown.

## 4. `corpus.jsonl`

Una línea por paper con los mismos campos del encabezado más `ruta` (ruta del `.md`). Se
genera al terminar el Gold y es lo que se versiona.

## 5. Reglas del scraper (de la Clase 2)

- Leer `robots.txt` y respetar `Disallow`.
- Esperar entre peticiones lo que declare el `Crawl-delay` de `robots.txt` (15 segundos en
  arXiv) y usar un `User-Agent` genérico, sin datos personales.
- Guardar siempre el crudo además del limpio.
- Cada paso debe poder volver a correrse sin repetir los anteriores.

## 6. Cómo se comprueba

- Cada `.md` de Gold tiene encabezado YAML válido con todos los campos obligatorios.
- No hay dos archivos con el mismo `arxiv_id`.
- `tokens` coincide con el cuerpo dentro de un margen del 10 %.
- Volver a correr el scraper sobre el mismo identificador no cambia el `hash`.
