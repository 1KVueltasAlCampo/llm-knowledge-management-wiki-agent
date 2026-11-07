## ADDED Requirements

### Requirement: Neutral T4 wording
Una pregunta T4 SHALL poder contestarse en cualquier paso con los papers ingeridos hasta entonces, por lo que su texto SHALL NOT mencionar el orden de los papers (palabras como `later`, `earlier`, `newer`, `older`, `subsequent`, `previous`, `prior`, `original`, `revised` o `superseded`).

#### Scenario: Borrador que nombra al paper posterior
- **WHEN** el redactor propone una T4 cuyo texto dice «According to the later paper…»
- **THEN** el borrador se descarta con el motivo

#### Scenario: Banco con una T4 que menciona el orden
- **WHEN** `validar-banco` recibe una T4 con `respuesta_por_paso` cuyo texto contiene `earlier`
- **THEN** informa un problema que nombra esa palabra

### Requirement: Previous answer keys
Una T4 con respuesta que cambia SHALL traer la respuesta previa y sus claves, y esas claves SHALL ser `respuesta_clave` del tramo inicial.

#### Scenario: Borrador sin claves de la respuesta previa
- **WHEN** el redactor propone una T4 con `answer_before` pero sin `answer_before_keys`
- **THEN** el borrador se descarta con el motivo

#### Scenario: Borrador completo
- **WHEN** el redactor propone una T4 neutra con `answer_before`, `answer_before_keys` y las claves de la respuesta nueva
- **THEN** la pregunta queda con `respuesta_clave` igual a las claves previas y con `respuesta_por_paso` con las nuevas

#### Scenario: Banco con una T4 sin claves previas
- **WHEN** `validar-banco` recibe una T4 con `respuesta_por_paso` y `respuesta_clave` vacía
- **THEN** informa un problema

### Requirement: Obsolete answer metric
Una respuesta a una T4 SHALL marcarse `obsoleta` cuando el paso es igual o mayor que el del primer cambio, el veredicto no es `correcta` y la respuesta contiene todas las claves de la respuesta previa. El agregado por sistema y paso SHALL reportar cuántas respuestas obsoletas hay y su tasa sobre las T4 ya actualizadas.

#### Scenario: Sigue dando el valor viejo
- **WHEN** una T4 cambia en el paso 3 y una respuesta del paso 3 contiene solo el valor previo
- **THEN** la respuesta es `obsoleta`

#### Scenario: Antes del cambio
- **WHEN** la misma respuesta se da en el paso 2
- **THEN** no es `obsoleta`

#### Scenario: Da el valor nuevo
- **WHEN** la respuesta del paso 3 contiene el valor nuevo
- **THEN** no es `obsoleta`
