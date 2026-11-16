# Implementation Plan: Pipeline sísmico completo H5

**Branch**: `003-pipeline-sismico-completo` | **Date**: 2026-11-16 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/003-pipeline-sismico-completo/spec.md`

## Summary

Completar el pipeline live e histórico de USGS sobre el backend que ya existe. Se conservarán originales y procedencia, se validarán y pondrán en cuarentena los registros excluidos o inválidos, y se reforzarán las claves y comparaciones para que reintentos y revisiones atrasadas sean idempotentes; contenido distinto con igual `updated` reemplaza la misma versión en-place. El catálogo Natural Earth ya está incluido y cargado; se preservará su integridad y se asignará país solo ante una coincidencia espacial única. La carga histórica será por intervalos verificables y recuperables, reutilizará el consumidor y mantendrá el modo `replay` aislado de `live`.

## Technical Context

**Language/Version**: Python 3.12 (imagen de backend existente).

**Primary Dependencies**: aiokafka 0.12.0, SQLAlchemy 2.0.36, Alembic 1.14.1, asyncpg 0.29.0, httpx 0.28.1, Shapely 2.0.6, pytest 8.3.3; versiones ya fijadas en `backend/requirements.txt`.

**Storage**: PostgreSQL 16 para eventos, versiones, runs, publicación, checkpoints, archivos y cuarentena; Kafka 3.9 para transporte; volumen Docker persistente para respuestas GeoJSON originales live e históricas. Los archivos se deduplican por hash y permanecen mientras haya datos procesados dependientes.

**Testing**: pytest con SQLite/aiosqlite para pruebas unitarias de validación y transacciones; pruebas de integración con PostgreSQL, Kafka y Compose para orden de confirmación, reinicios, reintentos y flujo completo.

**Target Platform**: Cinco servicios Docker Compose locales (productor, Kafka, consumidor, PostgreSQL y API/bootstrap); imágenes Linux ejecutadas desde el equipo anfitrión.

**Project Type**: Backend de ingestión y procesamiento distribuido con consumidor de eventos y persistencia relacional; la API de consulta y el frontend quedan fuera del alcance funcional de H5.

**Performance Goals**: Programar consultas live con reloj monotónico cada 60 segundos con tolerancia de 5 segundos; timeout HTTP de 8 segundos y hasta 3 reintentos por ciclo (esperas 1/2/4 segundos); evitar consultas solapadas y registrar deadlines perdidos sin reintentos catch-up. Respetar límites de respuesta del catálogo USGS procesando el histórico por intervalos de hasta 20.000 registros por respuesta; completar una consulta antes de iniciar la siguiente.

**Constraints**: Conservar UTC, unidades y originales; no inferir país por texto o proximidad; no borrar datos históricos por su ausencia del feed de 24 horas; persistir antes de confirmar offsets; mantener modo replay aislado; no introducir servicios adicionales a los exigidos.

**Scale/Scope**: Feed live global con ventana móvil de 24 horas, una carga histórica de un año (por defecto 2025, mundial, M≥4 y tipo earthquake), catálogo Natural Earth suministrado y recuperación documentada de paradas live superiores a 24 horas. Los intervalos históricos se subdividen al alcanzar el límite de 20.000 registros.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio / restricción | Evaluación | Evidencia y control del plan |
|---|---|---|
| Fuentes de referencia y contrato | PASS | El alcance deriva de H5 en `ROADMAP.md` y de `docs/ENUNCIADO.md`; la API pública no se amplía en este hito. |
| Procedencia y calidad explícitas | PASS | Se retienen respuestas GeoJSON completas y Features originales con metadatos de extracción; UTC y unidades se documentan; invalidaciones y exclusiones quedan en cuarentena. |
| Idempotencia y revisiones | PASS | Se preserva una sola fila por identidad `(mode, event_id, updated_at)`, la fuente/hash se reemplaza en-place ante payload distinto con igual identidad, el estado actual es monótono y el commit precede al offset. |
| Contratos y exposición segura | PASS | Kafka y PostgreSQL permanecen privados en Compose. El envelope interno se documenta; no se crean endpoints públicos como parte de H5. |
| Reproducibilidad y afirmaciones proporcionadas | PASS | Los lotes e intervalos registran filtros y recuentos; los ensayos sintéticos se etiquetan y no se mezclan con datos reales. |
| Servicios separados y dependencias justificadas | PASS | Se reutilizan los cinco servicios Compose existentes; no se agregan herramientas ni servicios nuevos. |

No se identifican violaciones que requieran justificación o gate bloqueante.

## Project Structure

### Documentation (this feature)

```text
specs/003-pipeline-sismico-completo/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── pipeline-message.md
    └── historical-extraction.md
```

### Source Code (repository root)

```text
backend/
├── src/observatorio/
│   ├── producer/       # USGS live, publicación, extracción histórica/replay
│   ├── consumer/       # validación, cuarentena, enriquecimiento y persistencia
│   ├── models/         # eventos, runs, catálogo, publicación y cuarentena
│   └── db/             # sesiones y carga validada del catálogo
├── data/               # copia y manifiesto de Natural Earth sin modificar
├── migrations/         # evolución del esquema PostgreSQL
└── tests/
    ├── unit/
    └── integration/
compose.yaml              # cinco servicios separados y volúmenes persistentes
```

**Structure Decision**: Extender el backend y las pruebas existentes, sin crear un segundo servicio o proyecto. La copia de Natural Earth ya reside en `backend/data/` y se valida contra su manifiesto; la copia entregada al frontend se mantiene intacta. Las pruebas unitarias permanecen en `backend/tests/unit/` y las pruebas con Kafka/PostgreSQL en `backend/tests/integration/`. El volumen persistente de archivos fuente, montado en el productor, se reutiliza para respuestas live e históricas; los runs y archivos compartidos se rastrean en PostgreSQL, sin añadir un servicio Compose. El loader reanudable vive en `producer/` o en el paquete de ingesta existente, más las migraciones necesarias.

## Complexity Tracking

No hay violaciones de la constitución ni complejidad adicional que registrar.

## Phase 0: Outline & Research

Consultar `research.md`. Las decisiones se basan en los documentos de referencia del proyecto y en la inspección de la implementación actual; no quedan decisiones de tecnología o alcance marcadas como `NEEDS CLARIFICATION`.

## Phase 1: Design & Contracts

- `data-model.md` define las entidades existentes y las extensiones mínimas para archivo fuente compartido, ledger de publicaciones por hash, una fuente/hash aceptada por versión, reemplazo same-version, procedencia heredada y progreso histórico.
- `contracts/pipeline-message.md` define el envelope Kafka y sus invariantes de idempotencia.
- `contracts/historical-extraction.md` define parámetros, intervalos, checkpoint y recuperación de extracción.
- `quickstart.md` reúne comprobaciones ejecutables de los casos H5, sin duplicar la suite de pruebas.

## Constitution Check (post-design)

| Gate | Resultado |
|---|---|
| Respuesta GeoJSON y Feature originales preservadas mientras haya datos procesados dependientes; copias idénticas deduplicadas | PASS |
| Rechazo durable y offset posterior al commit del resultado | PASS |
| Reintentos idempotentes, reemplazo same-version en una fila y versión actual no regresiva | PASS |
| Atribución geográfica única o «Sin país asignado» | PASS |
| Histórico recuperable, independiente de desaparición del feed live | PASS |
| Sin nuevas superficies públicas ni servicios no requeridos; el volumen persistente comparte archivos live e históricos en Compose | PASS |

El diseño satisface las restricciones; no se necesitan excepciones.
