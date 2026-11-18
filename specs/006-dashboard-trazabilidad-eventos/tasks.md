# Tasks: Dashboard de actividad y trazabilidad sísmica

**Input**: Design documents from `specs/006-dashboard-trazabilidad-eventos/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`

**Organization**: Tasks are grouped by user story to enable independent implementation and validation. No new dependencies or infrastructure are required; the existing Angular app, Leaflet map, ECharts components, API state service, and persisted event-version fields are reused.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel with another task in the phase because it edits separate files and has no dependency on unfinished work.
- **[Story]**: User-story label mapping to `spec.md`.
- Every task names the exact file path(s) it changes.

## Phase 1: Setup

No setup tasks are required. The Angular app, backend, dependencies, and test commands already exist.

## Phase 2: Foundational

No shared blocking changes are required. User stories can proceed after setup; US2's dashboard integration depends on the US1 dashboard composition to avoid conflicting edits.

## Phase 3: User Story 1 - Consultar actividad sísmica reciente (Priority: P1) 🎯 MVP

**Goal**: Present recent events on the dashboard map with selectable event details and show the API's hourly UTC activity series.

**Independent Test**: Provide a known recent-event collection and statistics response; confirm each valid event can be selected on the map and the hourly series uses the returned buckets, UTC labels, period, and filters. An empty event result remains a valid empty state.

### Implementation for User Story 1

- [X] T001 [P] [US1] Create `ActivityTimelineComponent` in `frontend/src/app/features/dashboard/activity-timeline.component.ts`, `activity-timeline.component.html`, and `activity-timeline.component.css`; render only `hourly_counts.buckets` from `StatisticsResponse`, label hours UTC, show the API period/filters and missing count, provide a textual or tabular alternative, and distinguish empty data from errors.
- [X] T002 [P] [US1] Add the `frontend/public/icon.png` favicon declaration in `frontend/src/index.html` and replace the text-only brand mark in `frontend/src/app/app.component.html` with the same asset, preserving proportions and an accessible name without repeating the logo on every page.
- [X] T003 [US1] Integrate the existing `EventMapComponent`, `EventDetailComponent`, and `ActivityTimelineComponent` in `frontend/src/app/features/dashboard/dashboard-page.component.ts` and `frontend/src/app/features/dashboard/dashboard-page.component.html`; select the event by `Feature.id`, show the corresponding detail, preserve the separate event/statistics snapshots and their period/filter attribution, visibly communicate `truncated` event responses without implying the map contains the complete collection, and provide an accessible list or table of the events' essential values linked to event selection.
- [X] T004 [US1] Add layout and responsive styles for the dashboard map, selected-event detail, and hourly activity in `frontend/src/app/features/dashboard/dashboard-page.component.css`, retaining both themes and preventing essential content from being hidden or causing page-level horizontal overflow.

**Checkpoint**: US1 delivers a dashboard MVP with event geography, selectable details, hourly activity, accessible alternatives, and global application branding.

## Phase 4: User Story 2 - Interpretar magnitud y profundidad (Priority: P1)

**Goal**: Add summaries of the existing magnitude and depth distributions without recomputing statistics or obscuring missing values.

**Independent Test**: Supply statistics with known bins, percentages, valid and missing counts, null percentages, and empty buckets; confirm the summary retains the API values and attributes itself to the statistics period and filters.

### Implementation for User Story 2

- [X] T005 [P] [US2] Create `DistributionSummaryComponent` in `frontend/src/app/features/dashboard/distribution-summary.component.ts`, `distribution-summary.component.html`, and `distribution-summary.component.css`; present the magnitude and depth bins, units, valid/missing counts and API percentages, with an accessible text/table alternative and no fabricated percentages or zero values.
- [X] T006 [US2] Add `DistributionSummaryComponent` to `frontend/src/app/features/dashboard/dashboard-page.component.ts` and `frontend/src/app/features/dashboard/dashboard-page.component.html`; show its statistics period and filters independently from the events collection, and preserve valid-empty, loading, error, and stale states.
- [X] T007 [US2] Extend responsive dashboard layout in `frontend/src/app/features/dashboard/dashboard-page.component.css` for the distribution summaries and their accessible tables in both visual themes.

**Checkpoint**: US2 independently adds API-backed magnitude and depth summaries to the completed dashboard composition.

## Phase 5: User Story 3 - Rastrear el origen de un evento (Priority: P2)

**Goal**: Expose compact per-version event traceability through the existing API and display it in the event detail without publishing source payloads or hashes.

**Independent Test**: Query a known current event and compare its displayed identity, mode, safe source, version time, ingestion time, and run ID with its public response. Also cover nullable trace values and a previous API response without traceability metadata.

### Implementation for User Story 3

- [X] T008 [P] [US3] Extend `EventRow` in `backend/src/observatorio/api/queries.py` to carry the current version's `mode`, `source`, `ingested_at`, and `ingestion_run_id` from `EventVersion`; keep `event_id` and `updated_at` as the existing canonical identity/version values and do not query or expose original payload/hash fields.
- [X] T009 [US3] Serialize `properties.traceability` in `backend/src/observatorio/api/routes.py` with `mode`, safe `source`, `ingested_at` as Unix milliseconds UTC or `null`, and `ingestion_run_id` as UUID string or `null`; whitelist only `usgs-live` and `usgs-replay` source labels and return `null` for any other source.
- [X] T010 [P] [US3] Document the additive `properties.traceability` object, its field meanings, nullability, UTC units, safe-source whitelist, and privacy exclusions in `docs/CONTRATO-API.md`; preserve all existing event and statistics semantics.
- [X] T011 [P] [US3] Add contract assertions in `backend/tests/contract/test_api_contract.py` for mode/source/version/ingestion metadata, nullable values, unchanged existing fields, and absence of original payload/hash; add a client fixture assertion in `frontend/tests/api-client.test.mjs` for a previous API response without traceability metadata.
- [X] T012 [US3] Add `EventTraceability` and optional `properties.traceability` types in `frontend/src/app/core/models/api.models.ts` with `mode` restricted to `"live" | "replay"`, nullable source/ingestion fields, and existing `Feature.id`/`properties.updated` retained as identity/version.
- [X] T013 [US3] Update `isEventCollection` in `frontend/src/api-client.mjs` to accept either a missing traceability object from an older API or a valid object whose `mode` is `"live" | "replay"`, `source` is `string | null`, and `ingested_at` is a finite number or `null`, `ingestion_run_id` is a string or `null`; reject malformed present traceability without weakening existing field validation.
- [X] T014 [US3] Extend `frontend/src/app/features/events/event-detail.component.html` and `frontend/src/app/features/events/event-detail.component.ts` to show the event ID, mode, source, version timestamp, ingestion timestamp, and run ID with Spanish labels, UTC dates, and “No disponible” for absent trace data; do not infer missing values.
- [X] T015 [US3] Add responsive styling for the traceability section in `frontend/src/app/features/events/event-detail.component.css` without hiding long IDs or making the detail unusable on narrow viewports.

**Checkpoint**: US3 exposes safe version-level provenance while preserving older consumers, older API responses, existing event properties, and statistics.

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T016 [P] Align `specs/006-dashboard-trazabilidad-eventos/contracts/dashboard-ui.md` and `specs/006-dashboard-trazabilidad-eventos/contracts/event-traceability.md` with `specs/006-dashboard-trazabilidad-eventos/spec.md`, preserving the documented UI states and the additive, privacy-safe event-traceability fields.
- [X] T017 Run the backend contract suite from `backend/` with `python -m pytest -q tests/contract/test_api_contract.py`, the frontend API-client suite from `frontend/` with `node --test tests/api-client.test.mjs`, the Angular suite with `npm test` including dashboard assertions for unique valid geometries, omission of invalid geometries, a visible truncation notice when `truncated` is true, an accessible event list/table linked to selection, and the logo's accessible name in `frontend/src/app/features/dashboard/dashboard-page.component.spec.ts` and `frontend/src/app/app.component.spec.ts`; verify logo legibility in every available theme and production build with `npm run build`; resolve failures in the relevant files.
- [X] T018 Run the end-to-end scenarios and timed usability protocol in `specs/006-dashboard-trazabilidad-eventos/quickstart.md`; record the environment, elapsed time, task correctness, and outcome in the test-execution evidence accompanying the delivery, and update the quickstart only if its commands or expected results changed.

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No tasks; current project structure and dependencies are already present.
- **Foundational (Phase 2)**: No tasks; no shared schema, service, dependency, or infrastructure work blocks the stories.
- **US1 (Phase 3)**: Starts immediately; provides the primary dashboard increment and MVP.
- **US2 (Phase 4)**: Dashboard summary component can be developed independently; its integration tasks depend on the US1 dashboard page composition to avoid simultaneous edits to the same page files.
- **US3 (Phase 5)**: Can proceed independently of US1 and US2; backend API, public contract, client model/validator, and detail UI changes affect separate files.
- **Polish (Phase 6)**: Depends on the desired stories being integrated; run all validation before completion.

### User Story Dependencies

- **US1 (P1)**: No story dependency.
- **US2 (P1)**: The summary component can be implemented in parallel with US1; dashboard integration follows US1's page composition.
- **US3 (P2)**: No story dependency. The traceability API shape is designed to be additive; the UI treats missing traceability as unavailable until the API change is deployed. T014 depends on T012's `EventTraceability` type; after T012 it can proceed in parallel with backend implementation.

### Parallel Opportunities

- After US1 page structure is in place, T005 can run alongside T008–T010 and T012–T013 because they edit separate files.
- In US1, T001 and T002 edit distinct component/asset files and can proceed in parallel; T003 depends on T001 and integrates its component.
- In US2, T005 is independent of the dashboard page; T006 follows T003 and T007 follows the integrated layout.
- In US3, T008 and T010 can proceed in parallel; T012 can proceed in parallel with backend work. T014 starts after T012 and can then proceed in parallel with backend work. T009 depends on T008; T013 also depends on T012's public type definition.
- T017 and T018 are final validation tasks after implementation and documentation have stabilized.

## Parallel Example: User Story 1

```text
Task: T001 Create the hourly activity timeline component in frontend/src/app/features/dashboard/activity-timeline.component.*
Task: T002 Add the global favicon and application brand asset in frontend/src/index.html and frontend/src/app/app.component.html
```

## Parallel Example: User Story 3

```text
Task: T008 Extend EventRow provenance fields in backend/src/observatorio/api/queries.py
Task: T010 Document the additive event traceability object in docs/CONTRATO-API.md
Task: T012 Define the frontend traceability types in frontend/src/app/core/models/api.models.ts
Task: T014 Present traceability fields in frontend/src/app/features/events/event-detail.component.html and .ts
```

## Implementation Strategy

### MVP First (User Story 1)

1. Reuse the current map and query snapshots; implement and integrate the hourly activity component and logo.
2. Validate US1 against the independent test and the corresponding dashboard acceptance scenarios.
3. Stop for a demonstrable dashboard increment before adding distribution summaries or API traceability.

### Incremental Delivery

1. Deliver US1 map and temporal activity as the MVP.
2. Add US2 magnitude/depth distribution summaries, preserving API-provided values and accessible alternatives.
3. Add US3 backend contract, client compatibility, and traceability in the shared event detail.
4. Run all validation commands and the feature quickstart.

## Notes

- `[P]` tasks edit separate files and do not depend on unfinished work.
- `[US1]`, `[US2]`, and `[US3]` map to the user stories in `spec.md`.
- Trace metadata uses existing persisted fields; no migration is required.
- Do not publish original payloads, hashes, source query parameters, credentials, or secrets.

## Phase 7: Convergence

- [X] T019 Make `test_events_contract_hides_unrecognized_traceability_source` in `backend/tests/contract/test_api_contract.py` use a deterministic query period containing its seeded event, then rerun the API contract suite and resolve failures per T017 / FR-008 (partial).
- [X] T020 Run the Angular Jasmine/Karma suite in an environment with ChromeHeadless available, resolve any failures, and verify logo legibility in each available theme per T017 / SC-001–SC-004, SC-006 (partial).
- [X] T021 Execute the end-to-end scenarios and timed usability protocol in `specs/006-dashboard-trazabilidad-eventos/quickstart.md` with a participant and known test data; record environment, elapsed time, task correctness, and outcome per T018 / SC-005 (partial).

## Phase 8: Convergence

- [X] T022 Run the complete Angular Jasmine/Karma suite in an environment with ChromeHeadless, resolve any test failures, and visually verify the logo in each available theme per T017 / SC-001–SC-004, SC-006 (partial).
- [X] T023 Conduct the guided usability protocol with a participant and known data, then record environment, elapsed time, task correctness, and outcome in delivery evidence per T018 / SC-005 (partial).
