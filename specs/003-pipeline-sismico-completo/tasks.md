# Tasks: Pipeline sísmico completo H5

**Input**: Design documents from `specs/003-pipeline-sismico-completo/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`.

**Organization**: Tasks are ordered by the five user stories and H5's pipeline sequence. Existing backend modules and tests are extended; tasks with `[P]` touch independent files and can proceed in parallel.

## Phase 1: Setup

**Purpose**: Prepare reusable test inputs for the existing Python backend without adding dependencies or services.

- [X] T001 [P] Add reusable GeoJSON Feature and Kafka-envelope fixture builders for real-like and malformed test cases in `backend/tests/conftest.py`.

## Phase 2: Foundational

**Purpose**: Provide a deterministic source-payload fingerprint for publisher deduplication and in-place version replacement, without inferring hashes for incomplete legacy payloads.

- [X] T002 [P] Add tests for stable fingerprints across JSON key ordering, changed source content, and exclusion of volatile envelope metadata in `backend/tests/unit/test_payload_fingerprint.py`.
- [X] T003 Implement canonical JSON SHA-256 fingerprinting of the complete source Feature, excluding envelope timestamps, in `backend/src/observatorio/payloads.py`.

**Checkpoint**: Shared fixtures and fingerprint utility are ready; publisher and consumer can apply changed source content to one version row.

## Phase 3: User Story 1 - Ingerir novedades de USGS con su procedencia (Priority: P1) 🎯 MVP

**Goal**: Poll USGS, archive each complete live response before extracting Features, publish new and changed events with traceable extraction metadata, and only record publication after Kafka ACK.

**Independent Test**: With a controlled feed, archive a complete response before processing, then ingest a new Feature and an exact repeat; identical response bytes share an archive while both extraction runs remain recorded, and a failed request leaves the previous successful run intact.

### Tests for User Story 1

- [X] T004 [P] [US1] Test live fixed-rate 60-second scheduling with 5-second tolerance, monotonic deadlines, missed-slot behavior, no overlap, 8-second timeout and at most 3 retries at 1/2/4 seconds; also verify the envelope's original Feature and provenance in `backend/tests/unit/test_live_ingestion.py`.
- [X] T005 [P] [US1] Test that a hash equal to the latest ACK for a version identity is skipped, a changed hash is forwarded, a previously seen hash is forwarded again after another hash was ACKed, and Kafka failure does not record publication in `backend/tests/unit/test_publisher.py`.

### Implementation for User Story 1

- [X] T006 [US1] Add `PublishedPayload` keyed by `(mode, event_id, updated_at, payload_sha256)` without changing legacy `PublishedVersion`; add `SourceArchive` keyed by response SHA-256 with auditable `deleted_at`, nullable `IngestionRun.query_metadata` and `source_archive_sha256`, and nullable `Quarantine.ingestion_run_id`; create a backfill-safe migration that leaves old fingerprints unknown in `backend/src/observatorio/models/publication.py`, `backend/src/observatorio/models/reference.py`, `backend/src/observatorio/models/quarantine.py`, and `backend/migrations/versions/0003_live_provenance.py`.
- [X] T007 [US1] Change `publish_event` to fingerprint and publish the complete original GeoJSON Feature; skip only when the hash equals the latest ACKed hash for that identity, forward a changed hash even if it appeared earlier before a different hash, treat legacy `PublishedVersion` rows as unknown rather than equal, and write the ledger only after `send_and_wait` succeeds in `backend/src/observatorio/producer/publisher.py`.
- [X] T008 [US1] Archive the complete live response atomically before extracting or publishing Features; deduplicate stored files by response SHA-256 while creating one `IngestionRun` per query with request URL, timestamps, HTTP status, count, source mode, and archive reference; schedule every 60 seconds with 5-second tolerance, 8-second request timeout, up to 3 retries at 1/2/4 seconds for network/429/5xx/unparseable responses, no retry for other 4xx, no overlap or catch-up burst, and preserve the previous successful run on errors in `backend/src/observatorio/producer/live.py`, `backend/src/observatorio/producer/source.py`, and `backend/src/observatorio/config.py`.
- [X] T009 [US1] Test controlled feed-to-consumer persistence, archive-before-publish ordering, identical response reuse across distinct runs, failed-poll recovery, and repeat-poll idempotence against `specs/003-pipeline-sismico-completo/contracts/pipeline-message.md` in `backend/tests/integration/test_live_pipeline.py`.

**Checkpoint**: Live polling and publication are traceable, duplicate-safe, and independently testable.

## Phase 4: User Story 2 - Validar y aislar datos no procesables (Priority: P2)

**Goal**: Validate consumed Features, retain optional nulls, and durably isolate non-earthquakes and invalid messages before committing offsets.

**Independent Test**: Consume a valid Feature with null optional fields, a non-earthquake Feature, a non-Point geometry, and out-of-range coordinates; only the valid earthquake becomes an event, other outcomes are durably classified, and offsets advance only after their database transactions commit.

### Tests for User Story 2

- [X] T010 [P] [US2] Test that a valid GeoJSON Point with null magnitude, depth, and place is accepted, non-earthquake types are excluded with a reason, and invalid Feature/geometry/coordinates are quarantined in `backend/tests/unit/test_validation.py`.
- [X] T011 [P] [US2] Test exclusion/quarantine idempotency by Kafka position and offset ordering after durable persistence in `backend/tests/unit/test_pipeline_persistence.py`.

### Implementation for User Story 2

- [X] T012 [US2] Validate `payload.type == "Feature"`, `geometry.type == "Point"`, required properties and coordinates, finite/range rules, and `properties.type == "earthquake"` while preserving optional nulls in `backend/src/observatorio/consumer/validation.py`.
- [X] T013 [US2] Persist non-earthquake exclusions with reason code `event_type_excluded`, preserve raw Kafka bytes, parsed original and `ingestion_run_id` when available, and keep the existing unique `(kafka_topic, kafka_partition, kafka_offset)` quarantine rule in `backend/src/observatorio/consumer/processor.py` and `backend/src/observatorio/models/quarantine.py`.
- [X] T014 [US2] Ensure invalid and excluded outcomes commit before Kafka offset advancement and database failures leave offsets uncommitted in `backend/src/observatorio/consumer/main.py` and `backend/tests/unit/test_pipeline_persistence.py`.

**Checkpoint**: Valid, excluded, and invalid records have distinct durable outcomes; no rejected input is exposed as a valid event.

## Phase 5: User Story 3 - Mantener versiones actuales correctas ante reintentos (Priority: P3)

**Goal**: Preserve one event-version row per `(mode, event_id, updated_at)`, replace its accepted source/hash in-place when a changed payload with that identity arrives, and keep one current event pointing to the newest timestamp.

**Independent Test**: Process E1 at 10:05, its repeat, E1 revision at 10:09, the older version again, and E2 at 10:12. Expect two current events and three distinct versions; E1 remains at 10:09. A changed Feature with E1's same `updated` replaces that one historical version and its accepted source/hash in-place, without adding an event, version, or quarantine; a lower or higher magnitude follows the latest received payload.

### Tests for User Story 3

- [X] T015 [P] [US3] Test the five-message E1/E2 acceptance sequence, duplicate retry, stale-version replay, and exact final counts in `backend/tests/unit/test_pipeline_persistence.py`.
- [X] T016 [P] [US3] Test same-version changed-payload in-place replacement of normalized data, accepted Feature/hash, and run provenance, with no second version or conflict quarantine; verify legacy versions without a complete source are upgraded from the incoming Feature in `backend/tests/unit/test_pipeline_persistence.py`.

### Implementation for User Story 3

- [X] T017 [US3] Add `EventVersionSource` with primary key/FK `(mode, event_id, updated_at)` and mutable `payload_sha256`, complete Feature, and accepted run provenance; keep the hash out of `EventVersion` and do not backfill from partial legacy payloads in `backend/src/observatorio/models/events.py`, `backend/src/observatorio/models/reference.py`, and `backend/migrations/versions/0004_event_version_source.py`.
- [X] T018 [US3] In `persist_message`, treat same-identity/same-hash input as an idempotent duplicate; when the hash differs, atomically replace normalized fields, the single `EventVersionSource` Feature/hash/provenance, and the historical `EventVersion` payload without creating another version or conflict quarantine; preserve `EventCurrent` unless this timestamp is newer, and accept a complete incoming source for legacy rows in `backend/src/observatorio/consumer/processor.py`.
- [X] T019 [US3] Keep version insertion/replacement and monotonic current-row advancement atomic, and ensure exact retries after commit do not repeat effects while changed same-version payloads deterministically replace the single row in `backend/src/observatorio/consumer/processor.py`.
- [X] T020 [US3] Run the sequence, same-version replacement, rollback, and offset-order tests and verify migration compatibility for an existing database in `backend/tests/unit/test_pipeline_persistence.py`, `backend/tests/integration/test_live_pipeline.py`, and `backend/tests/integration/test_migrations.py`.

**Checkpoint**: Duplicate and stale deliveries are idempotent; changed content with the same version identity replaces the one row and accepted source deterministically.

## Phase 6: User Story 4 - Enriquecer eventos con el catálogo geográfico (Priority: P4)

**Goal**: Enrich valid events from the checked-in Natural Earth catalog and assign a country only for exactly one spatial match.

**Independent Test**: A point uniquely inside Spain maps to `ESP`; ocean points, boundary points, and points matching multiple catalog entities persist with `country_id = null`, without using place text or nearest-country inference.

### Tests for User Story 4

- [X] T021 [US4] Test unique land match, ocean, boundary, multiple polygon matches, catalog code uniqueness, and unchanged source catalog checksum in `backend/tests/unit/test_geography.py` and `backend/tests/unit/test_catalog.py`.

### Implementation for User Story 4

- [X] T022 [US4] Extend `Country` with nullable `name_es`, `admin`, `continent`, and `subregion` while retaining the existing three-character `country_id` PK and compatible `country_name`; add the backfill-safe Alembic migration in `backend/src/observatorio/models/reference.py` and `backend/migrations/versions/0005_country_catalog_attributes.py`.
- [X] T023 [US4] Load and validate the catalog's `ADM0_A3`, `NAME_ES`, `ADMIN`, `CONTINENT`, and `SUBREGION` attributes without modifying the GeoJSON or assuming ADM0_A3 is an ISO code in `backend/src/observatorio/db/catalog.py`.
- [X] T024 [US4] Preserve the exactly-one-spatial-match rule and return no country for zero or multiple matches, including boundaries, in `backend/src/observatorio/consumer/geography.py`; verify catalog loading and assignment in `backend/tests/unit/test_geography.py` and `backend/tests/unit/test_catalog.py`.

**Checkpoint**: Country enrichment is repeatable and ambiguous locations remain unassigned.

## Phase 7: User Story 5 - Incorporar el histórico conservando su origen (Priority: P5)

**Goal**: Fetch, archive, and replay historical data by resumable UTC intervals, using common validation and persistence without duplicate results.

**Independent Test**: Load controlled historical intervals, interrupt between archive and publication and during consumption, resume, repeat the completed load, and restart Compose. Shared response archives, checkpoints, and provenance survive; identical response bytes are not stored twice and final version counts do not increase on replay.

### Tests for User Story 5

- [X] T025 [P] [US5] Test month-to-subinterval subdivision at 20,000 Features, inclusive-boundary deduplication, filters, and explicit failure when a time interval cannot be further split safely in `backend/tests/unit/test_replay_source.py`.
- [X] T026 [P] [US5] Test archive-before-publish, checksum verification, interval state transitions, restart/resume, repeated archive reuse, retention while dependent processed data exists, and repeat-load idempotency in `backend/tests/integration/test_replay_isolation.py` and `backend/tests/unit/test_replay_source.py`.

### Implementation for User Story 5

- [X] T027 [US5] Add `IngestionInterval` with unique `(run_id, interval_start, interval_end)`, UTC range, filters JSON, status in `pending/archived/publishing/complete/failed`, nonnegative attempts and counts, `SourceArchive` reference, stage timestamps, and error summary; add a backfill-safe migration in `backend/src/observatorio/models/reference.py` and `backend/migrations/versions/0006_ingestion_intervals.py`.
- [X] T028 [US5] Replace offset-only reliance with recursive UTC interval subdivision whenever a response reaches 20,000 Features; preserve effective filters and upsert inclusive-boundary inputs by `(mode, event_id, updated_at)`, replacing the accepted source/hash if content differs, in `backend/src/observatorio/producer/replay_source.py`.
- [X] T029 [US5] Reuse the live `SourceArchive` mechanism to archive each historical GeoJSON response atomically to the persistent producer volume, verify SHA-256, link intervals to the archive, and clean only archives with no processed dependents while recording `deleted_at`; make archive paths configurable without secrets in `backend/src/observatorio/producer/replay.py`, `backend/src/observatorio/config.py`, and `compose.yaml`.
- [X] T030 [US5] Publish archived Features incrementally as complete original Features in `quakes.replay`; update each interval checkpoint only after all records are published or already acknowledged, and resume incomplete intervals after failure in `backend/src/observatorio/producer/replay.py` and `backend/src/observatorio/producer/publisher.py`.
- [X] T031 [US5] Add CLI support for explicit UTC start/end ranges to recover live gaps over 24 hours, while keeping year 2025, global extent, magnitude >=4, and earthquake as defaults; record exact query filters and counts in `backend/src/observatorio/producer/replay.py`.
- [X] T032 [US5] Verify historical archive/replay behavior across PostgreSQL/Kafka restarts, preserve live/history separation, and confirm completed intervals and current event counts survive reruns in `backend/tests/integration/test_replay_isolation.py` and `backend/tests/integration/test_live_pipeline.py`.

**Checkpoint**: Historical runs are traceable, resumable from durable source archives, and safe to repeat or use for gap recovery.

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Verify the H5 pipeline as a whole, document its operation, and leave later query/panel work out of scope.

- [X] T033 [P] Create `docs/PIPELINE-OPERACION.md` and root `.env.example` with live/historical configuration, archive volume, deduplication and retention cleanup, legacy fingerprint handling, recovery commands, and provenance fields without adding credentials.
- [X] T034 Run all H5 scenarios from `specs/003-pipeline-sismico-completo/quickstart.md` against isolated tests and the five-service Compose stack; record actual commands/results in `specs/003-pipeline-sismico-completo/quickstart.md`.
- [X] T035 Verify no secrets or payloads are emitted in logs and no Kafka/PostgreSQL/archive service is publicly exposed in `backend/src/observatorio/logging.py` and `compose.yaml`.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependency; adds stable source fixtures.
- **Foundational (Phase 2)**: Depends on Setup; fingerprint utility blocks publication deduplication and consumer in-place replacement.
- **User Stories (Phase 3+)**: Depend on foundational tasks and follow H5 data flow.
- **Polish (Phase 8)**: Depends on all H5 stories selected for delivery.

### User Story Dependencies

- **US1 (P1)**: Depends on Phase 2; MVP begins live collection and delivery with source provenance.
- **US2 (P2)**: Follows US1 for end-to-end live flow; unit tests can use controlled fixtures independently.
- **US3 (P3)**: Follows US2 because in-place version replacement and persistence ordering depend on validated message outcomes.
- **US4 (P4)**: Follows US2 for applying geographic enrichment only to validated events; can run its catalog unit tests independently.
- **US5 (P5)**: Depends on US2, US3, and US4 because historical events must use common validation, versioning, and enrichment.

### Parallel Opportunities

- Phase 1: T001 is independently executable.
- Phase 2: T002 is test-first for the independent fingerprint utility T003; its test file and implementation file are separate.
- US1: T004, T005, and T008 touch independent test/producer areas; publisher implementation T007 depends on the fingerprint helper and schema T006.
- US2: T010 and T011 are separate test files and can be authored in parallel; T012 and T013 can proceed in separate modules after their acceptance is agreed.
- US3: T015 and T016 can be authored in parallel; T017 schema/model and T018 consumer behavior are separate after US1's fingerprint envelope is complete.
- US4: After test-first task T021, T023 catalog loading and T024 spatial matching touch separate modules and can proceed in parallel once T022's schema is applied.
- US5: T025 extraction algorithm tests and T027 model/migration work are parallel; T028 interval extraction and T029 archive storage can proceed on separate files after the interval model is set.
- The story gates remain ordered; parallel work does not permit skipping required upstream behavior.

### Within Each User Story

- Create acceptance tests before implementation; run them against controlled fixtures.
- Apply schema/model changes before relying on new persistence fields.
- Complete producer transport before consumer acceptance; commit durable results before offsets.
- Verify each story's independent criterion at its checkpoint before starting its dependent story.

## Implementation Strategy

1. **MVP (US1)**: Deliver real live USGS polling and source-preserving Kafka publication; prove retries and ACK-based publication state.
2. **Quality boundary (US2)**: Validate Features and durably classify exclusions/rejections before advancing consumer offsets.
3. **Correctness core (US3)**: Complete the exact event/version sequence, same-version in-place replacement, and monotonic current-state handling.
4. **Geographic enrichment (US4)**: Persist Natural Earth attributes and ensure ambiguous events remain unassigned.
5. **Historical completion (US5)**: Add interval archives/checkpoints, subdivision, replay reuse, and >24-hour gap recovery.
6. **Cross-cutting finish**: Run all quickstart checks against real Compose services, document results and retention cleanup, and keep H6 API/panel work outside this feature.
