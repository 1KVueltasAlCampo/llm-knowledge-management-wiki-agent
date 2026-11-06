## ADDED Requirements

### Requirement: Human-owned verification state
El sistema SHALL crear toda pregunta redactada por LLM con `estado_verificacion: borrador` y SHALL NOT cambiar ese estado a `verificado_a`, `verificado_b` ni `acordado`.

#### Scenario: Borrador nuevo
- **WHEN** el redactor produce una pregunta
- **THEN** su estado es `borrador` y registra `redactado_por`

### Requirement: Literal evidence
Un borrador SHALL entrar al banco solo si cada cita de evidencia aparece literal (salvo espacios) en el Gold de su fuente y se ancla a un `span_id`.

#### Scenario: Cita inventada
- **WHEN** la cita propuesta no aparece en el Gold
- **THEN** el borrador se descarta con el motivo

### Requirement: Two-layer correctness
La capa 1 SHALL decidir sin LLM con cifras y entidades clave; solo las respuestas `indeterminada` SHALL pasar al juez, con temperatura 0 y un modelo distinto del que responde y del redactor.

#### Scenario: Cifra presente
- **WHEN** la respuesta contiene todas las `respuesta_clave` (con coma o punto decimal, o como porcentaje)
- **THEN** el veredicto es `correcta` sin llamar al juez

### Requirement: Per-step coverage and abstention
Las métricas SHALL calcularse por sistema y paso de ingesta; antes de `ingesta_minima` lo correcto es abstenerse y responder cuenta como incorrecto.

#### Scenario: Pregunta aún no respondible
- **WHEN** el paso es menor que `ingesta_minima` y el sistema responde
- **THEN** el veredicto es `incorrecta`

### Requirement: Cost estimate before spending
Toda corrida que llame a una API de pago SHALL imprimir antes una estimación de tokens y costo y SHALL detenerse si supera 5 USD sin confirmación explícita.

#### Scenario: Tarifa no verificada
- **WHEN** faltan las tarifas del redactor en `.env`
- **THEN** la estimación usa una cota superior (4 veces las tarifas de Flash) y lo indica
