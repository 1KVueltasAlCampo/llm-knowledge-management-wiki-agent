## ADDED Requirements

### Requirement: Loading phases
`wikillm.corpus fases` SHALL reordenar el manifest indicado por fase y, dentro de cada fase, por fecha de la primera versión y luego por identificador, renumerar `orden_ingesta` desde 1 y añadir `fase` a cada fila. SHALL terminar con error, sin escribir, si los identificadores de las fases no coinciden con los del manifest o si alguna fase no es un entero desde 1.

#### Scenario: Orden por fases
- **WHEN** un paper de 2026 tiene la fase 1 y uno de 2024 tiene la fase 2
- **THEN** el de 2026 recibe un `orden_ingesta` menor que el de 2024

#### Scenario: Fases que no coinciden
- **WHEN** el archivo de fases incluye un identificador que no está en el manifest
- **THEN** el comando termina con error y el manifest no cambia
