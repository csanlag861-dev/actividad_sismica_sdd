# Feature Specification: Exploración sísmica avanzada

**Feature Branch**: `main` (rama de feature aún no creada)

**Created**: 2026-11-18

**Status**: Draft

**Input**: User description: "Añadir paginación en resumen y exploración, mejorar la visualización 2D y destacar el evento más reciente, comparar periodos y poblaciones, e incorporar una vista geográfica 3D."

## Clarifications

### Session 2026-11-18

- Q: ¿Cómo debe mostrarse en el globo 3D la profundidad de los terremotos? → A: Marcadores en superficie con escala de profundidad y valor en la ficha; no representar los eventos como puntos subterráneos.
- Q: ¿Cómo debe calcular el comparador las diferencias entre el primer grupo y el segundo? → A: Diferencia con signo calculada como segundo grupo menos primero.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Consultar eventos por páginas (Priority: P1)

Como visitante del observatorio, quiero recorrer los eventos consultados en páginas controlables desde el resumen y la exploración, para acceder a los resultados sin depender de un desplazamiento infinito.

**Why this priority**: Las tablas son una vía principal para consultar los eventos y su uso se degrada cuando la lista solo puede recorrerse mediante desplazamiento continuo.

**Independent Test**: Consultar un conjunto de eventos que abarque varias páginas en ambos apartados; comprobar tamaño de página, navegación, total de resultados y conservación de filtros.

**Acceptance Scenarios**:

1. **Given** que una consulta devuelve más eventos que el tamaño de página, **When** el visitante abre la tabla del resumen o de exploración, **Then** ve solo la página actual, el tamaño elegido, el total de resultados y controles para avanzar y retroceder.
2. **Given** que hay varias páginas disponibles, **When** el visitante cambia de página, **Then** se muestran los eventos correspondientes sin duplicar ni omitir registros y se conservan los filtros activos.
3. **Given** que el visitante cambia los filtros o el tamaño de página, **When** se actualizan los resultados, **Then** la navegación vuelve a una página válida y el total refleja la nueva consulta.
4. **Given** que la consulta no devuelve eventos, **When** se muestra la tabla, **Then** se indica que no hay resultados y no aparecen páginas vacías como si contuvieran datos.

### User Story 2 - Reconocer el evento más reciente en el mapa (Priority: P1)

Como visitante, quiero distinguir de inmediato el evento sísmico más reciente representado en el mapa 2D, para identificar cuál ocurrió último sin revisar cada ficha.

**Why this priority**: El evento más reciente es una referencia temporal clave y debe distinguirse de un vistazo en la visualización principal.

**Independent Test**: Presentar eventos con distintos tiempos de ocurrencia, incluyendo una respuesta desordenada y un tiempo de actualización diferente; verificar cuál se identifica y cómo se muestra.

**Acceptance Scenarios**:

1. **Given** que el mapa contiene eventos con tiempos de ocurrencia válidos, **When** se muestra el mapa, **Then** el evento con el tiempo de ocurrencia más reciente se distingue visualmente y se identifica como el más reciente.
2. **Given** que el orden recibido no coincide con el orden temporal, **When** se determina el evento más reciente, **Then** se usa el tiempo de ocurrencia y no el orden de respuesta ni el tiempo de actualización o ingesta.
3. **Given** que no hay eventos o ninguno tiene un tiempo de ocurrencia válido, **When** se muestra el mapa, **Then** no se destaca un evento arbitrario y se conserva la indicación adecuada de ausencia o dato desconocido.
4. **Given** que el visitante selecciona el evento destacado, **When** abre su ficha, **Then** los datos de la ficha corresponden al mismo evento identificado en el mapa.

### User Story 3 - Comparar periodos y poblaciones (Priority: P2)

Como visitante, quiero definir y comparar dos o más grupos de eventos por periodo y población geográfica, para observar diferencias estadísticas entre periodos, países o combinaciones de ambos.

**Why this priority**: La comparación histórica fija una referencia temporal y no permite formular una comparación múltiple entre periodos y poblaciones elegidos por el visitante.

**Independent Test**: Comparar dos o más grupos con periodos y países conocidos; contrastar los resultados mostrados con cálculos independientes para recuentos, tasas diarias y distribuciones.

**Acceptance Scenarios**:

1. **Given** que el visitante añade grupos de comparación, **When** elige el conjunto de datos actual o histórico y define para cada uno un periodo y una población geográfica, **Then** puede comparar entre dos y cinco grupos del mismo conjunto de datos, incluyendo grupos con periodos distintos, poblaciones distintas o ambos.
2. **Given** que los grupos tienen distinta duración, **When** se presentan sus recuentos, **Then** se muestran tanto los totales como las tasas diarias para que las diferencias de duración no se confundan con diferencias de actividad.
3. **Given** que existen datos válidos de magnitud y profundidad, **When** se muestran las distribuciones comparadas, **Then** se presentan sus proporciones por intervalo y las diferencias en puntos porcentuales, junto con los valores válidos y ausentes.
4. **Given** que un grupo no tiene eventos o carece de datos válidos para una medida, **When** se calcula la comparación, **Then** se comunica la ausencia y no se inventan diferencias, porcentajes ni valores.
5. **Given** que falla la consulta de uno de los grupos, **When** se presenta la comparación, **Then** la API devuelve un error explícito con el índice del grupo afectado y no presenta una comparación parcial como exitosa.
6. **Given** que también está disponible la comparación histórica existente, **When** el visitante abre el comparador, **Then** la comparación definida por el visitante se presenta como una función distinta y no modifica ni sustituye la comparación histórica.

### User Story 4 - Explorar eventos sobre un globo 3D (Priority: P3)

Como visitante, quiero explorar los eventos en una vista geográfica tridimensional, para relacionar su ubicación con la profundidad informada y comprender mejor su distribución espacial.

**Why this priority**: La vista tridimensional aporta una forma complementaria de explorar ubicaciones y profundidades, pero no es necesaria para consultar las tablas ni la actividad en el mapa principal.

**Independent Test**: Abrir la vista 3D con eventos de ubicación y profundidad conocidas; comprobar su posición, selección y ficha, así como el tratamiento de ubicaciones o profundidades desconocidas.

**Acceptance Scenarios**:

1. **Given** eventos con coordenadas y profundidad válidas, **When** el visitante abre la vista 3D, **Then** los eventos aparecen como marcadores en sus ubicaciones geográficas sobre la superficie del globo, su profundidad se muestra mediante una escala visual explícita relativa a la superficie y el valor exacto puede consultarse en la ficha.
2. **Given** un evento con ubicación válida pero profundidad desconocida, **When** se presenta en la vista 3D, **Then** se indica que su profundidad es desconocida y no se le atribuye una profundidad ficticia.
3. **Given** un evento con ubicación inválida, **When** se presenta la vista 3D, **Then** no se representa como una ubicación válida y se informa de la limitación cuando afecte a los resultados.
4. **Given** que la vista 3D no está disponible o no puede cargar sus datos, **When** el visitante vuelve a las demás vistas, **Then** la paginación, el mapa 2D y la consulta de eventos continúan disponibles.

### Edge Cases

- La consulta tiene exactamente una página, una página parcialmente llena o cero resultados: los controles y el total deben reflejar cada caso sin páginas inexistentes.
- Una actualización de filtros reduce el total por debajo de la página seleccionada: la tabla vuelve a una página válida y no muestra una página vacía engañosa.
- La respuesta de eventos está truncada o paginada: el total y los controles deben corresponder al conjunto completo consultable, no presentar una muestra como si fuera el total.
- Dos eventos comparten el tiempo de ocurrencia más reciente: ambos se identifican como empatados en la fecha más reciente, sin escoger uno arbitrariamente.
- Un evento carece de tiempo de ocurrencia válido: no puede convertirse en el más reciente por tener una fecha de actualización o ingesta más nueva.
- Un país no puede asignarse al evento: se puede incluir en la población «Sin país asignado» y no se le atribuye un país por proximidad.
- Los grupos de comparación usan rangos con inicio igual o posterior al final, o una población que no existe: se rechaza la selección con un mensaje comprensible y no se presentan resultados como válidos.
- Los periodos tienen distinta duración o uno de ellos está vacío: los totales se mantienen diferenciados de las tasas normalizadas y las medidas no calculables se indican como no disponibles.
- La magnitud o profundidad es nula: el dato se contabiliza como ausente y no se incluye en el denominador de porcentajes.
- La profundidad conocida se representa como información visual relativa a un marcador en la superficie; no se dibuja como una ubicación subterránea ni se convierte en una altura geográfica.
- Se comparan grupos con cobertura de datos incompleta: se comunica la limitación por grupo y no se interpreta la falta de cobertura como ausencia de eventos.
- Falla una consulta de tabla, mapa o comparación: se muestra el error en la vista afectada y no se transforma en una lista vacía o en valores cero.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Las tablas de eventos del resumen y de exploración DEBEN ofrecer paginación controlada y no depender exclusivamente de desplazamiento infinito.
- **FR-002**: La paginación DEBE ofrecer tamaños de 25, 50 o 100 eventos por página y seleccionar 25 por defecto.
- **FR-003**: Cada tabla DEBE mostrar la página actual, el tamaño de página, el total de eventos coincidentes y la navegación disponible.
- **FR-004**: Cambiar de página DEBE conservar los filtros de la consulta; cambiar filtros DEBE reiniciar la navegación a una página válida y actualizar el total.
- **FR-005**: La paginación DEBE permitir recorrer el conjunto completo de resultados coincidentes sin omisiones ni duplicados, e indicar explícitamente los errores o las limitaciones de cobertura.
- **FR-006**: El mapa 2D DEBE mostrar todos los eventos coincidentes con los filtros de la consulta que pueda recuperar la API, paginando internamente las solicitudes cuando sea necesario; DEBE permitir identificar y seleccionar un evento para consultar sus datos.
- **FR-007**: El mapa 2D DEBE destacar visualmente el evento o los eventos con el tiempo de ocurrencia válido más reciente, identificado en la interfaz como «Más reciente».
- **FR-008**: Para determinar el evento más reciente, el sistema DEBE utilizar el tiempo de ocurrencia; no DEBE sustituirlo por el orden de respuesta, el tiempo de actualización ni el de ingesta.
- **FR-009**: El mapa DEBE respetar la atribución cartográfica vigente y comunicar explícitamente si, tras solicitar todas las páginas, los datos siguen truncados o no cubren todos los resultados.
- **FR-010**: El comparador DEBE permitir definir entre dos y cinco grupos y, para cada grupo, un periodo con inicio inclusivo y final exclusivo, y una población geográfica. El visitante DEBE elegir un conjunto de datos actual o histórico común a todos los grupos de la misma comparación.
- **FR-011**: Para esta versión, una población geográfica DEBE definirse como todos los eventos, los eventos asociados a un país seleccionable del catálogo o los eventos sin país asignado. No se incluyen áreas dibujadas por el usuario ni subdivisiones geográficas que no estén disponibles en el catálogo.
- **FR-012**: El comparador DEBE aplicar de manera equivalente a todos los grupos los filtros de evento compartidos, incluida cualquier magnitud mínima seleccionada, y mostrar los periodos, poblaciones y filtros efectivos utilizados.
- **FR-013**: Para cada grupo, el comparador DEBE presentar el total de eventos, la tasa diaria de eventos, y las distribuciones de magnitud y profundidad con unidades, intervalos, conteos válidos y ausentes y porcentajes.
- **FR-014**: El comparador DEBE presentar, entre grupos, las diferencias con signo de totales y tasas diarias y las diferencias con signo en puntos porcentuales para los intervalos de magnitud y profundidad que puedan compararse; cada diferencia se calcula como el valor del segundo grupo menos el del primero.
- **FR-015**: Cuando una medida tenga un denominador cero, datos ausentes o cobertura insuficiente, el comparador DEBE indicarlo como no disponible; no DEBE generar porcentajes o diferencias engañosos.
- **FR-016**: La comparación múltiple definida por el visitante DEBE mantenerse separada de la comparación histórica existente, que conservará su semántica y resultado.
- **FR-017**: La vista geográfica 3D DEBE permitir explorar un globo con los eventos de ubicación válida como marcadores en la superficie, representar la profundidad conocida mediante una escala visual explícita relativa a esa superficie y permitir consultar su valor exacto en la ficha de cada evento; no DEBE representar el evento como una posición subterránea.
- **FR-018**: La vista 3D DEBE indicar las profundidades desconocidas sin asignarles un valor ficticio y excluir de la representación geográfica las ubicaciones inválidas.
- **FR-019**: Las visualizaciones geoespaciales avanzadas adicionales DEBEN ser complementarias; su ausencia o fallo no DEBE impedir la consulta tabular, el mapa 2D ni la vista 3D principal.
- **FR-020**: Las vistas DEBEN distinguir una consulta exitosa sin resultados de un error, y comunicar de forma explícita los errores, datos desactualizados y limitaciones de cobertura que afecten a la interpretación.

### Key Entities *(include if feature involves data)*

- **Evento sísmico**: Registro con identificador, tiempo de ocurrencia, geometría, magnitud, profundidad y país asociado cuando estén disponibles.
- **Página de resultados**: Segmento visible de una consulta de eventos, identificado por su número de página y tamaño, junto con el total de resultados coincidentes.
- **Grupo de comparación**: Población de eventos definida por un periodo, una población geográfica y los filtros compartidos por la comparación.
- **Población geográfica**: Conjunto de todos los eventos, los eventos de un país del catálogo o los eventos sin país asignado.
- **Resultado estadístico**: Recuento, tasa diaria o distribución de una medida para un grupo, incluidos sus valores válidos, ausentes y diferencias comparables.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: En pruebas con resultados que ocupen varias páginas, el 100 % de los eventos coincidentes puede recorrerse una sola vez y el total mostrado coincide con el total de la consulta.
- **SC-002**: Con una fixture reproducible de 1.000 eventos, se medirán 100 cambios de página en cada tabla para cada tamaño permitido (25, 50 y 100), desde la solicitud de navegación hasta que se rendericen los eventos solicitados; al menos el 95 % de los cambios en cada combinación de tabla y tamaño debe completarse en menos de 2 segundos. La documentación de la prueba debe registrar navegador/dispositivo, entorno de API y base de datos, tamaño de página y método de medición.
- **SC-003**: En una prueba sin ayuda con diez participantes, al menos nueve identifican correctamente el evento más reciente en menos de 10 segundos desde que el mapa termina de mostrarse.
- **SC-004**: En el 100 % de los casos de prueba del comparador, los totales, tasas diarias, proporciones por intervalo y diferencias mostradas coinciden con cálculos independientes y declaran correctamente los datos ausentes.
- **SC-005**: En el 100 % de los casos de prueba 3D, cada evento con ubicación válida y profundidad conocida se representa con esos datos, y ningún evento con profundidad desconocida recibe una profundidad inventada.
- **SC-006**: En una prueba sin ayuda con diez participantes, al menos nueve encuentran un evento indicado usando la paginación y explican correctamente el periodo y la población de una comparación.

## Assumptions

- Los eventos, el catálogo de países y los metadatos estadísticos disponibles en el proyecto son la fuente de verdad; no se infieren ubicaciones, países, tiempos ni profundidades.
- «Región» se concreta para esta versión como país del catálogo o «Sin país asignado», además de la población global. La comparación de polígonos libres y otras jerarquías geográficas queda fuera de alcance.
- Cada comparación utiliza un único conjunto de datos —actual o histórico— común a sus grupos; el resultado identifica ese conjunto y comunica la cobertura disponible. No se combinan silenciosamente eventos de conjuntos distintos.
- Cada comparación incluirá dos o más grupos definidos de manera independiente; las diferencias serán descriptivas y no inferirán significancia estadística, causalidad ni riesgo sísmico.
- Los periodos usan UTC, con inicio inclusivo y final exclusivo. Las tasas diarias normalizan la duración del periodo, y los porcentajes de distribución excluyen valores ausentes.
- En el globo, los eventos se sitúan en su ubicación geográfica sobre la superficie; la profundidad se comunica mediante una escala visual y el valor exacto, no mediante una altura inventada ni un punto subterráneo que quede oculto por el globo.
- Los intervalos de las distribuciones mantienen las unidades y anchuras declaradas por las estadísticas existentes; las medidas no disponibles no se sustituyen por cero.
- La comparación histórica existente se mantiene sin cambios y no satisface por sí sola los requisitos del nuevo comparador.
- La vista 3D y las visualizaciones avanzadas son complementarias; las capacidades de consulta y mapa 2D siguen siendo utilizables aunque no carguen.
