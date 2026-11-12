# Contrato interno de arranque, procesamiento y disponibilidad

Este contrato describe direcciones internas, orden de preparación, procesamiento y señales de salud de Compose. No implementa ni reemplaza el contrato funcional HTTP de [CONTRATO-API.md](../../../docs/CONTRATO-API.md), que se abordará en una entrega posterior.

## Servicios y destinos

| Servicio Compose | Dependencias | Destinos internos y función en esta entrega |
|---|---|---|
| `postgres` | Ninguna | Escucha en `postgres:5432`; persistencia mediante volumen |
| `kafka` | Ninguna | Listener de clientes en `kafka:9092`; listener de controlador KRaft interno |
| `api` | PostgreSQL saludable | Backend SQLAlchemy/Alembic: aplica migraciones y supervisa el esquema; no ejecuta HTTP |
| `productor` | Kafka y `api` saludables | Consulta USGS, lee/escribe `published_version`, publica eventos a `kafka:9092` |
| `consumidor` | Kafka y `api` saludables | Consume de Kafka y escribe versiones/cuarentena en `postgres:5432` |

`api`, `productor`, `consumidor`, `kafka` y `postgres` son cinco servicios/contenedores. Los tres procesos Python pueden construir la misma imagen con comandos diferentes. En esta entrega no hay puertos publicados, no se ejecuta Uvicorn y no existen endpoints. `api:8000` queda reservado para la entrega HTTP futura. Kafka y PostgreSQL permanecen en la red interna de Compose.

## Orden de preparación

1. PostgreSQL acepta conexiones según `pg_isready`; Kafka responde a una comprobación de protocolo sobre `kafka:9092`. Estos servicios pueden iniciar en paralelo.
2. `api` conecta a PostgreSQL, aplica `alembic upgrade head` con reintentos ante errores transitorios, confirma que la revisión esperada está aplicada y permanece activo supervisando la conectividad y el esquema.
3. Productor y consumidor esperan a Kafka y a que `api` esté saludable, y además prueban sus propias conexiones a PostgreSQL antes de operar.
4. Después del arranque inicial, productor, consumidor y backend reconectan con espera progresiva ante cortes posteriores.

`depends_on: condition: service_healthy` ordena el arranque inicial, pero no sustituye la reconexión de la aplicación.

## Definición de saludable

| Servicio | Está saludable cuando |
|---|---|
| PostgreSQL | El servidor acepta conexiones a la base configurada |
| Kafka | El broker responde por su listener interno anunciado, no solo está vivo el proceso |
| `api` | El proceso backend está activo, Alembic alcanzó la revisión esperada y una consulta confirma acceso al esquema |
| Productor | El proceso está activo y ha establecido acceso al broker y a `published_version` en PostgreSQL |
| Consumidor | El proceso está activo y ha establecido acceso al broker y a las tablas de versiones/cuarentena |

La salud del servicio `api` se comprueba mediante un comando interno de healthcheck, no mediante `/api/salud` ni HTTP. Una consulta USGS sin eventos nuevos no es un fallo de disponibilidad; su `ingestion_run` debe quedar registrado como correcto con cero registros.

## Procesamiento e idempotencia

- El productor live consulta el feed reciente aproximadamente cada 60 segundos, registra una ejecución de ingesta y conserva los originales antes de transformarlos.
- Para publicar, compara `event_id` y `updated_at` con `published_version`; usa el identificador de evento como clave Kafka y espera el ACK antes de persistir la publicación confirmada.
- Cada mensaje incluye `source`, `ingested_at`, `mode`, `ingestion_run_id` y el original. Live y replay usan topics distintos.
- El consumidor valida y procesa los efectos PostgreSQL en una transacción. Inserta una versión única y avanza `event_current` solo si la versión recibida es posterior a la actual.
- Un mensaje inválido se registra en `quarantine` con bytes originales, motivo y posición Kafka. Solo se confirma el offset después del commit de la versión o de la cuarentena.
- El enriquecimiento geográfico usa `ADM0_A3` del catálogo Natural Earth, previa verificación de unicidad. Sin coincidencia o con varias coincidencias, conserva país nulo; no asigna por proximidad.
- Replay reutiliza el consumidor normal, mantiene la fecha original y registra el tiempo de reproducción. Las claves compuestas y los topics separados impiden mezclarlo con live.

## Migraciones

- SQLAlchemy es la fuente de metadatos de las clases; Alembic es el único propietario normal de la creación y evolución del esquema.
- El proceso del servicio Compose `api` aplica revisiones versionadas antes de iniciar productor y consumidor. No crea revisiones automáticamente.
- Un fallo de migración impide que `api` alcance estado saludable; se registra el error sin secretos.
- En esta entrega el servicio `api` no ejecuta FastAPI/Uvicorn, no publica puerto y no implementa ninguna ruta HTTP.

## Reintentos y logs

- Los fallos temporales de conexión se registran con el servicio destino, tipo de error y número/espera del reintento.
- Las esperas progresivas tienen máximo, pero el proceso continúa reintentando mientras permanezca activo.
- El productor reintenta errores transitorios HTTP (incluidos timeout, 429 y 5xx) sin sustituir el último estado válido.
- Al recuperarse una dependencia, los clientes restablecen la conexión. Un offset no se confirma antes de persistir sus efectos.
- No se imprimen contraseñas, DSN completos, tokens ni payloads en logs.

## Fuentes de configuración

Las credenciales se reciben por variables de entorno fuera del repositorio. `.env.example` solo documenta nombres y valores de ejemplo no secretos. La fuente geográfica es `frontend/public/datos/paises.geojson`, como indica el enunciado; si falta en el checkout, se restaura desde Natural Earth y se registra su versión y procedencia.
