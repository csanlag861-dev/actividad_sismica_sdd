import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

import {
  ApiHttpError,
  ApiTransportError,
  createApiClient,
  loadApiClient,
} from "../src/api-client.mjs";

const collection = (id) => ({
  type: "FeatureCollection",
  metadata: { generated: id, last_ingestion: id + 1, mode: "live", count: 1, truncated: false },
  features: [{
    type: "Feature",
    id: `event-${id}`,
    geometry: { type: "Point", coordinates: [0, 0] },
    properties: {
      mag: null,
      magType: null,
      place: null,
      depth_km: null,
      time: id,
      updated: id,
      country_id: null,
      country_name: null,
    },
  }],
});

test("keeps last successful response after HTTP failure and recovers on next call", async () => {
  const responses = [
    new Response(JSON.stringify(collection(1)), { status: 200 }),
    new Response(JSON.stringify({ error: { code: "invalid_request" } }), { status: 422 }),
    new Response(JSON.stringify(collection(2)), { status: 200 }),
  ];
  const client = createApiClient({
    baseUrl: "https://api.example",
    fetchImpl: async () => responses.shift(),
  });

  await client.fetchEvents();
  await assert.rejects(client.fetchEvents(), ApiHttpError);
  assert.equal(client.getState().lastSuccess.data.features[0].id, "event-1");
  assert.equal(client.getState().possiblyStale, true);
  assert.equal(client.getState().lastSuccess.metadata.last_ingestion, 2);

  await client.fetchEvents();
  assert.equal(client.getState().lastSuccess.data.features[0].id, "event-2");
  assert.equal(client.getState().error, null);
  assert.equal(client.getState().possiblyStale, false);
  client.dispose();
});

test("classifies transport failures separately from API responses", async () => {
  const client = createApiClient({
    baseUrl: "https://api.example",
    fetchImpl: async () => {
      throw new TypeError("fetch failed");
    },
  });

  await assert.rejects(client.fetchEvents(), ApiTransportError);
  assert.equal(client.getState().error.kind, "transport");
  assert.equal(client.getState().error.status, undefined);
  client.dispose();
});

test("turns the request deadline into a timeout transport error", async () => {
  const client = createApiClient({
    baseUrl: "https://api.example",
    timeoutMs: 5,
    fetchImpl: (_url, { signal }) => new Promise((_resolve, reject) => {
      signal.addEventListener("abort", () => reject(new DOMException("Aborted", "AbortError")));
    }),
  });

  await assert.rejects(client.fetchEvents(), (error) => {
    assert.ok(error instanceof ApiTransportError);
    assert.match(error.message, /timed out/);
    return true;
  });
  client.dispose();
});

test("dispose cancels an active request", async () => {
  let observedAbort = false;
  const client = createApiClient({
    baseUrl: "https://api.example",
    fetchImpl: (_url, { signal }) => new Promise((_resolve, reject) => {
      signal.addEventListener("abort", () => {
        observedAbort = true;
        reject(new DOMException("Aborted", "AbortError"));
      });
    }),
  });
  const pendingRequest = client.fetchEvents();
  await new Promise((resolve) => setTimeout(resolve, 0));
  client.dispose();

  await assert.rejects(pendingRequest, ApiTransportError);
  assert.equal(observedAbort, true);
});

test("sends the browser warning header and allows successful empty collections", async () => {
  let requestUrl;
  let requestOptions;
  const client = createApiClient({
    baseUrl: "https://api.example/",
    fetchImpl: async (url, options) => {
      requestUrl = url;
      requestOptions = options;
      return new Response(JSON.stringify({
        ...collection(1),
        metadata: { ...collection(1).metadata, count: 0 },
        features: [],
      }), { status: 200 });
    },
  });

  const result = await client.fetchEvents();

  assert.equal(requestUrl, "https://api.example/api/eventos");
  assert.equal(requestOptions.headers["ngrok-skip-browser-warning"], "true");
  assert.deepEqual(result.features, []);
  client.dispose();
});

test("requests replay explicitly and validates the selected event mode", async () => {
  let requestUrl;
  const client = createApiClient({
    baseUrl: "https://api.example",
    fetchImpl: async (url) => {
      requestUrl = url;
      return new Response(JSON.stringify({
        ...collection(3),
        metadata: { ...collection(3).metadata, mode: "replay" },
      }), { status: 200 });
    },
  });

  const result = await client.fetchEvents(
    { start: "2025-01-01T00:00:00Z", end: "2025-01-02T00:00:00Z" },
    { limit: 100, offset: 0 },
    "replay",
  );

  const request = new URL(requestUrl);
  assert.equal(request.searchParams.get("mode"), "replay");
  assert.equal(request.searchParams.get("start"), "2025-01-01T00:00:00Z");
  assert.equal(request.searchParams.get("limit"), "100");
  assert.equal(result.metadata.mode, "replay");
  await assert.rejects(client.fetchEvents({}, null, "archive"), TypeError);
  client.dispose();
});

test("accepts previous event collections without traceability", async () => {
  const client = createApiClient({
    baseUrl: "https://api.example",
    fetchImpl: async () => new Response(JSON.stringify(collection(7)), { status: 200 }),
  });

  test("serializes validated page options and validates pagination metadata", async () => {
    let requestUrl;
    const page = {
      ...collection(1),
      metadata: {
        ...collection(1).metadata,
        count: 1,
        total_count: 21,
        offset: 20,
        limit: 25,
        truncated: true,
      },
    };
    const client = createApiClient({
      baseUrl: "https://api.example",
      fetchImpl: async (url) => {
        requestUrl = url;
        return new Response(JSON.stringify(page), { status: 200 });
      },
    });

    await client.fetchEvents({ country_id: "ESP" }, { limit: 25, offset: 20 });
    assert.match(requestUrl, /country_id=ESP/);
    assert.match(requestUrl, /limit=25/);
    assert.match(requestUrl, /offset=20/);
    await assert.rejects(client.fetchEvents({}, { limit: 24 }), TypeError);
    await assert.rejects(client.fetchEvents({}, { offset: -1 }), TypeError);
    client.dispose();
  });

  const result = await client.fetchEvents();

  assert.equal(Object.hasOwn(result.features[0].properties, "traceability"), false);
  assert.equal(result.features[0].id, "event-7");
  client.dispose();
});

test("validates present event traceability without weakening existing fields", async () => {
  const traceability = {
    mode: "live",
    source: "usgs-live",
    ingested_at: 1_760_000_000_000,
    ingestion_run_id: "02dfad0c-2c13-431c-95fb-4bdb4d253e23",
  };
  const client = createApiClient({
    baseUrl: "https://api.example",
    fetchImpl: async () => new Response(JSON.stringify({
      ...collection(8),
      features: [{
        ...collection(8).features[0],
        properties: { ...collection(8).features[0].properties, traceability },
      }],
    }), { status: 200 }),
  });

  const result = await client.fetchEvents();
  assert.deepEqual(result.features[0].properties.traceability, traceability);
  client.dispose();

  for (const invalidTraceability of [
    { ...traceability, mode: "unknown" },
    { ...traceability, source: "unrecognized-source" },
    { ...traceability, ingestion_run_id: "not-a-uuid" },
  ]) {
    const malformedClient = createApiClient({
      baseUrl: "https://api.example",
      fetchImpl: async () => new Response(JSON.stringify({
        ...collection(9),
        features: [{
          ...collection(9).features[0],
          properties: {
            ...collection(9).features[0].properties,
            traceability: invalidTraceability,
          },
        }],
      }), { status: 200 }),
    });

    await assert.rejects(malformedClient.fetchEvents(), ApiTransportError);
    malformedClient.dispose();
  }

  const nullableClient = createApiClient({
    baseUrl: "https://api.example",
    fetchImpl: async () => new Response(JSON.stringify({
      ...collection(10),
      features: [{
        ...collection(10).features[0],
        properties: {
          ...collection(10).features[0].properties,
          traceability: {
            mode: "replay",
            source: null,
            ingested_at: null,
            ingestion_run_id: null,
          },
        },
      }],
    }), { status: 200 }),
  });
  const nullableResult = await nullableClient.fetchEvents();
  assert.equal(nullableResult.features[0].properties.traceability.source, null);
  assert.equal(nullableResult.features[0].properties.traceability.ingested_at, null);
  nullableClient.dispose();
});

test("sends only contract filters to statistics and accepts health 503 as unavailable data", async () => {
  const requested = [];
  const statistics = {
    period: { start: "2025-01-01T00:00:00Z", end: "2025-01-02T00:00:00Z" },
    filters: { min_mag: 4, country_id: "ESP" },
    hourly_counts: { unit: "events/hour (UTC)", missing_count: 0, buckets: [] },
    country_counts: { unit: "events", missing_count: 0, buckets: [] },
    distributions: {
      magnitude: { unit: "magnitude", bin_width: 0.5, valid_count: 0, missing_count: 0, buckets: [] },
      depth_km: { unit: "km", bin_width: 10, valid_count: 0, missing_count: 0, buckets: [] },
    },
    historical_comparison: {
      baseline_period: { start: "2025-01-01T00:00:00Z", end: "2026-01-01T00:00:00Z" },
      baseline_days: 365,
      baseline_available: false,
      current_count: 0,
      current_period_days: 1,
      current_daily_average: 0,
      historical_daily_average: null,
      unit: "events/day",
    },
  };
  const client = createApiClient({
    baseUrl: "https://api.example",
    fetchImpl: async (url) => {
      requested.push(url);
      if (url.startsWith("https://api.example/api/estadisticas")) {
        return new Response(JSON.stringify(statistics), { status: 200 });
      }
      return new Response(JSON.stringify({ status: "unavailable", last_ingestion: null }), { status: 503 });
    },
  });

  await client.fetchStatistics({
    start: "2025-01-01T00:00:00Z",
    end: "2025-01-02T00:00:00Z",
    min_mag: 4,
    country_id: "ESP",
  });
  const health = await client.fetchHealth();

  assert.equal(
    requested[0],
    "https://api.example/api/estadisticas?start=2025-01-01T00%3A00%3A00Z&end=2025-01-02T00%3A00%3A00Z&min_mag=4&country_id=ESP",
  );
  assert.deepEqual(health, { status: "unavailable", last_ingestion: null });
  assert.equal(client.getResourceState("health").error, null);
  client.dispose();
});

test("posts validated temporal comparison requests and validates responses", async () => {
  let requestUrl;
  let requestOptions;
  const response = {
    mode: "live",
    filters: { min_mag: null },
    groups: ["first", "second"].map((id) => ({
      id,
      label: id,
      period: { start: "2025-01-01T00:00:00Z", end: "2025-01-02T00:00:00Z" },
      population: { type: "all", country_id: null, country_name: "Todos" },
      coverage: { status: "unknown", covered_days: 0, period_days: 1 },
      observed_count: 0,
      unavailable_metrics: {
        daily_rate: "coverage_unknown",
        magnitude: "coverage_unknown",
        depth_km: "coverage_unknown",
      },
      daily_rate: null,
      distributions: { magnitude: null, depth_km: null },
    })),
    pairwise_differences: [{
      first_group_id: "first",
      second_group_id: "second",
      observed_count_difference: null,
      daily_rate_difference: null,
      unavailable_reasons: { daily_rate_difference: "coverage_unknown" },
      distribution_percentage_point_differences: { magnitude: null, depth_km: null },
    }],
  };
  const request = {
    mode: "live",
    filters: { min_mag: null },
    groups: ["first", "second"].map((id) => ({
      id,
      label: id,
      period: { start: "2025-01-01T00:00:00Z", end: "2025-01-02T00:00:00Z" },
      population: { type: "all" },
    })),
  };
  const client = createApiClient({
    baseUrl: "https://api.example",
    fetchImpl: async (url, options) => {
      requestUrl = url;
      requestOptions = options;
      return new Response(JSON.stringify(response), { status: 200 });
    },
  });

  assert.deepEqual(await client.fetchComparison(request), response);
  assert.equal(requestUrl, "https://api.example/api/comparaciones");
  assert.equal(requestOptions.method, "POST");
  assert.equal(requestOptions.headers["Content-Type"], "application/json");
  assert.deepEqual(JSON.parse(requestOptions.body), request);
  await assert.rejects(client.fetchComparison({ ...request, groups: [] }), TypeError);
  client.dispose();

  const invalidResponseClient = createApiClient({
    baseUrl: "https://api.example",
    fetchImpl: async () => new Response(JSON.stringify({ ...response, groups: [] }), { status: 200 }),
  });
  await assert.rejects(invalidResponseClient.fetchComparison(request), ApiTransportError);
  invalidResponseClient.dispose();
});

test("loads the public config and uses its API base URL without exposing secrets", async () => {
  const configResponse = await readFile(new URL("../public/config.json", import.meta.url), "utf8");
  const publicConfig = JSON.parse(configResponse);
  assert.deepEqual(Object.keys(publicConfig), ["apiBaseUrl"]);
  assert.equal(new URL(publicConfig.apiBaseUrl).username, "");
  assert.equal(new URL(publicConfig.apiBaseUrl).password, "");

  for (const apiBaseUrl of ["https://first.example", "https://second.example"]) {
    const requested = [];
    const client = await loadApiClient({
      fetchImpl: async (url) => {
        requested.push(url);
        if (url === "/config.json") {
          return new Response(JSON.stringify({ apiBaseUrl }), { status: 200 });
        }
        return new Response(JSON.stringify(collection(1)), { status: 200 });
      },
    });

    await client.fetchEvents();
    assert.deepEqual(requested, ["/config.json", `${apiBaseUrl}/api/eventos`]);
    client.dispose();
  }
});

test("rejects public configuration containing credentials or extra values", async () => {
  const clientPromise = loadApiClient({
    fetchImpl: async () => new Response(
      JSON.stringify({ apiBaseUrl: "https://api.example", token: "secret" }),
      { status: 200 },
    ),
  });

  await assert.rejects(clientPromise, TypeError);
});
