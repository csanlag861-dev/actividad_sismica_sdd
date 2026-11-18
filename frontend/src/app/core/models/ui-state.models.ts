import { EventFilters, EventCollection, HealthResponse, StatisticsResponse } from "./api.models";

export type ResourceStatus = "idle" | "loading" | "success" | "error";
export type ResourceKind = "http" | "transport";

export interface ResourceError {
  kind: ResourceKind;
  message: string;
  status?: number;
}

export interface QueryContext {
  queryId: number;
  filters: EventFilters | null;
  period: { start: string; end: string } | null;
}

export interface ResourceSnapshot<T> {
  status: ResourceStatus;
  data: T | null;
  queryId: number;
  filters: EventFilters | null;
  period: { start: string; end: string } | null;
  readAt: number | null;
  error: ResourceError | null;
  possiblyStale: boolean;
  request: QueryContext | null;
}

export interface QueryState {
  events: ResourceSnapshot<EventCollection>;
  statistics: ResourceSnapshot<StatisticsResponse>;
  health: ResourceSnapshot<HealthResponse>;
}

export type SeismicTheme = "dark" | "light";
