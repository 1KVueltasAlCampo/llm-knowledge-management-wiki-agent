## MODIFIED Requirements

### Requirement: Isolated run state
Cada corrida SHALL usar su propia carpeta de wiki (`data/wiki/<corrida>`) y su propio índice vectorial (`data/qdrant/<corrida>`), y SHALL NOT reutilizar el estado de otra corrida. Un nombre de corrida que ya tenga resultados SHALL tratarse como una reanudación.

#### Scenario: Corridas distintas
- **WHEN** se lanzan dos corridas con nombres distintos
- **THEN** cada una tiene su wiki y su índice, y ninguna ve las páginas de la otra
