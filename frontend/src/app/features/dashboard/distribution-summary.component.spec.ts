import { ComponentFixture, TestBed } from "@angular/core/testing";
import { StatisticsResponse } from "../../core/models/api.models";
import { DistributionSummaryComponent } from "./distribution-summary.component";

describe("DistributionSummaryComponent", () => {
  let fixture: ComponentFixture<DistributionSummaryComponent>;

  const statistics: StatisticsResponse = {
    period: { start: "2025-01-01T00:00:00Z", end: "2025-01-02T00:00:00Z" },
    filters: { min_mag: null, country_id: null },
    hourly_counts: { unit: "events/hour (UTC)", missing_count: 0, buckets: [] },
    country_counts: { unit: "events", missing_count: 0, buckets: [] },
    distributions: {
      magnitude: {
        unit: "magnitude",
        bin_width: 0.5,
        valid_count: 2,
        missing_count: 1,
        buckets: [
          { min_inclusive: 3, max_exclusive: 3.5, count: 1, percentage: 50 },
          { min_inclusive: 3.5, max_exclusive: 4, count: 1, percentage: null },
        ],
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

  beforeEach(async () => {
    await TestBed.configureTestingModule({ imports: [DistributionSummaryComponent] }).compileComponents();
    fixture = TestBed.createComponent(DistributionSummaryComponent);
    fixture.componentRef.setInput("statistics", statistics);
    fixture.detectChanges();
  });

  it("shows API-provided units, counts, bins, percentages, and missing values", () => {
    const text = fixture.nativeElement.textContent as string;
    expect(text).toContain("magnitude");
    expect(text).toContain("km");
    expect(text).toContain("2 válidos");
    expect(text).toContain("1 ausentes");
    expect(text).toContain("[3, 3.5)");
    expect(text).toContain("50%");
    expect(text).toContain("No disponible");
    expect(text).toContain("No hay valores de profundidad válidos");
  });

  it("does not fabricate bins or percentages for an empty distribution", () => {
    fixture.componentRef.setInput("statistics", {
      ...statistics,
      distributions: {
        ...statistics.distributions,
        magnitude: { ...statistics.distributions.magnitude, valid_count: 0, buckets: [] },
      },
    });
    fixture.detectChanges();

    expect(fixture.nativeElement.textContent).toContain("No hay valores de magnitud válidos");
    expect(fixture.nativeElement.querySelectorAll("table tbody tr").length).toBe(0);
  });
});
