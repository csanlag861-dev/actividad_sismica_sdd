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

function serializeFilters(filters = {}) {
  const allowed = new Set(["start", "end", "min_mag", "country_id"]);
  const entries = Object.entries(filters).filter(([, value]) => value !== undefined);
  for (const [key] of entries) {
    if (!allowed.has(key)) {
      throw new TypeError(`Unsupported API filter: ${key}`);
    }
  }

  const values = Object.fromEntries(entries);
  if ((values.start === undefined) !== (values.end === undefined)) {
    throw new TypeError("Custom event filters must include both start and end");
  }
  if (values.start !== undefined && (
    typeof values.start !== "string"
    || typeof values.end !== "string"
    || !Number.isFinite(Date.parse(values.start))
    || !Number.isFinite(Date.parse(values.end))
    || Date.parse(values.start) >= Date.parse(values.end)
  )) {
    throw new TypeError("Event filter period must have valid start < end");
  }
  if (values.min_mag !== undefined && (
    typeof values.min_mag !== "number" || !Number.isFinite(values.min_mag)
  )) {
    throw new TypeError("Minimum magnitude must be a finite number");
  }
  if (values.country_id !== undefined && (
    typeof values.country_id !== "string" || !/^[A-Z0-9]{3}$/.test(values.country_id)
  )) {
    throw new TypeError("Country filter must be a three-character catalog identifier");
  }

  const params = new URLSearchParams();
  for (const [key, value] of entries) {
    params.set(key, String(value));
  }
  return params.size > 0 ? `?${params}` : "";
}

function isRecord(value) {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isFiniteOrNull(value) {
  return value === null || (typeof value === "number" && Number.isFinite(value));
}

function isPeriod(value) {
  return isRecord(value)
    && typeof value.start === "string"
    && typeof value.end === "string"
    && Number.isFinite(Date.parse(value.start))
    && Number.isFinite(Date.parse(value.end))
    && Date.parse(value.start) < Date.parse(value.end);
}

function isEventTraceability(value) {
  return isRecord(value)
    && ["live", "replay"].includes(value.mode)
    && (value.source === null || ["usgs-live", "usgs-replay"].includes(value.source))
    && isFiniteOrNull(value.ingested_at)
    && (value.ingestion_run_id === null
      || (typeof value.ingestion_run_id === "string"
        && /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(value.ingestion_run_id)));
}

function isEventCollection(data) {
  return isRecord(data)
    && data.type === "FeatureCollection"
    && isRecord(data.metadata)
    && Number.isFinite(data.metadata.generated)
    && isFiniteOrNull(data.metadata.last_ingestion)
    && typeof data.metadata.mode === "string"
    && Number.isInteger(data.metadata.count)
    && data.metadata.count >= 0
    && typeof data.metadata.truncated === "boolean"
    && Array.isArray(data.features)
    && data.features.every((feature) => isRecord(feature)
      && feature.type === "Feature"
      && typeof feature.id === "string"
      && isRecord(feature.geometry)
      && feature.geometry.type === "Point"
      && Array.isArray(feature.geometry.coordinates)
      && [2, 3].includes(feature.geometry.coordinates.length)
      && feature.geometry.coordinates.every(Number.isFinite)
      && isRecord(feature.properties)
      && isFiniteOrNull(feature.properties.mag)
      && (feature.properties.magType === null || typeof feature.properties.magType === "string")
      && (feature.properties.place === null || typeof feature.properties.place === "string")
      && isFiniteOrNull(feature.properties.depth_km)
      && Number.isFinite(feature.properties.time)
      && Number.isFinite(feature.properties.updated)
      && (feature.properties.country_id === null || typeof feature.properties.country_id === "string")
      && (feature.properties.country_name === null || typeof feature.properties.country_name === "string")
      && (feature.properties.traceability === undefined
        || isEventTraceability(feature.properties.traceability)));
}

function isDistribution(value) {
  return isRecord(value)
    && typeof value.unit === "string"
    && Number.isFinite(value.bin_width)
    && value.bin_width > 0
    && Number.isInteger(value.valid_count)
    && value.valid_count >= 0
    && Number.isInteger(value.missing_count)
    && value.missing_count >= 0
    && Array.isArray(value.buckets)
    && value.buckets.every((bucket) => isRecord(bucket)
      && Number.isFinite(bucket.min_inclusive)
      && Number.isFinite(bucket.max_exclusive)
      && bucket.min_inclusive < bucket.max_exclusive
      && Number.isInteger(bucket.count)
      && bucket.count >= 0
      && isFiniteOrNull(bucket.percentage));
}

function isStatisticsResponse(data) {
  if (!isRecord(data)
    || !isPeriod(data.period)
    || !isRecord(data.filters)
    || !(data.filters.min_mag === null || Number.isFinite(data.filters.min_mag))
    || !(data.filters.country_id === null || typeof data.filters.country_id === "string")
    || !isRecord(data.hourly_counts)
    || typeof data.hourly_counts.unit !== "string"
    || !Number.isInteger(data.hourly_counts.missing_count)
    || !Array.isArray(data.hourly_counts.buckets)
    || !data.hourly_counts.buckets.every((bucket) => isRecord(bucket)
      && typeof bucket.start === "string"
      && Number.isFinite(Date.parse(bucket.start))
      && Number.isInteger(bucket.count)
      && bucket.count >= 0)
    || !isRecord(data.country_counts)
    || typeof data.country_counts.unit !== "string"
    || !Number.isInteger(data.country_counts.missing_count)
    || !Array.isArray(data.country_counts.buckets)
    || !data.country_counts.buckets.every((bucket) => isRecord(bucket)
      && (bucket.country_id === null || typeof bucket.country_id === "string")
      && typeof bucket.country_name === "string"
      && Number.isInteger(bucket.count)
      && bucket.count >= 0)
    || !isRecord(data.distributions)
    || !isDistribution(data.distributions.magnitude)
    || !isDistribution(data.distributions.depth_km)
    || !isRecord(data.historical_comparison)) {
    return false;
  }

  const comparison = data.historical_comparison;
  return isPeriod(comparison.baseline_period)
    && Number.isFinite(comparison.baseline_days)
    && comparison.baseline_days > 0
    && typeof comparison.baseline_available === "boolean"
    && Number.isInteger(comparison.current_count)
    && comparison.current_count >= 0
    && Number.isFinite(comparison.current_period_days)
    && comparison.current_period_days > 0
    && Number.isFinite(comparison.current_daily_average)
    && isFiniteOrNull(comparison.historical_daily_average)
    && typeof comparison.unit === "string"
    && (comparison.daily_rate_difference === undefined || Number.isFinite(comparison.daily_rate_difference))
    && (comparison.daily_rate_ratio === undefined || Number.isFinite(comparison.daily_rate_ratio));
}

function isHealthResponse(data) {
  return isRecord(data)
    && ["ok", "unavailable"].includes(data.status)
    && isFiniteOrNull(data.last_ingestion);
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
  const resourceStates = {
    events: state,
    statistics: { lastSuccess: null, lastAttempt: null, error: null, possiblyStale: false },
    health: { lastSuccess: null, lastAttempt: null, error: null, possiblyStale: false },
  };

  const updateState = (changes) => {
    state = { ...state, ...changes };
    resourceStates.events = state;
  };

  const requestResource = async (resource, path, validator, filters = {}) => {
    if (disposed) {
      throw new ApiTransportError("API client has been disposed");
    }
    const resourceState = resourceStates[resource];
    const controller = new AbortController();
    activeControllers.add(controller);
    let timedOut = false;
    const startedAt = new Date().toISOString();
    resourceStates[resource] = {
      ...resourceState,
      lastAttempt: { status: "loading", startedAt },
      error: null,
    };
    const timeout = setTimeout(() => {
      timedOut = true;
      controller.abort();
    }, timeoutMs);

    try {
      const query = resource === "health" ? "" : serializeFilters(filters);
      const endpointUrl = `${baseUrl.replace(/\/+$/, "")}${path}${query}`;
      const response = await fetchImpl(endpointUrl, {
        method: "GET",
        headers: {
          Accept: "application/json",
          "ngrok-skip-browser-warning": "true",
        },
        credentials: "omit",
        signal: controller.signal,
      });

      let data;
      if (resource === "health" && response.status === 503) {
        data = await response.json();
        if (data?.status !== "unavailable") {
          throw new ApiTransportError("API returned an invalid health response");
        }
      } else {
        if (!response.ok) {
          let body = null;
          try {
            body = await response.json();
          } catch (error) {
            if (!(error instanceof SyntaxError)) {
              throw new ApiTransportError("Could not read the API error response", { cause: error });
            }
          }
          throw new ApiHttpError(response.status, body);
        }
        data = await response.json();
      }

      if (!validator(data)) {
        throw new ApiTransportError(`API returned an invalid ${resource} response`);
      }
      const readAt = new Date().toISOString();
      resourceStates[resource] = {
        lastSuccess: { data, readAt },
        lastAttempt: { status: "success", startedAt, finishedAt: readAt },
        error: null,
        possiblyStale: false,
      };
      return data;
    } catch (error) {
      const normalizedError = error instanceof ApiHttpError || error instanceof ApiTransportError
        ? error
        : new ApiTransportError(
          timedOut ? "API request timed out" : "API transport failed",
          { cause: error },
        );
      if (timedOut) normalizedError.message = "API request timed out";
      if (!disposed) {
        const current = resourceStates[resource];
        resourceStates[resource] = {
          ...current,
          lastAttempt: {
            status: "error",
            startedAt,
            finishedAt: new Date().toISOString(),
          },
          error: {
            kind: normalizedError.kind,
            message: normalizedError.message,
            ...(normalizedError instanceof ApiHttpError ? { status: normalizedError.status } : {}),
          },
          possiblyStale: current.lastSuccess !== null,
        };
      }
      throw normalizedError;
    } finally {
      clearTimeout(timeout);
      activeControllers.delete(controller);
    }
  };

  return {
    getState() {
      return { ...state };
    },

    getResourceState(resource) {
      if (!(resource in resourceStates)) {
        throw new TypeError(`Unknown API resource: ${resource}`);
      }
      return { ...resourceStates[resource] };
    },

    async fetchEvents(filters = {}) {
      if (disposed) {
        throw new ApiTransportError("API client has been disposed");
      }
      const query = serializeFilters(filters);
      const requestEndpoint = `${endpoint}${query}`;

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
        const response = await fetchImpl(requestEndpoint, {
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
        if (!isEventCollection(data)) {
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

    fetchStatistics(filters = {}) {
      return requestResource(
        "statistics",
        "/api/estadisticas",
        isStatisticsResponse,
        filters,
      );
    },

    fetchHealth() {
      return requestResource(
        "health",
        "/api/salud",
        isHealthResponse,
      );
    },

    dispose() {
      if (disposed) return;
      disposed = true;
      for (const controller of activeControllers) controller.abort();
      activeControllers.clear();
    },
  };
}
