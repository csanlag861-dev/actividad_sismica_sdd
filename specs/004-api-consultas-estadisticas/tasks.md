# Tasks: Consulta API y estadísticas sísmicas

**Input**: Design documents from `/specs/004-api-consultas-estadisticas/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md), [contracts/](contracts/), [quickstart.md](quickstart.md)

**Organization**: Tasks are grouped by user story so each story can be implemented and validated as an incremental deliverable. Tests are included because the stories define independent acceptance criteria and measurable correctness outcomes.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel with other marked tasks because it targets a separate file and has no unfinished prerequisite.
- **[Story]**: Maps a task to a user story in `spec.md`.
- Every task specifies its target file path(s).

## Phase 1: Setup

**Purpose**: Add the runtime dependencies required to expose the already-planned API over HTTP.

- [ ] T001 Add pinned FastAPI and Uvicorn dependencies to `backend/requirements.txt`, retaining the existing SQLAlchemy, asyncpg, httpx, and test dependencies.

---

## Phase 2: Foundational

**Purpose**: Make the existing `api` Compose service capable of starting the application and serving HTTP before any endpoint story is implemented.

- [ ] T002 Implement the FastAPI application factory and startup/lifespan integration in `backend/src/observatorio/api/app.py` and `backend/src/observatorio/api/bootstrap.py` so HTTP serving does not wait for a successful database connection or schema bootstrap. Run/retry bootstrap independently of accepting requests, and keep readiness false until database and required schema checks pass, allowing `/api/salud` to return HTTP 503 while they are unavailable.
- [ ] T003 Update the `api` command/container port declaration in `backend/Dockerfile` and publish the service in `compose.yaml` so Uvicorn serves on `0.0.0.0:8000` inside the existing `api` service while binding only `127.0.0.1:8000:8000` on the host, without adding a sixth service or exposing PostgreSQL/Kafka.

**Checkpoint**: The API process starts inside the existing Compose service, applies required startup setup, and is reachable on the configured local API port.

---

## Phase 3: User Story 1 - Consultar eventos sísmicos actuales (Priority: P1) 🎯 MVP

**Goal**: Provide a contract-compliant GeoJSON collection of current live events with default and explicit filters.

**Independent Test**: Against a known event sample, compare unfiltered and filtered collections, exact temporal boundaries, null magnitude/depth/country, zero matches, and storage failure behavior with the persisted current live state.

### Tests for User Story 1

- [ ] T004 [P] [US1] Specify `/api/eventos` response fields, temporal/filter boundaries, complete untruncated results when no limit is configured, empty-result behavior, 400 malformed-syntax and 422 invalid/unknown-parameter statuses, the common safe JSON error envelope, and storage-failure status in `backend/tests/contract/test_api_contract.py`.
- [ ] T005 [P] [US1] Specify UTC normalization, `[start, end)` filtering, inclusive `min_mag`, exact country matching, rejection of unknown parameters, and null-magnitude exclusion in `backend/tests/unit/test_api_queries.py`.
- [ ] T006 [P] [US1] Add database integration coverage for current-version joins, live/replay isolation, complete untruncated event results, and successful empty results in `backend/tests/integration/test_event_query_database.py`.

### Implementation for User Story 1

- [ ] T007 [US1] Define validated query parameters and shared UTC filter normalization in `backend/src/observatorio/api/schemas.py`, rejecting malformed request syntax with HTTP 400 and unknown parameters or invalid ISO 8601 values, non-finite magnitude, `start >= end`, and malformed country identifiers with HTTP 422 using the common error envelope.
- [ ] T008 [US1] Implement current-live query functions in `backend/src/observatorio/api/queries.py`, joining `event_current` to its referenced `(mode, event_id, updated_at)` version and applying the same AND-combined filters with defaults `[now_utc - 24h, now_utc)`.
- [ ] T009 [US1] Implement `GET /api/eventos` serialization and route in `backend/src/observatorio/api/routes.py`, returning one current live Feature per event, the required collection metadata, epoch-millisecond UTC times, and a valid 2D Point plus `properties.depth_km: null` when depth is unknown.
- [ ] T010 [US1] Register the event router and common JSON error handling for query/storage failures in `backend/src/observatorio/api/app.py` and `backend/src/observatorio/api/routes.py`, ensuring successful empty results remain distinct from errors and failures never return an empty success-shaped collection or expose internal details.

**Checkpoint**: User Story 1 is independently consumable through the event collection contract; no health, statistics, or visual panel work is required for this increment.

---

## Phase 4: User Story 2 - Consultar salud y estadísticas (Priority: P2)

**Goal**: Report API/database/schema readiness and provide reproducible current and historical statistics using the same filter semantics as event queries.

**Independent Test**: Reconcile health status and last successful ingestion with a known database state; independently calculate fixed UTC hourly/country counts, distributions, missing counts, and the 2025 replay daily baseline for a controlled sample.

### Tests for User Story 2

- [ ] T011 [P] [US2] Specify `/api/salud` HTTP 200/503 behavior, including a failed/unavailable startup bootstrap while the HTTP server is serving, status fields, null last-ingestion behavior, stale-ingestion behavior, and absence of sensitive response details in `backend/tests/contract/test_health_contract.py`.
- [ ] T012 [P] [US2] Specify statistics response groups, shared-filter semantics, fixed UTC hourly boundaries, null populations, semi-open bins aligned to integer multiples of their widths, baseline coverage, zero-day denominator, and distribution percentages calculated from `valid_count` with `missing_count` excluded and reported separately in `backend/tests/unit/test_statistics.py`.
- [ ] T013 [P] [US2] Specify `/api/estadisticas` response shape, valid zero counts, bin-count reconciliation to `valid_count`, percentages based on valid values (null when none are valid), magnitude's pre-`min_mag` missing-count population, explicit storage failures, and the common non-success error envelope in `backend/tests/contract/test_statistics_contract.py`.
- [ ] T014 [P] [US2] Add database integration coverage for health/schema readiness, statistics reconciled against the complete matching current-event set (not an event-response sample), replay baseline coverage, and missing-baseline behavior in `backend/tests/integration/test_statistics_database.py`.

### Implementation for User Story 2

- [ ] T015 [US2] Implement the health query and `GET /api/salud` route in `backend/src/observatorio/api/queries.py` and `backend/src/observatorio/api/routes.py`, returning HTTP 200 only when PostgreSQL and the required schema are available, HTTP 503 otherwise (including while bootstrap/readiness is unavailable), and the latest successful live USGS `request_end` or null without secrets.
- [ ] T016 [US2] Implement current-live hourly, country, magnitude, and depth aggregation functions in `backend/src/observatorio/api/statistics.py`, using shared filters, UTC `[HH:00, HH+1:00)` buckets, semi-open bins aligned to integer multiples of width 0.5 for magnitude and 10 km for depth, per-distribution valid denominators/percentages, and missing magnitude counts from the selected period/country scope before `min_mag`.
- [ ] T017 [US2] Implement historical comparison in `backend/src/observatorio/api/statistics.py` from replay current events and completed ingestion intervals, treating the baseline as available only with full 2025 coverage and otherwise returning an explicit unavailable baseline rather than zero.
- [ ] T018 [US2] Implement `GET /api/estadisticas` in `backend/src/observatorio/api/routes.py`, documenting period, normalized filters, units, missing counts, current-period daily rate, 365-day 2025 mean including zero-event days, and explicit query errors.

**Checkpoint**: User Story 2 is independently consumable using the API after the P1 event query increment and does not depend on visual charts or tables.

---

## Phase 5: User Story 3 - Comunicar fallos y actualidad al cliente (Priority: P3)

**Goal**: Permit browser requests from exact authorized origins and provide a small transport client that distinguishes empty data from failures while retaining the last successful response.

**Independent Test**: Review the requirements for both allowed origins and an unlisted origin; verify client requirements cover successful empty collections, 15-second timeout, network/HTTP failures, retained last success and its `metadata.last_ingestion` exposed to the consumer, and secret-free public configuration.

### Tests for User Story 3

- [ ] T019 [P] [US3] Specify allowed-origin preflight, GET/OPTIONS methods, `ngrok-skip-browser-warning`, denied unlisted origins, explicit failure for malformed/wildcard/non-HTTPS production-origin configuration without partial application, and distinction between browser transport/CORS failure and an accessible API HTTP error in `backend/tests/contract/test_cors_contract.py`.
- [ ] T020 [P] [US3] Specify the transport module's 15-second timeout, empty-versus-error distinction, last-success retention including exposure of the retained `metadata.last_ingestion` to its consumer after a later request fails, recovery on a later caller-initiated success (replace data, clear error/staleness, and allow further requests), and cancellation of an active request when disposed in `frontend/tests/api-client.test.mjs`; do not test or implement automatic retries or a periodic refresh timer.

### Implementation for User Story 3

- [ ] T021 [US3] Parse and validate the configurable production-origin list plus the `http://localhost:4200` default in `backend/src/observatorio/config.py`; reject invalid, wildcard, credentialed, non-HTTPS production or non-origin values explicitly without silently dropping entries or applying a partial list, then configure CORS in `backend/src/observatorio/api/app.py` for GET/OPTIONS and `ngrok-skip-browser-warning` without credentials.
- [ ] T022 [US3] Add the public API URL configuration without credentials to `frontend/public/config.json`, and implement the native-fetch transport module in `frontend/src/api-client.mjs` with a 15-second timeout, typed distinction between transport failure and accessible API HTTP error, last-success retention including `metadata.last_ingestion` exposed to its consumer, and recoverable error/staleness state that clears on a later caller-initiated success; do not add automatic retries, periodic refresh, or visual UI.

**Checkpoint**: User Story 3 completes browser transport and CORS only; map, event details, visible filters, tables, and charts remain out of scope.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Keep the published contract and operator validation guide aligned with the implemented requirements.

- [ ] T023 [P] Update `docs/CONTRATO-API.md` with the final event, health, statistics (including valid-value denominators and missing-value handling), common validation/error envelope, and availability response shapes established by the three user stories.
- [ ] T024 [P] Update `docs/README.md` with the actual client configuration, API reachability, exact multi-origin CORS setup and invalid-configuration behavior, and distinction between browser transport/CORS failures and API HTTP failures, without documenting secrets.
- [ ] T025 Run the focused backend unit/contract/integration tests, `node --test frontend/tests/api-client.test.mjs`, and the scenarios in `specs/004-api-consultas-estadisticas/quickstart.md`; resolve any contract mismatch in the owning user-story task before marking this validation task complete.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No prerequisite; T001 must complete before the HTTP application can start.
- **Foundational (Phase 2)**: Depends on T001; T002 and T003 establish the runnable API process and block all user stories.
- **User Stories (Phase 3+)**: Depend on the foundational application/runtime tasks.
- **Polish (Phase 6)**: Depends on all user stories selected for delivery.

### User Story Dependencies

- **User Story 1 (P1)**: Starts after Phase 2; no dependency on another feature story.
- **User Story 2 (P2)**: Depends on User Story 1 (R19 depends on R18); reuses its normalized filters and current event query semantics.
- **User Story 3 (P3)**: Depends on User Story 1 (R20 depends on R18); connects browser transport to the event endpoint. It does not depend on the statistics work in User Story 2.

### Within Each User Story

- Contract/unit tests are specified before implementation tasks for their story.
- Query/schema definitions precede their endpoint consumers.
- Statistics reuse User Story 1 filter semantics; health can be implemented independently within User Story 2 after Phase 2.
- User Story 3 CORS settings and browser transport can be implemented independently after User Story 1 is available.

### Parallel Opportunities

- T004, T005, and T006 can run in parallel because they touch separate event contract, query unit, and database integration files.
- T011, T012, T013, and T014 can run in parallel because they specify distinct health, statistics unit/contract, and statistics database integration files.
- T019 and T020 can run in parallel because they cover backend CORS and browser transport contracts in separate files.
- T023 and T024 can run in parallel after the API/client contracts stabilize.
- User Story 3 can proceed in parallel with the final portions of User Story 2 after User Story 1 is complete, if ownership avoids overlapping `routes.py`/`app.py` edits.

## Parallel Examples

### User Story 1

```text
Task: T004 event endpoint contract requirements in backend/tests/contract/test_api_contract.py
Task: T005 query/filter requirements in backend/tests/unit/test_api_queries.py
```

### User Story 2

```text
Task: T011 health contract requirements in backend/tests/contract/test_health_contract.py
Task: T012 statistics aggregation requirements in backend/tests/unit/test_statistics.py
Task: T013 statistics endpoint contract requirements in backend/tests/contract/test_statistics_contract.py
Task: T014 statistics database coverage in backend/tests/integration/test_statistics_database.py
```

### User Story 3

```text
Task: T019 CORS requirements in backend/tests/contract/test_cors_contract.py
Task: T020 client transport requirements in frontend/tests/api-client.test.mjs
```

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete T001–T003 to make the existing API service runnable over HTTP.
2. Complete T004–T010 for current live event queries.
3. Validate User Story 1 independently using its contract scenarios and the matching event-query steps in `specs/004-api-consultas-estadisticas/quickstart.md`.
4. Stop at this MVP boundary if only event consultation is required; do not begin the visual panel.

### Incremental Delivery

1. Setup + foundational runtime → HTTP service available inside the existing five-service Compose topology.
2. User Story 1 → current-event GeoJSON query, independently usable.
3. User Story 2 → operational health and reconciled aggregates/history.
4. User Story 3 → exact-origin browser access and reusable transport/error state.
5. Polish → align documentation and run complete feature quickstart validation.

## Notes

- Every task follows `- [ ] T### [P?] [US#?] Description with exact file path(s)`.
- `[P]` appears only where tasks operate on independent files and have no unfinished prerequisites.
- Tests remain grouped under their owning user story; no extra service, schema, or visualization tasks are included.
- `docs/README.md` references `frontend/public/config.json`, but the file is absent in the current repository snapshot; T022 creates it as part of the client story.
