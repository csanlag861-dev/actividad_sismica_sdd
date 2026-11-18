# Tasks: Exploración sísmica avanzada

**Input**: Design documents from `specs/007-exploracion-sismica-avanzada/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md), [data-model.md](./data-model.md), [API contracts](./contracts/), [quickstart.md](./quickstart.md)

**Tests**: No separate test-first phase was requested. Add or update focused tests in the implementation tasks below and run the full project validation in the final phase.

**Organization**: Tasks are grouped by user story so pagination, map improvements, comparisons, and the 3D globe can be delivered in independently testable increments.

## Phase 1: Setup

**Purpose**: Install the selected map/globe packages and record compatible exact resolutions in the lockfile.

- [X] T001 Add `maplibre-gl`, `@deck.gl/core`, `@deck.gl/layers`, `@deck.gl/maplibre`, and `cesium` to `frontend/package.json`, remove the replaced Leaflet packages, and regenerate `frontend/package-lock.json`.

---

## Phase 2: Foundational

**Purpose**: Establish the shared paged-event response shape used by the tables, 2D map, and 3D globe.

- [X] T002 Define typed event-page metadata (`total_count`, zero-based `offset`, validated `limit`) and event-page request options in `frontend/src/app/core/models/api.models.ts`; preserve existing GeoJSON fields and tolerate old responses where optional metadata is absent.

**Checkpoint**: Shared event-page types are available. User stories can proceed in priority order; US2 and US4 depend on the bounded events API delivered by US1.

---

## Phase 3: User Story 1 - Consultar eventos por páginas (Priority: P1) 🎯 MVP

**Goal**: Let users navigate complete, filtered event results in controlled pages from both the summary and exploration tables.

**Independent Test**: With 137 uniquely identified matching events, navigate pages of 25, 50, and 100 from both tables; verify correct totals, stable ordering, no gaps/duplicates, filter preservation, page reset, and a truthful empty state.

### Implementation for User Story 1

- [X] T003 [P] [US1] Add an event-page query type and validation in `backend/src/observatorio/api/schemas.py`: `limit` MUST be one of 25, 50, or 100 (default 25), `offset` MUST be a non-negative integer (default 0), and malformed/unknown values MUST keep the existing safe 400/422 error contract without making statistics accept pagination parameters.
- [X] T004 [P] [US1] Implement a bounded current-event page query and filtered total count in `backend/src/observatorio/api/queries.py`, ordered by `event_time DESC, event_id ASC`; do not materialize all matching rows to serve a page.
- [X] T005 [US1] Extend `GET /api/eventos` in `backend/src/observatorio/api/routes.py` to return the bounded page, preserve all existing event/provenance fields, and report page `count`, filtered `total_count`, `offset`, `limit`, and accurate `truncated` metadata.
- [X] T006 [P] [US1] Add API contract cases in `backend/tests/contract/test_api_contract.py` for defaults, allowed/invalid page sizes, negative/non-integer offset, empty results, total count, deterministic ordering, and page boundaries; assert existing filters and error envelopes remain unchanged.
- [X] T007 [P] [US1] Update `docs/CONTRATO-API.md` and `specs/004-api-consultas-estadisticas/contracts/query-api.md` with the event pagination query/response metadata, stable order, size limits, and unchanged statistics semantics.
- [X] T008 [P] [US1] Extend request serialization and response validation in `frontend/src/api-client.mjs` and its declarations in `frontend/src/api-client.d.mts` for `limit`/`offset` and pagination metadata; expose typed page fetching through `frontend/src/app/core/api/observatory-api.service.ts` without converting API failures to empty pages.
- [X] T009 [US1] Implement accessible page-size, previous/next, current-page, and total-result controls in `frontend/src/app/features/events/events-table.component.ts`, `frontend/src/app/features/events/events-table.component.html`, and `frontend/src/app/features/events/events-table.component.css`; load pages using active shared filters, reset offset on filter/size changes, preserve selected-event behavior, and show loading, error, empty, and out-of-range states.
- [X] T010 [US1] Wire independent table pagination into `frontend/src/app/features/dashboard/dashboard-page.component.html` and `frontend/src/app/features/events/events-page.component.html`; add/update component tests in `frontend/src/app/features/events/events-table.component.spec.ts` and relevant dashboard/event-page specs for both table instances and filter changes.

**Checkpoint**: Both tables page through the full matching result set and display the correct total without relying on client-side slicing.

---

## Phase 4: User Story 2 - Reconocer el evento más reciente en el mapa (Priority: P1)

**Goal**: Replace the Leaflet map with MapLibre GL JS, show the latest matching events first, and optionally provide an advanced deck.gl visualization.

**Independent Test**: Provide unsorted events with differing occurrence/update/ingestion times and ties; verify all matching event pages are combined, the newest occurrence is highlighted and selectable, any remaining truncation is disclosed, provider attribution is visible, and the map still works when deck.gl is not loaded.

### Implementation for User Story 2

- [X] T011 [P] [US2] Configure `frontend/angular.json` and `frontend/src/styles.css` for the MapLibre stylesheet and self-hosted MapLibre worker asset URL; remove Leaflet stylesheet configuration and verify the production output contains the worker at the configured path.
- [X] T012 [P] [US2] Replace Leaflet map creation and country-boundary rendering in `frontend/src/app/shared/map/map-layers.service.ts` with a MapLibre map, attributed OpenStreetMap raster style, local country GeoJSON source/fill layer, explicit load/error handling, and teardown-safe layer registration.
- [X] T013 [US2] Rebuild `frontend/src/app/shared/map/event-map.component.ts`, `.html`, and `.css` around MapLibre GeoJSON sources/layers; preserve valid-coordinate filtering and event selection, distinguish selected/latest features, retain the depth legend, surface load failures, and release map resources on destruction.
- [X] T014 [US2] Update `frontend/src/app/core/state/query-state.service.ts` and `frontend/src/app/features/dashboard/dashboard-page.component.ts` so map data uses the active filters, keeps table pages independent, and reports incomplete results; select every event tied for the maximum valid occurrence time, never by updated/ingested time.
- [X] T015 [US2] Add a lazy optional deck.gl advanced-density/hexagon overlay using `MapLibreOverlay` in the shared map feature; load it only on explicit user activation, keep the default MapLibre map fully interactive without it, and finalize its GPU resources when disabled or destroyed.
- [X] T016 [P] [US2] Add/update map tests in `frontend/src/app/shared/map/event-map.utils.spec.ts` and `frontend/src/app/shared/map/event-map.component.spec.ts` for latest-event ties, invalid/missing times and coordinates, selection identity, truncation, worker/style failures, deck.gl-disabled behavior, and lifecycle cleanup.

**Checkpoint**: MapLibre is the only primary 2D map, the latest event is highlighted across the complete matching event collection, and the optional overlay cannot block base-map or table behavior.

---

## Phase 5: User Story 3 - Comparar periodos y poblaciones (Priority: P2)

**Goal**: Compare two to five visitor-defined groups over a shared current or historical data mode without changing the existing fixed historical comparison.

**Independent Test**: Compare groups with known periods/populations in each mode; verify counts, coverage, daily rates, distributions, missing values, and pairwise differences against independent calculations; verify invalid groups fail explicitly and the existing historical comparison remains unchanged.

### Implementation for User Story 3

- [X] T017 [P] [US3] Add TypeScript request/response interfaces for two-to-five-group comparisons in `frontend/src/app/core/models/api.models.ts` and a typed `POST /api/comparaciones` client method in `frontend/src/api-client.mjs`, `frontend/src/api-client.d.mts`, and `frontend/src/app/core/api/observatory-api.service.ts`; include exact group IDs, periods, population selectors, coverage status, unavailable metrics, and pairwise differences.
- [X] T018 [P] [US3] Validate the comparison body in `backend/src/observatorio/api/schemas.py` and catalog membership in `backend/src/observatorio/api/routes.py`: common `mode` is `live` or `replay`, shared `min_mag` is finite or null, there are 2-5 groups with unique non-empty IDs/labels, each period is timezone-aware UTC with `start < end`, and each population is exactly all/country/unassigned.
- [X] T019 [US3] Implement comparison aggregation in `backend/src/observatorio/api/statistics.py` using existing distribution widths (0.5 magnitude and 10 km depth), valid/missing counts, and a bounded period-coverage calculation over successful ingestion intervals; identify each group as complete/partial/unknown and mark unavailable metrics with safe reason codes.
- [X] T020 [US3] Add `POST /api/comparaciones` in `backend/src/observatorio/api/routes.py` and its filtered group queries in `backend/src/observatorio/api/queries.py`; return exact-period observed counts, complete-coverage-only daily rates/distributions, signed second-minus-first pairwise differences, and safe unavailable reasons, without modifying `GET /api/estadisticas`.
- [X] T021 [P] [US3] Add comparison validation/math/coverage contract cases in `backend/tests/contract/test_statistics_contract.py` and relevant backend unit tests, including a failed query for one valid group that asserts an HTTP 500/503 safe error identifies its `groups[index]` and returns no partial comparison; update `docs/CONTRATO-API.md` and `specs/007-exploracion-sismica-avanzada/contracts/temporal-comparison-api.md` to match tested response/error semantics.
- [X] T022 [US3] Add a separate visitor-defined comparison form and results view in `frontend/src/app/features/analytics/analytics-page.component.ts`, `.html`, and `.css` with 2-5 editable groups, current/historical mode, catalog-country/all/unassigned populations, period validation, coverage and unavailable states, distributions, and pairwise differences; leave `historical-comparison.component.*` behavior unchanged and add focused component tests.

**Checkpoint**: The visitor can compare groups descriptively with complete filter/coverage context while the historical comparison continues to behave as before.

---

## Phase 6: User Story 4 - Explorar eventos sobre un globo 3D (Priority: P3)

**Goal**: Add a separately navigable, lazily loaded CesiumJS globe that shows event locations and communicates depth without inventing underground coordinates.

**Independent Test**: Open the 3D view with valid locations and known/unknown depths; verify surface markers, depth scale and exact detail value, event selection, attribution, lazy asset loading, cleanup, and a usable fallback when WebGL/assets fail.

### Implementation for User Story 4

- [X] T023 [P] [US4] Add a lazy `/globo-3d` route and navigation entry in `frontend/src/app/app.routes.ts` and `frontend/src/app/app.component.html`; ensure the Cesium module is not imported by the initial route bundle.
- [X] T024 [P] [US4] Configure `frontend/angular.json` to copy Cesium `Workers`, `ThirdParty`, `Assets`, and `Widgets` into the SPA output at a single documented base URL; load Cesium widget CSS only in the globe feature and do not add an ion token or other credential to `frontend/public/config.json`.
- [X] T025 [US4] Implement the Cesium viewer in `frontend/src/app/features/globe-3d/globe-3d-page.component.ts`, `.html`, and `.css`; initialize only after the browser host exists, request the newest filtered event page, render valid locations as surface markers, encode known depth with a labelled scale and exact ficha value (never a subsurface/negative ellipsoid position), indicate unknown depth, preserve Cesium/provider credits, and destroy the viewer on route teardown.
- [X] T026 [US4] Add globe component tests in `frontend/src/app/features/globe-3d/globe-3d-page.component.spec.ts` for unknown depth, invalid coordinates, selection, failed asset/WebGL initialization, retry/fallback, and viewer destruction; confirm the regular event table and MapLibre route remain usable when the globe fails.

**Checkpoint**: The globe is isolated from core navigation and does not invent depth or compromise the map/table experiences.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Align project guidance and verify the integrated frontend/API behavior.

- [X] T027 [P] Update `docs/README.md`, `docs/VALIDACION.md`, and `docs/FUENTES-Y-LICENCIAS.md` for the MapLibre migration, optional deck.gl layer, Cesium assets/attribution, and browser validation; leave the assignment's original Leaflet wording in `docs/ENUNCIADO.md` and `docs/FAQ-ALUMNADO.md` intact and retain the documented feature exception in `specs/007-exploracion-sismica-avanzada/plan.md`.
- [ ] T028 Run backend contract/unit tests from `backend/`, `npm test` and `npm run build` from `frontend/`, then execute the pagination, comparison, 2D attribution/worker, optional deck.gl, Cesium lazy-asset, and WebGL fallback scenarios in `specs/007-exploracion-sismica-avanzada/quickstart.md`; fix failures in the corresponding source/test files.
- [ ] T029 Measure pagination performance in both tables using the 1,000-event fixture and 100 page changes for each table/page-size combination (25, 50, and 100) defined in `specs/007-exploracion-sismica-avanzada/quickstart.md`; record every duration and each combination's p95, browser/device, API/database environment, and measurement method, and verify SC-002's 95% under-two-second threshold for every combination.
- [ ] T030 Conduct the 10-participant unaided usability evaluation defined in `specs/007-exploracion-sismica-avanzada/quickstart.md`; record aggregate SC-003 and SC-006 success counts without participant-identifying information and verify the required 9-of-10 outcomes.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No prerequisite; install and lock browser visualization packages.
- **Foundational (Phase 2)**: Depends on Setup; shared paged-event response types block API-client and visualization work.
- **US1 (Phase 3)**: Depends on Foundational; delivers the page endpoint and both paginated tables.
- **US2 (Phase 4)**: Depends on US1's bounded event endpoint and the shared filter/page types; it can start once T005 and T008 are complete.
- **US3 (Phase 5)**: Depends on Foundational types and the existing country catalog; independent of US1/US2 implementation.
- **US4 (Phase 6)**: Depends on Setup and the bounded current-event API from US1; it can start once T005 and T008 are complete.
- **Polish (Phase 7)**: T027 can run in parallel with feature implementation; T028 depends on all selected stories; T029 follows validated pagination and T030 follows validated map, pagination, and comparison experiences.

### User Story Dependencies

- **US1 (P1)**: First MVP increment; no story dependency.
- **US2 (P1)**: Shares filters and event-page API with US1; otherwise the MapLibre source/layer work is isolated.
- **US3 (P2)**: Independent after Foundational; does not replace or depend on the historical comparison.
- **US4 (P3)**: Uses the event-page API from US1 but is isolated behind its own route and can be implemented independently after that API is ready.

### Parallel Opportunities

- T003 and T004 can proceed in parallel; T006 can be authored alongside endpoint work.
- Within US1, frontend API/table work (T008-T010) can proceed in parallel with backend query/schema/route work (T003-T005) after T002; integration tests and final metadata wiring follow both.
- Within US2, T011 MapLibre build configuration, T012 map-layer service, and T016 test preparation can proceed in parallel after the package setup; T015 deck.gl overlay can proceed after the MapLibre map surface is available.
- US3 can be implemented independently of the map work after T002; T017-T018 can proceed in parallel, followed by aggregation/route and UI.
- US4 route/asset configuration (T023-T024) can proceed in parallel after Setup; the viewer task T025 follows both and the US1 page endpoint.
- T027 documentation work can run in parallel with any user story.
- T029 and T030 are separate acceptance evaluations and should run after the relevant implementation and automated validation are complete.

## Parallel Example: User Story 1

```text
Task: T003 Add and validate event pagination parameters in backend/src/observatorio/api/schemas.py
Task: T004 Implement the bounded stable query and total count in backend/src/observatorio/api/queries.py
Task: T006 Add pagination contract cases in backend/tests/contract/test_api_contract.py
Task: T008 Add typed pagination request support in frontend/src/api-client.mjs and frontend/src/app/core/api/observatory-api.service.ts
```

## Parallel Example: User Story 3

```text
Task: T017 Define comparison request/response types and typed frontend client in frontend/src/app/core/
Task: T018 Validate group, mode, period, filter, and population inputs in backend/src/observatorio/api/
Task: T021 Add the API contract examples and tests in backend/tests/contract/ and specs/007-exploracion-sismica-avanzada/contracts/
```

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Setup and Foundational phases.
2. Deliver the bounded API page query and shared table controls in US1.
3. Validate both summary and exploration tables independently with the 137-event fixture.
4. **STOP and VALIDATE** the pagination MVP before starting the map migration or comparison work.

### Incremental Delivery

1. Deliver US1 pagination as the first usable increment.
2. Deliver US2 MapLibre migration and latest-event highlight; keep deck.gl optional.
3. Deliver US3 as a separate comparison operation and analytics view; preserve historical comparison.
4. Deliver US4 as an opt-in lazy globe route.
5. Run the cross-story build, contracts, accessibility checks, attribution checks, and quickstart scenarios.

## Phase 8: Convergence

- [X] T031 Show an explicit map status when no event has a valid occurrence time and identify tied latest events as “Más reciente” per FR-007, US2/AC3 (partial).
- [X] T032 Count and disclose events excluded for invalid coordinates in the 3D globe when they affect the displayed results per FR-018, US4/AC3 (partial).
- [X] T033 Indicate when the globe is displaying a previous successful event response after a refresh fails, including its potentially stale status per FR-020, US4/AC4 (partial).
- [ ] T034 POSPUESTA por decisión del usuario: no ejecutar la batería completa de aceptación manual. Se hicieron comprobaciones parciales en navegador; quedan sin validar todos los escenarios integrados de paginación, comparación, MapLibre/deck.gl y Cesium/WebGL.
- [ ] T035 POSPUESTA at the user's request until the 1,000-event fixture and performance-test environment are available; then measure and record all 100 page-change durations and p95 results for both tables at page sizes 25, 50, and 100 per SC-002, T029 (missing).
- [ ] T036 POSPUESTA por decisión del usuario: no realizar ahora la evaluación con diez participantes ni registrar resultados de SC-003/SC-006.
- [X] T037 Retrieve and combine all event pages for the shared 2D map and Cesium globe using `ObservatoryApiService.fetchAllEvents`; preserve explicit incomplete-result messaging and verify multi-page retrieval in `observatory-api.service.spec.ts`.

### Cierre de implementación

La implementación de la spec 007 se considera cerrada y no bloquea el inicio de otra spec. T034 y T036 quedan pendientes por decisión del usuario; T035 continúa pospuesta hasta disponer del fixture y del entorno de medición. Estas validaciones no se marcan como completadas ni se consideran evidencia de aceptación.
