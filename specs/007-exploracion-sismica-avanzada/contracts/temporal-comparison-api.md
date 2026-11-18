# Temporal Comparison API Contract

Add an operation for visitor-defined comparisons. It is separate from `GET /api/estadisticas` and does not modify that endpoint's fixed historical comparison.

## `POST /api/comparaciones`

Content type: `application/json`. Request body:

```json
{
  "mode": "replay",
  "filters": {
    "min_mag": null
  },
  "groups": [
    {
      "id": "periodo-a-espana",
      "label": "España, primer periodo",
      "period": {
        "start": "2025-01-01T00:00:00Z",
        "end": "2025-04-01T00:00:00Z"
      },
      "population": {
        "type": "country",
        "country_id": "ESP"
      }
    },
    {
      "id": "periodo-b-sin-pais",
      "label": "Sin país, segundo periodo",
      "period": {
        "start": "2025-04-01T00:00:00Z",
        "end": "2025-07-01T00:00:00Z"
      },
      "population": {
        "type": "unassigned"
      }
    }
  ]
}
```

### Request validation

- `mode` is exactly `live` or `replay` and applies to all groups.
- `filters.min_mag` is absent/null or a finite number; it is shared by all groups.
- `groups` contains two to five definitions with unique non-empty IDs and labels.
- Every period has ISO 8601 timestamps with offsets, UTC-normalized before comparison, and `start < end`; intervals are start-inclusive/end-exclusive.
- `population` is exactly one of `{"type":"all"}`, `{"type":"country","country_id":"ESP"}`, or `{"type":"unassigned"}`. Country IDs must exist in the catalog.
- Do not accept client-supplied SQL, query fragments, geometries, raw event payloads, or arbitrary filter names.

Invalid JSON syntax uses HTTP 400 `malformed_request`; invalid or unknown fields/values use HTTP 422 `invalid_request`; service/database failures use the established HTTP 500/503 envelopes. Validation details contain only safe field names and reasons.
If an individual group definition is invalid, identify its safe index or field path in `error.details` (for example `groups[1].period`). Do not return a partial comparison as a successful response.
If querying an otherwise valid group fails, return the established HTTP 500 `internal_error` or HTTP 503 `dependency_unavailable` envelope, with a safe detail identifying its request index (for example `groups[1]`) and reason `query_failed` or `dependency_unavailable`. Do not include exception details, group labels, or a partial comparison in the error response.

### Successful response

```json
{
  "mode": "replay",
  "filters": {
    "min_mag": null
  },
  "groups": [
    {
      "id": "periodo-a-espana",
      "label": "España, primer periodo",
      "period": {
        "start": "2025-01-01T00:00:00Z",
        "end": "2025-04-01T00:00:00Z"
      },
      "population": {
        "type": "country",
        "country_id": "ESP",
        "country_name": "España"
      },
      "coverage": {
        "status": "complete",
        "covered_days": 90,
        "period_days": 90
      },
      "observed_count": 12,
      "unavailable_metrics": {},
      "daily_rate": 0.1333333333,
      "distributions": {
        "magnitude": {
          "unit": "magnitude",
          "bin_width": 0.5,
          "valid_count": 12,
          "missing_count": 0,
          "buckets": [
            {
              "min_inclusive": 3.0,
              "max_exclusive": 3.5,
              "count": 7,
              "percentage": 58.3333333333
            }
          ]
        },
        "depth_km": {
          "unit": "km",
          "bin_width": 10,
          "valid_count": 10,
          "missing_count": 2,
          "buckets": [
            {
              "min_inclusive": 10,
              "max_exclusive": 20,
              "count": 10,
              "percentage": 100
            }
          ]
        }
      }
    },
    {
      "id": "periodo-b-sin-pais",
      "label": "Sin país, segundo periodo",
      "period": {
        "start": "2025-04-01T00:00:00Z",
        "end": "2025-07-01T00:00:00Z"
      },
      "population": {
        "type": "unassigned",
        "country_id": null,
        "country_name": "Sin país asignado"
      },
      "coverage": {
        "status": "complete",
        "covered_days": 91,
        "period_days": 91
      },
      "observed_count": 15,
      "unavailable_metrics": {},
      "daily_rate": 0.1648351648,
      "distributions": {
        "magnitude": {
          "unit": "magnitude",
          "bin_width": 0.5,
          "valid_count": 15,
          "missing_count": 0,
          "buckets": [
            {
              "min_inclusive": 3.0,
              "max_exclusive": 3.5,
              "count": 5,
              "percentage": 33.3333333333
            }
          ]
        },
        "depth_km": {
          "unit": "km",
          "bin_width": 10,
          "valid_count": 15,
          "missing_count": 0,
          "buckets": [
            {
              "min_inclusive": 10,
              "max_exclusive": 20,
              "count": 15,
              "percentage": 100
            }
          ]
        }
      }
    }
  ],
  "pairwise_differences": [
    {
      "first_group_id": "periodo-a-espana",
      "second_group_id": "periodo-b-sin-pais",
      "observed_count_difference": 3,
      "daily_rate_difference": 0.0315018315,
      "unavailable_reasons": {},
      "distribution_percentage_point_differences": {
        "magnitude": [
          {
            "min_inclusive": 3.0,
            "max_exclusive": 3.5,
            "difference": -25
          }
        ],
        "depth_km": [
          {
            "min_inclusive": 10,
            "max_exclusive": 20,
            "difference": 0
          }
        ]
      }
    }
  ]
}
```

### Result semantics

- `observed_count` counts current event records in the selected mode and group filters; it is not an assertion that the source population is complete.
- `coverage.status` is `complete`, `partial`, or `unknown`, based on recorded successful coverage for that mode and period. Include covered and period durations. A gap is never treated as zero events.
- `daily_rate` is observed count divided by exact period days, but is `null` unless coverage is complete.
- Distribution bins use the existing widths and units (0.5 magnitude and 10 km depth), semi-open intervals, and valid-value denominators. Missing values are separate. When coverage is incomplete or unknown, distributions are unavailable and the response gives a reason; the UI must not present observed-only bins as complete population statistics.
- Emit one pairwise entry for each unordered group pair. Signed differences mean second group minus first group.
- `unavailable_metrics` maps unavailable metric names (such as `daily_rate`, `magnitude`, or `depth_km`) to a safe reason code such as `coverage_incomplete`, `coverage_unknown`, or `no_valid_values`. `unavailable_reasons` does the same for pairwise fields such as `observed_count_difference`, `daily_rate_difference`, or a distribution. These fields are empty when every metric is available.
- Pairwise count/rate/distribution differences are `null` or omitted with an explicit unavailability reason if either group lacks complete coverage or a required valid-value denominator. Never encode unavailable metrics as zero.
- For a group with no events, return an empty collection of bins, zero observed count, and null rate only when the period/source coverage is incomplete; if covered, its rate is zero.
- Echo the effective period, population, source mode, and shared filters so the client can identify exactly what was compared.
- Responses are not persisted; the endpoint does not change `GET /api/estadisticas` or its `historical_comparison`.
