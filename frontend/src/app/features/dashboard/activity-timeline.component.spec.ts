import { ComponentFixture, TestBed } from "@angular/core/testing";
import { StatisticsResponse } from "../../core/models/api.models";
import { ActivityTimelineComponent } from "./activity-timeline.component";

describe("ActivityTimelineComponent", () => {
  let fixture: ComponentFixture<ActivityTimelineComponent>;

  const statistics: StatisticsResponse = {
    period: { start: "2025-01-01T00:00:00Z", end: "2025-01-02T00:00:00Z" },
    filters: { min_mag: 4, country_id: "ESP" },
    hourly_counts: {
      unit: "events/hour (UTC)",
      missing_count: 1,
      buckets: [
        { start: "2025-01-01T01:00:00Z", count: 2 },
        { start: "2025-01-01T02:00:00Z", count: 0 },
      ],
    },
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

  beforeEach(async () => {
    await TestBed.configureTestingModule({ imports: [ActivityTimelineComponent] }).compileComponents();
    fixture = TestBed.createComponent(ActivityTimelineComponent);
    fixture.componentRef.setInput("statistics", statistics);
  });

  it("renders API hourly values, UTC context, and a textual table alternative", () => {
    fixture.detectChanges();

    const text = fixture.nativeElement.textContent as string;
    expect(text).toContain("2025");
    expect(text).toContain("UTC");
    expect(text).toContain("Magnitud mínima ≥ 4");
    expect(text).toContain("1 sin hora conocida");
    expect(fixture.nativeElement.querySelectorAll("table tbody tr").length).toBe(2);
    expect(text).toContain("01:00");
    expect(text).toContain("2");
  });

  it("treats missing buckets as a valid empty result", () => {
    fixture.componentRef.setInput("statistics", {
      ...statistics,
      hourly_counts: { ...statistics.hourly_counts, buckets: [] },
    });
    fixture.detectChanges();

    expect(fixture.nativeElement.textContent).toContain("No hay intervalos horarios");
    expect(fixture.nativeElement.querySelector("table")).toBeNull();
  });
});
