
# Data Model: Persistencia y procesamiento del observatorio

## Propósito y decisiones

El modelo soporta el flujo live/replay exigido por el enunciado y el alcance de ROADMAP R09. Las tablas y campos se explican por su grano y uso; no se añaden campos derivados sin un proceso que los necesite. SQLAlchemy define las entidades y Alembic conserva la creación y evolución del esquema. Esta entrega crea y utiliza el almacenamiento, pero no implementa endpoints HTTP.

Se usan tipos PostgreSQL con marcas de tiempo `TIMESTAMPTZ` normalizadas a UTC; el ORM las declara como `DateTime(timezone=True)` para conservar ese contrato al enlazar valores con PostgreSQL. El campo `mode` separa `live` de `replay` mediante claves compuestas y filtros explícitos; cada modo utiliza un topic distinto. No se mezclan eventos live y replay con el mismo `event_id`.

## Entidades

### `country`

Una fila por país del catálogo Natural Earth utilizado para enriquecer eventos. El identificador procede de `ADM0_A3` y debe comprobarse como único antes de sembrar el catálogo; el nombre preferido es `NAME_ES`, con `ADMIN` como alternativa si el nombre español no está disponible.

La geometría procede de Natural Earth **Admin 0 - Countries, escala 1:110m**. El original runtime está empaquetado en `backend/data/ne_110m_admin_0_countries.geojson`; su URL de origen, fecha de recuperación y SHA-256 están registrados en `backend/data/geodata_manifest.json`. El mismo GeoJSON se publica como recurso del frontend en `frontend/public/datos/paises.geojson`. El arranque valida el formato, la geometría y la unicidad de `ADM0_A3` antes de sembrar países o enriquecer eventos.

| Campo | Tipo propuesto | Requerido | Motivo |
|---|---|---:|---|
| `country_id` | `VARCHAR(3)` PK | Sí | Código estable utilizado por el frontend y las relaciones |
| `country_name` | `TEXT` | Sí | Nombre legible del catálogo |

Un evento sin país asignable conserva `country_id = NULL`; no se asigna al país más cercano.

### `calendar_date`

Una fila por día UTC, dimensión temporal del modelo.

| Campo | Tipo propuesto | Requerido | Motivo |
|---|---|---:|---|
| `date_utc` | `DATE` PK | Sí | Clave del día de ocurrencia para agrupaciones y relación con eventos |

No se duplican año, mes y día como columnas almacenadas: se derivan de `date_utc` cuando una consulta los necesita.

### `ingestion_run`

Una fila por consulta/ejecución de ingesta, para diferenciar una respuesta vacía válida de una consulta fallida y determinar la última ingesta correcta.

| Campo | Tipo propuesto | Requerido | Motivo |
|---|---|---:|---|
| `run_id` | `UUID` PK | Sí | Identidad estable de la consulta |
| `mode` | `TEXT` con CHECK (`live`, `replay`) | Sí | Mantener separada la procedencia live/replay |
| `source` | `TEXT` | Sí | Identificar la fuente consultada |
| `started_at` | `TIMESTAMPTZ` | Sí | Medir inicio y distinguirlo de los tiempos del evento |
| `finished_at` | `TIMESTAMPTZ` | No | Momento de cierre; nulo mientras está en curso |
| `outcome` | `TEXT` con CHECK (`running`, `succeeded`, `failed`) | Sí | Estado verificable de la ejecución |
| `request_start`, `request_end` | `TIMESTAMPTZ` | No | Periodo solicitado, cuando aplique |
| `http_status` | `SMALLINT` | No | Diagnosticar respuestas de la fuente sin guardar credenciales |
| `records_received` | `INTEGER` | Sí | Conteo de entrada, incluido cero cuando la consulta fue correcta |
| `error_code`, `error_summary` | `TEXT` | No | Explicar fallos sin sustituirlos por una respuesta de datos válida |

`last_ingestion` (para la futura API) se calcula usando la última ejecución `succeeded`; una ejecución fallida no reemplaza silenciosamente la fecha de la última consulta correcta.

### `event_version`

Una fila inmutable por versión observada de un terremoto. Su grano conserva el historial y el original.

| Campo | Tipo propuesto | Requerido | Motivo |
|---|---|---:|---|
| `mode` | `TEXT` con CHECK (`live`, `replay`) PK parte | Sí | Evitar colisiones entre live y replay |
| `event_id` | `TEXT` PK parte | Sí | Identidad del evento en la fuente |
| `updated_at` | `TIMESTAMPTZ` PK parte | Sí | Identidad/orden de la versión; si falta, el mensaje no puede versionarse y va a cuarentena |
| `event_time` | `TIMESTAMPTZ` | Sí | Tiempo de ocurrencia para filtros y ventanas UTC |
| `magnitude` | `NUMERIC` | No | Magnitud; se conserva como nula si es desconocida |
| `mag_type` | `TEXT` | No | Interpretación de la escala de magnitud |
| `place` | `TEXT` | No | Descripción textual original |
| `longitude`, `latitude` | `DOUBLE PRECISION` | Sí | Ubicación; deben ser finitas y estar dentro de rango para el procesamiento geográfico |
| `depth_km` | `DOUBLE PRECISION` | No | Profundidad en km; se conserva nula cuando falta |
| `country_id` | `VARCHAR(3)` FK a `country` | No | Enriquecimiento geográfico; nulo cuando no hay asignación |
| `date_utc` | `DATE` FK a `calendar_date` | Sí | Dimensión del día de ocurrencia |
| `source` | `TEXT` | Sí | Procedencia del evento |
| `ingested_at` | `TIMESTAMPTZ` | Sí | Momento de recepción, distinto de ocurrencia y actualización |
| `ingestion_run_id` | `UUID` FK a `ingestion_run` | Sí | Trazar la versión hasta la consulta que la obtuvo |
| `original_payload` | `JSONB` | Sí | Conservar el documento de fuente asociado a la versión para auditoría/reproceso |

La clave primaria es `(mode, event_id, updated_at)`: impide repetir la misma versión y permite que un mismo evento exista en ambos modos.

### `event_current`

Una fila por evento y modo; representa cuál versión es la actual. Guarda una referencia a la versión en lugar de duplicar todos sus atributos, evitando discrepancias entre el snapshot y el historial.

| Campo | Tipo propuesto | Requerido | Motivo |
|---|---|---:|---|
| `mode` | `TEXT` con CHECK (`live`, `replay`) PK parte | Sí | Separar los estados actuales por modo |
| `event_id` | `TEXT` PK parte | Sí | Garantizar una fila actual por evento y modo |
| `current_updated_at` | `TIMESTAMPTZ` | Sí | Apuntar a la versión más reciente conocida |

Una FK compuesta `(mode, event_id, current_updated_at)` referencia `event_version`. Las consultas futuras unirán `event_current` con esa versión. La clave primaria de `event_current` y la clave compuesta de `event_version` hacen explícita la unicidad.

### `published_version`

Una fila por versión confirmada por Kafka, necesaria para que el productor compare versiones publicadas después de reiniciar.

| Campo | Tipo propuesto | Requerido | Motivo |
|---|---|---:|---|
| `mode` | `TEXT` con CHECK (`live`, `replay`) PK parte | Sí | Mantener el estado de publicación aislado por modo |
| `event_id` | `TEXT` PK parte | Sí | Identidad del evento |
| `updated_at` | `TIMESTAMPTZ` PK parte | Sí | Identidad exacta de la versión confirmada |
| `published_at` | `TIMESTAMPTZ` | Sí | Registrar cuándo se recibió confirmación del broker |
| `kafka_topic` | `TEXT` | Sí | Diagnóstico de destino |
| `kafka_partition` | `INTEGER` | No | Metadato de confirmación, si está disponible |
| `kafka_offset` | `BIGINT` | No | Posición confirmada para auditoría |

Se escribe solo después del ACK de Kafka. No se agrega una FK a `event_version`: el productor puede confirmar y guardar su publicación antes de que el consumidor persista esa versión. Si el proceso cae entre ambos pasos, el consumidor debe tolerar la entrega repetida.

### `quarantine`

Una fila por mensaje rechazado, con motivo y bytes originales; no se exige que el mensaje tenga un `event_id` o JSON válido.

| Campo | Tipo propuesto | Requerido | Motivo |
|---|---|---:|---|
| `quarantine_id` | `UUID` PK | Sí | Identidad interna del rechazo |
| `mode` | `TEXT` con CHECK (`live`, `replay`) | Sí | Mantener trazabilidad de modo |
| `source` | `TEXT` | Sí | Procedencia del mensaje |
| `event_id` | `TEXT` | No | Facilitar búsqueda si pudo extraerse |
| `received_at` | `TIMESTAMPTZ` | Sí | Momento del rechazo |
| `reason_code` | `TEXT` | Sí | Categoría estable del rechazo |
| `reason_detail` | `TEXT` | Sí | Explicación accionable |
| `kafka_topic` | `TEXT` | Sí | Identificar el mensaje fuente |
| `kafka_partition` | `INTEGER` | Sí | Identificar el mensaje fuente |
| `kafka_offset` | `BIGINT` | Sí | Evitar duplicar la cuarentena al reprocesar la misma posición |
| `raw_message` | `BYTEA` | Sí | Preservar el mensaje incluso si no es JSON válido |
| `parsed_payload` | `JSONB` | No | Inspección estructurada cuando el JSON sí pudo analizarse |

La restricción única `(kafka_topic, kafka_partition, kafka_offset)` hace idempotente el registro del mismo mensaje rechazado. No se agrega FK a `event_current`, porque los mensajes malformados pueden no tener una identidad de evento válida.

## Relaciones

- `event_version.country_id` → `country.country_id` (muchas versiones pueden compartir país; país opcional).
- `event_version.date_utc` → `calendar_date.date_utc` (muchas versiones por día UTC).
- `event_version.ingestion_run_id` → `ingestion_run.run_id` (una ejecución produce cero o más versiones).
- `event_current` → `event_version` mediante `(mode, event_id, current_updated_at)` (una versión referenciada como actual por evento/modo).
- `published_version` representa confirmación de publicación, no persistencia del consumidor; se relaciona lógicamente por `(mode, event_id, updated_at)`, sin FK por el orden asíncrono de Kafka.
- `quarantine` conserva una referencia Kafka única, pero no obliga a crear una entidad de evento.

## Índices y restricciones

- Claves compuestas de `event_version`, `event_current` y `published_version`: unicidad e idempotencia en sus granos respectivos.
- Índice en `event_version(mode, event_time)`: filtros por modo y ventana temporal del API.
- Índice en `event_version(mode, country_id, event_time)`: filtros geográficos y temporales; justificar con las consultas efectivas.
- Índice en `ingestion_run(mode, outcome, finished_at)`: encontrar la última consulta correcta.
- Restricción única sobre la posición Kafka de cuarentena y rango válido de coordenadas.
- Restricciones de modo y claves foráneas: impedir estados de replay/live mezclados y referencias huérfanas.

Los índices son hipótesis ligadas a consultas; deberán verificarse con mediciones y no se consideran una aceleración universal.

## Transacciones y ciclo de vida

1. El productor crea `ingestion_run` para cada consulta, conserva su resultado incluso si no hay eventos y mantiene `outcome=failed` ante errores de fuente.
2. Para cada evento, el productor compara `event_id` y `updated_at` con `published_version`; publica solo versiones aún no confirmadas usando `event_id` como clave Kafka. El mensaje incluye `mode`, `source`, `ingested_at`, `ingestion_run_id` y el original.
3. El productor espera el ACK de Kafka y después inserta/actualiza `published_version`. Una caída entre el ACK y la escritura puede causar un reenvío; el consumidor tolera la entrega al menos una vez.
4. El consumidor valida el mensaje y procesa sus efectos en una transacción PostgreSQL: inserta la versión única y solo avanza `event_current` cuando `updated_at` es posterior. Conserva las versiones antiguas sin hacerlas actuales.
5. Si la validación falla, el consumidor persiste en `quarantine` el motivo, bytes originales y posición Kafka. Solo confirma el offset después del commit de la versión válida o de la cuarentena.
6. La restricción de cuarentena `(kafka_topic, kafka_partition, kafka_offset)` y las claves de versión hacen idempotentes los reintentos de persistencia.
7. El productor replay obtiene una selección histórica documentada y ordenada por tiempo original, la publica a un topic diferente con `mode=replay` y reutiliza el mismo consumidor. `event_time` permanece sin cambios; `ingested_at` registra el tiempo de reproducción.
8. La API futura consultará el modo solicitado; esta entrega no añade endpoints ni una capa de consulta HTTP.

## Migraciones

Las clases SQLAlchemy definen los metadatos de referencia. Alembic crea una migración inicial con estas entidades, restricciones e índices. Las migraciones autogeneradas deben revisarse antes de aplicarse; el proceso backend del servicio Compose `api` aplica la revisión disponible antes de declararse saludable y permanece activo para supervisar la disponibilidad del esquema. En esta entrega `api` no ejecuta FastAPI/Uvicorn ni sirve rutas HTTP. No se usa `metadata.create_all()` como segundo mecanismo de gestión del esquema.
