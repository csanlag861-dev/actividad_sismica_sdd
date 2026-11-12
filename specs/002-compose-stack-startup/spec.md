# Feature Specification: Arranque fiable y procesamiento del stack Compose

**Feature Branch**: `main`

**Created**: 2026-11-12

**Status**: Draft

**Input**: User description: Crear `compose.yaml` con productor, Kafka, consumidor, PostgreSQL y API en servicios separados; comprobar disponibilidad de PostgreSQL y Kafka mediante sus nombres/listeners internos, definir healthchecks, reintentos y logs ante dependencias no preparadas, definir el modelo con SQLAlchemy y Alembic y verificar el procesamiento live y replay. En esta entrega no se crea ningún endpoint HTTP: la API funcional se desarrollará después.

## Clarifications

### Session 2026-11-12

- Q: ¿Qué alcance del modelo lógico debe utilizar la inicialización del esquema del backend? → A: Seguir el alcance de ROADMAP R09: evento actual, versiones, dimensiones geográfica/temporal, original, estado de consultas de ingesta y cuarentena; proponer otras tablas necesarias y justificar cada tabla y sus campos.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Preparar el esquema desde el backend (Priority: P1)

Como responsable de ejecutar el observatorio, quiero que el servicio backend prepare y mantenga disponible el esquema PostgreSQL desde las migraciones versionadas, para que productor y consumidor trabajen sobre una base consistente sin inicialización manual.

**Why this priority**: El almacenamiento versionado y durable es un prerrequisito del procesamiento. En esta entrega el servicio Compose `api` ejecuta la inicialización y supervisión del backend, pero no inicia FastAPI/Uvicorn ni expone endpoints; la API de consulta pertenece a una entrega posterior.

**Independent Test**: Con una base vacía, iniciar el servicio `api` junto a PostgreSQL; comprobar que Alembic aplica el esquema, el servicio permanece saludable solo mientras la base y la revisión estén disponibles, y no hay rutas HTTP ni puertos publicados.

**Acceptance Scenarios**:

1. **Given** una base PostgreSQL vacía, **When** se inicia el stack, **Then** el backend aplica la revisión inicial antes de que los clientes dependientes empiecen a procesar.
2. **Given** un esquema con datos persistidos, **When** se reinicia el stack y vuelve a aplicarse Alembic, **Then** no se borran datos ni se duplican objetos estructurales.
3. **Given** PostgreSQL no acepta conexiones o falla una migración, **When** se inicia el servicio `api`, **Then** este registra el error, reintenta los fallos transitorios y no se declara saludable hasta poder verificar la revisión.
4. **Given** esta entrega no implementa HTTP, **When** se inspeccionan los cinco servicios, **Then** el servicio `api` no ejecuta Uvicorn, no define endpoints y no publica puertos.

---

### User Story 2 - Procesar eventos live de extremo a extremo (Priority: P2)

Como responsable de la ejecución, quiero que el productor consulte el feed reciente, publique versiones nuevas en Kafka y que el consumidor las valide, enriquezca y persista de forma idempotente para poder demostrar el pipeline completo sin depender de la API de consulta.

**Why this priority**: El repositorio debe demostrar un recorrido real desde USGS hasta PostgreSQL, incluyendo revisiones, datos originales, calidad y persistencia transaccional.

**Independent Test**: En un entorno con el esquema aplicado, procesar mensajes de prueba y una respuesta válida del feed USGS; consultar PostgreSQL para verificar procedencia, versión actual, enriquecimiento y cuarentena, sin invocar endpoints HTTP.

**Acceptance Scenarios**:

1. **Given** Kafka está saludable, **When** el productor y el consumidor inician, **Then** ambos usan el listener interno `kafka:9092`; el productor, el consumidor y el backend usan PostgreSQL en `postgres:5432`.
2. **Given** una consulta live correcta, **When** el productor compara `id` y `updated`, **Then** publica por Kafka las versiones nuevas con el evento original, modo, procedencia y hora de ingesta, y registra una versión publicada solo después del ACK.
3. **Given** el consumidor recibe una versión válida, **When** la procesa, **Then** conserva la versión, actualiza el evento actual solo si es más reciente, integra el país sin asignaciones por proximidad y confirma el offset después del commit PostgreSQL.
4. **Given** el consumidor recibe un duplicado, una versión antigua o un mensaje inválido, **When** procesa cada caso, **Then** no duplica ni retrocede el estado actual y persiste el rechazo con motivo y mensaje original antes de confirmar el offset.
5. **Given** la fuente USGS devuelve timeout, HTTP 429/5xx o JSON inválido, **When** el productor consulta el feed, **Then** reintenta con espera progresiva, registra el resultado de la consulta y no sustituye datos válidos por una respuesta de error.

---

### User Story 3 - Reproducir histórico sin contaminar datos live (Priority: P3)

Como responsable de la ejecución, quiero reproducir por Kafka una selección histórica en modo separado, conservando el tiempo original y el de procesamiento, para demostrar el pipeline sin mezclar resultados con los datos actuales.

**Why this priority**: El enunciado requiere una demostración controlada del pipeline cuando el feed live no produce novedades durante la defensa.

**Independent Test**: Publicar una selección de eventos históricos ordenada por fecha en el topic de replay; comprobar que el consumidor los procesa por el mismo camino que live, preserva sus fechas originales y no crea ni modifica filas live.

**Acceptance Scenarios**:

1. **Given** una selección del catálogo histórico USGS, **When** se inicia la reproducción, **Then** los eventos se publican en topic distinto con `mode=replay`, ordenados por fecha y sin alterar su tiempo de ocurrencia.
2. **Given** el consumidor procesa una reproducción, **When** persiste cada evento, **Then** `ingested_at` registra el tiempo de reproducción y las claves compuestas aíslan versiones y estado actual de live.
3. **Given** el mismo mensaje replay se reproduce más de una vez, **When** el consumidor lo procesa, **Then** las restricciones idempotentes evitan duplicados y no modifican el estado live.

---

### User Story 4 - Diagnosticar y recuperar el estado de los servicios (Priority: P4)

Como responsable de la ejecución, quiero healthchecks y logs útiles cuando una dependencia tarde o deje de responder, para saber qué servicio espera y confirmar su recuperación automática.

**Why this priority**: El arranque ordenado por Compose no basta para diagnosticar fallos ni recuperar conexiones posteriores.

**Independent Test**: Retrasar Kafka o PostgreSQL, verificar estado no saludable y logs sin secretos, restaurar la dependencia y comprobar que los cinco servicios vuelven a estar saludables sin reinicios manuales.

**Acceptance Scenarios**:

1. **Given** una dependencia requerida no disponible, **When** se inspecciona el estado de los servicios afectados, **Then** no aparecen saludables y los logs identifican destino, error e intento sin credenciales ni payloads sensibles.
2. **Given** la dependencia vuelve a estar disponible, **When** ocurre el siguiente reintento, **Then** los servicios se reconectan y recuperan su estado saludable.
3. **Given** falla PostgreSQL durante la migración o después del arranque, **When** el backend o un cliente intenta operar, **Then** reintenta, no confirma trabajo no persistido y no indica falsamente que está listo.
4. **Given** cualquiera de los cinco servicios deja de cumplir su función, **When** se ejecuta su healthcheck, **Then** el resultado es no saludable hasta que su dependencia y operación necesaria se recuperen.

### Edge Cases

- PostgreSQL tarda en aceptar conexiones mientras el backend, productor o consumidor ya han empezado.
- Kafka inicia el proceso del broker antes de que su listener interno acepte conexiones o antes de anunciar una dirección alcanzable desde otros contenedores.
- PostgreSQL se desconecta durante una migración o entre el commit de datos y el ACK de Kafka.
- La respuesta del feed no contiene eventos nuevos, contiene una revisión antigua o falla por timeout/HTTP 429/5xx/JSON inválido.
- El esquema ya existe y contiene datos cuando el backend vuelve a arrancar.
- El proceso de un servicio sigue vivo, pero una dependencia necesaria no responde; el healthcheck no debe confundir proceso activo con servicio listo.
- Un evento está en frontera o coincide con varios polígonos, tiene coordenadas inválidas o no pertenece a ningún país; no se asigna un país por proximidad.
- Un mensaje replay tiene el mismo `event_id` y `updated` que live; sus claves y topic no deben colisionar.
- Los logs registran errores sin imprimir credenciales, cadenas de conexión sensibles, secretos ni payloads.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: La solución MUST definir en `compose.yaml` cinco servicios separados para productor, Kafka, consumidor, PostgreSQL y API, que puedan iniciarse conjuntamente con el procedimiento de Compose documentado por el proyecto.
- **FR-002**: La solución MUST conservar los datos de PostgreSQL mediante almacenamiento persistente, de modo que reiniciar los contenedores no elimine el estado del observatorio.
- **FR-003**: El productor y el consumidor MUST conectarse a Kafka mediante el nombre de servicio `kafka` y el listener interno anunciado para clientes de la red Compose (por defecto, `kafka:9092`); no MUST depender de `localhost` dentro de un contenedor.
- **FR-004**: El productor, consumidor y API MUST localizar PostgreSQL mediante el nombre de servicio `postgres` (por defecto, `postgres:5432`). El productor la necesita para el estado persistente de versiones publicadas. La configuración de red MUST permitir esas conexiones internas sin exponer PostgreSQL ni Kafka a través del acceso público a la API.
- **FR-005**: El servicio Compose `api` MUST ejecutar el backend de SQLAlchemy/Alembic que inicializa y supervisa el esquema antes de declararse saludable. En esta entrega MUST NOT iniciar FastAPI/Uvicorn, definir endpoints HTTP ni publicar puertos; las rutas de consulta pertenecen a una entrega posterior.
- **FR-006**: La inicialización del esquema MUST ser repetible y no destructiva: al arrancar de nuevo con datos existentes no debe borrar datos ni volver a crear objetos o registros lógicos duplicados.
- **FR-007**: El esquema inicial MUST representar el evento actual, las versiones observadas, las dimensiones geográfica y temporal, los datos originales, las consultas/estado de ingesta, el estado de versiones publicadas y los registros rechazados con sus motivos. MUST preservar la distinción entre el estado actual y el historial de versiones y permitir claves/restricciones que eviten duplicar la identidad de eventos y versiones.
- **FR-008**: El esquema y el procesamiento MUST mantener los datos replay aislados de live mediante `mode`, claves compuestas y topics diferenciados o mecanismos equivalentes documentados. Replay MUST preservar el tiempo de ocurrencia y registrar el tiempo de reproducción.
- **FR-009**: Los cinco servicios MUST disponer de comprobaciones de salud adecuadas a su función. La salud del broker y de PostgreSQL MUST depender de su disponibilidad efectiva; la API MUST depender de poder alcanzar PostgreSQL y completar la inicialización del esquema; productor y consumidor MUST reflejar la disponibilidad de sus dependencias necesarias, no solo que el proceso siga activo.
- **FR-010**: Los servicios dependientes MUST reintentar conexiones fallidas con esperas progresivas mientras Kafka o PostgreSQL no estén listos y MUST alcanzar disponibilidad automáticamente cuando la dependencia responda, sin intervención o reinicio manual.
- **FR-011**: Mientras una dependencia requerida no esté lista, los servicios afectados MUST permanecer no saludables/no preparados y registrar logs que permitan identificar el servicio dependiente, el fallo de conexión y los reintentos. Los logs MUST omitir credenciales y secretos.
- **FR-012**: El backend MUST registrar explícitamente los fallos de conexión y migración y permanecer no saludable mientras no pueda confirmar acceso al esquema. No se define comportamiento HTTP en esta entrega porque no se implementan endpoints.
- **FR-013**: En esta entrega ningún servicio MUST publicar puertos al host ni exponer endpoints; Kafka y PostgreSQL permanecerán accesibles únicamente por la red de Compose. La futura API de consulta se expondrá en una entrega posterior conforme al contrato público.
- **FR-014**: El diseño del modelo MUST explicar, para cada tabla y campo propuestos, qué representa, por qué se necesita, de qué dato o proceso procede y cómo se relaciona con las demás entidades. MUST justificar las claves, opcionalidad e índices; toda tabla o campo adicional MUST tener una necesidad documentada.
- **FR-015**: El productor live MUST consultar el feed reciente de USGS aproximadamente cada 60 segundos, conservar el original y metadatos de consulta, comparar `id`/`updated`, usar el identificador de evento como clave Kafka y publicar solo versiones no confirmadas.
- **FR-016**: El productor MUST esperar el ACK Kafka antes de persistir `published_version`; si falla la publicación o la persistencia, MUST tolerar reenvío sin perder procedencia ni duplicar efectos.
- **FR-017**: El consumidor MUST validar cada mensaje, guardar versiones idempotentemente y actualizar `event_current` solo cuando `updated_at` sea posterior. MUST confirmar el offset solo después del commit de la versión válida o de la cuarentena.
- **FR-018**: El procesamiento válido MUST integrar el punto con el catálogo Natural Earth mediante `ADM0_A3` verificado como único. Puntos sin coincidencia o con varias coincidencias MUST conservar `country_id = NULL`; MUST NOT asignar país por proximidad. La fuente geográfica y la regla de frontera deben documentarse.
- **FR-019**: Los mensajes inválidos MUST conservar bytes originales, motivo y posición Kafka en cuarentena; reintentar el mismo offset no debe duplicar el registro.
- **FR-020**: El productor replay MUST obtener una selección histórica documentada (por defecto, año 2025, global, magnitud ≥4 y tipo earthquake), ordenarla por tiempo original y publicarla a un topic separado con `mode=replay`. El consumidor MUST reutilizar el mismo camino de validación y persistencia que live.

### Key Entities *(include if feature involves data)*

- **País**: Elemento del catálogo geográfico asociado a eventos cuando la ubicación pertenece a un país; su asociación puede ser desconocida.
- **Fecha**: Día UTC utilizado para agrupar o relacionar eventos, manteniendo los tiempos completos del evento.
- **Evento actual**: Estado más reciente conocido de un terremoto, con un único registro lógico por `(mode, event_id)`.
- **Versión de evento**: Cada versión recibida de un evento, identificada por el evento y su tiempo de actualización; se conserva aunque llegue una versión más antigua que la actual.
- **Estado de publicación**: Marca qué versión fue confirmada por Kafka para que el productor pueda distinguirla de versiones pendientes al reiniciarse.
- **Dato original**: Representación recibida de la fuente, conservada para explicar y reproducir las transformaciones aplicadas a cada versión.
- **Consulta de ingesta**: Registro de una consulta a la fuente y su resultado, necesario para distinguir una consulta correcta de una fallida y explicar la actualidad de los datos.
- **Registro en cuarentena**: Mensaje rechazado y motivo del rechazo, conservados para auditoría.
- **Datos de reproducción**: Eventos procesados en modo replay, identificables y aislados de los datos live para que no se mezclen en análisis posteriores.
- **Esquema de almacenamiento**: Estructura inicial que el servicio backend prepara para que productor y consumidor persistan las entidades anteriores; una entrega posterior añadirá las consultas HTTP.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Después de que las imágenes estén disponibles, al menos 4 de 5 arranques de prueba de un entorno limpio alcanzan el estado saludable de los cinco servicios en un máximo de 180 segundos, sin reinicios manuales.
- **SC-002**: En cinco pruebas con Kafka o PostgreSQL retrasados deliberadamente, los servicios dependientes se recuperan en menos de 60 segundos desde que la dependencia queda disponible y sin reiniciar manualmente ningún servicio.
- **SC-003**: En cinco de cinco pruebas de integración, productor y consumidor alcanzan Kafka y productor, consumidor y API alcanzan PostgreSQL mediante las direcciones internas configuradas, sin depender de una conexión al host anfitrión.
- **SC-004**: En cinco de cinco inicializaciones sobre una base vacía, el backend deja disponible el esquema requerido; en dos reinicios posteriores el esquema y los datos previamente guardados permanecen utilizables y no aparecen duplicados estructurales.
- **SC-005**: En todas las pruebas de dependencia no disponible, los logs permiten identificar el servicio y la dependencia que falla, y no contienen credenciales ni secretos.
- **SC-006**: En cinco de cinco pruebas live, un evento nuevo llega desde el productor a PostgreSQL con original y procedencia; la secuencia de duplicado, revisión posterior y revisión antigua produce exactamente una versión actual, conserva las versiones observadas y nunca retrocede el estado actual.
- **SC-007**: En cinco de cinco pruebas replay de al menos diez eventos históricos, el consumidor conserva el tiempo original, registra el tiempo de reproducción y no inserta ni modifica filas del modo live.
- **SC-008**: En cinco de cinco pruebas de rechazo, el mensaje original y su motivo quedan persistidos antes del ACK de Kafka; repetir el mismo topic/partition/offset no genera otra fila de cuarentena.

## Assumptions

- El nombre Compose `api` se conserva para cumplir el requisito de cinco servicios. Durante esta entrega es un proceso backend de inicialización/supervisión del esquema, no un servidor HTTP; FastAPI, Uvicorn y cualquier endpoint se añaden después.
- El usuario ha fijado SQLAlchemy para el mapeo de entidades y Alembic para generar y ejecutar migraciones; no se presupone que `metadata.create_all` sustituya al historial de migraciones.
- ROADMAP R09 define el alcance del modelo que debe diseñarse, pero deja pendiente decidir su estructura exacta. El FAQ presenta `pais`, `fecha`, `evento_actual`, `evento_version` y `cuarentena` como ejemplos, no como un esquema completo aprobado. El diseño propondrá cómo representar también los originales y las consultas de ingesta, y justificará cada tabla y campo; podrá añadir otros solo cuando explique su necesidad.
- Se utilizarán los nombres y puertos internos de los ejemplos documentados (`kafka:9092` y `postgres:5432`) salvo que Compose defina otros valores coherentes; en cualquier caso, los nombres y listeners anunciados deberán coincidir entre la configuración de servicios y sus clientes.
- Los reintentos ante dependencias temporalmente no disponibles continúan con espera progresiva hasta que la dependencia responda; el servicio no informa disponibilidad antes de conectarse y completar sus tareas de inicialización.
- La copia indicada por el enunciado como `frontend/public/datos/paises.geojson` es la fuente geográfica prevista. Si no está presente en el checkout, se restaurará desde la fuente Natural Earth documentando versión y procedencia; no se sustituirá por geocodificación aproximada.
- La API funcional, sus endpoints y la exposición por ngrok/host quedan explícitamente fuera de esta entrega; el frontend no forma parte del recorrido de aceptación.
- Los umbrales de 180 y 60 segundos son objetivos iniciales para pruebas locales después de disponer de las imágenes; no incluyen la descarga o construcción inicial de imágenes.
- Se preservan las responsabilidades y contratos del [enunciado](../../docs/ENUNCIADO.md), el [contrato de API](../../docs/CONTRATO-API.md), el [FAQ](../../docs/FAQ-ALUMNADO.md) y la [guía de entregables](../../docs/Guia-entregables-observatorio-sismico.md); esta especificación no amplía los endpoints públicos.
