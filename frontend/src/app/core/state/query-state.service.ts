import { DestroyRef, Injectable, inject, signal } from "@angular/core";
import { EventCollection, EventFilters, HealthResponse, StatisticsResponse } from "../models/api.models";
import { QueryState, ResourceSnapshot } from "../models/ui-state.models";
import { ObservatoryApiService } from "../api/observatory-api.service";

function emptySnapshot<T>(): ResourceSnapshot<T> {
  return {
    status: "idle",
    data: null,
    queryId: 0,
    filters: null,
    period: null,
    readAt: null,
    error: null,
    possiblyStale: false,
    request: null,
  };
}

@Injectable({ providedIn: "root" })
export class QueryStateService {
  private readonly api = inject(ObservatoryApiService);
  private readonly destroyRef = inject(DestroyRef);
  private nextQueryId = 0;
  private debounceTimer: ReturnType<typeof setTimeout> | null = null;
  readonly filters = signal<EventFilters>({});
  readonly state = signal<QueryState>({
    events: emptySnapshot<EventCollection>(),
    statistics: emptySnapshot<StatisticsResponse>(),
    health: emptySnapshot<HealthResponse>(),
  });

  constructor() {
    const refreshTimer = setInterval(() => void this.refresh(), 60_000);
    this.destroyRef.onDestroy(() => {
      clearInterval(refreshTimer);
      if (this.debounceTimer !== null) clearTimeout(this.debounceTimer);
    });
  }

  setFilters(filters: EventFilters): void {
    this.filters.set(filters);
    if (this.debounceTimer !== null) clearTimeout(this.debounceTimer);
    this.debounceTimer = setTimeout(() => {
      this.debounceTimer = null;
      void this.refreshData(false);
    }, 300);
  }

  async refresh(): Promise<void> {
    await this.refreshData(true);
  }

  private async refreshData(includeHealth: boolean): Promise<void> {
    if (this.debounceTimer !== null) {
      clearTimeout(this.debounceTimer);
      this.debounceTimer = null;
    }

    const queryId = ++this.nextQueryId;
    const filters = this.filters();
    const period = filters.start && filters.end
      ? { start: filters.start, end: filters.end }
      : null;
    this.state.update((current) => ({
      ...current,
      events: this.loadingSnapshot(current.events, queryId, filters, period),
      statistics: this.loadingSnapshot(current.statistics, queryId, filters, period),
      ...(includeHealth
        ? {
          health: {
            ...this.loadingSnapshot(current.health, queryId, null, null),
          },
        }
        : {}),
    }));

    const requests = [
      this.loadResource(
        queryId,
        () => this.api.fetchAllEvents(filters),
        (current, data, readAt) => ({
          ...current,
          events: {
            status: "success",
            data,
            queryId,
            filters,
            period,
            readAt,
            error: null,
            possiblyStale: false,
            request: null,
          },
        }),
        (current, error) => ({
          ...current,
          events: this.failedSnapshot(current.events, error),
        }),
      ),
      this.loadResource(
        queryId,
        () => this.api.fetchStatistics(filters),
        (current, data, readAt) => ({
          ...current,
          statistics: {
            status: "success",
            data,
            queryId,
            filters,
            period: data.period,
            readAt,
            error: null,
            possiblyStale: false,
            request: null,
          },
        }),
        (current, error) => ({
          ...current,
          statistics: this.failedSnapshot(current.statistics, error),
        }),
      ),
    ];
    if (includeHealth) {
      requests.push(this.loadResource(
        queryId,
        () => this.api.fetchHealth(),
        (current, data, readAt) => ({
          ...current,
          health: {
            status: "success",
            data,
            queryId,
            filters: null,
            period: null,
            readAt,
            error: null,
            possiblyStale: false,
            request: null,
          },
        }),
        (current, error) => ({
          ...current,
          health: this.failedSnapshot(current.health, error),
        }),
      ));
    }

    await Promise.all(requests);
  }

  private async loadResource<T>(
    queryId: number,
    request: () => Promise<T>,
    onSuccess: (current: QueryState, data: T, readAt: number) => QueryState,
    onError: (current: QueryState, error: ReturnType<ObservatoryApiService["getError"]>) => QueryState,
  ): Promise<void> {
    try {
      const data = await request();
      if (queryId !== this.nextQueryId) return;
      this.state.update((current) => onSuccess(current, data, Date.now()));
    } catch (error) {
      if (queryId !== this.nextQueryId) return;
      const apiError = this.api.getError(error);
      this.state.update((current) => onError(current, apiError));
    }
  }

  private failedSnapshot<T>(
    previous: ResourceSnapshot<T>,
    error: ReturnType<ObservatoryApiService["getError"]>,
  ): ResourceSnapshot<T> {
    return {
      ...previous,
      status: "error",
      error,
      possiblyStale: previous.data !== null,
    };
  }

  setEvents(snapshot: ResourceSnapshot<EventCollection>): void {
    this.state.update((current) => ({ ...current, events: snapshot }));
  }

  setStatistics(snapshot: ResourceSnapshot<StatisticsResponse>): void {
    this.state.update((current) => ({ ...current, statistics: snapshot }));
  }

  setHealth(snapshot: ResourceSnapshot<HealthResponse>): void {
    this.state.update((current) => ({ ...current, health: snapshot }));
  }

  loadingSnapshot<T>(
    previous: ResourceSnapshot<T>,
    queryId: number,
    filters: EventFilters | null,
    period: { start: string; end: string } | null,
  ): ResourceSnapshot<T> {
    return {
      ...previous,
      status: "loading",
      request: { queryId, filters, period },
      error: null,
      possiblyStale: false,
    };
  }
}
