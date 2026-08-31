# llm-knowledge-management-wiki-agent

Proyecto de maestría en Inteligencia Artificial Aplicada sobre **WikiLLMs**: bases de
conocimiento en markdown que un agente LLM construye y mantiene de forma incremental,
como alternativa a recuperar y sintetizar en cada consulta.

## Estado

Fase de fundamentación. Todavía no hay implementación.

## Documentos

- [Estado del arte](docs/estado-del-arte.md) — revisión de literatura, panorama de
  implementaciones, vacíos de investigación y propuesta de encuadre del proyecto.

## Punto de partida

Tres preguntas de investigación candidatas, detalladas en §11 del estado del arte:

1. **Degradación bajo mantenimiento** — cómo evoluciona la calidad de un WikiLLM a lo
   largo de N ingestas incrementales, y qué políticas de mantenimiento la preservan.
2. **Lint como tarea evaluable** — formalizar detección de contradicciones y
   obsolescencia con ground truth, comparando enfoques LLM puro, neuro-simbólico y
   bitemporal.
3. **Frontera compilar vs. recuperar** — bajo qué régimen de consultas, volatilidad y
   costo el WikiLLM supera a RAG y GraphRAG.

La primera es la más defendible en un semestre y la que ataca el vacío más claro de la
literatura: toda la evaluación existente mide artefactos generados de una sola pasada,
ninguna mide qué le pasa a un corpus mantenido en el tiempo.
