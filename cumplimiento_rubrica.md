> **Nota para revisión (Compañero de equipo):**
> *Este documento es un primer borrador para justificar el cumplimiento de la rúbrica (Entregable 3). Para alcanzar el nivel "Outstanding", estamos asumiendo un enfoque automatizado sólido para los criterios DevOps/MLOps (R.7.1 y R.7.2): uso de pipelines CI/CD que detonen automáticamente la ingesta y "linting" cuando se suben nuevos documentos, y uso de herramientas automatizadas. Por favor, revisa si este nivel técnico y de forma se ajusta a lo que consideras viable de implementar en el semestre, o si preferirías que atenuáramos la complejidad arquitectónica (ej. algo más manual/local).*

---

# Entregable 3: Cumplimiento de la Rúbrica de Evaluación

Este documento detalla y justifica por qué el proyecto **"Agente de Gestión del Conocimiento basado en WikiLLMs"** cumple con los criterios de evaluación de la Maestría en Inteligencia Artificial Aplicada, alineándose al nivel **Level 4: Outstanding**.

## R.6.1: Implementar modelos de inteligencia artificial generativa para la creación de nuevos productos, servicios o experiencias en diferentes áreas empresariales

*   **Cr1: Formulación del problema y comprensión del contexto (Outstanding):**
    El proyecto formula una necesidad de negocio transversal y estratégica: la ineficiencia y fragmentación del conocimiento interno. Supera el planteamiento genérico al identificar las debilidades reales de las soluciones actuales (sistemas RAG costosos y propensos a contradicciones) y traduce este problema en un producto innovador (un WikiLLM) con métricas de impacto claras (ahorro de tiempo y reducción de costos de inferencia).
*   **Cr2: Argumenta la elección del modelo (Outstanding):**
    La justificación técnica es exhaustiva. Se contrastan las capacidades de los LLMs de frontera frente a las arquitecturas clásicas de recuperación (Vector RAG) y búsqueda en grafos (GraphRAG). Se argumenta la elección del modelo en función de sus capacidades de razonamiento complejas, necesarias para la síntesis pre-calculada y la resolución de contradicciones (Truth Maintenance).
*   **Cr3: Integración del modelo (Outstanding):**
    El modelo no se plantea como un simple chatbot de preguntas y respuestas, sino que se integra de manera innovadora y escalable en el ciclo de vida documental de la organización. Actúa de manera asíncrona como un agente autónomo que ingesta documentos crudos, redacta, enlaza y compila archivos persistentes (Markdown).
*   **Cr4: Interpretar la evaluación del desempeño del modelo (Outstanding):**
    La evaluación no se limita a métricas de similitud semántica. Se aplicarán métricas orientadas al mantenimiento del conocimiento en el tiempo, tales como la tasa de resolución de contradicciones, consistencia temporal de creencias y detección de obsolescencia bajo ingestas incrementales.

## R.6.2: Automatizar tareas utilizando modelos de inteligencia artificial generativa para optimizar la eficiencia y la productividad en diferentes áreas organizacionales

*   **Cr5: Selección de tareas automatizables (Outstanding):**
    El proyecto selecciona un proceso con altísimo potencial de mejora: el trabajo de curaduría, consolidación y auditoría (linting) de los manuales y documentos internos de la empresa, reemplazando una tarea humana tediosa por un agente orquestado.
*   **Cr6: Demuestra la eficiencia lograda mediante la automatización (Outstanding):**
    Se sustentará la escalabilidad y mejora en eficiencia demostrando (a través de la arquitectura) cómo el costo computacional se traslada a la ingesta (una vez) abaratando la fase de recuperación (infinitas veces). Además, esto mejora el tiempo de respuesta y productividad para los empleados.
*   **Cr7: Mitigación de riesgos éticos (Outstanding):**
    Se propondrán estrategias proactivas para abordar los riesgos críticos: mitigación de alucinaciones (mediante el anclaje a fuentes crudas inmutables), sesgos algorítmicos al sintetizar, y seguridad/privacidad de los datos corporativos, evaluando la viabilidad de modelos seguros o locales.
*   **Cr8: Documentación de la solución (Outstanding):**
    Se entregará una documentación técnica estructurada y modular (siguiendo patrones de código abierto y repositorios como ETLInfrati). Se documentará el diseño del agente (prompts como esquemas del sistema), la configuración y las guías de uso de manera clara.

## R.7.1 y R.7.2: Despliegue de modelos y herramientas MLOps/DevOps

*   **R.7.1 (Herramientas y preparación de datos):**
    El pipeline automatizará el preprocesamiento de la información cruda (limpieza de PDFs/Docs empresariales), transformándolos y validándolos antes de pasarlos al LLM. El diseño modular permite la fácil ingesta y alimentación del sistema de forma robusta y reutilizable.
*   **R.7.2 (Automatización DevOps - MLOps):**
    La automatización del despliegue se abordará orquestando tareas continuas. Por ejemplo, mediante el uso de CI/CD (ej. GitHub Actions / Airflow), cuando se suban nuevos documentos al repositorio base, se ejecutarán automáticamente los scripts que detonan al agente para actualizar el Wiki, generar los logs y auditar la calidad, manteniendo mecanismos de versionado y trazabilidad absolutos (log.md).

## RA1 y RA2: Estrategias de comunicación escrita y oral

*   **RA1 (Comunicación Escrita):** Los entregables (incluyendo la definición del problema, readme, y reportes técnicos) presentarán cohesión gramatical, uso riguroso de fuentes bibliográficas y conclusiones críticas alineadas con los hallazgos técnicos sobre la degradación del conocimiento.
*   **RA2 (Comunicación Oral):** La sustentación del proyecto evidenciará un manejo fluido de lenguaje disciplinar técnico (diferenciando arquitecturas de agentes, RAG, GraphRAG), soportando argumentos técnicos con fluidez y claridad frente al jurado evaluador.
