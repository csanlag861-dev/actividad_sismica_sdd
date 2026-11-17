# Feature Specification: Pipeline sísmico completo H5

**Feature Branch**: `[no creada]`

**Created**: 2026-11-16

**Status**: Completed

**Input**: User description: "Quiero poder completar una ingesta, procesar datos reales, reintentos sin perder procedencia ni crear eventos/versiones incorrectas ni duplicar datos. Para ello, debemos implementar el productor live de USGS y posteriormente implementar la validacion, limpieza y cuarentena del consumidor. Luego, implementar la persistenia idempotente y versionada, incorporar el catálogo y enrequicimiento geográfico y luego cargar el histórico y conservar origen. Básicamente, quiero construir el pipeline completo que se especifica en este archivo ROADMAP.md en el HITO H5. Puedes consultar la documentacion en docs si surge alguna duda ya que son nuestra fuente de verdad. En caso de que tengas dudas, puedes preguntarme."

## Clarifications

### Session 2026-11-16

- Q: Si llega el mismo evento con la misma marca de actualización, pero con datos distintos, ¿cómo debe tratarse? → A: Reemplazar in-place los datos de esa versión por el payload entrante más reciente, mantener una sola versión y un solo Feature/hash aceptado para esa identidad, sin cuarentena por conflicto.
- Q: ¿Durante cuánto tiempo deben conservarse los originales de eventos y las respuestas históricas descargadas? → A: Conservar cada original distinto mientras exista el dato procesado correspondiente, deduplicar copias idénticas y documentar la limpieza.
- Q: ¿Qué debe ocurrir si un evento cae exactamente en una frontera o coincide con varios países del catálogo? → A: Asignar «Sin país asignado» cuando no exista una única coincidencia inequívoca.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ingerir novedades de USGS con su procedencia (Priority: P1)

Como responsable del observatorio, quiero recoger periódicamente eventos y revisiones recientes de USGS, para procesar datos reales y poder explicar de dónde proviene cada dato.

**Why this priority**: La ingesta live inicia el pipeline y proporciona eventos y versiones que deben conservarse y procesarse.

**Independent Test**: Con respuestas de fuente controladas, comprobar que cada contenido GeoJSON original distinto queda archivado antes de transformarse, que las consultas repetidas conservan metadatos de extracción sin duplicar el archivo, y que las novedades y revisiones mantienen su Feature original y procedencia.

**Acceptance Scenarios**:

1. **Given** una fuente disponible con un evento nuevo, **When** se realiza una consulta live, **Then** se registra el evento original con su identificador, versión, origen, hora de ingesta y modo live.
2. **Given** que se vuelve a consultar la misma versión con el mismo contenido que el payload actualmente aceptado, **When** se compara con el estado ya conocido, **Then** no se repiten la publicación ni los efectos de persistencia.
3. **Given** una interrupción temporal o una respuesta defectuosa de la fuente, **When** se reintenta la consulta, **Then** el último estado válido se conserva y el error no se presenta como una consulta correcta.
4. **Given** una respuesta live completa de GeoJSON, **When** el productor extrae sus eventos, **Then** archiva primero el original completo y vincula su huella y ubicación a la ejecución de extracción.
5. **Given** dos consultas con respuestas originales idénticas, **When** se registran ambas ejecuciones, **Then** comparten un único archivo original y cada ejecución conserva sus propios metadatos de extracción.

---

### User Story 2 - Validar y aislar datos no procesables (Priority: P2)

Como responsable del observatorio, quiero que cada registro se valide y que los que no puedan procesarse se conserven con el motivo, para evitar datos engañosos y poder revisar los rechazos.

**Why this priority**: Los eventos deben pasar controles de calidad antes de afectar al estado consultable; un dato defectuoso no debe perderse ni detener indefinidamente el procesamiento.

**Independent Test**: Procesar registros válidos, no sísmicos y malformados, y comprobar sus resultados, motivos y referencias a los originales.

**Acceptance Scenarios**:

1. **Given** un terremoto con fecha y geometría válidas y campos opcionales nulos, **When** se procesa, **Then** se conservan los nulos como desconocidos y el registro sigue siendo utilizable.
2. **Given** un registro que no sea un terremoto, **When** se procesa, **Then** queda excluido de los eventos actuales con un motivo identificable.
3. **Given** un registro no procesable por campos, tipos, fecha o coordenadas inválidas, **When** se procesa, **Then** su original, motivo y referencia al mensaje quedan en cuarentena duradera antes de darlo por atendido.

---

### User Story 3 - Mantener versiones actuales correctas ante reintentos (Priority: P3)

Como responsable del observatorio, quiero que la repetición o llegada desordenada de mensajes no duplique eventos ni haga retroceder su versión actual, para que las consultas reflejen el estado más reciente conocido.

**Why this priority**: Reintentos y revisiones forman parte normal de la ingesta; los recuentos deben representar eventos y versiones distintas, no el número de mensajes recibidos.

**Independent Test**: Procesar la secuencia de control E1 10:05, repetición E1 10:05, revisión E1 10:09, repetición tardía de E1 10:05 y E2 10:12. El resultado debe ser dos eventos actuales y tres versiones distintas, con E1 en su versión 10:09.

**Acceptance Scenarios**:

1. **Given** una versión ya procesada, **When** se recibe el mismo mensaje otra vez, **Then** no cambia el número de eventos actuales ni el de versiones distintas.
2. **Given** una revisión posterior de un evento, **When** se procesa, **Then** se conserva la revisión y el estado actual se actualiza sin crear un segundo evento.
3. **Given** que llega una versión anterior después de la revisión, **When** se procesa, **Then** el estado actual permanece en la versión más reciente conocida.
4. **Given** que el proceso se interrumpe tras guardar el resultado, **When** el mensaje se recibe de nuevo al reanudar, **Then** el efecto persistido sigue siendo único y coherente.
5. **Given** la misma identidad `(mode, event_id, updated_at)` con otro contenido, **When** se recibe el payload nuevo, **Then** se actualiza la única fila de esa versión y su fuente/hash por el payload entrante, sin crear otra versión ni una cuarentena por conflicto.

---

### User Story 4 - Enriquecer eventos con el catálogo geográfico (Priority: P4)

Como responsable del observatorio, quiero asociar a cada evento los atributos del país que cubre su ubicación, para poder analizar los datos geográficamente sin atribuciones inventadas.

**Why this priority**: El catálogo es la fuente geográfica complementaria necesaria para enriquecer eventos; la ubicación textual o la proximidad no son sustitutos fiables.

**Independent Test**: Usar puntos de control en países, en el mar y en fronteras o zonas con más de una coincidencia, y verificar la regla documentada y los atributos asignados.

**Acceptance Scenarios**:

1. **Given** un evento dentro de un país del catálogo, **When** se enriquece, **Then** se conservan el identificador verificado y los atributos correspondientes al catálogo original.
2. **Given** un evento marítimo o sin coincidencia inequívoca, **When** se enriquece, **Then** permanece como «Sin país asignado» y no se asigna por texto ni cercanía.
3. **Given** un punto en una frontera o con varias coincidencias no inequívocas, **When** se enriquece, **Then** permanece como «Sin país asignado».

---

### User Story 5 - Incorporar el histórico conservando su origen (Priority: P5)

Como responsable del observatorio, quiero cargar un periodo histórico reproducible con las mismas reglas de calidad y enriquecimiento, para disponer de datos históricos sin duplicarlos ni confundirlos con las novedades live.

**Why this priority**: El histórico completa el conjunto de datos y debe mantenerse aunque los eventos dejen de aparecer en la ventana móvil live.

**Independent Test**: Cargar intervalos históricos controlados, repetir su carga y reiniciar el sistema; comparar los recuentos, los originales y metadatos de extracción antes y después.

**Acceptance Scenarios**:

1. **Given** un intervalo histórico con resultados, **When** se carga, **Then** se conservan sus originales, origen, filtros, intervalo, fecha de extracción y recuentos.
2. **Given** intervalos que comparten límites de tiempo o una respuesta que supera el límite de resultados de la fuente, **When** se divide y procesa la carga, **Then** no se pierden resultados ni se duplican eventos por el solapamiento.
3. **Given** una interrupción de la ingesta live superior a 24 horas, **When** se sigue el procedimiento de recuperación documentado, **Then** el hueco puede recuperarse sin borrar el histórico ni duplicar resultados existentes.

### Edge Cases

- La fuente live devuelve una ventana móvil de 24 horas; la ausencia de un evento en una consulta posterior no significa que deba borrarse.
- USGS responde con limitación temporal, error de servicio o red, JSON inválido o sin cambios.
- Campos opcionales como magnitud, profundidad o lugar son nulos, y hay valores inusuales que siguen siendo válidos.
- Un evento tiene fecha no interpretable, coordenadas no finitas o fuera de rango, o geometría distinta de un punto válido.
- El consumidor se detiene entre guardar un resultado o una cuarentena y confirmar que el mensaje se atendió.
- Llegan duplicados, revisiones con la misma marca temporal o versiones más antiguas después de una versión reciente.
- Llega un mismo evento con la misma marca de actualización pero con contenido distinto; se reemplazan en-place sus datos y su Feature/hash aceptados por los del último payload recibido, sin crear otra versión ni una cuarentena por conflicto.
- El catálogo no cubre el punto, o un punto coincide con una frontera o más de una entidad sin una coincidencia inequívoca; queda «Sin país asignado».
- Los intervalos históricos se solapan, superan el límite de respuesta o se vuelven a cargar tras un reinicio.
- La fuente deja de estar disponible durante una carga; los intervalos terminados y la procedencia ya conservada no se presentan como perdidos ni como completados falsamente.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema MUST programar consultas live a USGS en intervalos de 60 segundos usando reloj monotónico, con tolerancia máxima de 5 segundos respecto al instante programado. Cada solicitud tiene timeout de 8 segundos y hasta 3 reintentos, espaciados 1, 2 y 4 segundos, ante errores de red, HTTP 429/5xx o respuesta no interpretable; otros HTTP 4xx fallan sin reintento. Los reintentos pertenecen al mismo ciclo, no se solapan consultas y un ciclo fallido queda registrado antes del siguiente ciclo programado. Si un ciclo supera su próximo instante programado, se registra el intervalo perdido, no se solapa ni se ejecutan consultas de recuperación en ráfaga; se retoma en el siguiente instante futuro de la cadencia.
- **FR-002**: El sistema MUST distinguir versiones por evento y marca de actualización. Una entrega con identidad y contenido iguales al actualmente aceptado no debe repetir efectos; un contenido distinto con la misma identidad reemplaza en-place esa versión; timestamps distintos se conservan como versiones y solo el timestamp más reciente se proyecta como estado actual.
- **FR-003**: Antes de transformar una respuesta, el sistema MUST conservar su GeoJSON original completo y metadatos suficientes para identificar origen, momento de extracción, momento de ingesta y modo live o histórico. Debe conservar cada original distinto mientras exista el dato procesado correspondiente, deduplicar respuestas originales idénticas sin perder los metadatos de cada extracción y documentar la limpieza de originales que ya no estén vinculados a datos procesados.
- **FR-004**: El sistema MUST esperar confirmación de publicación antes de marcar una versión como publicada; un fallo no debe borrar el último estado válido ni ocultar la posibilidad de reenvío.
- **FR-005**: El sistema MUST validar campos requeridos, tipos, geometría, fechas y coordenadas; normalizar fechas a UTC sin perder los originales ni sus unidades.
- **FR-006**: El sistema MUST conservar como desconocidos los valores nulos y aceptar valores válidos aunque sean inusuales, salvo que una regla de rechazo esté documentada.
- **FR-007**: El sistema MUST excluir registros cuyo tipo no sea earthquake, conservar el motivo de exclusión y evitar que aparezcan como terremotos válidos.
- **FR-008**: El sistema MUST guardar duraderamente en cuarentena cada registro no procesable, junto con su original, motivo y referencia al mensaje; no debe darlo por atendido antes de conservar esa información.
- **FR-009**: El sistema MUST conservar una sola ocurrencia de cada versión identificada por modo, evento y marca de actualización, y mantener un solo estado actual por evento que solo avance a una versión más reciente. Si llega otra Feature con la misma identidad de versión y distinto contenido, MUST actualizar en-place los datos procesados, el Feature original y su hash por los del payload entrante; no crea otra versión ni una cuarentena por conflicto. Para una versión heredada sin original completo verificable, MUST etiquetar esa limitación y no inventar una huella completa; el payload entrante pasa a ser la fuente completa aceptada.
- **FR-010**: El sistema MUST hacer que reintentar un mensaje o carga ya persistidos no incremente el número de eventos actuales ni duplique las versiones, la cuarentena u otros efectos de persistencia.
- **FR-011**: El sistema MUST conservar de forma coherente cada versión y el estado actual; solo debe dar por atendido un mensaje después de persistir su resultado o su rechazo durable.
- **FR-012**: El sistema MUST enriquecer eventos con el catálogo geográfico suministrado, sin alterar el original, y conservar identificadores y atributos de país verificados.
- **FR-013**: El sistema MUST asignar «Sin país asignado» cuando no exista una coincidencia geográfica única e inequívoca, incluidos puntos en fronteras o con varias coincidencias; no debe inferir el país por el texto de ubicación o por proximidad.
- **FR-014**: El sistema MUST permitir cargar un año histórico completo; salvo que se documenten filtros alternativos, el alcance predeterminado será 2025, mundial, magnitud mínima 4 y tipo earthquake.
- **FR-015**: El sistema MUST dividir consultas históricas por intervalos cuando se alcance el límite de resultados de la fuente, deduplicar solapamientos y registrar intervalo, filtros, fecha de extracción y recuentos.
- **FR-016**: El sistema MUST aplicar a datos históricos las mismas reglas de validación, cuarentena, enriquecimiento e idempotencia que a los datos live, conservando su origen y su clasificación temporal.
- **FR-017**: El sistema MUST mantener los datos históricos aunque un evento desaparezca de la ventana móvil live y documentar cómo recuperar huecos causados por una interrupción live superior a 24 horas.
- **FR-018**: El sistema MUST permitir reconstruir y verificar la carga histórica desde los archivos originales o el registro de extracción, sin duplicar resultados.
- **FR-019**: El alcance de esta entrega termina al completar y verificar el pipeline del Hito H5; el servicio de consulta, el panel, las estadísticas, el despliegue público y la aceptación final pertenecen a hitos posteriores.

### Key Entities *(include if feature involves data)*

- **Evento sísmico**: Identidad estable del evento, tiempo de ocurrencia, ubicación y atributos medidos, que puede tener varias revisiones.
- **Versión de evento**: Observación del evento asociada a una marca de actualización; mantiene su original y su procedencia.
- **Extracción**: Consulta a una fuente, con origen, modo, fecha, filtros, intervalo y resultado registrado.
- **Registro procesado**: Evento validado y normalizado con sus atributos geográficos y vínculos a los datos de origen.
- **Registro en cuarentena**: Entrada no procesable conservada con el original, el motivo y la referencia a su recepción.
- **País del catálogo**: Entidad geográfica con identificador verificado y atributos procedentes del catálogo entregado.
- **Lote histórico**: Grupo de intervalos extraídos con filtros, fecha de ejecución y recuentos, reproducible sin duplicados.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Durante una ejecución estable, cada consulta live comienza dentro de los 5 segundos de su instante programado, a intervalos de 60 segundos y sin solaparse; cada ejecución vincula la respuesta GeoJSON completa archivada con su origen y metadatos de extracción, y cada evento/versión puede trazarse hasta esa respuesta y su Feature original. Una consulta fallida se reintenta como máximo 3 veces con esperas de 1, 2 y 4 segundos y timeout de 8 segundos por intento.
- **SC-002**: En la secuencia de control de cinco mensajes (evento nuevo, repetición, revisión posterior, versión antigua y segundo evento), el resultado es exactamente dos eventos actuales y tres versiones distintas; la revisión antigua no revierte el estado actual.
- **SC-003**: El 100 % de los registros de prueba no procesables queda conservado con original, motivo y referencia antes de avanzar su procesamiento; ninguno aparece como evento válido.
- **SC-004**: En los casos de control geográfico, todos los puntos con una única coincidencia reciben los atributos de esa entidad, y los puntos sin coincidencia, en fronteras o con varias coincidencias permanecen identificados como «Sin país asignado», sin inferencias por cercanía o texto.
- **SC-005**: Tras cargar dos veces un mismo conjunto de intervalos históricos y reiniciar, los recuentos de eventos y versiones permanecen iguales y coinciden con la carga única.
- **SC-006**: Un responsable puede trazar cada evento de control desde su origen live o histórico hasta su versión, resultado de validación, enriquecimiento o motivo de cuarentena, y repetir el procedimiento documentado para recuperar un hueco live superior a 24 horas.

## Assumptions

- La infraestructura del recorrido mínimo del Hito H4 y el modelo de datos de las fases anteriores están disponibles para completar este hito.
- El alcance histórico predeterminado sigue el enunciado: un año completo (2025), ámbito mundial, magnitud igual o superior a 4 y tipo earthquake. Todo filtro alternativo se registra y se mantiene igual durante la reconstrucción.
- Cada respuesta GeoJSON completa y cada Feature original distinto se conserva mientras exista el dato procesado correspondiente; las respuestas idénticas comparten archivo sin perder la trazabilidad de las ejecuciones, y la limpieza de originales no vinculados queda documentada.
- La falta de huella en filas heredadas se trata como desconocida, nunca se sustituye por una huella calculada a partir de un payload parcial; el primer payload completo entrante sustituye los datos de esa versión y se convierte en su fuente verificable.
- Los registros rechazados o excluidos se conservan separados de los eventos válidos; los campos desconocidos no se sustituyen por valores inventados.
- Los puntos de frontera o con varias coincidencias que no puedan atribuirse inequívocamente quedan como «Sin país asignado»; no se elige arbitrariamente un país.
- La recuperación de eventos que hayan desaparecido de la ventana live se realiza mediante el procedimiento histórico documentado; no se considera que la ausencia en el feed sea una eliminación.
