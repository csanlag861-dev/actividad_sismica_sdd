import { ComponentFixture, TestBed } from "@angular/core/testing";
import { StatisticsResponse } from "../../core/models/api.models";
import { StatisticsViewComponent } from "./statistics-view.component";

describe("StatisticsViewComponent", () => {
  let fixture: ComponentFixture<StatisticsViewComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({ imports: [StatisticsViewComponent] }).compileComponents();
    fixture = TestBed.createComponent(StatisticsViewComponent);
  });

  it("shows API periods, units, missing values, and the unassigned-country category", () => {
    const response: StatisticsResponse = {
      period: { start: "2025-01-01T00:00:00Z", end: "2025-01-02T00:00:00Z" },
      filters: { min_mag: 4, country_id: "ESP" },
      hourly_counts: {
        unit: "events/hour (UTC)",
        missing_count: 2,
        buckets: [{ start: "2025-01-01T00:00:00Z", count: 3 }],
      },
      country_counts: {
        unit: "events",
        missing_count: 1,
        buckets: [{ country_id: null, country_name: "Sin país asignado", count: 1 }],
      },
      distributions: {
        magnitude: {
          unit: "magnitude",
          bin_width: 0.5,
          valid_count: 1,
          missing_count: 1,
          buckets: [{ min_inclusive: 1, max_exclusive: 1.5, count: 1, percentage: 100 }],
        },
        depth_km: {
          unit: "km",
          bin_width: 10,
          valid_count: 0,
          missing_count: 2,
          buckets: [],
        },
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
    fixture.componentRef.setInput("statistics", response);
    fixture.detectChanges();

    const text = fixture.nativeElement.textContent as string;
    expect(text).toContain("2025-01-01T00:00:00Z");
    expect(text).toContain("Filtros efectivos para todos los gráficos");
    expect(text).toContain("Magnitud mínima ≥ 4");
    expect(text).toContain("País ESP");
    expect(text).toContain("events/hour (UTC)");
    expect(text).toContain("Sin país asignado");
    expect(text).toContain("2 sin hora");
    expect(text).toContain("1 ausentes");
    expect(text).toContain("No hay profundidades válidas");
  });
});
