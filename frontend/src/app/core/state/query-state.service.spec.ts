import { fakeAsync, flushMicrotasks, TestBed, tick } from "@angular/core/testing";
import { EventCollection, HealthResponse, StatisticsResponse } from "../models/api.models";
import { ObservatoryApiService } from "../api/observatory-api.service";
import { QueryStateService } from "./query-state.service";

function events(id: string): EventCollection {
  return {
    type: "FeatureCollection",
    metadata: { generated: 1, last_ingestion: null, mode: "live", count: 1, truncated: false },
    features: [{
      type: "Feature",
      id,
      geometry: { type: "Point", coordinates: [0, 0] },
      properties: {
        mag: 1,
        magType: null,
        place: null,
        depth_km: null,
        time: 1,
        updated: 1,
        country_id: null,
        country_name: null,
      },
    }],
  };
}

function statistics(): StatisticsResponse {
  return {
    period: { start: "2025-01-01T00:00:00Z", end: "2025-01-02T00:00:00Z" },
    filters: { min_mag: null, country_id: null },
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
}

function health(): HealthResponse {
  return { status: "ok", last_ingestion: null };
}

describe("QueryStateService", () => {
  let service: QueryStateService;
  let api: jasmine.SpyObj<ObservatoryApiService>;

  beforeEach(() => {
    api = jasmine.createSpyObj<ObservatoryApiService>(
      "ObservatoryApiService",
      ["fetchEvents", "fetchStatistics", "fetchHealth", "getError"],
    );
    api.fetchEvents.and.resolveTo(events("event"));
    api.fetchStatistics.and.resolveTo(statistics());
    api.fetchHealth.and.resolveTo(health());
    api.getError.and.callFake((error: unknown) => ({
      kind: "http",
      message: error instanceof Error ? error.message : "Error HTTP",
      status: 503,
    }));

    TestBed.configureTestingModule({
      providers: [
        QueryStateService,
        { provide: ObservatoryApiService, useValue: api },
      ],
    });
    service = TestBed.inject(QueryStateService);
  });

  it("uses the same default filters and updates each resource independently", async () => {
    await service.refresh();

    expect(api.fetchEvents).toHaveBeenCalledOnceWith({});
    expect(api.fetchStatistics).toHaveBeenCalledOnceWith({});
    expect(api.fetchHealth).toHaveBeenCalledTimes(1);
    expect(service.state().events.status).toBe("success");
    expect(service.state().events.period).toBeNull();
    expect(service.state().statistics.period).toEqual(statistics().period);
    expect(service.state().health.data?.status).toBe("ok");
  });

  it("keeps each endpoint's effective period attributed to its own response", async () => {
    const eventPeriod = {
      start: "2025-02-01T00:00:00.000Z",
      end: "2025-02-02T00:00:00.000Z",
    };
    service.filters.set(eventPeriod);
    await service.refresh();

    expect(service.state().events.period).toEqual(eventPeriod);
    expect(service.state().statistics.period).toEqual(statistics().period);
  });

  it("discards responses from an older query and preserves the newest result", async () => {
    let resolveOld!: (value: EventCollection) => void;
    const oldResponse = new Promise<EventCollection>((resolve) => {
      resolveOld = resolve;
    });
    api.fetchEvents.and.returnValues(oldResponse, Promise.resolve(events("new")));

    const firstQuery = service.refresh();
    service.filters.set({ min_mag: 4 });
    const secondQuery = service.refresh();
    await secondQuery;
    resolveOld(events("old"));
    await firstQuery;

    expect(service.state().events.data?.features[0].id).toBe("new");
  });

  it("retains a successful snapshot after a partial refresh failure", async () => {
    api.fetchEvents.and.returnValues(
      Promise.resolve(events("last-good")),
      Promise.reject(new Error("backend unavailable")),
      Promise.resolve(events("recovered")),
    );
    await service.refresh();
    await service.refresh();

    expect(service.state().events.status).toBe("error");
    expect(service.state().events.error?.kind).toBe("http");
    expect(service.state().events.data?.features[0].id).toBe("last-good");
    expect(service.state().events.possiblyStale).toBeTrue();
    expect(service.state().statistics.status).toBe("success");
    expect(service.state().health.status).toBe("success");

    await service.refresh();
    expect(service.state().events.status).toBe("success");
    expect(service.state().events.data?.features[0].id).toBe("recovered");
    expect(service.state().events.error).toBeNull();
    expect(service.state().events.possiblyStale).toBeFalse();
  });

  it("preserves the successful query context while a newer query loads and fails", async () => {
    let rejectNewRequest!: (reason: Error) => void;
    const newRequest = new Promise<EventCollection>((_resolve, reject) => {
      rejectNewRequest = reject;
    });
    api.fetchEvents.and.returnValues(Promise.resolve(events("last-good")), newRequest);
    service.filters.set({
      start: "2025-01-01T00:00:00.000Z",
      end: "2025-01-02T00:00:00.000Z",
      min_mag: 2,
    });
    await service.refresh();
    const previous = service.state().events;

    const nextFilters = {
      start: "2025-02-01T00:00:00.000Z",
      end: "2025-02-02T00:00:00.000Z",
      min_mag: 4,
      country_id: "ESP",
    };
    service.filters.set(nextFilters);
    const nextRefresh = service.refresh();
    const loading = service.state().events;

    expect(loading.status).toBe("loading");
    expect(loading.data).toBe(previous.data);
    expect(loading.queryId).toBe(previous.queryId);
    expect(loading.filters).toEqual(previous.filters);
    expect(loading.period).toEqual(previous.period);
    expect(loading.readAt).toBe(previous.readAt);
    expect(loading.request?.queryId).toBeGreaterThan(previous.queryId);
    expect(loading.request?.filters).toEqual(nextFilters);

    rejectNewRequest(new Error("backend unavailable"));
    await nextRefresh;
    const failed = service.state().events;

    expect(failed.status).toBe("error");
    expect(failed.data).toBe(previous.data);
    expect(failed.queryId).toBe(previous.queryId);
    expect(failed.filters).toEqual(previous.filters);
    expect(failed.period).toEqual(previous.period);
    expect(failed.readAt).toBe(previous.readAt);
    expect(failed.request?.filters).toEqual(nextFilters);
    expect(failed.possiblyStale).toBeTrue();
  });

  it("debounces filter updates before refreshing the shared query", fakeAsync(() => {
    service.setFilters({ min_mag: 3.5 });
    tick(299);
    expect(api.fetchEvents).not.toHaveBeenCalled();
    tick(1);
    flushMicrotasks();

    expect(api.fetchEvents).toHaveBeenCalledOnceWith({ min_mag: 3.5 });
    expect(api.fetchStatistics).toHaveBeenCalledOnceWith({ min_mag: 3.5 });
    expect(api.fetchHealth).not.toHaveBeenCalled();
  }));

  it("schedules coordinated refreshes at 60-second intervals", () => {
    const intervalSpy = spyOn(window, "setInterval").and.callThrough();
    TestBed.resetTestingModule();
    TestBed.configureTestingModule({
      providers: [
        QueryStateService,
        { provide: ObservatoryApiService, useValue: api },
      ],
    });
    TestBed.inject(QueryStateService);

    expect(intervalSpy).toHaveBeenCalledWith(jasmine.any(Function), 60_000);
  });
});
