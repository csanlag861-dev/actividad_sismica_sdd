# Implementation Plan: Exploración sísmica avanzada

**Branch**: `main` (feature branch pendiente) | **Date**: 2026-11-18 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/007-exploracion-sismica-avanzada/spec.md`; requested libraries: MapLibre GL JS as the primary 2D cartographic library, deck.gl as an optional advanced-visualization complement, and CesiumJS for the specialized 3D globe.

## Summary

Add server-side event pagination for the summary and exploration tables, deterministically highlight the newest event by occurrence time on the 2D map, add a separate multi-group temporal comparison operation, and provide an opt-in 3D globe view. Keep the existing five-service Compose topology and public API error semantics.

Use MapLibre GL JS for the 2D map with the existing local country GeoJSON and an attributed OpenStreetMap raster style. Keep event selection and the accessible event table available without map interaction. Load deck.gl only in the optional advanced-visualization experience. Load CesiumJS only when the dedicated globe route is opened, serve its required static assets from the SPA, and retain Cesium's attribution display. Do not require a public Cesium ion credential. In 3D, keep event markers on the surface and encode known depth with a labelled visual indicator and exact value; do not claim that a point inside the solid globe is visible or use a fabricated altitude.

Extend `GET /api/eventos` with bounded offset pagination and stable newest-first ordering. Tables request their selected page; maps retrieve and combine every page of matching events, and explicitly indicate when the resulting collection remains incomplete. Add `POST /api/comparaciones` for two to five groups, with a shared data mode and minimum-magnitude filter; each group supplies a half-open period and one population (all, one catalogued country, or unassigned). Report coverage with each group, and withhold rates and pairwise differences when coverage or valid-value denominators are insufficient. Keep the existing historical comparison response unchanged.

## Technical Context

**Language/Version**: Frontend TypeScript 5.9 / Angular 20.3; backend Python 3.12.

**Primary Dependencies**: MapLibre GL JS (primary 2D map); deck.gl (`@deck.gl/maplibre`, optional advanced visualization); CesiumJS (specialized 3D globe); existing Angular Router, RxJS, FastAPI, SQLAlchemy 2, and PostgreSQL driver.

**Storage**: Existing PostgreSQL current-event, country-catalog, ingestion-run, and ingestion-interval tables; no new persistent entities or migrations expected.

**Testing**: Angular/Karma/Jasmine unit and component tests; frontend `npm run build`; API contract and integration tests with pytest; `git diff --check`. Browser checks for worker/static asset loading, map interaction, WebGL fallback, and provider attribution.

**Target Platform**: Existing Angular SPA deployed on Netlify or served locally; existing FastAPI API in Docker Compose; current supported desktop/mobile browsers with WebGL2 for MapLibre/deck interleaving and Cesium's required WebGL capabilities.

**Project Type**: Existing full-stack web application (Angular frontend and FastAPI API).

**Performance Goals**: Meet SC-002: with a reproducible 1,000-event fixture, measure 100 page changes in each table at each allowed page size (25, 50, and 100), from navigation request to rendered results; at least 95% in every table/size combination must complete in under 2 seconds. Record browser/device, API/database environment, page size, and measurement method. Load deck.gl and CesiumJS outside the initial application chunk; do not regress the existing production bundle budget without an explicit budget review.

**Constraints**: Pagination sizes are 25/50/100, with 25 default and 100 maximum. Comparison groups share a data mode and common event filters; their date ranges and populations may differ. Periods are UTC, start-inclusive/end-exclusive. Report incomplete or unknown coverage instead of treating absent observations as zero. Keep the historical comparison's behavior and API fields stable. No credentials in public configuration. Preserve map-provider attribution and release WebGL resources when views are destroyed.

**Scale/Scope**: Summary, event exploration, analytics, a new optional 3D route, up to 100 events per API page and all matching events across pages in map views, and two to five groups per comparison; no new Compose service, free-drawn polygon regions, or persistent comparison history.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle / restriction | Gate | Plan evidence |
|---|---|---|
| I. Reference documents and contracts | PASS with documented feature exception | The source [ENUNCIADO](../../docs/ENUNCIADO.md) and FAQ specify Angular + Leaflet. The user explicitly requested Leaflet's replacement by MapLibre; this plan documents the exception while preserving the SPA, required services, and query/data contracts. Update the canonical API contract and implementation guidance during implementation; do not silently change the assignment's original wording. |
| II. Explicit provenance and data quality | PASS | Use event occurrence time for recency; keep live/replay modes distinct; retain nulls; expose coverage and missing-value counts; never infer country or depth. |
| III. Idempotent processing and revisions | PASS | No producer, consumer, event-version, or aggregation write-path changes are planned. Read current versions only. |
| IV. Interoperable and secure exposure | PASS | New API is additive and public-data-only; validate inputs and country IDs; reuse stable safe error envelopes; introduce no credentials or private endpoint. |
| V. Reproducible, proportionate analysis | PASS | Compare descriptive observed rates/distributions only when coverage supports them; retain period, filters, units, denominators, and missing counts; make no risk or prediction claims. |
| Project topology and cartography | PASS after the recorded v1.1.0 constitution amendment | Keep the five required Compose services and the Angular SPA. Replace the former Leaflet implementation restriction with the explicitly requested MapLibre primary map, optional deck.gl, and dedicated CesiumJS globe. See the constitution Sync Impact Report and feature exception above. |
| Optional complexity | PASS | deck.gl is lazy/optional; CesiumJS is isolated to an explicit route and lazy chunk. Neither becomes a required backend service or blocks the core table and 2D map. |

**Post-design gate**: PASS. The schema requires no migrations, the API additions preserve existing operations, and map/globe dependencies are client-side and lazy where optional. The accepted library change is documented in `.specify/memory/constitution.md` version 1.1.0.

## Project Structure

### Documentation (this feature)

```text
specs/007-exploracion-sismica-avanzada/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── events-pagination-api.md
│   └── temporal-comparison-api.md
└── tasks.md                         # generated in Phase 2, not by this command
```

### Source Code (repository root)

```text
backend/src/observatorio/api/
├── routes.py                         # paginated events and comparison operation
├── schemas.py                        # validated query/body contracts
├── queries.py                        # stable bounded event page and filtered counts
└── statistics.py                     # shared distribution/coverage calculations

backend/tests/
├── contract/                         # pagination and comparison response contracts
├── integration/                      # DB filtering, ordering, coverage, error behavior
└── unit/                             # comparison math and input validation

frontend/src/app/
├── core/api/                         # typed calls for event pages and comparison
├── core/models/                      # page and comparison types
├── core/state/                       # filters and current page state
├── features/events/                  # shared paginated table controls
├── features/analytics/               # separate multi-group temporal comparison
├── features/globe-3d/                # lazy Cesium viewer and depth legend
└── shared/map/                       # MapLibre event/country sources and layers

frontend/
├── angular.json                      # MapLibre worker/CSS and Cesium static assets
├── package.json                      # pinned compatible client dependencies
└── src/styles.css                    # MapLibre CSS and application-wide map layout
```

**Structure Decision**: Extend the existing single Angular SPA and FastAPI API in place. Reuse shared event/query models and the country catalog. Keep the 2D map in the existing shared-map feature, place the advanced comparison beside the current historical comparison without replacing it, and lazy-load Cesium from a separate route.

## Complexity Tracking

No unresolved constitution violations. The extra visualization libraries are user-selected and bounded to optional/lazy experiences; the single additional comparison operation is needed because the current API has no multi-group operation.
