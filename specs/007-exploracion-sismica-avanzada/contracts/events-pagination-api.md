# Events Pagination API Contract

This is an additive extension of `GET /api/eventos`. Existing filter, GeoJSON, provenance, null-value, and error-envelope semantics remain unchanged.

## `GET /api/eventos`

### Query parameters

| Name | Type | Default | Rules |
|---|---|---:|---|
| `start` | ISO 8601 timestamp with timezone | now UTC minus 24 hours | Inclusive. |
| `end` | ISO 8601 timestamp with timezone | now UTC | Exclusive; `start < end`. |
| `min_mag` | finite number | absent | Inclusive minimum; null magnitudes do not match. |
| `country_id` | catalog country identifier | absent | Exact match; null country does not match. |
| `limit` | integer | 25 | Allowed values: 25, 50, 100. |
| `offset` | non-negative integer | 0 | Zero-based offset into the deterministic filtered result. |

Unknown or repeated parameters and invalid values use the existing safe HTTP 422 `invalid_request` response. Malformed query syntax uses HTTP 400. API/database failures preserve the existing 500/503 error envelope. All event filters are combined with AND.

### Ordering and consistency

Order rows by `event_time DESC, event_id ASC` so the most recent occurrences appear first and ties are deterministic. Execute a filtered total count and the bounded page against the same database transaction/snapshot where practical. The page request must not load all matching event rows into application memory. A later request can observe a newer database snapshot; page navigation is not a durable snapshot token.

### `200 OK`

Keep the existing GeoJSON Feature fields and `metadata` fields. `metadata.count` remains the number of features in this response. Add:

```json
{
  "metadata": {
    "count": 25,
    "total_count": 137,
    "offset": 25,
    "limit": 25,
    "truncated": true
  },
  "features": ["... existing GeoJSON features ..."]
}
```

- `total_count` is the number of events matching all filters before pagination.
- `offset` and `limit` echo the validated request.
- `truncated` is true exactly when this response does not contain the full matching collection (including pages whose offset is non-zero).
- An empty result has `count: 0`, `total_count: 0`, and `features: []`.
- Retain the existing `generated`, `last_ingestion`, and `mode` fields.

The UI computes page number from `offset / limit` and reports the total. If concurrent ingestion changes the result set between pages, stable ordering prevents ambiguous ordering within a response; a changed page total is displayed and an out-of-range offset is normalized to a valid page or returned as an empty page with the true total, never as a false zero-total query. Tables request one page at a time. The 2D map and 3D globe request successive pages of 100 under the same filters and combine them to display the complete matching collection. If a later page fails or the API still reports incomplete coverage after all pages are requested, the view reports the error or remaining truncation explicitly rather than presenting a partial collection as complete.

## Compatibility

Existing clients may ignore the additional metadata. The existing fields, feature shape, endpoint path, default event filters, and error contract remain compatible. The summary and exploration tables use the same page contract; map views aggregate pages through that contract and clearly indicate if the resulting collection remains partial.
