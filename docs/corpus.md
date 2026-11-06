# Selección del corpus (50 papers)

**Estado:** criterios fijados el 6-nov-2026; la lista final está en `data/corpus_ids.txt` y los
metadatos en `data/manifest_corpus.jsonl`. Reproducir:

```bash
uv run python -m wikillm.corpus candidatos   # metadatos de la API de arXiv (.bib + búsquedas)
uv run python -m wikillm.ingest              # Bronze → Silver → Gold de data/corpus_ids.txt
uv run python -m wikillm.corpus manifest     # orden de ingesta, mitad, señales
uv run python -m wikillm.corpus spans        # fragmentos citables
```

## 1. Fuentes de candidatos

1. **Referencias de arXiv de `docs/estado-del-arte/referencias.bib`**: 61 identificadores. Los
   61 aparecen en la API de arXiv con sus metadatos. Quedan fuera las 4 entradas que no son
   de arXiv: el gist de Karpathy (`karpathy2026`, literatura gris sin texto citable estable),
   el preprint de SciErXiv (`zhang2026pilot`) y dos artículos de revista (`zhang2026lco` en
   *Transactions on Artificial Intelligence* y `zhang2026prov` en *Artificial Intelligence and
   Emerging Technologies*). Los tres de Zhang están como PDF en `papers/` y son muy
   pertinentes (wiki mantenido por LLM), pero solo podrían entrar por PDF, que el pipeline no
   implementa y que da peor extracción. Recomendación: dejarlos fuera del corpus y citarlos en
   el informe; si se quieren dentro, haría falta un plan B de PDF. El gist es el origen del
   patrón y conviene citarlo, pero no como fuente. `2602.16902` (LLM-WikiRace), cuyo PDF está
   en `papers/`, queda fuera porque el estado del arte ya lo excluyó: evalúa planificación sobre
   hipervínculos de Wikipedia, no wikis mantenidos por LLM.
2. **Búsquedas en la API** (`data/consultas_busqueda.txt`) limitadas a papers con primera
   versión desde el 1-ene-2026, para completar los 50 con trabajos del mismo tema.

Los metadatos (título, autores, fechas, versión, categoría, `journal_ref`, DOI) salen siempre
de la API, nunca del `.bib` ni de memoria.

## 2. Criterios

| Criterio | Regla | Por qué |
|---|---|---|
| Posterior al corte | Primera versión desde el **1-ene-2026**; las excepciones se marcan `pre_corte=true`. | El modelo no debe responder de memoria. El corte de DeepSeek-V4.1-Flash **no está publicado** (decisión 0003); un agregador indica mayo de 2025, sin verificar. Enero de 2026 deja más de 7 meses de margen frente a esa cifra, y el control a libro cerrado lo comprueba (§4). |
| HTML disponible | `html_available=true` (captura HTML con estado 200). Si no hay HTML, el paper se excluye y entra el siguiente candidato. | El Gold sale del HTML de LaTeXML; el PDF es un plan B que el pipeline no implementa. No se inventa contenido. |
| Tema | Memoria de agentes, RAG, wikis o compilación de conocimiento con LLM. | Es el estado del arte que los autores conocen, lo que hace viable fijar respuestas a mano. |
| Densidad de citas | Se prefieren los candidatos que citan o son citados por otros del corpus (`referencias_en_corpus`, `citado_por_en_corpus`). | Permite preguntas multi-fuente (T2) y de superación (T3, T4). |
| Resultados que chocan | Se incluyen a propósito pares que se superan o contradicen (p. ej. HippoRAG → HippoRAG 2 → LLM-Wiki; RAG simple frente a wiki compilado; "Naive RAG Is Stronger Than We Thought"). | Mide contradicciones y persistencia del error. |
| Mezcla de calidad | Se registran `senal_codigo`, `estado_publicacion` (`revisado` si hay `journal_ref` o DOI) y la versión. No se filtra por ellos. | Variabilidad realista y análisis por subgrupo. |

**Semillas obligatorias:** 2405.14831 (HippoRAG, 2024) y 2502.14802 (HippoRAG 2, 2025) son
anteriores al corte y entran con `pre_corte=true`. Se reportan aparte y no se usan como única
fuente de preguntas T1. Las otras tres (2605.25480, 2605.18490, 2607.04576) son de 2026.

## 3. Orden, prefijo de 30 y mitades

- **Orden de ingesta:** `fecha_publicacion` (primera versión) ascendente; empate por `arxiv_id`.
- **Mitad:** posición impar → A (Juan Diego), par → B (Juan David). Es reproducible, no
  depende de juicio y da a cada autor la mitad de cualquier prefijo: con las primeras 30
  ingestas cada uno tiene 15 papers.
- **Validez con 30:** las cadenas de contradicción de las semillas caen dentro de las primeras
  30 ingestas, y al menos 20 de las 30 preguntas de cada autor deben tener
  `ingesta_minima ≤ 30`.
- **Preguntas multi-fuente:** pertenecen al autor del paper que entra más tarde, porque ese fija
  `ingesta_minima`.

## 4. Control de contaminación

`uv run python -m wikillm.eval libro-cerrado --ejecutar` pasa el banco al modelo que responde,
sin contexto. Las preguntas que acierta así se reportan como contaminadas y se analizan
aparte. Cuesta centavos (unos 60 × 200 tokens).

## 5. Resultado

Se completa en la sección siguiente al cerrar la selección.
