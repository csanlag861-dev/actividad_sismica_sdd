# Quickstart: Validar el arranque y procesamiento Compose

Esta guía valida los cinco servicios, las migraciones, el procesamiento live/replay y la recuperación ante dependencias no disponibles. Requiere que la implementación prevista en [plan.md](./plan.md) exista. No se debe esperar ningún endpoint HTTP en esta entrega.

## Prerrequisitos

- Docker Desktop con Docker Compose v2 y contenedores Linux.
- Un archivo `.env` local con la configuración de desarrollo; no se versiona ni se copia desde `.env.example` con secretos reales.
- Los archivos `compose.yaml`, `backend/Dockerfile`, dependencias fijadas y el catálogo Natural Earth indicado en [ENUNCIADO.md](../../docs/ENUNCIADO.md).

## Escenario 1: levantar servicios y revisar estado

Desde la raíz del repositorio (PowerShell):

```powershell
if (!(Test-Path .env)) { Copy-Item .env.example .env }
# Completa .env con los valores locales requeridos antes de continuar.
docker compose up --build -d
docker compose ps
docker compose logs --tail 100 postgres kafka api productor consumidor
docker compose exec api python -m observatorio.healthcheck api
docker compose exec productor python -m observatorio.healthcheck productor
docker compose exec consumidor python -m observatorio.healthcheck consumidor
```

En Linux/macOS, el equivalente para preparar y levantar el stack es:

```bash
test -f .env || cp .env.example .env
docker compose up --build -d
docker compose ps
docker compose logs --tail 100 postgres kafka api productor consumidor
docker compose exec api python -m observatorio.healthcheck api
docker compose exec productor python -m observatorio.healthcheck productor
docker compose exec consumidor python -m observatorio.healthcheck consumidor
```

**Resultado esperado**:

- Se muestran exactamente los cinco servicios: `productor`, `kafka`, `consumidor`, `postgres` y `api`.
- Todos alcanzan estado saludable en el objetivo de hasta 180 segundos después de construir las imágenes.
- Productor y consumidor conectan a `kafka:9092`; productor, consumidor y backend conectan a `postgres:5432`.
- El backend `api` aplica Alembic y permanece activo sin Uvicorn, endpoints HTTP ni puertos publicados.
- No aparece ningún mapeo `ports`; los logs no muestran DSN, contraseñas, tokens ni payloads.

## Escenario 2: comprobar la migración y el catálogo

```powershell
docker compose exec api alembic current
docker compose exec postgres sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "select version_num from alembic_version;"'
docker compose exec postgres sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "select count(*) from country;"'
```

**Resultado esperado**: Alembic muestra la revisión esperada; existe `alembic_version`; el catálogo `country` contiene códigos `ADM0_A3` únicos. En esta entrega no se consulta `/api/salud` ni ningún otro endpoint.

## Escenario 3: comprobar el procesamiento live

```powershell
docker compose logs --since 5m productor consumidor
docker compose exec postgres sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "select mode, outcome, records_received, started_at, finished_at from ingestion_run order by started_at desc limit 5;"'
docker compose exec postgres sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "select mode, count(*) from event_version group by mode;"'
docker compose exec postgres sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "select mode, count(*) from event_current group by mode;"'
```

**Resultado esperado**: `ingestion_run` distingue consulta correcta sin eventos de consulta fallida; las versiones live conservan procedencia y original; existe como máximo una fila actual por `(mode, event_id)`. Un país no asignable permanece nulo.

## Escenario 4: comprobar replay aislado

```powershell
docker compose exec productor python -m observatorio.producer.replay --year 2025 --min-magnitude 4 --event-type earthquake --interval-seconds 2
docker compose exec postgres sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "select mode, count(*) from event_version group by mode;"'
docker compose exec postgres sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "select mode, min(event_time), min(ingested_at) from event_version group by mode;"'
```

**Resultado esperado**: el productor consulta el catálogo histórico FDSN de USGS por meses, aplica los filtros de año, magnitud y tipo, ordena los eventos por su tiempo de ocurrencia y publica en `quakes.replay`. Si la selección devuelve eventos, quedan en modo replay; el tiempo de ocurrencia se conserva y `ingested_at` refleja la reproducción. El mismo evento replay no crea ni modifica la fila live.

El parámetro `--interval-seconds` controla la pausa entre publicaciones. Para probar únicamente si la consulta produce eventos sin esperar entre ellos, se puede indicar `--interval-seconds 0`.

## Escenario 5: fallos, reintentos y recuperación

Con el stack iniciado y sin pruebas de carga en curso:

```powershell
docker compose stop kafka
docker compose ps
docker compose logs --since 2m productor consumidor
docker compose start kafka
docker compose ps
```

Repite de forma equivalente con PostgreSQL, inspeccionando los logs de `api`, `productor` y `consumidor`.

**Resultado esperado**: los servicios afectados dejan de estar saludables, registran destino y reintentos sin secretos ni payloads, y recuperan conexión en menos de 60 segundos desde que vuelve la dependencia, sin reinicio manual de esos clientes. Si la escritura PostgreSQL falla, el consumidor no confirma el offset.

## Escenario 6: persistencia y arranque limpio sin borrar datos

Para comprobar una base realmente nueva, ejecuta una instancia Compose aislada:

```powershell
docker compose -p observatorio-check up --build -d
docker compose -p observatorio-check ps
docker compose -p observatorio-check exec api alembic current
```

Comprueba y anota el recuento de versiones/publicaciones, detén e inicia la instancia con el mismo nombre de proyecto:

```powershell
docker compose -p observatorio-check down
docker compose -p observatorio-check up -d
docker compose -p observatorio-check ps
docker compose -p observatorio-check exec api alembic current
```

**Resultado esperado**: la migración repetida conserva la revisión, el catálogo y los registros guardados. Repite el ciclo de reinicio dos veces. No uses `down -v` para validar persistencia.

## Pruebas automatizadas

Ejecuta las pruebas unitarias e integración de la imagen Python:

```powershell
docker compose run --rm --no-deps --entrypoint python api -m pytest /app/tests
```

La suite automatizada cubre la persistencia idempotente sobre SQLite, revisiones actuales, cuarentena idempotente, orden de persistencia antes del ACK en el consumidor, ACK antes del registro de publicación, aislamiento de modos, filtrado/orden temporal del catálogo histórico, readiness por rol, reintentos y redacción de secretos:

```bash
.venv/bin/python -m pytest backend/tests -q
```

Las pruebas contra Kafka/PostgreSQL reales y los límites temporales de recuperación se verifican con los escenarios Compose anteriores; no se consideran demostrados solo por las pruebas SQLite/mock.

## Cierre

```powershell
docker compose down
```

Esto conserva los volúmenes. Elimina volúmenes solo en un entorno desechable y cuando la prueba requiera explícitamente borrar sus datos.
