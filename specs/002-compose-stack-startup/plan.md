# Implementation Plan: Arranque y procesamiento del stack Compose

**Branch**: `main` (feature: `002-compose-stack-startup`) | **Date**: 2026-11-12 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/002-compose-stack-startup/spec.md`; el usuario ha seleccionado SQLAlchemy para el mapeo y Alembic para las migraciones.

## Summary

Crear el stack local de cinco servicios con Kafka y PostgreSQL accesibles por DNS interno, comprobaciones de salud y reintentos ante dependencias no disponibles. Un único backend Python compartido por los servicios productor, consumidor y `api` usará SQLAlchemy 2.x asíncrono con `asyncpg`; Alembic mantendrá las migraciones versionadas. En esta entrega `api` es el proceso de inicialización/supervisión del esquema: no instala FastAPI, no ejecuta Uvicorn y no expone endpoints. Productor y consumidor procesan eventos live y replay de extremo a extremo con persistencia idempotente. El modelo y las validaciones se detallan en [data-model.md](./data-model.md), [contracts/runtime-readiness.md](./contracts/runtime-readiness.md) y [quickstart.md](./quickstart.md).

## Technical Context

**Language/Version**: Python 3.12 como baseline práctico para la primera implementación; no se declara como versión mínima de compatibilidad.

**Primary Dependencies**: aiokafka, SQLAlchemy 2.x con API asíncrona, Alembic, asyncpg, cliente HTTP asíncrono y Shapely para integración punto-en-polígono. Pruebas con pytest y pytest-asyncio. FastAPI/Uvicorn quedan para la entrega de endpoints.

**Storage**: PostgreSQL con volumen persistente y una versión mantenida fijada en Compose; Kafka de un nodo en modo KRaft y retención limitada; historial de esquema mediante Alembic.

**Testing**: Pruebas unitarias con pytest; integración en Compose para migraciones, catálogo geográfico, consultas USGS, publicación/consumo Kafka, persistencia transaccional, idempotencia live/replay, healthchecks y recuperación.

**Target Platform**: Contenedores Linux coordinados con Docker Compose v2; desarrollo desde el host Windows/Docker Desktop.

**Project Type**: Backend Python con tres procesos de aplicación (productor, consumidor y API) y dos dependencias de infraestructura (Kafka y PostgreSQL), ejecutados como cinco servicios Compose.

**Performance Goals**: Cumplir los criterios de la especificación: cinco conexiones internas correctas en cinco pruebas; servicios recuperados en menos de 60 segundos tras volver una dependencia; estado saludable de los cinco servicios en el objetivo de arranque de hasta 180 segundos una vez disponibles las imágenes; cinco recorridos de procesamiento live y replay con resultados idempotentes.

**Constraints**: Exactamente cinco servicios Compose. Los tres procesos Python pueden compartir imagen, pero no proceso/contenedor. En esta entrega no se publican puertos ni se implementan endpoints; el servicio Compose `api` permanece como proceso backend de migración/supervisión. Kafka y PostgreSQL no tienen puertos publicados. Nombres internos: `kafka:9092` y `postgres:5432`; `api:8000` se reserva para la entrega HTTP futura. El backend aplica las migraciones antes de estar saludable; no se añade un sexto servicio de migraciones. Reintentos de aplicación complementan `depends_on: service_healthy`. Secretos fuera de Git y de los logs.

**Scale/Scope**: Un nodo Kafka, una instancia PostgreSQL y una réplica de cada servicio de aplicación en el equipo local; feed live y replay histórico quedan aislados. Se implementa el pipeline productor-consumidor y el esquema, pero no la API HTTP, frontend, agregaciones analíticas ni alta disponibilidad/escalado horizontal.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Cumplimiento de referencias**: PASS. Se mantienen los cinco servicios separados del enunciado. El servicio `api` se reserva como proceso backend sin HTTP hasta la entrega posterior; ningún endpoint del contrato se crea ahora.
- **Procedencia y calidad**: PASS. El modelo conserva originales, fuente, tiempos diferenciados y cuarentena; los valores desconocidos siguen siendo nulos.
- **Idempotencia y revisiones**: PASS. Las tareas incluyen el flujo del productor, las transacciones del consumidor, cuarentena y confirmación de offset posterior al commit, con pruebas de duplicados y revisiones antiguas/nuevas.
- **Contratos y exposición segura**: PASS. No se altera el contrato público, no se implementan endpoints en esta entrega, no se exponen Kafka/PostgreSQL y no se registran secretos.
- **Análisis reproducible**: PASS. El modelo registra consulta y procedencia de ingesta; los criterios de validación no convierten los datos en predicción o riesgo.
- **Complejidad**: PASS. No se añaden servicios, brokers adicionales, PostGIS ni una transacción distribuida.

No se identifica una violación que requiera excepción.

## Project Structure

### Documentation (this feature)

```text
specs/002-compose-stack-startup/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── runtime-readiness.md
└── tasks.md             # Se generará con /speckit-tasks
```

### Source Code (planned)

```text
compose.yaml
.env.example
backend/
├── Dockerfile
├── requirements.txt
├── alembic.ini
├── migrations/
│   ├── env.py
│   └── versions/
├── src/observatorio/
│   ├── api/
│   │   └── bootstrap.py
│   ├── consumer/
│   │   ├── processor.py
│   │   ├── validation.py
│   │   ├── geography.py
│   │   └── main.py
│   ├── producer/
│   │   ├── source.py
│   │   ├── live.py
│   │   ├── replay_source.py
│   │   ├── replay.py
│   │   └── publisher.py
│   ├── db/
│   ├── models/
│   └── config.py
└── tests/
    ├── unit/
    └── integration/
```

**Structure Decision**: El repositorio aún no tiene backend ni `compose.yaml`. Se propone un paquete Python único bajo `backend/` y una imagen compartida para productor, consumidor y `api`, iniciados con comandos distintos. Esto conserva los tres servicios/contenedores requeridos sin duplicar dependencias. El proceso `api` aplica Alembic y permanece activo supervisando acceso a PostgreSQL y revisión aplicada; no inicia un servidor HTTP ni publica un puerto en esta entrega. Productor y consumidor esperan a que `api` esté saludable para no procesar antes de la migración. No se crea un servicio Compose separado de inicialización. La cartografía se toma de `frontend/public/datos/paises.geojson`; como ese archivo no aparece en el checkout actual, las tareas deben verificarlo y, si falta, restaurar una copia Natural Earth con procedencia registrada.

## Complexity Tracking

No hay violaciones de la constitución ni complejidad adicional que justificar. La tabla `published_version` está justificada por el requisito de conservar las versiones confirmadas por Kafka a través de reinicios; no es una abstracción opcional.

## Phase 0: Outline & Research

Las decisiones investigadas, alternativas y fuentes oficiales están en [research.md](./research.md). SQLAlchemy asíncrono y asyncpg dan acceso no bloqueante al consumidor y al proceso backend; Alembic aplica un historial versionado desde `api`. Compose coordina la disponibilidad inicial por healthchecks, mientras que el productor y el consumidor conservan reintentos propios para interrupciones posteriores. La futura API HTTP no forma parte de este plan.

## Phase 1: Design & Contracts

- [data-model.md](./data-model.md) define entidades, campos, relaciones, claves, transiciones e índices con su justificación. El original se almacena junto a cada versión; publicación, cuarentena y ejecución de ingesta conservan sus propios ciclos de vida.
- [contracts/runtime-readiness.md](./contracts/runtime-readiness.md) define la topología, destinos internos, salud del proceso backend sin HTTP, orden de migraciones, procesamiento y señales de error. El contrato HTTP [CONTRATO-API.md](../../docs/CONTRATO-API.md) queda para una entrega posterior.
- [quickstart.md](./quickstart.md) especifica pasos de arranque, verificación SQL del esquema y pipeline, recuperación y persistencia sin borrar volúmenes de usuario.

### Post-design Constitution Check

- **Jerarquía documental**: PASS; no se crean endpoints en esta entrega; `CONTRATO-API.md` permanece como obligación de la futura API.
- **Datos y calidad**: PASS; originales y rechazos son duraderos; UTC, nulabilidad, claves y revisiones están definidos.
- **Transacciones e idempotencia**: PASS; el consumidor escribe versión o cuarentena antes de confirmar el offset; productor y replay conservan idempotencia y separación.
- **Servicios y exposición**: PASS; cinco servicios exactos y DNS interno; esta entrega no publica puertos.
- **Alembic y cambios de esquema**: PASS; migraciones versionadas, revisadas y aplicadas por el backend antes de su estado saludable; no compiten con `metadata.create_all`.
- **Operación reproducible**: PASS; healthchecks, reintentos, logs sin secretos y pruebas de inicio/parada están documentados.

No quedan decisiones de arquitectura que requieran una aclaración del usuario para iniciar la fase de tareas.
