import { ComponentFixture, TestBed } from "@angular/core/testing";
import { StatisticsResponse } from "../../core/models/api.models";
import { HistoricalComparisonComponent } from "./historical-comparison.component";

function comparison(baselineAvailable: boolean, historicalAverage: number | null): StatisticsResponse {
  return {
    period: { start: "2026-01-01T00:00:00Z", end: "2026-01-02T00:00:00Z" },
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
      baseline_available: baselineAvailable,
      current_count: 0,
      current_period_days: 1,
      current_daily_average: 0,
      historical_daily_average: historicalAverage,
      unit: "events/day",
    },
  };
}

describe("HistoricalComparisonComponent", () => {
  let fixture: ComponentFixture<HistoricalComparisonComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({ imports: [HistoricalComparisonComponent] }).compileComponents();
    fixture = TestBed.createComponent(HistoricalComparisonComponent);
  });

  it("keeps unavailable baseline distinct from a zero rate", () => {
    fixture.componentRef.setInput("statistics", comparison(false, null));
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain("Cobertura no disponible");
    expect(fixture.nativeElement.textContent).not.toContain("0 events/day");
  });

  it("shows a real zero baseline without inventing difference or ratio fields", () => {
    fixture.componentRef.setInput("statistics", comparison(true, 0));
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain("La tasa histórica es cero");
    expect(fixture.nativeElement.textContent).not.toContain("Diferencia de tasa");
    expect(fixture.nativeElement.textContent).not.toContain("Cociente de tasas");
  });

  it("shows only the difference and ratio fields provided by the API", () => {
    const response = comparison(true, 2);
    response.historical_comparison.daily_rate_difference = 3;
    response.historical_comparison.daily_rate_ratio = 2.5;
    fixture.componentRef.setInput("statistics", response);
    fixture.detectChanges();

    expect(fixture.nativeElement.textContent).toContain("Diferencia de tasa (API)");
    expect(fixture.nativeElement.textContent).toContain("3 events/day");
    expect(fixture.nativeElement.textContent).toContain("2,5×");
  });
});
