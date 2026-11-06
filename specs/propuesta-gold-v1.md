# Propuesta de cambios al formato Gold (v0 → v1)

**Autor:** Juan Diego. **Estado:** borrador para revisión de Juan David. Nada de esto cambia
`specs/formato-gold.md` hasta que ambos lo acepten.

**Motivo:** el diseño experimental necesita citar fragmentos exactos (métrica de fundamentación),
saber en qué paso de ingesta entra cada paper y dividir el corpus entre los dos autores. El v0
no cubre eso. Todos los cambios son **aditivos**: un lector del v0 sigue funcionando.

## 1. `sources` con versión

**Hoy:** `sources: ["https://arxiv.org/html/2605.18490"]`. Esa URL sirve siempre la última
versión, así que dentro de un mes puede devolver otro texto.
**Propuesta:** `sources: ["https://arxiv.org/html/2605.18490v3"]`, con la versión capturada.

## 2. Fragmentos citables: `data/gold/spans.jsonl` (nuevo, versionado)

Una línea por fragmento (párrafo, celda de tabla agrupada por tabla, pie de figura), calculada
de forma determinista sobre el cuerpo del `.md` Gold:

```json
{"span_id": "2605.18490#s3.p2", "arxiv_id": "2605.18490", "version": "v3",
 "seccion": "3 Method", "tipo": "parrafo", "inicio": 10422, "fin": 11187,
 "sha256": "…"}
```

- `inicio` y `fin` son offsets en caracteres del cuerpo Gold (después del encabezado YAML).
- `sha256` es la huella del texto del fragmento: permite comprobar que la cita sigue apuntando
  al mismo texto sin versionar el texto (regla 8 de la constitución).
- La wiki y el RAG pueden citar `span_id`; la métrica de fundamentación resuelve el `span_id`
  contra el Gold local y verifica la huella.

## 3. Campos nuevos en `corpus.jsonl` (no en el encabezado del `.md`)

| Campo | Qué es |
|---|---|
| `orden_ingesta` | Posición 1..N al ordenar por `fecha_publicacion` (empate: `arxiv_id`). |
| `mitad` | `A` (Juan Diego) o `B` (Juan David): impar → A, par → B según `orden_ingesta`. |
| `html_available` | `true` si `/html/<id>v<n>` respondió 200 con contenido LaTeXML. |
| `pre_corte` | `true` si la primera versión es anterior al 1-ene-2026 (ver `docs/corpus.md`). |
| `senal_codigo` | `true` si el resumen o el cuerpo enlaza a un repositorio de código. |
| `journal_ref`, `doi` | De la API de arXiv; si existen, `estado_publicacion` pasa a `revisado`. |

## 4. Detalles menores

- `fecha_captura` hoy es un timestamp ISO completo y el spec dice fecha. Propuesta: aceptar el
  timestamp (es más preciso) y corregir el spec.
- `estado_publicacion` deja de ser siempre `desconocido`: `revisado` si hay `journal_ref` o DOI
  externo, `preprint` en otro caso. Sigue siendo una señal ligera, no entra al ranking.
