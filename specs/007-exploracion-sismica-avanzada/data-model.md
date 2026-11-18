# Data Model: Exploración sísmica avanzada

## Existing source entities

### Current event

An event's latest version in one data mode, already represented by `EventVersion` and selected through `EventCurrent`.

| Field | Type / meaning | Validation and use |
|---|---|---|
| `mode` | `live` or `replay` dataset | All groups in one comparison use the same mode. |
| `event_id` | Stable event identifier | Used as a deterministic ordering tie-breaker and GeoJSON feature ID. |
| `event_time` | UTC occurrence instant | Filters use `[start, end)`; recency compares this field only. |
| `updated_at`, `ingested_at` | Version and ingestion instants | Provenance only; neither determines the newest occurrence. |
| `magnitude`, `depth_km` | Nullable finite measurements | Null remains missing; magnitude filter excludes null. |
| `longitude`, `latitude` | Geographic point | Must be valid for display; invalid points are not rendered. |
| `country_id` | Catalog code or null | Null means unassigned; never infer a country from proximity. |

### Country

The existing country catalog entry with `country_id` and display names. Country populations must validate against this catalog. `unassigned` is a distinct selector matching a null country identifier; it is not a country code.

### Ingestion coverage

Existing successful live request intervals and completed replay intervals provide the evidence used to describe coverage of a requested period. A group is `complete` only when the union of successful intervals covers its whole half-open period under the source mode's documented ingestion semantics. Otherwise it is `partial` when some interval evidence exists, or `unknown` when coverage cannot be established. A gap must not be interpreted as zero events.

## Request and view entities

### Event page

An API view over current events after applying the existing period, magnitude, and country filters.

| Field | Type / meaning | Invariant |
|---|---|---|
| `limit` | Page size | One of 25, 50, or 100; default 25. |
| `offset` | Zero-based row offset | Integer, non-negative; default 0. |
| `count` | Number of returned features | Equals the response page length. |
| `total_count` | All matching rows before paging | Stable for the query snapshot. |
| `features` | Current event page | Ordered by `(event_time DESC, event_id ASC)`, with no duplicates across non-overlapping offsets. |

### Comparison request

One non-persistent request containing:

- `mode`: one shared source dataset, `live` or `replay`.
- `min_mag`: nullable shared magnitude threshold.
- `groups`: two to five group definitions with unique caller-supplied IDs, a non-empty display label, UTC `start` and `end`, and a population selector.

The population selector is exactly one of `all`, `country(country_id)`, or `unassigned`. Periods must satisfy `start < end`; country IDs must exist in the catalog. Requests do not persist or mutate event data.

### Comparison group result

The response for one requested group echoes its ID, label, mode, period, population, shared filters, and `coverage.status`. It reports the observed event count and missing-value counts. The daily rate and distributions are available only when coverage is complete and their denominators are valid; otherwise the response identifies the unavailable measure and reason.

### Pairwise difference

For each unordered pair of requested comparison groups, the response may report:

- Signed absolute difference for observed counts and daily rates (second group minus first group).
- Distribution differences in percentage points for matching half-open magnitude and depth bins (second group minus first group).

Differences are unavailable if either group's coverage is incomplete, a required denominator is zero, or bin definitions do not match. The existing historical baseline is not an entity or input to this operation.

## Map and globe projections

- **2D map feature**: A valid GeoJSON point backed by one event. The map uses an independent first page of up to 100 newest events under the active filters; if the full matching set is larger, it shows the latest 100 and discloses truncation. The latest marker is the event or tied events with the maximum valid occurrence time among those displayed features.
- **3D globe marker**: A surface location backed by one valid geographic event. Known depth is encoded as a labelled visual value/scale relative to the surface and shown exactly in the event detail; it is not converted into an ellipsoid altitude or presented as a visible underground coordinate.

## State and validation rules

1. A page request preserves all active event filters and applies the same stable newest-first ordering.
2. Changing filters or page size resets the offset to zero; navigation beyond `total_count` is rejected or normalized to the final valid page.
3. If total is zero, `count` and `features` are empty and there is no current page with data.
4. A comparison's shared mode/filter apply to every group. Group period/population may differ; no groups may silently mix `live` and `replay`.
5. Unknown measurement values remain null and contribute to missing counts, not bins or denominators.
6. Only a complete coverage status permits normalized rates and pairwise comparisons. Partial/unknown coverage is surfaced next to observed counts and never described as a complete population.
7. Map recency uses occurrence time; ties are retained and an event with an invalid time cannot win by update/ingestion time.
