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
  metadata: { generated: id, last_ingestion: id + 1 },
  features: [{ type: "Feature", id }],
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
  assert.equal(client.getState().lastSuccess.data.features[0].id, 1);
  assert.equal(client.getState().possiblyStale, true);
  assert.equal(client.getState().lastSuccess.metadata.last_ingestion, 2);

  await client.fetchEvents();
  assert.equal(client.getState().lastSuccess.data.features[0].id, 2);
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
      return new Response(JSON.stringify({ ...collection(1), features: [] }), { status: 200 });
    },
  });

  const result = await client.fetchEvents();

  assert.equal(requestUrl, "https://api.example/api/eventos");
  assert.equal(requestOptions.headers["ngrok-skip-browser-warning"], "true");
  assert.deepEqual(result.features, []);
  client.dispose();
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
