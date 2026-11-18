# Quickstart: Exploración sísmica avanzada

This guide validates the planned behavior end-to-end. Use a disposable test database and clearly labelled synthetic fixtures for deterministic scenarios; do not present fixture data as real earthquakes.

## Prerequisites

- Node.js 22.12+ or 24 and npm, consistent with the existing project guide.
- Python 3.12 with the backend requirements installed.
- Docker Compose, a configured `POSTGRES_PASSWORD`, and an API reachable from the frontend.
- A browser with WebGL2 for MapLibre and deck.gl; a supported WebGL browser for CesiumJS.

## Start the application

From the repository root, start the existing service stack:

```bash
docker compose up --build -d
```

In another terminal:

```bash
cd frontend
npm ci
npm start
```

Open `http://localhost:4200`. The public frontend configuration must contain only the API base URL; do not add Cesium ion, tile-provider, or API secrets.

## Validate contract and calculations

Run backend contract tests:

```bash
cd backend
python3 -m pytest -q tests/contract
```

Run frontend tests and the production build:

```bash
cd frontend
npm test
npm run build
```

Expected: API contract tests accept valid pagination and comparison inputs, reject invalid values with the safe error envelope, and preserve the historical-comparison response; all frontend tests and the strict Angular production build pass with MapLibre worker and Cesium static assets present.

## Manual acceptance scenarios

1. **Pagination**: use a fixture with 137 uniquely identified events and navigate through sizes 25, 50, and 100 on both the summary and exploration tables. Confirm displayed totals, stable ordering, no gaps/duplicates, filter preservation, page reset on filter/size change, and an accurate empty state.
2. **Latest event**: provide unsorted events with differing occurrence, update, and ingestion times; verify only the maximum occurrence time is marked, with all ties marked, and the map/table selection opens the same event.
3. **Map migration**: check local country boundaries, event selection, selected/latest styling, attribution, resize, and teardown/recreation. With deck.gl not loaded, confirm all core 2D behavior remains available. Open the advanced visualization and confirm the overlay is created and finalized without breaking map controls.
4. **Temporal comparison**: submit two or more known groups with different periods and populations, once in each source mode. Compare counts, exact-day rates, distributions, and pairwise differences with independent calculations. Use a coverage gap, zero valid magnitudes, and a country not in the catalog to confirm unavailable/validation behavior; confirm the fixed historical comparison still renders unchanged.
5. **3D globe**: open and leave the lazy route, verify no Cesium assets load before entry, then confirm the surface events, depth legend/detail, attribution, and worker/assets load. Destroy and re-enter the route to ensure resources are released. Disable WebGL or block a required asset and verify the fallback leaves the 2D map and tables usable.

## Reproducible performance and usability evaluation

1. Seed a disposable database with 1,000 uniquely identified, filter-matching events and use the same fixture for both tables. Record the browser/device, API and database environment, selected page size, and measurement method.
2. For each table and each page size (25, 50, and 100), perform 100 page changes, cycling through valid pages. Measure from the navigation request (click/key activation) until the requested rows and page controls are rendered. Record every duration and calculate the 95th percentile separately for each table/size combination; SC-002 passes only when at least 95 of the 100 changes in every combination complete in under 2 seconds.
3. Conduct an unaided task evaluation with 10 participants using clearly labelled fixture data. For SC-003, start timing once the map is displayed and ask each participant to identify the event marked most recent; success requires the correct event within 10 seconds, with at least 9 of 10 participants succeeding.
4. For SC-006, ask each participant to locate a specified event using table pagination and to explain the period and population in a displayed comparison. Count a participant as successful only if both tasks are completed correctly without assistance; at least 9 of 10 must succeed. Record only aggregate outcomes and do not include participant-identifying information.
