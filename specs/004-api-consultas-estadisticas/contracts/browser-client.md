# Browser Client and CORS Contract

## Allowed origins and preflight

- Allow the exact deployed HTTPS frontend origin supplied by runtime configuration; never use `*`.
- Also allow `http://localhost:4200` for development.
- Allow methods `GET` and `OPTIONS`.
- Allow request header `ngrok-skip-browser-warning` and the normal CORS negotiation headers.
- Do not enable credentialed requests or cookies; this public read API has no browser authentication.
- A preflight for an allowed origin/method/header succeeds and authorizes the following GET. An unlisted origin is not granted access.
- CORS origins are supplied as a list of exact HTTPS origins; `http://localhost:4200` is always the explicit development origin. An empty production list permits development only. Wildcards, malformed origins, non-HTTPS production origins, credentials, paths, query strings, and fragments make the configuration invalid; startup MUST report the configuration error explicitly and MUST NOT silently discard invalid entries or apply a partial list.
- A request from an unlisted origin may reach the API, but the response has no CORS permission for that origin and browser JavaScript cannot read it. This browser-side CORS/network failure is distinct from an accessible non-2xx HTTP response produced by the API. Fetch may not reveal whether an inaccessible transport error was specifically caused by CORS or by network failure, so the client MUST classify it as a transport error rather than claim a definite CORS cause.

The production origin must be a configuration value (for example a comma-separated environment setting), not a hard-coded wildcard. If no production origin is configured, only the development origin is allowed.

## Public client configuration

The public configuration contains the API base URL only. The API URL is HTTPS for a published client and contains no credentials, token, or trailing `/api`; endpoint paths are appended by the client. The ngrok warning-skip behavior is an ordinary request header, not an auth token. The transport module does not configure or schedule periodic refreshes; its caller initiates each update.

## Query lifecycle and failures

1. Send a request to `/api/eventos` with a 15-second deadline.
2. On successful response, replace the prior current event collection, and record local read time plus API `metadata.generated` and `metadata.last_ingestion` in the state exposed to the consumer.
3. A valid collection with zero Features is a successful empty result, not an error.
4. On timeout or network/CORS transport failure, expose a transport error distinct from empty data and without an HTTP status. On a non-2xx HTTP response, expose an API HTTP error including its status and safe error envelope. If a previous successful result exists, retain it and identify it as the last successful read; expose its `metadata.last_ingestion` alongside the possible-staleness state for the consumer.
5. After a failed request, a later caller-initiated request remains available. If it succeeds, replace the retained data and metadata, clear the previous error and possible-staleness state, and expose the new successful read. Do not retry automatically.
6. Do not infer staleness from a fixed age threshold. An old/null ingestion timestamp alone does not make the API health response unhealthy.
7. When the transport module is disposed, cancel any active request. Any refresh scheduling belongs to its caller, not this module.

The module exposes the latest successful data, read/ingestion timestamps (including the retained response's `metadata.last_ingestion` after a later failure), and current error/staleness state as data for its consumer. It does not render messages, map elements, or other UI.

Visual map, event details, filter controls, tables, charts and historical-analysis presentation are not part of this transport contract; those are subsequent R21–R23 work.
