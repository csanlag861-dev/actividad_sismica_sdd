# Feature Specification: Panel web del observatorio sísmico

**Feature Branch**: `[no creada]`

**Created**: 2026-11-17

**Status**: Completed

**Input**: User description: "Completar H6 con la interfaz: integrar mapa y fichas (R21), añadir filtros, tabla y visualizaciones (R22) y presentar la comparación histórica (R23). Crear la aplicación web del Observatorio de Actividad Sísmica, estableciendo la estructura de navegación, el dashboard principal y los módulos de visualización y análisis de eventos sísmicos. La interfaz debe seguir el sistema visual definido en docs/design/design-system.md, ofrecer temas oscuro y claro, y consumir exclusivamente la API del backend FastAPI conforme a docs/CONTRATO-API.md. Mantener Leaflet como solución cartográfica 2D existente. Revisar la documentación fuente de verdad, los artefactos SDD existentes y la estructura actual del frontend antes de definir funcionalidades. No inventar endpoints, datos, permisos ni requisitos funcionales. Diferenciar claramente los requisitos confirmados de las propuestas opcionales. Priorizar una primera versión funcional del dashboard y la navegación principal, respetando las restricciones tecnológicas y académicas del proyecto. Actualizar ROADMAP.md si hace falta para definir H6."

## Clarifications

### Session 2026-11-17

- Q: ¿Qué escala debe usar el mapa para traducir la profundidad del evento a color? → A: Usar intervalos semiabiertos de 10 km, como las distribuciones del contrato, con una escala secuencial Mars Station y una leyenda explícita; mantener un color diferenciado para valores sin profundidad.
- Q: ¿También deben actualizarse las estadísticas y la comparación histórica cada 60 segundos junto con el mapa, o solo cuando cambien los filtros? → A: Actualizar eventos y estadísticas juntos cada 60 segundos y cuando cambien los filtros, mostrando sus periodos efectivos.
- Q: ¿Dónde deben presentarse las tres conclusiones numéricas que pide R23: dentro del panel web o en la memoria/informe del proyecto? → A: Las tres conclusiones se documentan en la memoria/informe; la interfaz muestra la comparación y sus datos.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Orientarse en el observatorio (Priority: P1)

Como visitante del observatorio, quiero llegar a un dashboard y navegar a la exploración y al análisis de eventos para encontrar la información sísmica principal sin aprender una interfaz compleja.

**Why this priority**: La navegación y la vista de entrada hacen posible utilizar y demostrar los demás recorridos de H6.

**Independent Test**: Abrir la aplicación, validar el dashboard con datos y ante un fallo de consulta, comprobar la navegación principal disponible y cambiar entre los temas. Esta prueba no exige que las vistas de eventos y análisis estén terminadas; el recorrido completo se valida al integrar sus historias correspondientes.

**Acceptance Scenarios**:

1. **Given** que el servicio de consulta responde correctamente, **When** el visitante abre la aplicación, **Then** ve el periodo consultado, el estado de salud y última ingesta informada, el número de eventos devueltos (identificado como muestra si está truncada) y accesos a exploración y análisis, todo respaldado por la API.
2. **Given** que solo está implementado el incremento MVP, **When** el visitante consulta la navegación principal, **Then** puede identificar el dashboard y las secciones previstas, sin que se exija que los destinos de eventos y análisis sean funcionales antes de completar las historias correspondientes. La navegación funcional entre todas las secciones se valida como integración posterior.
3. **Given** que el visitante usa cualquiera de los dos temas, **When** cambia entre tema oscuro y claro, **Then** los textos y controles disponibles en el incremento actual siguen siendo legibles y coherentes con el sistema visual; la legibilidad del mapa, la tabla y las visualizaciones se valida al integrar sus historias.
4. **Given** que falla la consulta de salud o de datos, **When** se presenta el dashboard, **Then** informa del fallo sin anunciar un estado saludable ni sustituirlo por datos ficticios.

---

### User Story 2 - Explorar eventos en el mapa y consultar su ficha (Priority: P1)

Como visitante, quiero explorar los eventos del periodo en el mapa y seleccionar uno para consultar sus datos, para relacionar cada evento con su ubicación y atributos disponibles.

**Why this priority**: El mapa interactivo y la ficha de evento son el recorrido geográfico central definido por R21 y el enunciado.

**Independent Test**: Con una respuesta conocida de eventos, comprobar la ubicación de varios puntos, seleccionar uno y cotejar su ficha con sus propiedades de origen.

**Acceptance Scenarios**:

1. **Given** que la API devuelve eventos con coordenadas geográficas válidas (longitud entre −180 y 180 y latitud entre −90 y 90), **When** se muestra el mapa, **Then** cada evento aparece en sus coordenadas longitud/latitud; las geometrías fuera de esos rangos no se dibujan.
2. **Given** que se muestra un evento en el mapa, **When** se representa su magnitud, **Then** el radio en píxeles es `clamp(4 + 2 × max(0, magnitud), 4, 18)` y una magnitud nula se representa con radio de 5 px, contorno discontinuo y estilo neutral, sin inferir su magnitud.
3. **Given** que se conoce la profundidad de un evento, **When** se representa en el mapa, **Then** su color corresponde al intervalo semiabierto de 10 km `[k*10, (k+1)*10)` aplicado por el contrato de estadísticas, la leyenda explica los intervalos con la escala secuencial Mars Station y los valores nulos o negativos se distinguen sin asignarles una profundidad ficticia o un intervalo válido.
4. **Given** que se selecciona un evento, **When** se abre su ficha, **Then** se presentan los atributos disponibles del evento, sus unidades y los valores nulos como desconocidos, sin inferir país ni otra propiedad.
5. **Given** que se completa una nueva consulta, **When** se actualiza el mapa, **Then** la capa anterior se sustituye en vez de acumular marcadores, y se conserva la atribución cartográfica del material proporcionado.

---

### User Story 3 - Filtrar y consultar eventos y estadísticas (Priority: P2)

Como visitante, quiero filtrar eventos por periodo, magnitud mínima y país, y consultar tanto el mapa como una tabla y estadísticas, para examinar los mismos criterios de consulta de varias formas.

**Why this priority**: Los filtros compartidos, la tabla accesible y las vistas estadísticas completan la exploración R22 y permiten interpretar los datos más allá del mapa.

**Independent Test**: Aplicar filtros a una muestra conocida y verificar el periodo y filtros declarados, los eventos de la tabla y el mapa, los agregados recibidos y el tratamiento de datos ausentes.

**Acceptance Scenarios**:

1. **Given** una selección de periodo, magnitud mínima y país, **When** el visitante aplica los filtros, **Then** la consulta de eventos y la de estadísticas usan los mismos valores admitidos por el contrato; al cambiar entre exploración y análisis, los controles muestran esos filtros compartidos y no los reinician.
2. **Given** que existen eventos que cumplen los filtros, **When** el visitante consulta la tabla, **Then** puede recorrer los eventos y acceder a su ficha como alternativa al mapa y al color.
3. **Given** que hay datos para el periodo consultado, **When** se muestran las estadísticas, **Then** se presentan los recuentos por hora UTC y país, las distribuciones de magnitud y profundidad, sus unidades, periodo y cantidades ausentes.
4. **Given** que la API declara ausencia de datos, **When** se presenta la respuesta, **Then** la interfaz diferencia ausencia de cero y mantiene visible la categoría «Sin país asignado».
5. **Given** que la API devuelve un error, una colección vacía o resultados limitados, **When** se actualiza una consulta, **Then** la interfaz diferencia esos estados y no presenta una muestra limitada como si fuera el total global.
6. **Given** que la aplicación está abierta, **When** llega el ciclo de actualización de 60 segundos o cambian los filtros, **Then** vuelve a consultar eventos y estadísticas con filtros equivalentes, comunica el error o la posible desactualización y conserva identificable la última lectura correcta.
7. **Given** que una consulta nueva está cargando o falla, **When** todavía se muestran datos de una respuesta correcta anterior, **Then** el periodo, los filtros y la hora de lectura que se muestran siguen perteneciendo a esa respuesta anterior, separados del contexto solicitado más recientemente.

---

### User Story 4 - Interpretar la comparación histórica (Priority: P3)

Como visitante, quiero comparar la tasa del periodo consultado con el baseline histórico disponible y conocer sus límites, para interpretar la actividad sin confundir periodos, filtros o falta de cobertura.

**Why this priority**: La comparación R23 solo es interpretable después de que existan consultas y filtros coherentes en las vistas del panel.

**Independent Test**: Usar respuestas de muestra con baseline completo, incompleto y con tasa histórica cero; cotejar periodos, filtros, tasas y mensajes con el contrato.

**Acceptance Scenarios**:

1. **Given** que la API informa un baseline histórico disponible, **When** se muestra la comparación, **Then** se presentan el periodo consultado, el baseline, los filtros, la unidad de eventos por día y las tasas o diferencias que devuelve la API.
2. **Given** que no existe cobertura histórica completa, **When** se muestra la comparación, **Then** se indica que el baseline no está disponible y no se representa como una tasa cero.
3. **Given** que el promedio diario histórico es cero o que el último periodo puede estar incompleto, **When** se interpreta la comparación, **Then** se omiten los cocientes no definidos y se explica el límite de cobertura o actualidad aplicable.
4. **Given** cualquier comparación, **When** el visitante revisa el resultado, **Then** la interfaz no lo presenta como predicción sísmica ni evaluación de riesgo.

---

### Edge Cases

- La colección de eventos es válida pero está vacía para el periodo y filtros elegidos.
- Magnitud, profundidad, lugar, tipo de magnitud o país son nulos; no se reemplazan por valores inventados.
- Hay eventos sin país asignado; se conservan en el mapa/tabla cuando hay geometría y en el grupo estadístico correspondiente.
- La respuesta de eventos indica truncamiento o la respuesta de estadísticas tiene cobertura histórica no disponible.
- El servicio devuelve HTTP 400, 422, 500 o 503, una respuesta malformada o una respuesta no accesible por fallo de red/CORS; se informa del motivo comprensible y se ofrece reintentar la consulta vigente.
- El visitante introduce un periodo incompleto, inválido o invertido; se indica qué debe corregir y no se envía la consulta.
- Una actualización falla después de una lectura correcta: se conserva la última lectura válida, se indica el fallo y no se trata como información recién obtenida.
- El periodo reciente puede estar incompleto y la cobertura del replay histórico puede no acreditar el año completo.
- Una geometría o respuesta no válida no se dibuja como si fuera un evento válido.
- El usuario cambia de tema o viewport mientras mapa, tabla o estadísticas están cargando.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: La aplicación MUST proporcionar una navegación principal para el dashboard, la exploración de eventos y el análisis cubierto por esta especificación.
- **FR-002**: La aplicación MUST ofrecer el tema oscuro Mars Station como tema predeterminado y permitir cambiar al tema claro definido en el sistema visual; ambos temas MUST usar sus tokens de texto/superficie y conservar los contrastes indicados por el sistema visual. Los estados y categorías MUST tener etiqueta o forma además de color.
- **FR-003**: La aplicación MUST obtener los eventos, el estado del servicio y las estadísticas únicamente del servicio de consulta del proyecto, respetando los endpoints, parámetros y esquemas documentados; MUST NOT consultar USGS desde el navegador ni introducir endpoints, datos o permisos no definidos.
- **FR-004**: El mapa MUST conservar la solución cartográfica 2D existente y dibujar solo geometrías con longitud entre −180 y 180 y latitud entre −90 y 90, interpretadas en orden longitud/latitud. El radio de marcador en píxeles MUST ser `clamp(4 + 2 × max(0, magnitud), 4, 18)`; para magnitud nula MUST usar radio de 5 px, contorno discontinuo y estilo neutral. La profundidad MUST representarse con bins semiabiertos de 10 km `[k*10, (k+1)*10)` mediante una escala secuencial Mars Station consistente, con leyenda. Una profundidad negativa es un valor recibido fuera de esos bins: MUST mostrarse en una categoría visual separada etiquetada como valor recibido y no asignarse a un intervalo válido. La profundidad nula MUST distinguirse sin asignarle valor. La atribución cartográfica MUST permanecer accesible.
- **FR-005**: La ficha y las demás vistas MUST mostrar los atributos que la API proporciona, con unidades y valores nulos explícitos; MUST NOT inferir magnitud, profundidad, ubicación, país, tipo o estado de ingesta.
- **FR-006**: La selección de fecha/hora, magnitud mínima y país MUST aplicarse con semántica coherente a las consultas de eventos y estadísticas. Los filtros confirmados MUST conservarse al cambiar entre las vistas de exploración y análisis, y los controles MUST reflejar los valores compartidos vigentes. La UI MUST identificar el periodo y filtros asociados a cada resultado: eventos muestran los filtros enviados en su solicitud y estadísticas los filtros efectivos declarados por la API.
- **FR-007**: La interfaz MUST proporcionar una tabla consultable como alternativa al mapa y permitir acceder desde ella al detalle del evento.
- **FR-008**: Las vistas estadísticas MUST mostrar recuentos horarios UTC, recuentos por país, distribuciones de magnitud y profundidad, unidades y valores ausentes, de acuerdo con la respuesta de estadísticas.
- **FR-009**: La comparación MUST presentar el periodo consultado frente al baseline de 2025 que devuelve la API, sus filtros y unidades; MUST distinguir baseline no disponible de promedio cero y no presentar diferencias o cocientes omitidos como cero.
- **FR-010**: La aplicación MUST distinguir carga, resultado correcto vacío, error HTTP, error de transporte o respuesta malformada, resultado limitado y última lectura posiblemente desactualizada. Un error MUST NOT convertirse en resultado vacío ni en valores estadísticos de cero. Un intervalo inválido MUST mostrar el motivo y no iniciar la consulta; un filtro rechazado o una respuesta malformada MUST mostrar un mensaje comprensible y permitir reintentar la consulta vigente.
- **FR-011**: Cuando falle una actualización tras una lectura correcta, la aplicación MUST conservar identificable la última lectura correcta y comunicar su posible desactualización; el periodo, filtros y hora mostrados MUST seguir atribuidos a esa lectura, sin sustituirse por el contexto solicitado más recientemente. Una nueva consulta iniciada por la aplicación que tenga éxito MUST actualizarla y limpiar el error.
- **FR-012**: La aplicación MUST actualizar eventos y estadísticas —incluida la comparación histórica— juntos cada 60 segundos y cuando cambien los filtros, pero conservar por separado el contexto de cada respuesta independiente. Para eventos, el periodo personalizado y los filtros mostrados son los enviados en la solicitud; sin intervalo personalizado, la UI MUST identificar el periodo móvil predeterminado de 24 horas y MUST NOT atribuirle el periodo efectivo de la respuesta estadística ni inventar límites que el endpoint de eventos no devuelve. Las estadísticas MUST mostrar su periodo y filtros declarados por la API. Este refresco pertenece a la experiencia de la aplicación y no cambia la regla del cliente de transporte de no realizar reintentos o refrescos automáticos por sí mismo.
- **FR-013**: Los enlaces de navegación, el selector de tema, los controles de filtro, las acciones de actualizar/reintentar, la tabla y los controles de divulgación MUST ser operables por teclado, tener nombre accesible y foco visible. Mapa y gráficos MUST tener alternativas textuales o tabulares, y ninguna información MUST depender solo del color. La interfaz MUST adaptarse a móvil (320–760 px), tablet (761–1024 px) y escritorio (más de 1024 px) sin ocultar filtros, datos o acciones esenciales ni provocar desplazamiento horizontal de la página; las tablas podrán desplazarse dentro de su contenedor.
- **FR-014**: La interfaz MUST usar la jerarquía, tokens cromáticos, tipografía, patrones de estado y criterios científicos del sistema visual; la claridad de los datos prevalece sobre la decoración.

### Confirmed scope and constraints

- La aplicación web sigue siendo una SPA Angular, conserva Leaflet para el mapa 2D y consulta exclusivamente la API FastAPI del proyecto.
- La consulta usa las operaciones ya documentadas para eventos, salud y estadísticas; no se diseña ni exige un endpoint adicional.
- Las operaciones existentes son `GET /api/eventos`, `GET /api/salud` y `GET /api/estadisticas`; el cliente utiliza únicamente parámetros documentados en el contrato.
- El contrato de consulta documenta actualmente `start`, `end`, `min_mag` y `country_id`. No se añade un filtro de tipo de magnitud ni una agrupación/filtro subregional sin soporte contractual.
- La comparación disponible usa el periodo consultado y el baseline histórico de 2025 calculado por el backend; no ofrece selección libre de años históricos.
- Las tres conclusiones cuantitativas que pide R23 se documentan en la memoria/informe académico; el panel presenta la comparación histórica y sus datos, pero no genera ni exige mostrar esas conclusiones.
- El panel es público y de solo lectura. No se incorporan autenticación, permisos de edición ni operaciones administrativas.
- Las funcionalidades de base son navegación, dashboard, mapa y ficha, filtros acordados, tabla, estadísticas y comparación histórica, además de estados de error/vacío/desactualización.

### Resolved scope decision

- Decisión confirmada por el usuario: H6 se limita a los filtros admitidos por el contrato vigente (`start`, `end`, `min_mag`, `country_id`). Los filtros por región/subregión y tipo de magnitud quedan fuera de esta entrega; no se derivarán en el navegador. Para incorporarlos, primero se deberá ampliar el contrato API en una especificación separada.

### Optional proposals excluded from this feature

- El globo 3D con CesiumJS, capas de placas tectónicas y reproducción visual de eventos son ampliaciones opcionales mencionadas por el sistema visual, no requisitos de H6.
- La administración de cuarentena, edición de eventos, alertas, predicción sísmica, evaluación de riesgo y páginas o indicadores adicionales quedan fuera del panel público y no se presuponen endpoints ni permisos.
- Las tarjetas KPI y gráficos adicionales no descritos por el enunciado o la respuesta estadística solo podrán proponerse como ampliaciones separadas; esta especificación no les atribuye datos nuevos.

### Key Entities *(include if feature involves data)*

- **Evento sísmico actual**: evento con identificador, geometría, tiempo, magnitud, tipo de magnitud, profundidad, lugar y atributos de país disponibles; algunos atributos pueden ser nulos.
- **Consulta**: periodo y filtros admitidos cuyos valores efectivos se muestran junto a sus resultados.
- **Resultado estadístico**: recuentos por hora y país, distribuciones con valores ausentes y unidades declaradas para un periodo y filtros.
- **Estado de consulta**: última respuesta correcta, hora de lectura local, metadatos de generación/ingesta y posible error o desactualización.
- **Comparación histórica**: tasa diaria del periodo actual frente al baseline del año 2025, con cobertura y campos comparativos condicionados por el contrato.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: En una prueba guiada de hasta 5 minutos, el visitante puede llegar desde el dashboard a la exploración, seleccionar un evento y localizar en su ficha sus valores disponibles de magnitud, tiempo y lugar.
- **SC-002**: En el 100% de los casos de aceptación con filtros válidos, el mapa y la tabla muestran el intervalo/filtros enviados para eventos y las estadísticas muestran el periodo/filtros efectivos declarados por la API, sin aplicar filtros divergentes.
- **SC-003**: En el 100% de las pruebas de estado vacío, truncamiento, fallo de consulta y pérdida de actualización, la interfaz distingue el estado de un resultado completo correcto y no muestra el fallo como cero eventos.
- **SC-004**: En el 100% de las respuestas de estadísticas comprobadas, se presentan unidades, periodo y valores ausentes; la comparación histórica diferencia cobertura no disponible, promedio cero y tasas válidas.
- **SC-005**: En los viewports móvil (320–760 px), tablet (761–1024 px) y escritorio (más de 1024 px), las tareas de navegación, aplicación de filtros, consulta tabular y lectura de la comparación están disponibles en ambos temas; pueden completarse con teclado y sin depender únicamente del color o del mapa.
- **SC-006**: En una prueba guiada de hasta 5 minutos, el visitante puede identificar el periodo actual, la disponibilidad del baseline y las tasas comparadas en la vista de análisis, sin interpretar la comparación como predicción o evaluación de riesgo.

## Assumptions

- La implementación de R18–R20 está disponible y sus respuestas cumplen `docs/CONTRATO-API.md`; los fallos de disponibilidad siguen siendo estados normales que la interfaz debe comunicar.
- El `public/config.json` existente configura la URL base pública del backend y no contendrá credenciales.
- El mapa conserva las fronteras y la atribución del material geográfico existente; no se incorpora una fuente cartográfica externa nueva sin validación y atribución.
- El servicio desplegado actualmente no aplica límite ni paginación; si la API devuelve truncamiento, la interfaz lo identificará y no calculará totales globales sobre la muestra. El contrato exige que una API que trunque declare el total y un mecanismo de paginación, pero H6 no inventará parámetros o controles de continuación que no estén definidos en el contrato de consulta vigente.
- El documento de análisis o memoria conserva las tres conclusiones fundamentadas exigidas por el enunciado; la interfaz no las genera automáticamente ni las presenta como requisito del panel.
- El contrato vigente no permite resolver filtros regionales/subregionales ni de tipo de magnitud en la interfaz; se mantienen fuera del alcance de H6 hasta que una ampliación contractual los defina.
- Esta entrega no establece objetivos propios de latencia, concurrencia, disponibilidad, tamaño máximo de respuesta ni carga visual; el timeout de transporte de 15 segundos no es una garantía de servicio.
- Las fronteras y el catálogo geográfico local son ayudas de visualización/filtro, no fuentes de eventos sísmicos; el API es la única fuente de esos datos.
