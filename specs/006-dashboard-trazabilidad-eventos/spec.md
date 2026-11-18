# Feature Specification: Dashboard de actividad y trazabilidad sísmica

**Feature Branch**: `[no creada]`

**Created**: 2026-11-17

**Status**: Completed

**Input**: User description: "Vamos a terminar de completar el dashboard haciendo esta tarea: Añadir un mapa de eventos recientes, resúmenes de magnitud y profundidad y gráficos de actividad temporal. Los agregados horarios y las distribuciones ya existen en la respuesta estadística, pero no se muestran como resumen en el dashboard. Y luego también incluir trazabilidad en la ficha, definir en el mismo ciclo el cambio necesario en la API. Añadir también el logo de la aplicación como favicon y en la aplicación donde sea necesario, usando frontend/public/icon.png."

## Clarifications

### Session 2026-11-17

- Q: ¿Qué nivel de trazabilidad debe exponer la API para cada evento y mostrar su ficha? → A: Trazabilidad compacta: identificador del evento, modo, fuente segura, fecha de versión, fecha de ingesta e identificador de ejecución cuando exista; sin payload original ni hash.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Consultar actividad sísmica reciente (Priority: P1)

Como visitante del observatorio, quiero ver en el dashboard un mapa de eventos recientes y un resumen de actividad temporal, para entender de un vistazo dónde y cuándo se han producido eventos.

**Why this priority**: El mapa reciente y la actividad temporal son la información principal que falta para completar el dashboard y permiten contextualizar la actividad sin navegar primero a otra sección.

**Independent Test**: Con una respuesta conocida de eventos y estadísticas, abrir el dashboard y cotejar las ubicaciones dibujadas y la serie horaria con los datos del periodo declarado.

**Acceptance Scenarios**:

1. **Given** que el servicio de consulta devuelve eventos recientes con geometría válida, **When** el visitante abre el dashboard, **Then** ve un mapa con cada evento de la respuesta en su ubicación y puede seleccionar un evento para abrir su ficha.
2. **Given** que la respuesta estadística contiene recuentos horarios, **When** se presenta la actividad temporal, **Then** el dashboard muestra la serie horaria en UTC con sus horas y recuentos correspondientes al periodo y filtros declarados.
3. **Given** que no hay eventos recientes, **When** se presenta el dashboard, **Then** se indica que no hay eventos en el periodo y no se dibujan ubicaciones ficticias ni se presenta la ausencia como error.
4. **Given** que la respuesta de eventos está truncada o contiene geometrías inválidas, **When** se representa el mapa, **Then** se indica la limitación o se omiten las geometrías inválidas sin presentarlas como ubicaciones válidas ni afirmar que el mapa contiene el total completo.
5. **Given** que el visitante abre la aplicación, **When** consulta la pestaña del navegador y la identidad global de la interfaz, **Then** reconoce el logo del observatorio como favicon y en los espacios de marca de la aplicación donde aporte orientación, sin duplicarlo como decoración innecesaria.

---

### User Story 2 - Interpretar magnitud y profundidad (Priority: P1)

Como visitante, quiero consultar resúmenes de las distribuciones de magnitud y profundidad, para comprender la composición de los eventos del periodo sin tener que interpretar una respuesta de datos sin resumir.

**Why this priority**: Las distribuciones ya están disponibles en las estadísticas y hacerlas legibles en el dashboard entrega directamente el resumen que falta, sin introducir medidas no respaldadas por la fuente.

**Independent Test**: Usar estadísticas de muestra con bins conocidos, valores ausentes y filtros; comparar los resúmenes visibles, las unidades y los conteos con la respuesta.

**Acceptance Scenarios**:

1. **Given** que las estadísticas incluyen distribuciones de magnitud y profundidad, **When** el visitante consulta el dashboard, **Then** ve ambos resúmenes con los intervalos, conteos, unidades y porcentajes devueltos.
2. **Given** que una distribución informa valores válidos y ausentes, **When** se muestra el resumen, **Then** los valores ausentes se identifican por separado y no se muestran como cero ni se incluyen en el denominador de los porcentajes.
3. **Given** que no hay valores válidos para una distribución, **When** se muestra el resumen, **Then** la interfaz comunica que no hay valores disponibles y no inventa porcentajes.

---

### User Story 3 - Rastrear el origen de un evento (Priority: P2)

Como visitante del observatorio, quiero consultar en la ficha de un evento su identificador de origen, procedencia y datos de versión e ingesta disponibles, para entender de qué registro procede y cuándo fue incorporado.

**Why this priority**: La trazabilidad permite interpretar y auditar los datos mostrados y debe estar disponible junto a los atributos del evento, no inferida a partir del mapa.

**Independent Test**: Consultar un evento cuya procedencia y metadatos de ingesta se conocen, abrir su ficha y cotejar cada dato de trazabilidad con la respuesta pública del servicio; verificar también los campos desconocidos.

**Acceptance Scenarios**:

1. **Given** un evento cuya respuesta contiene datos de trazabilidad, **When** el visitante abre su ficha desde el mapa, **Then** la ficha muestra el identificador de evento, el modo/origen, la fuente, la fecha de versión y los datos de ingesta disponibles con etiquetas comprensibles.
2. **Given** que un dato de trazabilidad no está disponible, **When** se presenta la ficha, **Then** se identifica como desconocido o no disponible y no se inventa ni se infiere.
3. **Given** que una respuesta de evento incluye nuevos campos de trazabilidad, **When** la consume un cliente que solo necesita los campos existentes, **Then** los campos existentes conservan su significado y la ampliación no cambia la consulta ni el formato de los agregados estadísticos.

### Edge Cases

- La respuesta estadística es válida pero no contiene eventos ni bins: el dashboard diferencia la ausencia de eventos de la ausencia de valores válidos y evita porcentajes ficticios.
- La serie temporal no contiene buckets: se informa de que no hay actividad horaria disponible para ese resultado; no se rellenan recuentos inventados.
- Los datos de evento y estadísticas difieren en su periodo efectivo: cada visualización conserva y muestra el periodo y filtros de su propia respuesta.
- Falla una de las consultas o la respuesta no puede interpretarse: se comunica el error en la visualización afectada y no se sustituye por cero ni por datos ficticios.
- La actualización falla tras una consulta correcta: se conserva la última lectura identificada como correcta y se señala su posible desactualización.
- Un evento carece de coordenadas válidas: no se representa como punto geográfico; los demás datos del evento siguen disponibles cuando la consulta los proporciona.
- El servicio no proporciona fuente, identificador de ejecución u otro dato de trazabilidad para un evento: la ficha indica que no está disponible sin deducirlo de otros campos.
- El dato de fuente incluye información sensible: la respuesta pública y la ficha no exponen credenciales, tokens ni parámetros secretos.
- El logo aparece sobre fondos de ambos temas y en pantallas pequeñas: debe mantener legibilidad y proporciones sin desplazar ni ocultar controles esenciales.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El dashboard MUST incluir un mapa de los eventos recientes proporcionados por el servicio de consulta y permitir abrir la ficha de un evento seleccionado.
- **FR-002**: El mapa MUST representar únicamente geometrías válidas de los eventos recibidos, respetar la atribución cartográfica vigente y comunicar si la respuesta de eventos está truncada.
- **FR-003**: El dashboard MUST presentar los recuentos horarios como una visualización temporal legible, identificada en UTC y acompañada por el periodo y los filtros efectivos declarados para las estadísticas.
- **FR-004**: El dashboard MUST presentar los resúmenes de las distribuciones de magnitud y profundidad existentes en la respuesta estadística, incluyendo bins, unidades, recuentos válidos y ausentes, y porcentajes cuando estén disponibles.
- **FR-005**: Los resúmenes MUST conservar los valores y semántica recibidos; los valores ausentes, porcentajes nulos, distribuciones sin datos, errores y resultados vacíos MUST distinguirse entre sí y MUST NOT convertirse en ceros ni valores inventados.
- **FR-006**: Cada visualización MUST atribuir sus datos al periodo y filtros de su respuesta correspondiente; no MUST atribuir el periodo de las estadísticas a los eventos ni presentar poblaciones distintas como si fueran idénticas.
- **FR-007**: La ficha de evento MUST mostrar los datos de trazabilidad proporcionados por el servicio, incluyendo identidad del registro de origen, modo de procedencia, fuente, marca temporal de versión e información de ingesta disponible, con fechas en UTC y etiquetas comprensibles.
- **FR-008**: El contrato público del servicio MUST ampliarse de forma aditiva para exponer en cada evento consultado trazabilidad compacta de su versión actual: identificador del evento, modo (`live` o `replay`), fuente segura, marca temporal de actualización/versión, fecha de ingesta e identificador de ejecución de ingesta cuando exista. Los campos no disponibles MUST expresarse explícitamente como desconocidos; la ampliación MUST preservar los campos vigentes y no exponer el payload original, su hash, credenciales ni secretos.
- **FR-009**: La documentación del contrato del servicio MUST definir los campos nuevos de trazabilidad, sus significados, unidades y representación de datos ausentes, y MUST mantener sin cambios la semántica de los agregados horarios y distribuciones ya existentes.
- **FR-010**: La ficha y las visualizaciones MUST distinguir carga, resultado válido vacío, error y última lectura posiblemente desactualizada; un fallo MUST NOT presentarse como una lectura correcta.
- **FR-011**: El mapa y los gráficos MUST incluir una alternativa textual o tabular accesible con los mismos valores esenciales, y ninguna información MUST depender exclusivamente del color.
- **FR-012**: La aplicación MUST usar el logo existente `frontend/public/icon.png` como favicon y en las ubicaciones globales de identidad visual donde ayude a reconocer u orientarse en el observatorio. Su uso MUST preservar proporciones, legibilidad en los temas disponibles y texto alternativo accesible cuando se muestre como imagen; no MUST repetirse como elemento decorativo en cada vista.

### Key Entities *(include if feature involves data)*

- **Evento reciente**: Registro actual de un evento sísmico con ubicación y atributos disponibles, perteneciente al periodo reciente consultado.
- **Resultado estadístico**: Recuentos horarios y distribuciones de magnitud y profundidad con bins, unidades, periodo, filtros, valores válidos y ausentes.
- **Datos de trazabilidad del evento**: Identidad de origen, modo, fuente, versión y metadatos de ingesta disponibles para relacionar el evento expuesto con el registro que se procesó.
- **Ficha de evento**: Presentación de los atributos y datos de trazabilidad de un evento seleccionado, respetando valores desconocidos y su procedencia.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: En todos los casos de aceptación con respuestas de muestra, el mapa representa cada evento con geometría válida una sola vez y permite acceder a su ficha; no dibuja geometrías inválidas.
- **SC-002**: El 100% de los valores de recuento horario, bins, unidades, porcentajes válidos y valores ausentes visibles en el dashboard coincide con la respuesta estadística asociada.
- **SC-003**: En el 100% de las pruebas de distribuciones sin datos, ausentes, errores y respuestas vacías, la interfaz distingue correctamente esos estados y no presenta valores ficticios.
- **SC-004**: Para todos los eventos de una muestra de contrato que incluya datos de trazabilidad, la ficha permite identificar origen, versión e ingesta; los campos inexistentes se identifican como no disponibles.
- **SC-005**: En una prueba guiada con datos conocidos que incluyan actividad horaria, distribuciones de magnitud y profundidad y un evento con trazabilidad disponible, el visitante identifica la actividad horaria en UTC, interpreta las unidades y los valores válidos/ausentes de ambas distribuciones y localiza la fuente y versión del evento en un máximo de 180 segundos desde que se muestra el dashboard.
- **SC-006**: El favicon del navegador y las ubicaciones globales de marca definidas para la aplicación muestran el logo del observatorio; el logo sigue siendo reconocible en los temas disponibles y cuenta con alternativa accesible cuando se presenta dentro de la interfaz.

## Assumptions

- «Recientes» usa la ventana predeterminada de 24 horas definida para la consulta de eventos, salvo que el dashboard ya muestre y aplique un periodo explícito.
- Las estadísticas ya devuelven recuentos horarios y distribuciones con periodo, filtros, bins, unidades, denominadores y valores ausentes; este cambio los presenta, no redefine cómo se calculan.
- Los identificadores y datos de procedencia/versionado/ingesta requeridos para trazabilidad son los que se conservan para la versión actual del evento; cualquier dato que no exista se expresa como no disponible.
- La ampliación del contrato es aditiva y mantiene compatibles los campos existentes; no requiere un nuevo servicio ni altera los agregados estadísticos.
- El archivo `frontend/public/icon.png` es el recurso visual aprobado para el favicon y la identidad global del observatorio; se reutiliza sin generar una identidad alternativa.
- El dashboard continúa usando exclusivamente el servicio de consulta del proyecto; no incorpora fuentes externas de eventos ni predicciones o evaluaciones de riesgo.
- La actualización, los estados de error, los filtros compartidos, los temas y las reglas generales de accesibilidad existentes se mantienen; esta especificación añade el resumen de dashboard y la trazabilidad de la ficha.
