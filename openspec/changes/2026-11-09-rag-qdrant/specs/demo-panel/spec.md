## ADDED Requirements

### Requirement: Readiness check with the index held by the panel
Qdrant en modo local permite un solo proceso por carpeta. Cuando el panel tiene abierto el índice de la demostración, la verificación de la preparación (`scripts/verificar_demo.py`, también lanzada desde el panel) SHALL obtener el número de fragmentos del panel (`/api/estado`, campo `rag_fragmentos`) en lugar de abrir la carpeta, y SHALL NOT reportar el índice como fallido solo porque está en uso. Si el panel no corre, SHALL abrir el índice directamente.

#### Scenario: Panel con el índice cargado
- **WHEN** el panel tiene cargado el índice y se ejecuta la verificación
- **THEN** la revisión del índice vectorial sale `[OK]` con el número de fragmentos que informa el panel

#### Scenario: Panel apagado
- **WHEN** no hay panel corriendo y se ejecuta la verificación
- **THEN** la verificación abre `data/qdrant` y cuenta los fragmentos ella misma

#### Scenario: Estado del panel
- **WHEN** se pide `/api/estado` con el índice cargado
- **THEN** la respuesta incluye `rag_fragmentos` con el total de fragmentos del índice (o `null` si no está cargado)
