import type {
  EventCollection,
  EventFilters,
  HealthResponse,
  StatisticsResponse,
} from "./app/core/models/api.models";

export type ApiResource = "events" | "statistics" | "health";

export interface ApiClientErrorState {
  kind: "http" | "transport";
  message: string;
  status?: number;
}

export interface ApiClientResourceState<T> {
  lastSuccess: { data: T; readAt: string } | null;
  lastAttempt: {
    status: "loading" | "success" | "error";
    startedAt: string;
    finishedAt?: string;
  } | null;
  error: ApiClientErrorState | null;
  possiblyStale: boolean;
}

type ApiResourceData = {
  events: EventCollection;
  statistics: StatisticsResponse;
  health: HealthResponse;
};

export class ApiTransportError extends Error {
  readonly kind: "transport";
  constructor(message: string, options?: ErrorOptions);
}

export class ApiHttpError extends Error {
  readonly kind: "http";
  readonly status: number;
  readonly body: unknown;
  constructor(status: number, body: unknown);
}

export interface ApiClient {
  getState(): ApiClientResourceState<EventCollection>;
  getResourceState<R extends ApiResource>(resource: R): ApiClientResourceState<ApiResourceData[R]>;
  fetchEvents(filters?: EventFilters): Promise<EventCollection>;
  fetchStatistics(filters?: EventFilters): Promise<StatisticsResponse>;
  fetchHealth(): Promise<HealthResponse>;
  dispose(): void;
}

export function createApiClient(options: {
  baseUrl: string;
  fetchImpl?: typeof fetch;
  timeoutMs?: number;
}): ApiClient;

export function loadApiClient(options?: {
  configUrl?: string;
  fetchImpl?: typeof fetch;
  timeoutMs?: number;
}): Promise<ApiClient>;
