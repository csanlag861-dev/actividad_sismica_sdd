export class ApiTransportError extends Error {
  constructor(message, options = {}) {
    super(message, options);
    this.name = "ApiTransportError";
    this.kind = "transport";
  }
}

export class ApiHttpError extends Error {
  constructor(status, body) {
    super(body?.error?.message || `API request failed with HTTP ${status}`);
    this.name = "ApiHttpError";
    this.kind = "http";
    this.status = status;
    this.body = body;
  }
}

export async function loadApiClient({
  configUrl = "/config.json",
  fetchImpl = globalThis.fetch,
  timeoutMs = 15_000,
} = {}) {
  if (typeof fetchImpl !== "function") {
    throw new TypeError("A Fetch implementation is required");
  }

  let response;
  try {
    response = await fetchImpl(configUrl, {
      method: "GET",
      headers: { Accept: "application/json" },
      credentials: "omit",
    });
  } catch (error) {
    throw new ApiTransportError("Could not load public API configuration", { cause: error });
  }
  if (!response.ok) {
    throw new ApiTransportError(
      `Could not load public API configuration (HTTP ${response.status})`,
    );
  }

  let config;
  try {
    config = await response.json();
  } catch (error) {
    throw new ApiTransportError("Public API configuration is not valid JSON", { cause: error });
  }
  if (
    config === null
    || typeof config !== "object"
    || Array.isArray(config)
    || Object.keys(config).length !== 1
    || !Object.hasOwn(config, "apiBaseUrl")
  ) {
    throw new TypeError("Public API configuration must contain only apiBaseUrl");
  }

  return createApiClient({
    baseUrl: config.apiBaseUrl,
    fetchImpl,
    timeoutMs,
  });
}

export function createApiClient({
  baseUrl,
  fetchImpl = globalThis.fetch,
  timeoutMs = 15_000,
} = {}) {
  if (typeof baseUrl !== "string" || !baseUrl.trim()) {
    throw new TypeError("An API base URL is required");
  }
  if (typeof fetchImpl !== "function") {
    throw new TypeError("A Fetch implementation is required");
  }

  const parsedBaseUrl = new URL(baseUrl);
  if (
    !["https:", "http:"].includes(parsedBaseUrl.protocol)
    || (parsedBaseUrl.protocol === "http:"
      && !["localhost", "127.0.0.1", "::1"].includes(parsedBaseUrl.hostname))
    || parsedBaseUrl.username
    || parsedBaseUrl.password
    || parsedBaseUrl.search
    || parsedBaseUrl.hash
    || parsedBaseUrl.pathname.replace(/\/+$/, "").endsWith("/api")
  ) {
    throw new TypeError("The API base URL must be an origin or path without credentials or /api");
  }
  if (!Number.isFinite(timeoutMs) || timeoutMs <= 0) {
    throw new TypeError("The API timeout must be a positive finite number");
  }

  const endpoint = `${baseUrl.replace(/\/+$/, "")}/api/eventos`;
  const activeControllers = new Set();
  let disposed = false;
  let state = {
    lastSuccess: null,
    lastAttempt: null,
    error: null,
    possiblyStale: false,
  };

  const updateState = (changes) => {
    state = { ...state, ...changes };
  };

  return {
    getState() {
      return { ...state };
    },

    async fetchEvents() {
      if (disposed) {
        throw new ApiTransportError("API client has been disposed");
      }

      const controller = new AbortController();
      activeControllers.add(controller);
      let timedOut = false;
      const startedAt = new Date().toISOString();
      updateState({
        lastAttempt: { status: "loading", startedAt },
        error: null,
      });
      const timeout = setTimeout(() => {
        timedOut = true;
        controller.abort();
      }, timeoutMs);

      try {
        const response = await fetchImpl(endpoint, {
          method: "GET",
          headers: {
            Accept: "application/json",
            "ngrok-skip-browser-warning": "true",
          },
          credentials: "omit",
          signal: controller.signal,
        });

        if (!response.ok) {
          let body = null;
          try {
            body = await response.json();
          } catch (error) {
            if (!(error instanceof SyntaxError)) {
              throw new ApiTransportError("Could not read the API error response", { cause: error });
            }
            body = null;
          }
          throw new ApiHttpError(response.status, body);
        }

        const data = await response.json();
        if (data?.type !== "FeatureCollection" || !Array.isArray(data.features)) {
          throw new ApiTransportError("API returned an invalid event collection");
        }
        const readAt = new Date().toISOString();
        const lastSuccess = {
          data,
          readAt,
          metadata: {
            generated: data.metadata?.generated ?? null,
            last_ingestion: data.metadata?.last_ingestion ?? null,
          },
        };
        updateState({
          lastSuccess,
          lastAttempt: { status: "success", startedAt, finishedAt: readAt },
          error: null,
          possiblyStale: false,
        });
        return data;
      } catch (error) {
        const normalizedError = error instanceof ApiHttpError || error instanceof ApiTransportError
          ? error
          : new ApiTransportError(
            timedOut ? "API request timed out" : "API transport failed",
            { cause: error },
          );
        if (timedOut) {
          normalizedError.message = "API request timed out";
        }
        if (!disposed) {
          const failedAt = new Date().toISOString();
          updateState({
            lastAttempt: { status: "error", startedAt, finishedAt: failedAt },
            error: {
              kind: normalizedError.kind,
              message: normalizedError.message,
              ...(normalizedError instanceof ApiHttpError ? { status: normalizedError.status } : {}),
            },
            possiblyStale: state.lastSuccess !== null,
          });
        }
        throw normalizedError;
      } finally {
        clearTimeout(timeout);
        activeControllers.delete(controller);
      }
    },

    dispose() {
      if (disposed) return;
      disposed = true;
      for (const controller of activeControllers) controller.abort();
      activeControllers.clear();
    },
  };
}
