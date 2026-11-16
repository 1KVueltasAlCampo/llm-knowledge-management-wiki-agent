## ADDED Requirements

### Requirement: Blind export of items to audit
`auxiliar exportar` SHALL escribir `<corrida>/auxiliar/items.jsonl` con una línea por ítem y SHALL incluir solo `item_id`, `question`, `reference_answer` y `answer_to_grade`, sin el veredicto principal, el sistema ni el paso. SHALL incluir todas las respuestas cuyo `veredicto_capa1` es `indeterminada` y una muestra de `--muestra` (por defecto 40) de las demás respondibles, elegida con `--semilla` (por defecto 1) de forma reproducible. SHALL guardar la correspondencia `item_id` → (pregunta, sistema, paso) en `auxiliar/claves.jsonl`.

#### Scenario: Ítems ciegos
- **WHEN** se exporta una corrida evaluada
- **THEN** ningún ítem de `items.jsonl` contiene los campos `veredicto`, `system` ni `ingest_step`

#### Scenario: Indeterminadas siempre incluidas
- **WHEN** hay 3 respuestas indeterminadas y la muestra pedida es 0
- **THEN** `items.jsonl` tiene exactamente esos 3 ítems

#### Scenario: Muestra reproducible
- **WHEN** se exporta dos veces con la misma semilla
- **THEN** `items.jsonl` es idéntico byte a byte

### Requirement: Agreement with the primary verdict
`auxiliar importar` SHALL leer `auxiliar/veredictos_claude.jsonl` (una línea por `item_id` con `veredicto` en `correcta|incorrecta|indeterminada`), SHALL unirlo con los evaluados mediante `claves.jsonl` y SHALL escribir `auxiliar/acuerdo.json` y `auxiliar/acuerdo.md` con n, porcentaje de acuerdo y kappa, en total, por origen del veredicto principal (`determinista` o `juez`) y por sistema. Un veredicto fuera del conjunto o un `item_id` desconocido SHALL terminar con código distinto de cero sin escribir resultados.

#### Scenario: Acuerdo calculado
- **WHEN** hay veredictos de Claude para los ítems exportados
- **THEN** `acuerdo.json` incluye n, porcentaje y kappa totales y por origen y sistema

#### Scenario: Veredicto inválido
- **WHEN** una línea trae `veredicto` igual a `tal vez`
- **THEN** el comando termina con código 1 y no crea `acuerdo.json`

### Requirement: Auxiliary labelling
`acuerdo.md` SHALL declarar que es evaluación auxiliar, que no reemplaza el veredicto principal y que su costo no está en `consumo.csv`, e SHALL incluir el modelo y la fecha indicados en el archivo de veredictos.

#### Scenario: Rótulo
- **WHEN** se escribe `acuerdo.md`
- **THEN** contiene la palabra "auxiliar" y el modelo declarado en los veredictos
