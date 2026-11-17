# Quickstart: Consulta API y estadísticas sísmicas

This guide validates the API feature after implementation. It does not publish the frontend or configure a real tunnel/domain.

## Prerequisites

- Docker Compose v2 and the repository's non-public `.env` values (at minimum `POSTGRES_PASSWORD`).
- Backend Python dependencies installed if running pytest on the host.
- Backend at the repository root; the API listens on port 8000 inside Compose.

## Start the services

```bash
docker compose up --build -d
docker compose ps
```

Expected: `postgres`, `kafka`, `api`, `productor` and `consumidor` start; the API healthcheck becomes healthy after migrations/schema are ready. The API listens on `0.0.0.0:8000` inside its container and is published on the host only as `127.0.0.1:8000:8000`; do not expose PostgreSQL or Kafka. External HTTPS access remains through the configured tunnel.

## Run focused tests

```bash
cd backend
pytest -q tests/unit/test_api_queries.py tests/unit/test_statistics.py
pytest -q tests/contract/test_api_contract.py tests/contract/test_health_contract.py tests/contract/test_statistics_contract.py tests/contract/test_cors_contract.py
pytest -q tests/integration/test_event_query_database.py tests/integration/test_statistics_database.py
cd ..
node --test frontend/tests/api-client.test.mjs
```

Expected: unit tests cover boundaries/nulls/aggregations, contract tests assert JSON/status/CORS behavior, integration tests verify current-version joins, full-set aggregate reconciliation, and real PostgreSQL/schema readiness, and Node tests exercise client timeout/errors while retaining the last successful response.

To run the PostgreSQL-backed API integration against the already-started Compose database without replacing the long-running API service:

```bash
docker compose run --rm --no-deps api python -m pytest -q tests/integration/test_postgresql_api.py
```

The test creates and removes a uniquely named temporary schema; it does not modify the application schema or persistent application data.

## Check events and filters

With the API reachable as `http://127.0.0.1:8000`:

```bash
curl -i 'http://127.0.0.1:8000/api/eventos'
curl -i 'http://127.0.0.1:8000/api/eventos?start=2026-11-16T00%3A00%3A00Z&end=2026-11-17T00%3A00%3A00Z&min_mag=4&country_id=ESP'
```

Expected: `200 application/json`; a valid FeatureCollection with every matching current live version exactly once, times in epoch ms, valid point geometry, and metadata indicating no truncation. No match is `features: []`; a DB failure is non-2xx. A request syntax error returns HTTP 400; unknown or invalid parameters return HTTP 422. Query errors use the common `{"error":{"code":"...","message":"..."}}` JSON envelope (optional safe parameter/reason details only), not an empty success-shaped collection. Verify start is inclusive and end exclusive using the contract fixture.

## Check health and statistics

```bash
curl -i 'http://127.0.0.1:8000/api/salud'
curl -i 'http://127.0.0.1:8000/api/estadisticas'
```

Expected: health remains reachable and returns `200` with database/schema ready or `503` if the database, schema, or bootstrap readiness is unavailable; an old or null last ingestion does not change health. Statistics identify the time period, applied filters, units and missing counts, include unassigned-country and empty hourly buckets, and compare the current daily rate against replay 2025 including zero days. For each distribution, bin percentages use `valid_count`; absent values are excluded from that denominator and reported separately. With no valid values, percentages are `null`. Magnitude `missing_count` is measured before `min_mag`, so when that filter is present it does not share the filtered population used by magnitude bins and `valid_count`. If no replay baseline exists, it is explicitly unavailable rather than a zero-valued valid baseline.

## Check browser preflight

```bash
curl -i -X OPTIONS 'http://127.0.0.1:8000/api/eventos' \
  -H 'Origin: http://localhost:4200' \
  -H 'Access-Control-Request-Method: GET' \
  -H 'Access-Control-Request-Headers: ngrok-skip-browser-warning'
curl -i -X OPTIONS 'http://127.0.0.1:8000/api/eventos' \
  -H 'Origin: https://unlisted.example' \
  -H 'Access-Control-Request-Method: GET'
```

Expected: development preflight authorizes the requested GET/header; the unlisted origin receives no CORS allow-origin permission. Repeat the first command with the exact deployed origin configured for the API.

The configured production-origin list accepts exact HTTPS origins only, in addition to the explicit development origin. An invalid, wildcard, or non-HTTPS production entry must produce an explicit startup configuration error; no invalid entry may be silently dropped and no partial list may be applied. An unlisted browser origin is denied CORS access, which may appear to `fetch` as a transport failure with no accessible HTTP response; this differs from an accessible non-2xx API response.

## Verify client failure behavior

Use the client transport test or browser dev environment to simulate a request taking longer than 15 seconds, a disconnected/unavailable API, and an accessible non-2xx API response. Expected: timeout/network/CORS transport failures are distinct from an HTTP error with a response status, and both are distinct from an empty collection. After a failure, a new caller-initiated query remains possible; if it succeeds, it replaces the retained read and clears the error and possible-staleness state. Until then, the previous successful read is retained and marked possibly stale, with its `metadata.last_ingestion` value still exposed to the consumer. The module does not schedule retries or periodic refreshes and does not render UI. A valid empty FeatureCollection remains a successful result.

## Stop

```bash
docker compose down
```

Do not remove persistent volumes as part of routine validation.
