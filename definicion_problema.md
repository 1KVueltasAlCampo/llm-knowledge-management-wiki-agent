> **Nota para revisión (Compañero de equipo):**
> *Este documento es un primer borrador de la Definición del Problema (Entregable 1). Estamos asumiendo un enfoque general (aplicable a cualquier empresa con problemas de fragmentación de conocimiento corporativo). El argumento central asume que el mayor valor de negocio está en: 1) Reducir costos de inferencia (compilar en la ingesta vs. recuperar en cada consulta) y 2) Mejorar la consistencia (mitigando contradicciones). Por favor, confirma si estás de acuerdo con: el caso de uso (forma y contenido), si los argumentos resuenan con la visión técnica que tienes del WikiLLM y si los temas tratados cubren todo lo que queremos exponer.*

---

# Entregable 1: Definición del Problema

## Contexto y Necesidad de Negocio
En el entorno empresarial actual, el conocimiento corporativo —procesos, decisiones técnicas, manuales, políticas— se encuentra altamente fragmentado y sujeto a rápida obsolescencia. Los trabajadores del conocimiento dedican un porcentaje significativo de su jornada buscando información interna, lo que representa una ineficiencia transversal en la industria.

Para mitigar esto, las organizaciones están adoptando asistentes de Inteligencia Artificial basados en sistemas de Recuperación Aumentada por Generación (RAG). Sin embargo, la evaluación sistemática de arquitecturas de recuperación y generación demuestra que los enfoques RAG convencionales y los sistemas de grafos presentan desafíos importantes dependiendo de la naturaleza de la consulta y la actualización del conocimiento (Han et al., 2025). Específicamente, el enfoque RAG tradicional presenta grandes limitaciones a nivel de negocio:

1. **Altos costos operativos (Inferencia por consulta):** En un sistema RAG, el modelo debe recuperar, leer y sintetizar múltiples fragmentos de texto crudo *cada vez* que un usuario hace una pregunta, lo cual resulta redundante computacionalmente (Karpathy, 2026).
2. **Degradación de la coherencia:** Los sistemas recuperan frecuentemente documentos obsoletos o que entran en conflicto con políticas recientes. El intento del LLM de resolver estas contradicciones en tiempo de consulta propaga errores, alucinaciones y deriva en la coherencia (*drift coherence*) de las respuestas institucionales (Myakala, Agrawal & Manche, 2026; Semnani et al., 2023).
3. **Incapacidad de consolidación:** El conocimiento generado no persiste. La empresa no construye un activo a largo plazo, sino un buscador iterativo y volátil.

## Solución Propuesta (WikiLLMs)
Se propone el desarrollo e implementación de un **Agente de Gestión del Conocimiento basado en WikiLLMs**. A diferencia de un RAG clásico, este sistema invierte el orden operativo: utiliza LLMs para **compilar, sintetizar y mantener una base de conocimiento viva** (en formato Markdown interenlazado) de una sola vez durante la ingesta de las fuentes, y no en la consulta.

El agente actúa como un curador autónomo. Al recibir documentos nuevos, los ingiere y efectúa una pasada de validación (*Lint*) detectando contradicciones frente a la base de conocimientos existente, evaluando y retrayendo hechos obsoletos de manera controlada.

## Impacto Esperado y Métricas de Éxito
*   **Reducción de costos de inferencia (Tokens):** Trasladar la carga computacional desde las infinitas *consultas* de los empleados hacia la *fase única de ingesta y mantenimiento*.
*   **Eficiencia operativa:** Disminución drástica del tiempo de búsqueda documental de los empleados al acceder a resúmenes pre-compilados y estructurados.
*   **Calidad de la información:** Mantener alta precisión factual, minimizando la propagación de alucinaciones y obsolescencias a través de una alta *tasa de resolución de contradicciones* en el mantenimiento del corpus.

---

## Referencias
* Han, X., et al. (2025). *Evaluación sistemática de arquitecturas de recuperación y generación de conocimiento* (arXiv:2502.11371). arXiv. https://arxiv.org/abs/2502.11371
* Karpathy, A. (2026). *LLM Wiki: A pattern for knowledge management* [Gist de GitHub]. 
* Myakala, S., Agrawal, A., & Manche, V. (2026). *BeliefShift: Benchmark longitudinal de dinámica de creencias* (arXiv:2603.23848). arXiv. https://arxiv.org/abs/2603.23848
* Semnani, S. J., Yao, Z., Zhang, Z., & Lam, M. S. (2023). *WikiChat: Stopping the Hallucination of Large Language Model Chatbots by Few-Shot Grounding on Wikipedia* (arXiv:2305.14292). arXiv. https://arxiv.org/abs/2305.14292
