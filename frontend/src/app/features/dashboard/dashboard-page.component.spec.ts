import { signal } from "@angular/core";
import { ComponentFixture, TestBed } from "@angular/core/testing";
import { By } from "@angular/platform-browser";
import { provideRouter } from "@angular/router";
import { EventCollection, EventFeature, StatisticsResponse } from "../../core/models/api.models";
import { ObservatoryApiService } from "../../core/api/observatory-api.service";
import { QueryStateService } from "../../core/state/query-state.service";
import { QueryState } from "../../core/models/ui-state.models";
import { EventMapComponent } from "../../shared/map/event-map.component";
import { DashboardPageComponent } from "./dashboard-page.component";

describe("DashboardPageComponent", () => {
  let fixture: ComponentFixture<DashboardPageComponent>;
  let queryState: ReturnType<typeof createQueryState>;
  let eventApi: jasmine.SpyObj<ObservatoryApiService>;

  function makeEvent(
    id: string,
    coordinates: EventFeature["geometry"]["coordinates"],
    place: string | null = id,
  ): EventFeature {
    return {
      type: "Feature",
      id,
      geometry: { type: "Point", coordinates },
      properties: {
        mag: 3.2,
        magType: "ml",
        place,
        depth_km: 12,
        time: Date.UTC(2025, 0, 1),
        updated: Date.UTC(2025, 0, 1),
        country_id: null,
        country_name: null,
      },
    };
  }

  function makeStatistics(): StatisticsResponse {
    return {
      period: { start: "2025-01-01T00:00:00Z", end: "2025-01-02T00:00:00Z" },
      filters: { min_mag: null, country_id: null },
      hourly_counts: {
        unit: "events/hour (UTC)",
        missing_count: 0,
        buckets: [{ start: "2025-01-01T01:00:00Z", count: 2 }],
      },
      country_counts: { unit: "events", missing_count: 0, buckets: [] },
      distributions: {
        magnitude: {
          unit: "magnitude",
          bin_width: 0.5,
          valid_count: 1,
          missing_count: 0,
          buckets: [{ min_inclusive: 3, max_exclusive: 3.5, count: 1, percentage: 100 }],
        },
        depth_km: {
          unit: "km",
          bin_width: 10,
          valid_count: 1,
          missing_count: 0,
          buckets: [{ min_inclusive: 10, max_exclusive: 20, count: 1, percentage: 100 }],
        },
      },
      historical_comparison: {
        baseline_period: { start: "2025-01-01T00:00:00Z", end: "2026-01-01T00:00:00Z" },
        baseline_days: 365,
        baseline_available: false,
        current_count: 1,
        current_period_days: 1,
        current_daily_average: 1,
        historical_daily_average: null,
        unit: "events/day",
      },
    };
  }

  function createQueryState() {
    return {
      state: signal<QueryState>({
        events: {
          status: "success",
          data: {
            type: "FeatureCollection",
            metadata: { generated: 1, last_ingestion: 1, mode: "live", count: 1, truncated: false },
            features: [],
          },
          queryId: 1,
          filters: {},
          period: null,
          readAt: 1,
          error: null,
          possiblyStale: false,
          request: null,
        },
        statistics: {
          status: "success",
          data: makeStatistics(),
          queryId: 1,
          filters: {},
          period: makeStatistics().period,
          readAt: 1,
          error: null,
          possiblyStale: false,
          request: null,
        },
        health: {
          status: "success",
          data: { status: "ok", last_ingestion: null },
          queryId: 1,
          filters: null,
          period: null,
          readAt: 1,
          error: null,
          possiblyStale: false,
          request: null,
        },
      }),
      refresh: jasmine.createSpy("refresh").and.resolveTo(undefined),
    };
  }

  beforeEach(async () => {
    queryState = createQueryState();
    eventApi = jasmine.createSpyObj<ObservatoryApiService>("ObservatoryApiService", ["fetchEvents", "getError"]);
    eventApi.fetchEvents.and.callFake(async () => {
      const collection = queryState.state().events.data!;
      return {
        ...collection,
        features: [...new Map(collection.features.map((event) => [event.id, event])).values()],
      };
    });
    eventApi.getError.and.callFake((error: unknown) => ({
      kind: "http",
      message: error instanceof Error ? error.message : "Error HTTP",
      status: 503,
    }));
    await TestBed.configureTestingModule({
      imports: [DashboardPageComponent],
      providers: [
        provideRouter([]),
        { provide: QueryStateService, useValue: queryState },
        { provide: ObservatoryApiService, useValue: eventApi },
      ],
    }).compileComponents();
    fixture = TestBed.createComponent(DashboardPageComponent);
  });

  it("shows a healthy API state and a period backed by the default API query", () => {
    fixture.detectChanges();
    const text = fixture.nativeElement.textContent as string;
    expect(text).toContain("Servicio disponible");
    expect(text).toContain("Últimas 24 horas");
    expect(text).toContain("0 eventos");
  });

  it("reports unavailable health and API failures without substituting healthy data", () => {
    queryState.state.update((current) => ({
      ...current,
      health: {
        ...current.health,
        data: { status: "unavailable", last_ingestion: null },
      },
      events: {
        ...current.events,
        status: "error",
        data: null,
        error: { kind: "http", message: "Servicio no disponible", status: 503 },
      },
    }));
    fixture.detectChanges();
    const text = fixture.nativeElement.textContent as string;
    expect(text).toContain("Servicio no disponible");
    expect(text).toContain("No se pudieron cargar los eventos");
    expect(text).not.toContain("Servicio disponible");
  });

  it("maps each unique valid event once and keeps the accessible event table selectable", async () => {
    const first = makeEvent("event-1", [1, 2]);
    const duplicate = makeEvent("event-1", [3, 4], "Duplicate");
    const invalid = makeEvent("invalid-coordinate", [1, 91]);
    queryState.state.update((current) => ({
      ...current,
      events: {
        ...current.events,
        data: {
          ...current.events.data!,
          metadata: { ...current.events.data!.metadata, count: 3 },
          features: [first, duplicate, invalid],
        },
      },
    }));

    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();

    const map = fixture.debugElement.query(By.directive(EventMapComponent))
      .componentInstance as EventMapComponent;
    expect(map.events?.features.map((event) => event.id)).toEqual(["event-1"]);
    const eventRows = fixture.nativeElement.querySelectorAll("app-events-table tbody tr");
    expect(eventRows.length).toBe(2);
    const selectButton = fixture.nativeElement.querySelector("app-events-table tbody button") as HTMLButtonElement;
    selectButton.click();
    fixture.detectChanges();
    expect((fixture.nativeElement.textContent as string)).toContain("Identificador de origen");
    expect((fixture.nativeElement.textContent as string)).toContain("event-1");
  });

  it("announces truncated event collections and keeps statistics context independent", () => {
    queryState.state.update((current) => ({
      ...current,
      events: {
        ...current.events,
        data: {
          ...current.events.data!,
          metadata: { ...current.events.data!.metadata, truncated: true },
        },
      },
      statistics: {
        ...current.statistics,
        data: {
          ...makeStatistics(),
          period: { start: "2025-02-01T00:00:00Z", end: "2025-02-02T00:00:00Z" },
        },
      },
    }));

    fixture.detectChanges();
    const text = fixture.nativeElement.textContent as string;
    expect(text).toContain("La respuesta está truncada");
    expect(text).toContain("Periodo de eventos");
    expect(text).toContain("Periodo estadístico");
    expect(text).toContain("2025");
  });
});
