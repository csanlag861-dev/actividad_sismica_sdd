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

function serializeFilters(filters = {}, page = null) {
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
  if (page !== null) {
    const limit = page.limit ?? 25;
    const offset = page.offset ?? 0;
    if (![25, 50, 100].includes(limit)) {
      throw new TypeError("Event page size must be 25, 50, or 100");
    }
    if (!Number.isSafeInteger(offset) || offset < 0) {
      throw new TypeError("Event page offset must be a non-negative integer");
    }
    params.set("limit", String(limit));
    params.set("offset", String(offset));
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
  const metadata = isRecord(data) && isRecord(data.metadata) ? data.metadata : {};
  const pageMetadataValid = !(
    "total_count" in metadata
    || "offset" in metadata
    || "limit" in metadata
  ) || (
    Number.isInteger(metadata.total_count)
    && metadata.total_count >= metadata.count
    && Number.isInteger(metadata.offset)
    && metadata.offset >= 0
    && [25, 50, 100].includes(metadata.limit)
    && metadata.count <= metadata.limit
  );
  return isRecord(data)
    && data.type === "FeatureCollection"
    && isRecord(data.metadata)
    && Number.isFinite(data.metadata.generated)
    && isFiniteOrNull(data.metadata.last_ingestion)
    && typeof data.metadata.mode === "string"
    && Number.isInteger(data.metadata.count)
    && data.metadata.count >= 0
    && typeof data.metadata.truncated === "boolean"
    && pageMetadataValid
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

function isStringRecord(value) {
  return isRecord(value)
    && Object.values(value).every((item) => typeof item === "string");
}

function isComparisonPopulation(value) {
  if (!isRecord(value) || typeof value.type !== "string") return false;
  if (value.type === "all" || value.type === "unassigned") {
    return Object.keys(value).length === 1;
  }
  return value.type === "country"
    && Object.keys(value).length === 2
    && typeof value.country_id === "string"
    && /^[A-Z]{3}$/.test(value.country_id);
}

function isComparisonRequest(value) {
  if (!isRecord(value)
    || !["live", "replay"].includes(value.mode)
    || !Array.isArray(value.groups)
    || value.groups.length < 2
    || value.groups.length > 5) {
    return false;
  }
  if (Object.keys(value).some((key) => !["mode", "filters", "groups"].includes(key))) return false;
  const filters = value.filters ?? {};
  if (!isRecord(filters)
    || Object.keys(filters).some((key) => key !== "min_mag")
    || !(filters.min_mag === undefined || isFiniteOrNull(filters.min_mag))) {
    return false;
  }
  const ids = new Set();
  const labels = new Set();
  return value.groups.every((group) => {
    if (!isRecord(group)
      || Object.keys(group).some((key) => !["id", "label", "period", "population"].includes(key))
      || typeof group.id !== "string"
      || !group.id.trim()
      || typeof group.label !== "string"
      || !group.label.trim()
      || ids.has(group.id)
      || labels.has(group.label)
      || !isPeriod(group.period)
      || !isComparisonPopulation(group.population)) {
      return false;
    }
    ids.add(group.id);
    labels.add(group.label);
    return true;
  });
}

function isComparisonGroupResult(value) {
  return isRecord(value)
    && typeof value.id === "string"
    && typeof value.label === "string"
    && isPeriod(value.period)
    && isRecord(value.population)
    && ["all", "country", "unassigned"].includes(value.population.type)
    && (value.population.country_id === null || typeof value.population.country_id === "string")
    && (value.population.country_name === null || typeof value.population.country_name === "string")
    && isRecord(value.coverage)
    && ["complete", "partial", "unknown"].includes(value.coverage.status)
    && Number.isFinite(value.coverage.covered_days)
    && value.coverage.covered_days >= 0
    && Number.isFinite(value.coverage.period_days)
    && value.coverage.period_days > 0
    && Number.isInteger(value.observed_count)
    && value.observed_count >= 0
    && isStringRecord(value.unavailable_metrics)
    && isFiniteOrNull(value.daily_rate)
    && isRecord(value.distributions)
    && (value.distributions.magnitude === null || isDistribution(value.distributions.magnitude))
    && (value.distributions.depth_km === null || isDistribution(value.distributions.depth_km));
}

function isPairwiseComparison(value) {
  return isRecord(value)
    && typeof value.first_group_id === "string"
    && typeof value.second_group_id === "string"
    && isFiniteOrNull(value.observed_count_difference)
    && isFiniteOrNull(value.daily_rate_difference)
    && isStringRecord(value.unavailable_reasons)
    && isRecord(value.distribution_percentage_point_differences)
    && ["magnitude", "depth_km"].every((metric) => {
      const differences = value.distribution_percentage_point_differences[metric];
      return differences === null || (
        Array.isArray(differences)
        && differences.every((difference) => isRecord(difference)
          && Number.isFinite(difference.min_inclusive)
          && Number.isFinite(difference.max_exclusive)
          && difference.min_inclusive < difference.max_exclusive
          && Number.isFinite(difference.difference))
      );
    });
}

function isTemporalComparisonResponse(data) {
  return isRecord(data)
    && ["live", "replay"].includes(data.mode)
    && isRecord(data.filters)
    && isFiniteOrNull(data.filters.min_mag)
    && Array.isArray(data.groups)
    && data.groups.length >= 2
    && data.groups.length <= 5
    && data.groups.every(isComparisonGroupResult)
    && Array.isArray(data.pairwise_differences)
    && data.pairwise_differences.every(isPairwiseComparison);
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
    comparison: { lastSuccess: null, lastAttempt: null, error: null, possiblyStale: false },
  };

  const updateState = (changes) => {
    state = { ...state, ...changes };
    resourceStates.events = state;
  };

  const requestResource = async (
    resource,
    path,
    validator,
    filters = {},
    { method = "GET", body } = {},
  ) => {
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
      const query = method !== "GET" || resource === "health" ? "" : serializeFilters(filters);
      const endpointUrl = `${baseUrl.replace(/\/+$/, "")}${path}${query}`;
      const response = await fetchImpl(endpointUrl, {
        method,
        headers: {
          Accept: "application/json",
          "ngrok-skip-browser-warning": "true",
          ...(body === undefined ? {} : { "Content-Type": "application/json" }),
        },
        credentials: "omit",
        signal: controller.signal,
        ...(body === undefined ? {} : { body: JSON.stringify(body) }),
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

    async fetchEvents(filters = {}, page = null) {
      if (disposed) {
        throw new ApiTransportError("API client has been disposed");
      }
      const query = serializeFilters(filters, page);
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

    async fetchComparison(request) {
      if (!isComparisonRequest(request)) {
        throw new TypeError("Temporal comparison request is invalid");
      }
      return requestResource(
        "comparison",
        "/api/comparaciones",
        isTemporalComparisonResponse,
        {},
        { method: "POST", body: request },
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
