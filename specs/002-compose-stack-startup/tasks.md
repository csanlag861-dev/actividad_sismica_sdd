# Tasks: Arranque y procesamiento del stack Compose

**Input**: Design documents from `/specs/002-compose-stack-startup/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/runtime-readiness.md`, `quickstart.md`

**Tests**: Se incluyen pruebas porque la especificación y el enunciado requieren verificar el pipeline live/replay, idempotencia, persistencia, conectividad, healthchecks y recuperación.

**Organization**: Las tareas se agrupan por historia. US2 depende del esquema de US1; US3 reutiliza el procesamiento de US2; US4 comprueba la recuperación de los servicios del stack.

## Phase 1: Setup

**Purpose**: Crear la estructura Python y la topología inicial de cinco servicios.

- [X] T001 Create the backend package, producer/consumer modules, and test directories in `backend/src/observatorio/__init__.py` and `backend/tests/__init__.py`
- [X] T002 [P] Pin asyncpg, SQLAlchemy, Alembic, aiokafka, HTTP client, Shapely, pytest, and pytest-asyncio dependencies and build the shared image in `backend/requirements.txt` and `backend/Dockerfile`
- [X] T003 [P] Document non-secret settings for PostgreSQL, Kafka, USGS, polling, and replay in `.env.example`
- [X] T004 Define exactly `productor`, `kafka`, `consumidor`, `postgres`, and `api` services, internal networking, persistent volumes, and a no-HTTP/no-published-port `api` backend coordinator in `compose.yaml`

## Phase 2: Foundational

**Purpose**: Implement shared configuration, connections, logging, and retry primitives required by every story.

**⚠️ CRITICAL**: Complete this phase before implementing any user story.

- [X] T005 [P] Validate service settings and internal defaults (`kafka:9092`, `postgres:5432`) in `backend/src/observatorio/config.py`
- [X] T006 [P] Configure logging that redacts DSNs, passwords, tokens, and payloads in `backend/src/observatorio/logging.py`
- [X] T007 Create the SQLAlchemy async engine and per-unit-of-work session factory in `backend/src/observatorio/db/session.py`
- [X] T008 Create reusable aiokafka producer/consumer configuration and broker connection helpers in `backend/src/observatorio/kafka.py`
- [X] T009 Implement capped progressive async retry/backoff with destination, attempt, and delay logging in `backend/src/observatorio/retry.py`
- [X] T010 [P] Define the SQLAlchemy declarative base and shared metadata in `backend/src/observatorio/models/base.py`

**Checkpoint**: Shared settings, database/Kafka clients, safe logs, retry support, and model metadata base are ready.

## Phase 3: User Story 1 - Preparar el esquema desde el backend (Priority: P1) 🎯 MVP

**Goal**: Create the complete initial schema through reviewed Alembic migrations; keep the `api` Compose service healthy without starting HTTP.

**Independent Test**: Against an isolated empty PostgreSQL database, the backend applies the initial revision, confirms every required table/constraint, preserves a seeded row over two restarts, and exposes no HTTP route or published port.

### Tests for User Story 1

- [X] T011 [US1] Write integration tests for migration on an empty database, all table constraints, seeded data persistence over two restarts, and backend readiness without HTTP in `backend/tests/integration/test_migrations.py`

### Implementation for User Story 1

- [X] T012 [P] [US1] Map `country` (`country_id VARCHAR(3)` primary key and required `country_name TEXT`), `calendar_date` (`date_utc DATE` primary key), and every `ingestion_run` field: required `run_id UUID`, `mode TEXT CHECK (live, replay)`, `source TEXT`, `started_at TIMESTAMPTZ`, `outcome TEXT CHECK (running, succeeded, failed)`, `records_received INTEGER`; nullable `finished_at`, `request_start`, `request_end`, `http_status SMALLINT`, `error_code`, and `error_summary` in `backend/src/observatorio/models/reference.py`
- [X] T013 [US1] Map every `event_version` column and nullability from `data-model.md`: required `mode TEXT CHECK (live, replay)`, `event_id TEXT`, `updated_at TIMESTAMPTZ`, `event_time TIMESTAMPTZ`, `longitude DOUBLE PRECISION`, `latitude DOUBLE PRECISION`, `date_utc DATE` FK, `source TEXT`, `ingested_at TIMESTAMPTZ`, `ingestion_run_id UUID` FK, and `original_payload JSONB`; nullable `magnitude NUMERIC`, `mag_type TEXT`, `place TEXT`, `depth_km DOUBLE PRECISION`, and `country_id VARCHAR(3)` FK. Enforce finite coordinates in longitude `[-180, 180]` and latitude `[-90, 90]`; map `event_current` with required checked `mode`, `event_id`, and `current_updated_at`, primary key `(mode, event_id)`, and composite FK to its current version in `backend/src/observatorio/models/events.py`
- [X] T014 [P] [US1] Map all required `published_version` columns (`mode TEXT CHECK (live, replay)`, `event_id TEXT`, `updated_at TIMESTAMPTZ`, `published_at TIMESTAMPTZ`, `kafka_topic TEXT`) with primary key `(mode, event_id, updated_at)` and nullable `kafka_partition INTEGER`/`kafka_offset BIGINT`; map all required `quarantine` columns (`quarantine_id UUID` primary key, `mode TEXT CHECK (live, replay)`, `source TEXT`, `received_at TIMESTAMPTZ`, `reason_code TEXT`, `reason_detail TEXT`, `kafka_topic TEXT`, `kafka_partition INTEGER`, `kafka_offset BIGINT`, `raw_message BYTEA`) and nullable `event_id TEXT`/`parsed_payload JSONB`; enforce unique `(kafka_topic, kafka_partition, kafka_offset)` in `backend/src/observatorio/models/publication.py` and `backend/src/observatorio/models/quarantine.py`
- [X] T015 [US1] Verify `frontend/public/datos/paises.geojson`; if absent, restore the documented Natural Earth country catalog and record version/source, validate unique `ADM0_A3`, and implement idempotent country seeding in `backend/src/observatorio/db/catalog.py` and `backend/data/geodata_manifest.json`
- [X] T016 [US1] Register every entity module in the shared SQLAlchemy metadata exports used by Alembic in `backend/src/observatorio/models/__init__.py`
- [X] T017 [US1] Configure Alembic's async environment, asyncpg URL, model metadata imports, and sanitized logging in `backend/alembic.ini` and `backend/migrations/env.py`
- [X] T018 [US1] Create and review the initial migration for all model fields, checks, keys, foreign keys, unique constraints, and justified indexes in `backend/migrations/versions/0001_initial_schema.py`
- [X] T019 [US1] Implement the long-running `api` backend coordinator to retry PostgreSQL, apply `alembic upgrade head`, run idempotent country seeding, then periodically recheck database access and the expected revision so Compose can mark it unhealthy/recovered; do not start FastAPI/Uvicorn or HTTP routes in `backend/src/observatorio/api/bootstrap.py`
- [X] T020 [US1] Run and fix the fresh-database, migration-repeat, seeded-row persistence, schema, and no-HTTP readiness tests in `backend/tests/integration/test_migrations.py`

**Checkpoint**: The five-service stack has a migrated and persistent schema; `api` is a backend coordinator only and serves no HTTP.

## Phase 4: User Story 2 - Procesar eventos live de extremo a extremo (Priority: P2)

**Goal**: Fetch recent USGS data, publish new versions to Kafka, validate/enrich them, and persist current/history/quarantine state transactionally.

**Independent Test**: With the US1 schema applied, exercise a controlled live sequence and query PostgreSQL directly; verify original/provenance, one current version per event, idempotency, quarantine, and offset ordering without calling an API endpoint.

### Tests for User Story 2

- [X] T021 [P] [US2] Write a live pipeline integration test for USGS response metadata, Kafka delivery, PostgreSQL version/current writes, and internal service DNS in `backend/tests/integration/test_live_pipeline.py`
- [X] T022 [P] [US2] Write tests for duplicate, newer/older revisions, invalid coordinates/message quarantine, country ambiguity, and no offset commit before database commit in `backend/tests/unit/test_event_processing.py`

### Implementation for User Story 2

- [X] T023 [P] [US2] Implement the async USGS recent-feed client with configurable URL, request timeout, progressive retry for timeout/429/5xx, response parsing, and preserved original GeoJSON in `backend/src/observatorio/producer/source.py`
- [X] T024 [P] [US2] Implement publication deduplication from `published_version`, Kafka key `event_id`, message fields `source`, `ingested_at`, `mode`, `ingestion_run_id`, and original payload; persist publication only after broker ACK in `backend/src/observatorio/producer/publisher.py`
- [X] T025 [US2] Implement the live polling loop at approximately 60-second intervals; create/update `ingestion_run` for successful, empty, and failed requests and pass its id to published messages in `backend/src/observatorio/producer/live.py`
- [X] T026 [P] [US2] Implement Natural Earth point-in-polygon enrichment from `ADM0_A3`; set country null for no match or multiple matches and never assign by proximity in `backend/src/observatorio/consumer/geography.py`
- [X] T027 [P] [US2] Implement message validation and normalization for event identity, mode, timestamps, required fields, finite/ranged coordinates, original bytes, and stable quarantine reason codes in `backend/src/observatorio/consumer/validation.py`
- [X] T028 [US2] Implement a PostgreSQL unit of work that inserts unique `event_version`, advances `event_current` only for a newer `updated_at`, or persists the complete quarantine record in `backend/src/observatorio/consumer/processor.py`
- [X] T029 [US2] Implement manual Kafka offset commits only after the processor's PostgreSQL transaction commits, with duplicate delivery treated idempotently in `backend/src/observatorio/consumer/main.py`
- [X] T030 [US2] Configure live producer/consumer commands, topics, environment, database connections, and healthy-dependency gates in `compose.yaml`
- [X] T031 [US2] Run and fix the live pipeline, revision, quarantine, enrichment, and post-commit offset tests in `backend/tests/integration/test_live_pipeline.py` and `backend/tests/unit/test_event_processing.py`

**Checkpoint**: Live events flow through USGS, Kafka, and PostgreSQL with source provenance, idempotent revisions, explicit quarantine, and commit-before-ACK semantics.

## Phase 5: User Story 3 - Reproducir histórico aislado (Priority: P3)

**Goal**: Demonstrate the same Kafka/consumer pipeline with historical events isolated from live.

**Independent Test**: Publish at least ten historical events in event-time order, replay the same selection twice, and compare live/replay rows and timestamps directly in PostgreSQL.

### Tests for User Story 3

- [X] T032 [US3] Write replay integration tests for ten ordered historical events, original event-time preservation, replay ingestion time, repeat delivery, and zero live-row changes in `backend/tests/integration/test_replay_isolation.py`

### Implementation for User Story 3

- [X] T033 [P] [US3] Implement a paginated/monthly USGS catalog source using the documented default selection (2025, global, magnitude at least 4, earthquake type) and record its query metadata in `backend/src/observatorio/producer/replay_source.py`
- [X] T034 [P] [US3] Implement replay publication ordered by original event time to a distinct topic, with `mode=replay`, unchanged `event_time`, replay `ingested_at`, and a configurable interval defaulting to two seconds in `backend/src/observatorio/producer/replay.py`
- [X] T035 [US3] Route live and replay messages through the same consumer processor while applying composite mode keys and preserving distinct published/current state in `backend/src/observatorio/consumer/main.py`
- [X] T036 [US3] Run and fix replay isolation, repeat-delivery, and live-state preservation tests in `backend/tests/integration/test_replay_isolation.py`

**Checkpoint**: Replay demonstrates the real Kafka pipeline, preserves original timestamps, and cannot contaminate live state.

## Phase 6: User Story 4 - Diagnosticar y recuperar el estado de los servicios (Priority: P4)

**Goal**: Report functional health, safe dependency errors, and automatic recovery across all five services.

**Independent Test**: Run five controlled Kafka/PostgreSQL delay or outage cases; affected services become unhealthy, log safe retry details, and recover within 60 seconds after restoration without manual restart.

### Tests for User Story 4

- [X] T037 [P] [US4] Write dependency outage/recovery tests that measure five recovery runs against the 60-second target in `backend/tests/integration/test_readiness_retries.py`
- [X] T038 [P] [US4] Write tests that verify service/dependency/attempt logs omit credentials, DSNs, tokens, and payloads in `backend/tests/unit/test_safe_logging.py`

### Implementation for User Story 4

- [X] T039 [US4] Implement readiness state and a role-specific healthcheck CLI that checks API migration/schema, producer Kafka/PostgreSQL, and consumer Kafka/PostgreSQL rather than process liveness alone in `backend/src/observatorio/health.py` and `backend/src/observatorio/healthcheck.py`
- [X] T040 [US4] Integrate progressive retry, reconnect, readiness transitions, and safe destination/error/attempt logging into API bootstrap and both producer/consumer loops in `backend/src/observatorio/api/bootstrap.py`, `backend/src/observatorio/producer/live.py`, and `backend/src/observatorio/consumer/main.py`
- [X] T041 [US4] Add effective healthchecks for PostgreSQL, Kafka, API coordinator, producer, and consumer; gate dependencies with `service_healthy` and publish no ports in `compose.yaml`
- [X] T042 [US4] Run and fix five-case recovery, unhealthy-state, readiness, and secret-redaction tests in `backend/tests/integration/test_readiness_retries.py` and `backend/tests/unit/test_safe_logging.py`

**Checkpoint**: All services reflect functional dependency readiness, log failures safely, and recover without manual restart.

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Keep the handoff instructions and final acceptance aligned with the no-endpoint scope.

- [X] T043 Update PowerShell instructions for migrations, SQL verification, live/replay processing, outage recovery, and persistent volumes without HTTP calls in `specs/002-compose-stack-startup/quickstart.md`
- [X] T044 Validate the user-approved minimum H3/H4 path: confirm all five services are healthy, Alembic is at head, and the country catalog is initialized; publish one clearly synthetic event to Kafka, verify its persisted version/current/original data and consumer offset in PostgreSQL, confirm it does not enter live mode, and run the backend test suite. Evidence (2026-11-16): event `H4-SYNTHETIC-20261116T2333Z-cf9d9183` was consumed from `quakes.replay` partition 0 offset 83; PostgreSQL contains its replay version/current/original and succeeded synthetic run; consumer offset is 84 with zero lag; no live row exists; all five services are healthy; Alembic revision is `0006_ingestion_intervals`; 177 countries are seeded; 59 backend tests pass. Per the agreed scope, query UI/map and the repeated operational acceptance trials remain outside this H3/H4 closure and belong to later delivery/roadmap H7 validation.

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No prerequisite; T002 and T003 can run in parallel after T001.
- **Foundational (Phase 2)**: Starts after Setup. T005, T006, and T010 can proceed independently; DB/Kafka/retry helpers depend on their corresponding settings/logging.
- **User Story 1 (Phase 3)**: Starts after Foundation; provides the schema and Natural Earth country catalog.
- **User Story 2 (Phase 4)**: Depends on US1's migrated schema and country catalog; implements live processing.
- **User Story 3 (Phase 5)**: Depends on the reusable consumer processor from US2.
- **User Story 4 (Phase 6)**: Depends on the five running services and their processing loops.
- **Polish (Phase 7)**: Depends on all four user stories.

### User Story Dependencies

- **US1 (P1)**: Can start after Phase 2; no dependency on another story.
- **US2 (P2)**: Requires US1 schema/catalog to persist and geolocate events.
- **US3 (P3)**: Reuses the US2 producer/consumer pipeline with replay-specific source/topic/mode.
- **US4 (P4)**: Tests service readiness and recovery after the backend and processing loops exist.

### Within Each User Story

- Write tests before the implementation tasks for that story.
- Register every SQLAlchemy model before generating the Alembic revision.
- The producer persists a `published_version` only after Kafka ACK.
- The consumer commits an offset only after PostgreSQL commits its version or quarantine result.
- Replay publication and persistence reuse the live path and keep mode/topic isolation.
- Healthcheck wiring follows implementation of the role-specific readiness checks.

### Parallel Opportunities

- **Setup**: T002 and T003 can run in parallel after T001.
- **Foundation**: T005, T006, and T010 are independent; T007/T008 follow settings and T009 follows logging.
- **US1**: T012 and T014 can run in parallel after T011; T013 follows T012; catalog seeding follows its source/model; Alembic follows all models.
- **US2**: T021/T022 can be written in parallel; after tests, T023/T024/T026/T027 can proceed in separate modules; orchestration and database/offset integration follow.
- **US3**: T033 and T034 can be developed in parallel against the documented event message contract; T035 wires them to the shared consumer.
- **US4**: T037 and T038 can be written in parallel before readiness implementation.
- **Polish**: T043 must finish before the full quickstart validation T044.

## Parallel Examples

### User Story 1

```text
After T011, parallelize:
Task: T012 country/date/ingestion models in backend/src/observatorio/models/reference.py
Task: T014 publication/quarantine models in backend/src/observatorio/models/publication.py and backend/src/observatorio/models/quarantine.py
Then implement event FKs and current-state keys in T013 before registering all metadata.
```

### User Story 2

```text
After T021 and T022, parallelize:
Task: T023 USGS client in backend/src/observatorio/producer/source.py
Task: T024 publication state in backend/src/observatorio/producer/publisher.py
Task: T026 geography resolver in backend/src/observatorio/consumer/geography.py
Task: T027 message validation in backend/src/observatorio/consumer/validation.py
Then wire the live loop, transaction processor, and offset commit order.
```

### User Story 3

```text
After T032, parallelize:
Task: T033 historical USGS query source in backend/src/observatorio/producer/replay_source.py
Task: T034 replay topic publisher in backend/src/observatorio/producer/replay.py
Then wire both through the shared consumer processor in T035.
```

### User Story 4

```text
Parallelize the test-first work:
Task: T037 outage/recovery timing tests in backend/tests/integration/test_readiness_retries.py
Task: T038 safe logging tests in backend/tests/unit/test_safe_logging.py
Then implement readiness/reconnect behavior and Compose healthchecks.
```

## Implementation Strategy

### MVP First (User Story 1)

1. Complete Setup and Foundational phases.
2. Complete US1: SQLAlchemy entities, country catalog, initial Alembic revision, and healthy backend coordinator with no HTTP.
3. Validate a fresh isolated database and repeated startup before proceeding.

### Incremental Delivery

1. Add US2 live pipeline; validate one event, duplicate, revision, invalid record, and PostgreSQL offset ordering.
2. Add US3 historical replay using the same processing path and verify strict isolation from live.
3. Add US4 healthchecks/recovery and run all measurable acceptance trials.
4. Run the final quickstart without calling any HTTP endpoint.

## Notes

- Every task uses the required checkbox, sequential ID, optional `[P]`, story label for story phases, and an explicit file path.
- Model tasks preserve all fields and constraints from `data-model.md`; processing tests are explicit because the enunciado requires the Kafka/PostgreSQL pipeline.
- No HTTP endpoint, FastAPI route, Uvicorn process, or published port belongs to this feature; that work remains for a later delivery.

## Phase 8: Convergence

- [X] T045 Implement the actual Kafka-backed live pipeline and PostgreSQL publication state transitions in `backend/src/observatorio/producer/live.py`, `backend/src/observatorio/producer/publisher.py`, and `backend/src/observatorio/consumer/main.py` per US2/AC2 and Constitution III (missing)
- [X] T046 Implement replay isolation, duplicate/version ordering, quarantine persistence, and country enrichment before offset commit in `backend/src/observatorio/consumer/validation.py`, `backend/src/observatorio/consumer/geography.py`, `backend/src/observatorio/consumer/processor.py`, and the model layer per US2/AC3-5, US3/AC1-3, and Constitution II/III (partial)
- [X] T047 Replace the stub readiness logic with dependency-aware health checks and reconnect/retry loops in `backend/src/observatorio/health.py`, `backend/src/observatorio/healthcheck.py`, `backend/src/observatorio/api/bootstrap.py`, and `compose.yaml` per US4/AC1-4 and Constitution IV (missing)
- [X] T048 Add end-to-end migration readiness verification and failure recovery assertions that match the schema contract and no-HTTP scope in `backend/tests/integration/test_readiness_retries.py`, `backend/tests/unit/test_safe_logging.py`, and the Alembic/bootstrap flow per US1/AC1-3 and Constitution IV (partial)

## Phase 9: Convergence

- [X] T049 Replace the generated sample country polygons with the documented Natural Earth dataset, verify unique `ADM0_A3` codes, and record its actual provenance in `backend/src/observatorio/db/catalog.py`, `frontend/public/datos/paises.geojson`, and `backend/data/geodata_manifest.json` per Constitution II and FR-018 (contradicts)
- [X] T050 Make Alembic failures observable and retryable; remove manual creation of `alembic_version` and verify the expected head revision and required schema before readiness in `backend/src/observatorio/api/bootstrap.py` and `backend/tests/integration/test_migrations.py` per US1/AC1-3 and FR-005/006/012 (partial)
- [X] T051 Persist ingestion query outcomes and publish state, compare event `id`/`updated`, and publish every unconfirmed new version before recording it after Kafka ACK in `backend/src/observatorio/producer/live.py`, `backend/src/observatorio/producer/publisher.py`, and the database layer per US2/AC2 and FR-015/016 (missing)
- [X] T052 Implement shared durable live/replay processing: validate timestamps and finite/ranged coordinates, persist event versions and only advance current state for newer revisions, quarantine invalid Kafka bytes idempotently, enrich from verified polygons, and commit offsets only after PostgreSQL commit in `backend/src/observatorio/consumer/main.py`, `backend/src/observatorio/consumer/processor.py`, `backend/src/observatorio/consumer/validation.py`, and `backend/src/observatorio/consumer/geography.py` per US2/AC3-5, FR-017/019, and Constitution II/III (partial)
- [X] T053 Implement the documented historical USGS replay source with year/type/magnitude filters, event-time ordering, preserved occurrence time, configurable interval, and replay topic consumption through the shared processor in `backend/src/observatorio/producer/replay_source.py`, `backend/src/observatorio/producer/replay.py`, and `backend/src/observatorio/consumer/main.py` per US3/AC1-3 and FR-008/020 (partial)
- [X] T054 Implement per-role healthchecks that test the required Kafka/PostgreSQL dependencies, add Compose healthchecks for producer and consumer, and make both processing loops reconnect with progressive retries after outages in `backend/src/observatorio/health.py`, `backend/src/observatorio/healthcheck.py`, `backend/src/observatorio/producer/live.py`, `backend/src/observatorio/consumer/main.py`, and `compose.yaml` per US4/AC1-4 and FR-009/010/011 (partial)
- [X] T055 Add integration and recovery tests for live/replay persistence, revisions, quarantine-before-offset-commit, internal connectivity, and safe logs; update `specs/002-compose-stack-startup/quickstart.md` so every claimed check matches executable behavior per plan: testing strategy and T021/T022/T032/T037/T038/T044 (missing)
