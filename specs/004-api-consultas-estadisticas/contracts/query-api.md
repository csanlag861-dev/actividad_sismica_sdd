# Query API Contract

Todos los endpoints comparten prefijo `/api`, JSON UTF-8 y fechas UTC. Los nombres de ruta y campos se conservan como los define `docs/CONTRATO-API.md`.

## `GET /api/eventos`

### Query parameters

| Parámetro | Tipo | Obligatorio | Regla |
|---|---|---:|---|
| `start` | ISO 8601 con zona/offset | no | Incluido. Default: ahora UTC menos 24 horas. |
| `end` | ISO 8601 con zona/offset | no | Excluido. Default: ahora UTC. |
| `min_mag` | número finito | no | Magnitud mínima inclusiva; excluye magnitud null. |
| `country_id` | código de país catalogado | no | Coincidencia exacta del identificador; país null no coincide. |
| `limit` | entero | no | Tamaño de página: 25, 50 o 100; default 25. |
| `offset` | entero no negativo | no | Posición base cero; default 0. |

`start` debe preceder a `end`. Los filtros se combinan con AND. La consulta es solo de eventos `live` actuales, no de mensajes ni todas las versiones. El orden es `event_time DESC, event_id ASC`. Parámetros desconocidos, malformados o con valores inválidos se rechazan; no se ignoran silenciosamente.

### `200 OK`

```json
{
  "type": "FeatureCollection",
  "metadata": {
    "generated": 1793113200000,
    "last_ingestion": 1793113140000,
    "mode": "live",
    "count": 1,
    "total_count": 1,
    "offset": 0,
    "limit": 25,
    "truncated": false
  },
  "features": [
    {
      "type": "Feature",
      "id": "event-id",
      "geometry": {"type": "Point", "coordinates": [-3.7, 40.4, 12]},
      "properties": {
        "mag": 3.2,
        "magType": "ml",
        "place": "Lugar",
        "depth_km": 12,
        "time": 1793109600000,
        "updated": 1793110000000,
        "country_id": null,
        "country_name": null
      }
    }
  ]
}
```

- Epoch ms UTC. Coordinates are longitude, latitude, depth in km.
- `mag`, `place`, magnitude type, depth, country id/name may be null where unknown. `properties.depth_km` is always present; if depth is null, use a valid 2D GeoJSON position `[longitude, latitude]` instead of a null third coordinate.
- No matches returns `200` with `features: []`, `count: 0`.
- `generated` is response generation time, not evidence that ingestion is running.
- `last_ingestion` is latest successful live USGS request end time or null.
- `count` is the response page size; `total_count` is the full filtered count before pagination. `truncated` is true exactly when the response omits matching events.
- `/api/estadisticas` retains its existing filters and does not accept `limit` or `offset`.

## `GET /api/salud`

Checks that the HTTP API is serving and PostgreSQL plus the required schema are available. HTTP serving does not wait for a successful database/schema bootstrap: while bootstrap or readiness is unavailable, this endpoint remains reachable and returns 503. Ingestion age does not change health.

### `200 OK`

```json
{"status": "ok", "last_ingestion": 1793113140000}
```

When no successful live ingestion exists, `last_ingestion` is null.

### `503 Service Unavailable`

```json
{"status": "unavailable", "last_ingestion": null}
```

Do not include credentials, DSNs, tokens, SQL, stack traces or internal exception text. Return 503 when database or schema readiness fails; do not report 200 merely because the process started.

## `GET /api/estadisticas`

Accepts the same `start`, `end`, `min_mag` and `country_id` parameters with the same defaults and filter semantics as `/api/eventos`. Current aggregates use live current events, and the historical comparison uses replay current events from 2025.

### `200 OK`

```json
{
  "period": {"start": "2026-11-16T00:00:00Z", "end": "2026-11-17T00:00:00Z"},
  "filters": {"min_mag": null, "country_id": null},
  "hourly_counts": {
    "unit": "events/hour (UTC)",
    "missing_count": 0,
    "buckets": [
      {"start": "2026-11-16T00:00:00Z", "count": 0},
      {"start": "2026-11-16T01:00:00Z", "count": 2}
    ]
  },
  "country_counts": {
    "unit": "events",
    "missing_count": 1,
    "buckets": [
      {"country_id": null, "country_name": "Sin país asignado", "count": 1},
      {"country_id": "ESP", "country_name": "España", "count": 1}
    ]
  },
  "distributions": {
    "magnitude": {
      "unit": "magnitude",
      "bin_width": 0.5,
      "valid_count": 1,
      "missing_count": 1,
      "buckets": [{"min_inclusive": 3.0, "max_exclusive": 3.5, "count": 1, "percentage": 100.0}]
    },
    "depth_km": {
      "unit": "km",
      "bin_width": 10,
      "valid_count": 1,
      "missing_count": 0,
      "buckets": [{"min_inclusive": 10, "max_exclusive": 20, "count": 1, "percentage": 100.0}]
    }
  },
  "historical_comparison": {
    "baseline_period": {"start": "2025-01-01T00:00:00Z", "end": "2026-01-01T00:00:00Z"},
    "baseline_days": 365,
    "baseline_available": true,
    "current_count": 2,
    "current_period_days": 1,
    "current_daily_average": 2.0,
    "historical_daily_average": 1.5,
    "daily_rate_difference": 0.5,
    "daily_rate_ratio": 1.3333333333333333,
    "unit": "events/day"
  }
}
```

The example shows the response shape, not live project data. Hour buckets are fixed UTC hour intervals, include empty hours in the requested period, and count by event occurrence time. Country null is retained as «Sin país asignado» and included in both its bucket and the informational `missing_count`. Distribution bins use semi-open boundaries `[k*w, (k+1)*w)` for integer `k`, with fixed widths 0.5 magnitude and 10 km depth, and report missing values separately. For each distribution, `valid_count` is the denominator for percentages: each bin's `percentage` is `100 * count / valid_count`; percentages are null when `valid_count` is zero. Missing values are excluded from both the denominator and bins and remain in `missing_count`. For depth, `valid_count + missing_count` reconciles to the filtered population. `magnitude.missing_count` is counted within the selected period/country scope before the `min_mag` filter, while magnitude `valid_count` and bin percentages use the selected results after all filters; therefore these two fields describe different populations when `min_mag` is set and must not be added together. Null magnitudes do not enter magnitude bins or satisfy that filter. `historical_comparison` compares the current-period daily rate to the mean daily count across all 365 days of replay 2025, including zero-event days; apply matching magnitude/country filters. Mark the baseline available only when completed historical intervals show coverage for the full calendar year. If no complete baseline coverage exists, set `baseline_available: false`, `historical_daily_average: null`, and omit any rate difference or ratio. When a baseline is available and its daily average is greater than zero, report `daily_rate_difference = current_daily_average - historical_daily_average` and `daily_rate_ratio = current_daily_average / historical_daily_average`. If the valid baseline average is zero, omit both fields rather than implying a finite comparison.

## Errors

| Status | Error code | Stable public message | Meaning |
|---|---|---|---|
| `400` | `malformed_request` | `Request syntax is malformed` | Request syntax that cannot be parsed. |
| `422` | `invalid_request` | `Request parameters are invalid` | Unknown query parameter or invalid ISO date, timezone-free date, non-finite magnitude, `start >= end`, or malformed/unsupported filter value. |
| `500` | `internal_error` | `The request could not be completed` | Unexpected query/serialization failure; body contains no internal exception details. |
| `503` | `dependency_unavailable` | `A required service is unavailable` | Database/schema unavailable for query dependencies; `/api/salud` retains its documented `status` response instead of this envelope. |

A non-success API response for malformed requests, invalid parameters, query failures, or unavailable dependencies uses this JSON shape:

```json
{
  "error": {
    "code": "invalid_request",
    "message": "Request parameters are invalid",
    "details": [
      {"parameter": "start", "reason": "must include a timezone offset"}
    ]
  }
}
```

`details` is an optional list of safe parameter names and validation reasons; it MUST NOT echo secret or sensitive input values. The `code` and public `message` must match the status mapping above. The health endpoint keeps its explicit `{"status": "unavailable", "last_ingestion": null}` response on 503. A failed event/statistics query must not return an empty collection or zero-valued aggregate as success. Empty and zero are valid only when the query completed successfully.
