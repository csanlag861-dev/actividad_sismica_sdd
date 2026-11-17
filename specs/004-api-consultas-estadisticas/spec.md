# Feature Specification: Consulta API y estadísticas sísmicas

**Feature Branch**: `[no creada]`

**Created**: 2026-11-17

**Status**: Completed

**Input**: User description: "A continuacion debemos implementar la consulta de eventos según contrato de api, implementar el endpoint de salud y estadísticas y configurar CORS y manejar el cliente. Esta tarea se centrará únicamente en estas características. En la siguiente tarea / spec nos centraremos en finalizar H6 que sería comenzar a implementar la web. Es decir, esta spec llevará a cabo R18, R19 y R20 de mi @ROADMAP.md"

## Clarifications

### Session 2026-11-17

- Q: ¿Qué debe considerar el endpoint de salud para informar que el servicio está operativo? → A: Comprobar la API y que la base de datos y su esquema estén disponibles; informar la última ingesta por separado.
- Q: Si la base de datos o su esquema no están disponibles, ¿qué respuesta debe recibir quien consulta el endpoint de salud? → A: Responder HTTP 503 si la base o el esquema no están disponibles; HTTP 200 si están disponibles, independientemente de la antigüedad de la ingesta.
- Q: ¿Cuándo debe el cliente advertir que los datos podrían estar desactualizados? → A: Advertir si falla la actualización y mostrar la fecha de última ingesta, sin umbral de antigüedad.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Consultar eventos sísmicos actuales (Priority: P1)

Como consumidor de los datos del observatorio, quiero consultar los terremotos actuales con filtros temporales, de magnitud y de país, para explorar información fiable y compatible con el contrato acordado.

**Why this priority**: La consulta de eventos es la base para que cualquier cliente del observatorio use los datos preparados y constituye R18.

**Independent Test**: Consultar una muestra conocida con y sin filtros, y comparar la respuesta con los eventos actuales de la muestra; repetir con una muestra vacía y con campos desconocidos.

**Acceptance Scenarios**:

1. **Given** que existen eventos actuales, **When** un consumidor consulta sin filtros, **Then** recibe una colección GeoJSON válida con los eventos ocurridos en las últimas 24 horas, metadatos de generación e ingesta y una sola versión actual por evento.
2. **Given** eventos dentro y fuera de un periodo, **When** el consumidor indica inicio y fin, **Then** se incluyen los eventos en el inicio inclusivo y se excluyen los que coinciden con el final exclusivo.
3. **Given** eventos con distintas magnitudes y países, **When** el consumidor aplica magnitud mínima o país, **Then** solo se incluyen los eventos que cumplen todos los filtros indicados y la magnitud desconocida no satisface el filtro de magnitud.
4. **Given** que un evento tiene profundidad desconocida, **When** se representa en GeoJSON, **Then** la geometría conserva coordenadas válidas de longitud y latitud y la profundidad se informa como `null` en sus propiedades.
5. **Given** que no hay eventos que cumplan la consulta, **When** se solicita la colección, **Then** se devuelve una colección vacía válida, no un error ni datos inventados.
6. **Given** que ocurre un fallo de almacenamiento, **When** se solicita la colección, **Then** el consumidor recibe un error explícito y no una colección vacía presentada como válida.
7. **Given** que una solicitud contiene parámetros desconocidos o inválidos, **When** se valida la consulta, **Then** la API responde con un estado no exitoso y el formato de error JSON común definido por el contrato.

---

### User Story 2 - Consultar salud y estadísticas (Priority: P2)

Como consumidor de los datos del observatorio, quiero conocer el estado del servicio y obtener estadísticas con su periodo, filtros y limitaciones, para interpretar correctamente la actualidad y distribución de los eventos.

**Why this priority**: El estado y las agregaciones completan la consulta de los datos y permiten validar su consistencia sin confundir errores, nulos o revisiones con resultados reales.

**Independent Test**: Consultar el estado y calcular manualmente recuentos por hora y país, distribuciones y comparación histórica sobre una muestra de control; repetir con filtros y con un fallo de almacenamiento.

**Acceptance Scenarios**:

1. **Given** que el servicio está operativo, **When** se consulta su estado, **Then** se informa del estado y de la fecha de la última ingesta correcta, sin exponer credenciales.
2. **Given** que la base de datos o el esquema no están disponibles, **When** se consulta el estado, **Then** se devuelve HTTP 503; si ambos están disponibles, se devuelve HTTP 200 incluso si no existe una ingesta o esta es antigua.
3. **Given** una muestra conocida, **When** se solicitan estadísticas, **Then** los recuentos por hora UTC y país, las distribuciones y la comparación histórica coinciden con cálculos sobre los eventos actuales de la muestra e incluyen los eventos sin país asignado.
4. **Given** una consulta de estadísticas con filtros, **When** se aplican los filtros, **Then** se utilizan las mismas reglas que en la consulta de eventos y cada resultado declara periodo, filtros, unidad y número de registros sin valor.
5. **Given** un fallo de almacenamiento durante una consulta de estadísticas, **When** se solicita el análisis, **Then** se comunica un error explícito y no se devuelve cero como si fuera un resultado correcto.

---

### User Story 3 - Exponer estado de consulta al consumidor (Priority: P3)

Como consumidor del módulo de transporte del navegador, quiero recibir los datos de la última consulta correcta y el estado de error o posible desactualización, para distinguir un fallo de conexión de una colección vacía sin requerir una interfaz gráfica en esta entrega.

**Why this priority**: Una consulta correcta depende también de que los clientes puedan comunicarse desde los orígenes permitidos y distinguir resultados válidos de fallos o datos antiguos.

**Independent Test**: Desde el origen de desarrollo y el origen publicado, comprobar la consulta y su preflight; simular una demora y una desconexión y verificar que el módulo de transporte expone el error, conserva la última lectura correcta y la distingue de una colección vacía.

**Acceptance Scenarios**:

1. **Given** un navegador en el origen publicado o en `http://localhost:4200`, **When** solicita datos y el navegador envía un preflight, **Then** el servicio permite el origen exacto, GET, OPTIONS y la cabecera `ngrok-skip-browser-warning`.
2. **Given** un origen no autorizado, **When** intenta leer la respuesta, **Then** el servicio no concede acceso CORS a ese origen.
3. **Given** una consulta que no termina dentro del límite de 15 segundos, **When** vence el plazo, **Then** el módulo de transporte expone un error de timeout distinto de una colección vacía.
4. **Given** que ya existe un resultado válido y la consulta posterior falla, **When** el módulo de transporte informa del problema, **Then** expone el último resultado correcto y un estado de posible desactualización junto con la fecha de última ingesta disponible, sin aplicar un umbral de antigüedad ni construir una interfaz visual.
5. **Given** que se configura el cliente para acceder al servicio, **When** se publica su configuración, **Then** la dirección de servicio puede cambiarse sin incluir credenciales o secretos en los recursos públicos.
6. **Given** que una consulta anterior falló, **When** el consumidor inicia una nueva consulta que termina correctamente, **Then** el módulo reemplaza la lectura conservada por la nueva, limpia el error y el estado de posible desactualización, y permite nuevas consultas tras cualquier fallo sin reintentos automáticos ni refresco periódico.
7. **Given** que la solicitud no obtiene una respuesta HTTP accesible por un fallo de red o bloqueo CORS, **When** el módulo expone el error, **Then** lo distingue de una respuesta HTTP no exitosa producida por la API y no atribuye con certeza un rechazo de transporte a CORS si el navegador no permite identificar la causa.

### Edge Cases

- La colección consultada no contiene eventos, pero el servicio de almacenamiento está disponible: se devuelve una colección vacía válida.
- La magnitud, profundidad o país de un evento son desconocidos: se conservan como `null` y se contabilizan aparte en las estadísticas aplicables.
- El periodo comienza o termina exactamente en la hora de un evento: el inicio se incluye y el final se excluye.
- Una revisión cambia hora, magnitud o país: consulta y estadísticas representan el estado actual y no cuentan la revisión como un evento nuevo.
- La muestra de comparación histórica contiene días sin eventos: esos días se incluyen en el promedio diario.
- El último periodo reciente puede estar incompleto por retrasos de ingesta: el cliente y las estadísticas no lo presentan como una cobertura completa.
- La última ingesta puede ser antigua o no existir aunque la API y la base de datos estén disponibles: el estado de salud continúa siendo operativo y comunica la fecha o `null`; el cliente solo advierte de posible desactualización cuando falla una actualización, sin un umbral de antigüedad.
- La URL del origen publicado cambia: solo se autoriza el origen exacto vigente, sin habilitar todos los orígenes mediante un comodín.
- Una configuración CORS contiene un origen malformado o un comodín: se informa explícitamente del error de configuración y no se ignora ni se inicia la API con una lista parcial.
- Un origen no autorizado realiza una solicitud: no recibe cabeceras CORS que permitan al navegador leer la respuesta; el cliente distingue este fallo de transporte de un estado HTTP no exitoso accesible devuelto por la API.
- El servicio o la red no responden antes del timeout: el módulo de transporte expone el fallo y conserva identificable la última lectura correcta para que una interfaz consumidora pueda mostrarla.
- El resultado de eventos excede un límite documentado: si se limita, se informa del total, truncamiento y mecanismo de continuación; las estadísticas globales no se calculan sobre una muestra parcial.
- Esta entrega no configura un refresco periódico del cliente: el consumidor inicia las consultas; el módulo solo define el estado y el resultado de cada actualización.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: La consulta `GET /api/eventos` MUST devolver HTTP 200 y una colección GeoJSON con metadatos de generación, última ingesta, modo, cantidad y estado de truncamiento.
- **FR-002**: Cada evento devuelto MUST aparecer una sola vez en su versión actual, con geometría de punto válida, coordenadas en orden longitud/latitud/profundidad en kilómetros cuando haya profundidad conocida, y fechas en milisegundos Unix UTC. Si la profundidad es desconocida, la geometría MUST mantener una posición válida de dos coordenadas y MUST informar `depth_km: null` en las propiedades.
- **FR-003**: La consulta de eventos MUST usar por defecto las últimas 24 horas y admitir inicio ISO 8601 inclusivo, fin ISO 8601 exclusivo, magnitud mínima y país.
- **FR-004**: Los valores desconocidos de magnitud, profundidad o país MUST expresarse como `null`; un evento sin magnitud MUST quedar fuera de una consulta con magnitud mínima y contabilizarse aparte donde corresponda.
- **FR-005**: Una consulta válida sin coincidencias MUST devolver una colección vacía. Los fallos de almacenamiento MUST comunicarse como errores explícitos, nunca como una respuesta vacía o agregación cero que parezca válida. Los parámetros desconocidos o inválidos MUST rechazarse con un estado no exitoso y el envelope de error JSON común; las solicitudes cuya sintaxis no pueda interpretarse MUST rechazarse explícitamente.
- **FR-006**: Si la consulta de eventos aplica un límite de tamaño, MUST comunicar el total completo, el truncamiento y cómo continuar la consulta.
- **FR-007**: La consulta `GET /api/salud` MUST devolver HTTP 200 cuando la API, la base de datos y el esquema estén disponibles, e HTTP 503 cuando la base de datos o el esquema no lo estén. MUST informar de la fecha de la última ingesta correcta —o `null` si aún no existe ninguna—, sin usar la antigüedad de la ingesta para cambiar el estado HTTP y sin incluir secretos ni credenciales.
- **FR-008**: La consulta `GET /api/estadisticas` MUST proporcionar recuentos en ventanas fijas de una hora UTC basadas en el tiempo de ocurrencia, recuentos por país, distribuciones de magnitud y profundidad y una comparación histórica sobre el estado actual de los eventos.
- **FR-009**: Las estadísticas MUST aplicar los filtros temporales, de magnitud y de país con las mismas reglas que la consulta de eventos, e indicar en cada resultado el periodo, los filtros, la unidad y el número de registros sin valor aplicable. Las distribuciones MUST usar bins semiabiertos `[k*w, (k+1)*w)` para enteros `k`, con anchura `w=0.5` para magnitud y `w=10 km` para profundidad. Cada distribución MUST incluir el recuento de valores válidos usado como denominador y calcular el porcentaje de cada bin como `100 * bin_count / valid_count`; los valores ausentes se contabilizan aparte y no forman parte del denominador. Si `valid_count` es cero, los porcentajes MUST ser `null`. El `missing_count` de magnitud MUST contar los nulos en el ámbito temporal/geográfico antes de `min_mag`; por ello, cuando se aplica ese filtro, puede no compartir población con `valid_count` y los bins.
- **FR-010**: Los recuentos por país MUST incluir la categoría de eventos sin país asignado. La comparación histórica MUST usar filtros equivalentes e incluir los días con cero eventos en su promedio diario.
- **FR-011**: Los fallos de almacenamiento durante una consulta estadística MUST producir un error explícito y no cifras de cero con apariencia de éxito.
- **FR-012**: El acceso desde navegador MUST autorizar los orígenes HTTPS exactos de publicación configurados y `http://localhost:4200` para desarrollo, permitir GET y OPTIONS y la cabecera `ngrok-skip-browser-warning`; MUST denegar acceso CORS a orígenes no configurados. Una configuración de orígenes malformada, con comodín o con valores no permitidos MUST generar un error explícito de configuración y MUST NOT ignorarse ni aplicarse parcialmente; si no hay origen de publicación configurado, solo se permite el origen de desarrollo. Un bloqueo CORS sin respuesta accesible MUST distinguirse de un estado HTTP no exitoso recibido de la API.
- **FR-013**: El módulo de transporte MUST aplicar un timeout de 15 segundos, distinguir fallos de una respuesta vacía, conservar identificable la última lectura correcta y exponer a su consumidor el estado de error o posible desactualización y la fecha de última ingesta disponible. MUST señalar posible desactualización cuando una actualización falle, sin aplicar un umbral de antigüedad ni requerir una interfaz visual en esta entrega.
- **FR-014**: La configuración pública del cliente MUST permitir especificar la dirección del servicio sin publicar secretos, credenciales ni tokens.
- **FR-015**: Cuando se limite una respuesta de eventos, las estadísticas MUST representar el conjunto completo consultado y no una muestra truncada.
- **FR-016**: Los errores HTTP por solicitudes malformadas, parámetros inválidos, indisponibilidad o fallo interno MUST usar el envelope JSON común definido por el contrato, con código y mensaje públicos; las respuestas MUST NOT exponer trazas, SQL, credenciales, valores secretos ni texto interno de excepciones.
- **FR-017**: Tras un fallo, una nueva consulta iniciada por el consumidor MUST poder ejecutarse. Si tiene éxito, el módulo MUST sustituir la última lectura correcta, limpiar el error y el estado de posible desactualización y actualizar sus metadatos; MUST NOT iniciar reintentos automáticos ni refresco periódico.

### Key Entities *(include if feature involves data)*

- **Evento sísmico actual**: Una entidad sísmica con identidad única, tiempo de ocurrencia, magnitud y profundidad opcionales, país opcional y geometría consultable. La profundidad desconocida se representa como `depth_km: null` y no como una posición GeoJSON no numérica.
- **Colección de eventos**: Resultado de una consulta con eventos actuales y metadatos que describen generación, ingesta, cantidad, modo y posible truncamiento.
- **Estado del servicio**: Estado observable del servicio de consulta y fecha de la última ingesta correcta.
- **Resultado estadístico**: Agregación de eventos para un periodo y filtros declarados, con unidad y cantidad de valores ausentes.
- **Lectura del cliente**: Último resultado satisfactorio conocido y el estado de la consulta más reciente, incluida su actualidad o error.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: El 100% de los casos de aceptación de eventos —colección completa sin límite, colección vacía, valores desconocidos, ventana predeterminada, límites temporales y filtros de magnitud y país— produce resultados que cumplen el contrato.
- **SC-002**: En una muestra de control, todos los recuentos por hora UTC/país, las distribuciones y la comparación histórica coinciden con los cálculos independientes; en cada distribución, los porcentajes usan como denominador solo valores válidos y los ausentes se informan aparte, incluidos nulos y días históricos sin eventos.
- **SC-003**: El 100% de las pruebas de salud devuelve el estado y la última ingesta conocida sin revelar credenciales; una indisponibilidad de almacenamiento nunca se presenta como cero eventos o estadísticas correctas.
- **SC-004**: Los preflights y consultas desde ambos orígenes autorizados se completan sin bloqueo CORS, mientras que los orígenes no autorizados no reciben permiso de lectura.
- **SC-005**: Una consulta que excede 15 segundos se identifica como timeout; en el 100% de los casos de fallo, el módulo de transporte distingue el error de una respuesta vacía y conserva la referencia a la última lectura correcta para su consumidor.
- **SC-006**: Ningún recurso público del cliente contiene credenciales, tokens ni secretos.

## Assumptions

- La ventana de consulta predeterminada es de 24 horas, como establece el contrato.
- La comparación histórica predeterminada sigue el ejemplo del enunciado: últimas 24 horas frente al promedio diario de 2025; usa los mismos filtros y cuenta también los días históricos sin eventos.
- Las distribuciones usan bins semiabiertos alineados a múltiplos de anchura 0.5 para magnitud y 10 km para profundidad.
- Cada distribución calcula porcentajes sobre el número de eventos que tienen un valor válido para esa variable dentro de la población a la que se aplican los filtros correspondientes. Devuelve `valid_count` y `missing_count` por separado; si no existen valores válidos, el porcentaje es `null`.
- El baseline histórico solo está disponible si los intervalos de ingesta completados cubren todo el año calendario 2025; si la cobertura es incompleta, se informa como no disponible, no como cero.
- El origen de publicación se configura con el dominio HTTPS exacto vigente. No se autoriza un comodín; el origen de desarrollo es `http://localhost:4200`.
- El límite de 15 segundos y la distinción entre error, última lectura válida y datos desactualizados siguen las expectativas del README existente.
- El alcance de cliente se limita a un módulo JavaScript nativo de transporte, timeout y exposición de estado para una interfaz consumidora. No se implementan temporizador de refresco periódico ni interfaz visual; la integración Angular del mapa, fichas, filtros de interfaz, tabla y gráficos corresponde a R21–R23 y a la siguiente especificación.
- La base y el estado de ingesta establecidos por las tareas previas R15–R17 son la fuente de los eventos actuales y del historial disponible.
- Si no se requiere un límite de tamaño para la consulta de eventos, se devuelve la colección completa; si se aplica uno, se cumplen las obligaciones de truncamiento y continuación del contrato.
