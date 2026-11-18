## ADDED Requirements

### Requirement: Report multi-hop questions without changing them
El análisis SHALL repartir las preguntas existentes según el número de papers que exigen y si alguno cita a otro de ellos, y SHALL calcular la cobertura de cada sistema por grupo y la comparación pareada del wiki frente a cada RAG en las preguntas de varios papers. SHALL NOT modificar ninguna pregunta ni llamar a un modelo.

#### Scenario: Preguntas encadenadas por citas
- **WHEN** una pregunta exige dos o más papers y alguno cita a otro en `referencias_en_corpus`
- **THEN** cuenta como encadenada y se reporta su cobertura aparte

### Requirement: Test a citation tool end to end
La prueba SHALL comparar, sobre las mismas preguntas y con el mismo agente, las herramientas `search` y `read` con y sin la acción `cites`, y SHALL reportar aciertos, papers exigidos citados, llamadas, tokens y costo.

#### Scenario: Herramienta sin efecto
- **WHEN** el agente no usa `cites` o no mejora los aciertos
- **THEN** el resultado se reporta como negativo con la fracción de preguntas en que se usó la herramienta
