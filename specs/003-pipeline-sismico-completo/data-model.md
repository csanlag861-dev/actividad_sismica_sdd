# Data Model: Pipeline sísmico completo H5

## Alcance del modelo

El diseño amplía el esquema existente de `backend/src/observatorio/models/`. Una versión observada se identifica por modo, evento y timestamp `updated`; el hash determinista vive únicamente en `EventVersionSource` y permite reconocer una repetición exacta o reemplazar en-place el contenido de esa identidad. Los datos procesados se separan por modo (`live` o `replay`) para mantener el flujo de reproducción/histórico aislado.

## Entidades

### IngestionRun — ejecución de extracción

Una consulta live o una carga histórica de un periodo. La actual tabla `ingestion_run` se amplía con parámetros y resultado de extracción.

| Campo | Tipo conceptual | Regla |
|---|---|---|
| `run_id` | UUID | Clave primaria; única por ejecución. |
| `mode` | enum `live`, `replay` | Distingue consulta live de histórico/replay. |
| `source` | texto | URL/feed o fuente identificable; nunca contiene secretos. |
| `started_at`, `finished_at` | instante UTC nullable | Inicio y fin de ejecución. |
| `outcome` | enum `running`, `succeeded`, `failed` | Solo `succeeded` cuando la operación termina y registra su resultado. |
| `request_start`, `request_end` | instante UTC nullable | Límites del periodo solicitado, no la hora de extracción. |
| `query_metadata` | objeto JSON | Filtros, intervalos, status HTTP, páginas, conteos, huella de la respuesta y detalles de ejecución no secretos. |
| `source_archive_sha256` | SHA-256 nullable | FK al archivo GeoJSON original completo asociado a la respuesta de esta ejecución; ejecuciones con contenido idéntico pueden compartir archivo. |
| `records_received` | entero no negativo | Registros recibidos de la fuente. |
| `error_code`, `error_summary` | texto nullable | Fallo explícito sin credenciales ni payload sensible en logs. |

Relaciones: una ejecución tiene cero o más `IngestionInterval`, puede ser referenciada por muchas `EventVersionSource` y `Quarantine`, y referencia el archivo original completo de su respuesta.

### SourceArchive — respuesta GeoJSON original

Registro nuevo para contenido de respuesta original, tanto live como histórico. La clave es `sha256`; el archivo se escribe atómicamente en un volumen persistente antes de transformar o publicar Features.

| Campo | Tipo conceptual | Regla |
|---|---|---|
| `sha256` | SHA-256 | Huella del contenido original exacto; deduplica archivos idénticos. |
| `storage_path` | texto | Ruta durable bajo el volumen de archivos; no contiene credenciales. |
| `size_bytes` | entero no negativo | Tamaño del original archivado. |
| `source`, `created_at` | texto/instante UTC | Fuente y primera fecha de archivo. |
| `deleted_at` | instante UTC nullable | Fecha de limpieza auditable; un archivo reutilizado se recrea/verifica y limpia este campo. |

Cada `IngestionRun` conserva su propio registro y apunta a `SourceArchive`, incluso si el contenido ya existía. Un archivo se mantiene mientras al menos una ejecución que lo referencia tenga `EventVersionSource` o `Quarantine` asociado; al quedar sin datos procesados dependientes, puede limpiarse mediante un proceso auditable que registra archivo y fecha de eliminación.

### IngestionInterval — intervalo histórico y checkpoint

Registro nuevo por intervalo de consulta de catálogo. Permite distinguir avance completo de extracción, publicación y consumo.

| Campo | Tipo conceptual | Regla |
|---|---|---|
| `run_id` | UUID | FK a `IngestionRun`. |
| `interval_start`, `interval_end` | instante UTC | Inicio inclusivo y fin exclusivo de la consulta lógica; la fuente puede incluir ambos extremos. |
| `filters` | objeto JSON | Año, magnitud mínima, tipo, ámbito y otros filtros exactos. |
| `status` | enum | `pending`, `archived`, `publishing`, `complete` o `failed`. |
| `attempt_count` | entero no negativo | Número de intentos de extracción. |
| `records_received`, `unique_versions` | enteros no negativos | Conteos distinguen registros recibidos de versiones únicas. |
| `source_archive_sha256` | SHA-256 nullable | FK a la respuesta GeoJSON original, compartida con `SourceArchive`. |
| `requested_at`, `archived_at`, `completed_at` | instantes UTC nullable | Tiempos de las etapas, no tiempos de ocurrencia de los eventos. |
| `error_summary` | texto nullable | Último error del intervalo, sin sustituir el checkpoint válido anterior. |

Clave única: `(run_id, interval_start, interval_end)`. Intervalos que deban subdividirse se registran como intervalos hijos disjuntos; los registros que se repitan por límites inclusivos se deduplican por identidad de versión.

### EventVersion — versión de evento sísmico

Una Feature de terremoto validada, normalizada y enriquecida. Corresponde a la tabla existente `event_version`.

| Campo | Tipo conceptual | Regla |
|---|---|---|
| `mode` | enum `live`, `replay` | Parte de la identidad para mantener los flujos aislados. |
| `event_id` | texto | Identificador USGS no vacío. |
| `updated_at` | instante UTC | Timestamp USGS que identifica esta revisión. |
| `event_time` | instante UTC | Tiempo de ocurrencia original normalizado a UTC. |
| `magnitude`, `mag_type`, `place` | decimal/texto nullable | Los valores ausentes permanecen nulos. |
| `longitude`, `latitude` | decimal finito | Longitud en `[-180, 180]`, latitud en `[-90, 90]`; ambos son necesarios para una geometría válida. |
| `depth_km` | decimal nullable | Profundidad en km, sin sustituir ausencia por cero. |
| `country_id` | código de texto nullable | FK a `Country`; null significa «Sin país asignado». |
| `date_utc` | fecha | Día UTC derivado de `event_time`, FK a `CalendarDate`. |
| `source`, `ingested_at`, `ingestion_run_id` | texto/instante/UUID | Procedencia, momento de ingesta y ejecución de origen. |
| `original_payload` | objeto GeoJSON | Feature recibida; las filas nuevas deben ser completas y las filas heredadas pueden ser parciales. En filas nuevas es una copia compatible del original completo de `EventVersionSource`; la huella vive solo en esa tabla. |

Clave primaria: `(mode, event_id, updated_at)`. Una versión distinta no puede ser sobreescrita. Las Features completas aceptadas se registran en `EventVersionSource`; las filas heredadas pueden no tener aún una huella fuente completa.

### EventVersionSource — fuente completa actualmente aceptada por versión

Registro nuevo de la única Feature fuente completa actualmente aceptada para una identidad de versión. Las discrepancias de contenido con la misma identidad actualizan este registro en-place, no crean otra fuente aceptada.

| Campo | Tipo conceptual | Regla |
|---|---|---|
| `mode`, `event_id`, `updated_at` | clave primaria y FK a `EventVersion` | Garantiza como máximo una fuente aceptada por identidad de versión. |
| `payload_sha256` | SHA-256 | Huella canónica del Feature completo aceptado; campo mutable al reemplazarlo, no forma parte de la clave. |
| `original_feature` | objeto GeoJSON | Única Feature completa actualmente aceptada, exacta y sin reconstrucción ni transformación. |
| `ingestion_run_id`, `source`, `ingested_at` | UUID/texto/instante UTC | Ejecución y procedencia del payload actualmente aceptado. |

Huella e identidad iguales son un duplicado sin efectos nuevos. Si la identidad ya existe con otro hash, el consumidor actualiza en una sola transacción `EventVersion`, `EventVersionSource` y el enlace de estado/procedencia para reflejar el payload entrante; la magnitud puede subir o bajar porque prevalece el payload recibido más recientemente. No crea una segunda fila, no pone el mensaje en cuarentena por conflicto y no altera `EventCurrent` salvo que su `updated_at` sea posterior al actual. Para una versión heredada sin fuente completa, el payload entrante sustituye los campos conocidos y se registra como primera fuente verificable; no se calcula un hash del payload heredado parcial.

### EventCurrent — estado actual del evento

Proyección de una sola versión actual por evento y modo; corresponde a `event_current`.

| Campo | Tipo conceptual | Regla |
|---|---|---|
| `mode`, `event_id` | clave compuesta | PK; un estado por evento en cada modo. |
| `current_updated_at` | instante UTC | FK a la versión exacta `(mode, event_id, updated_at)`. |

Transición: al persistir una nueva `EventVersion`, crear el estado si no existe; actualizarlo solo si `updated_at` es posterior. Versiones atrasadas se conservan en el historial pero nunca hacen retroceder `EventCurrent`.

### PublishedVersion — candidato publicado a Kafka

Registro de publicación confirmada; la tabla `published_version` existente permanece intacta para compatibilidad con sus claves heredadas. Las publicaciones nuevas se registran en `published_payload`.

### PublishedPayload — ledger de publicaciones por huella

Tabla nueva que permite rastrear ACKs distintos para una misma identidad temporal sin cambiar la clave primaria existente de `PublishedVersion`.

| Campo | Tipo conceptual | Regla |
|---|---|---|
| `mode`, `event_id`, `updated_at`, `payload_sha256` | clave compuesta | Identifica el Feature completo confirmado para el evento y timestamp. |
| `published_at` | instante UTC | Se escribe después del ACK de Kafka. |
| `kafka_topic`, `kafka_partition`, `kafka_offset` | texto/enteros | Posición de la publicación confirmada. |

El publisher no registra como publicado un mensaje sin ACK. Solo omite una repetición cuyo hash coincide con el último ACK de esa identidad, determinado por el orden de offsets de Kafka; si llega un hash distinto, lo publica. Si reaparece un hash antiguo después de otro contenido, se publica de nuevo para que el consumidor aplique la regla de último payload recibido. `PublishedPayload` es un ledger de entregas, no una colección de versiones/eventos aceptados. Las filas heredadas de `published_version` no tienen huella conocida y no se usan como si probaran igualdad: ante la primera observación se permite publicar y se registra el ACK por hash en `published_payload`.

### Quarantine — rechazo o exclusión

Registro durable de un mensaje que no debe modificar el estado actual; corresponde a `quarantine`.

| Campo | Tipo conceptual | Regla |
|---|---|---|
| `quarantine_id` | UUID | Clave primaria. |
| `mode`, `source`, `event_id` | enum/texto/nullable | Contexto de origen, si puede identificarse. |
| `ingestion_run_id` | UUID nullable | Run del mensaje, cuando se pudo parsear; permite conservar la relación con el original fuente completo. |
| `received_at` | instante UTC | Hora de recepción en el consumidor. |
| `reason_code`, `reason_detail` | texto | Motivo estable y explicable, por ejemplo `invalid_geometry` o `event_type_excluded`. Los cambios de contenido con la misma identidad de versión no son motivo de cuarentena. |
| `kafka_topic`, `kafka_partition`, `kafka_offset` | texto/enteros | Referencia al mensaje; única para que un reintento de la misma posición no cree otra cuarentena. |
| `raw_message` | bytes | Mensaje recibido sin alterar. |
| `parsed_payload` | objeto JSON nullable | Payload parseado sin alterar, cuando pudo interpretarse. |

Un rechazo/exclusión se confirma solo después del commit de la transacción de cuarentena. Coordenadas o tiempos inválidos no generan `EventVersion` ni `EventCurrent`.

### Country — entidad del catálogo Natural Earth

Dimensión cargada desde el GeoJSON entregado; se amplía el modelo actual para conservar los atributos utilizados.

| Campo | Tipo conceptual | Regla |
|---|---|---|
| `country_id` | texto de 3 caracteres | PK basada en `ADM0_A3`; no se presenta como código ISO garantizado. |
| `name_es`, `admin`, `continent`, `subregion` | texto nullable | Atributos del catálogo original. `country_name` actual podrá migrarse o mantenerse como atributo compatible. |
| Geometría | Polygon/MultiPolygon en archivo fuente | Se consulta desde el GeoJSON inmutable, no se reescribe al cargar la dimensión. |

Regla espacial: un punto dentro/cubierto por exactamente una entidad obtiene su `country_id`; cero o varias coincidencias, incluyendo fronteras, producen `country_id = null`.

### CalendarDate — fecha UTC

Dimensión de fecha existente, identificada por `date_utc`; cada evento enlaza al día UTC obtenido de su tiempo de ocurrencia.

## Relaciones principales

```text
IngestionRun 1 ── * IngestionInterval
SourceArchive 1 ── * IngestionRun
IngestionRun 1 ── * EventVersionSource
IngestionRun 1 ── * Quarantine
EventVersion 1 ── 0..1 EventVersionSource (único original completo actualmente aceptado)
EventVersion 1 ── 0..1 EventCurrent (la versión actual referenciada)
Country 1 ── 0..* EventVersion
CalendarDate 1 ── 0..* EventVersion
Kafka message 1 ── 0..1 Quarantine (posición de partición única)
```

`PublishedPayload` identifica un ACK de publicación y puede producir un mensaje Kafka; no implica que el consumidor ya haya persistido la versión. Los registros preexistentes en `PublishedVersion` se conservan sin atribuirles una huella desconocida.

## Reglas transaccionales y validación

1. Validar envelope, Feature, `properties.type == earthquake`, geometría Point, timestamps e identidad antes de escribir eventos.
2. Normalizar timestamps a UTC, preservando el payload original y unidades USGS (epoch ms, profundidad km, coordenadas longitud/latitud).
3. Archivar cada respuesta GeoJSON completa antes de extraer Features; deduplicar el archivo por SHA-256 y registrar un run separado por consulta.
4. Calcular una huella estable del Feature fuente completo mediante serialización JSON canónica UTF-8; no incluir campos volátiles del envelope como `ingested_at`.
5. En una transacción, insertar una versión única y su fuente completa; si la identidad ya existe, el mismo hash es duplicado y un hash distinto reemplaza en-place los campos, Feature, hash y procedencia del payload aceptado.
6. Una revisión con `updated_at` menor puede actualizar su propia versión histórica, pero no hace retroceder `EventCurrent`; una revisión con `updated_at` mayor avanza el estado actual. No se crea cuarentena por discrepancias de contenido con la misma identidad.
7. Para entradas no válidas o excluidas, insertar cuarentena y confirmar la transacción antes del offset Kafka.
8. El consumidor confirma el offset solo después del commit PostgreSQL. Reintentar tras el commit no repite los efectos.
9. Los archivos originales permanecen disponibles mientras existan datos procesados dependientes. Copias idénticas se deduplican y la limpieza de originales huérfanos se registra.
10. Los runs live fallidos no sustituyen el último run exitoso; una ausencia en la ventana live nunca elimina filas históricas.
11. El sondeo live sigue una cadencia de 60 s con tolerancia de 5 s; los intentos tienen timeout de 8 s, hasta 3 reintentos (esperas 1/2/4 s) solo para fallos temporales, y nunca hay solicitudes solapadas.

## Retención y reconstrucción

- Los volúmenes PostgreSQL y Kafka persisten a reinicios según Compose.
- Las respuestas GeoJSON live e históricas se archivan en almacenamiento persistente antes de transformar o publicar; el run y el intervalo referencian el archivo compartido y su huella.
- El avance del backfill se reanuda por intervalos completos/incompletos, y el contenido por evento se aplica a una única fila por clave natural; un hash distinto en la misma identidad reemplaza la fuente aceptada.
- La limpieza solo elimina originales que ya no están vinculados a datos procesados y registra qué archivos se retiraron y cuándo.
