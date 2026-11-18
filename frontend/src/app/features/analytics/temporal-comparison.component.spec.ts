import { signal } from "@angular/core";
import { ComponentFixture, TestBed } from "@angular/core/testing";
import {
  TemporalComparisonRequest,
  TemporalComparisonResponse,
} from "../../core/models/api.models";
import { ObservatoryApiService } from "../../core/api/observatory-api.service";
import { CountryCatalogService } from "../events/country-catalog.service";
import { TemporalComparisonComponent } from "./temporal-comparison.component";

describe("TemporalComparisonComponent", () => {
  let fixture: ComponentFixture<TemporalComparisonComponent>;
  let api: jasmine.SpyObj<ObservatoryApiService>;
  let countries: jasmine.SpyObj<CountryCatalogService>;

  const response: TemporalComparisonResponse = {
    mode: "live",
    filters: { min_mag: null },
    groups: ["grupo-1", "grupo-2"].map((id) => ({
      id,
      label: id,
      period: { start: "2025-01-01T00:00:00Z", end: "2025-01-02T00:00:00Z" },
      population: { type: "all", country_id: null, country_name: "Todos" },
      coverage: { status: "unknown", covered_days: 0, period_days: 1 },
      observed_count: 0,
      unavailable_metrics: {
        daily_rate: "coverage_unknown",
        magnitude: "coverage_unknown",
        depth_km: "coverage_unknown",
      },
      daily_rate: null,
      distributions: { magnitude: null, depth_km: null },
    })),
    pairwise_differences: [{
      first_group_id: "grupo-1",
      second_group_id: "grupo-2",
      observed_count_difference: null,
      daily_rate_difference: null,
      unavailable_reasons: { daily_rate_difference: "coverage_unknown" },
      distribution_percentage_point_differences: { magnitude: null, depth_km: null },
    }],
  };

  beforeEach(async () => {
    api = jasmine.createSpyObj<ObservatoryApiService>(
      "ObservatoryApiService",
      ["fetchComparison", "getError"],
    );
    api.fetchComparison.and.resolveTo(response);
    api.getError.and.callFake((error: unknown) => ({
      kind: "http",
      message: error instanceof Error ? error.message : "Error HTTP",
      status: 503,
    }));
    countries = jasmine.createSpyObj<CountryCatalogService>("CountryCatalogService", ["load"]);
    Object.defineProperty(countries, "countries", { value: signal([]) });
    countries.load.and.resolveTo();

    await TestBed.configureTestingModule({
      imports: [TemporalComparisonComponent],
      providers: [
        { provide: ObservatoryApiService, useValue: api },
        { provide: CountryCatalogService, useValue: countries },
      ],
    }).compileComponents();
    fixture = TestBed.createComponent(TemporalComparisonComponent);
    fixture.detectChanges();
    await fixture.whenStable();
  });

  it("submits two UTC periods and displays unavailable metrics explicitly", async () => {
    const component = fixture.componentInstance;
    await component.compare();
    fixture.detectChanges();

    const request = api.fetchComparison.calls.mostRecent().args[0] as TemporalComparisonRequest;
    expect(request.groups.length).toBe(2);
    expect(request.groups[0].period.start.endsWith("Z")).toBeTrue();
    expect(fixture.nativeElement.textContent).toContain("coverage_unknown");
    expect(fixture.nativeElement.textContent).toContain("Diferencias por pares");
  });

  it("enforces group bounds and rejects duplicate identifiers before sending", async () => {
    const component = fixture.componentInstance;
    component.groups[1].id = component.groups[0].id;
    await component.compare();

    expect(api.fetchComparison).not.toHaveBeenCalled();
    expect(component.errorMessage).toContain("debe ser único");

    component.groups[1].id = "grupo-2";
    component.addGroup();
    component.addGroup();
    component.addGroup();
    expect(component.groups.length).toBe(5);
    component.addGroup();
    expect(component.groups.length).toBe(5);
    component.removeGroup(0);
    component.removeGroup(0);
    component.removeGroup(0);
    component.removeGroup(0);
    expect(component.groups.length).toBe(2);
  });
});
