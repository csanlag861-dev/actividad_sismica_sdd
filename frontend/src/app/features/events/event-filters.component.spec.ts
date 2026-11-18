import { signal } from "@angular/core";
import { TestBed } from "@angular/core/testing";
import { CountryCatalogService } from "./country-catalog.service";
import { EventFiltersComponent } from "./event-filters.component";
import { QueryStateService } from "../../core/state/query-state.service";
import { EventFilters } from "../../core/models/api.models";

describe("EventFiltersComponent", () => {
  let fixture: ReturnType<typeof TestBed.createComponent<EventFiltersComponent>>;
  let setFilters: jasmine.Spy;
  let sharedFilters: ReturnType<typeof signal<EventFilters>>;

  beforeEach(async () => {
    setFilters = jasmine.createSpy("setFilters");
    sharedFilters = signal<EventFilters>({});
    await TestBed.configureTestingModule({
      imports: [EventFiltersComponent],
      providers: [
        { provide: QueryStateService, useValue: { setFilters, filters: sharedFilters, state: signal({}) } },
        {
          provide: CountryCatalogService,
          useValue: { countries: signal([{ id: "ESP", name: "España" }]), load: jasmine.createSpy("load").and.resolveTo(undefined) },
        },
      ],
    }).compileComponents();
    fixture = TestBed.createComponent(EventFiltersComponent);
    fixture.detectChanges();
  });

  it("sends the shared UTC period and only contract-supported filters", () => {
    const component = fixture.componentInstance;
    component.startValue = "2025-01-01T00:00";
    component.endValue = "2025-01-02T00:00";
    component.countryId = "ESP";
    const magnitudeInput = fixture.nativeElement.querySelector('input[name="minMagnitude"]') as HTMLInputElement | null;
    if (!magnitudeInput) throw new Error("Magnitude input was not rendered.");
    magnitudeInput.value = "4.5";
    magnitudeInput.dispatchEvent(new Event("input"));
    fixture.detectChanges();

    component.apply();

    expect(setFilters).toHaveBeenCalledOnceWith({
      start: "2025-01-01T00:00:00.000Z",
      end: "2025-01-02T00:00:00.000Z",
      min_mag: 4.5,
      country_id: "ESP",
    });
  });

  it("does not submit an incomplete or reversed period", () => {
    const component = fixture.componentInstance;
    component.startValue = "2025-01-02T00:00";
    component.endValue = "2025-01-01T00:00";

    component.apply();

    expect(setFilters).not.toHaveBeenCalled();
    expect(component.filterError).toContain("inicio anterior al fin");
  });

  it("leaves start/end absent for the API's default mobile period", () => {
    fixture.componentInstance.clear();
    expect(setFilters).toHaveBeenCalledOnceWith({});
  });

  it("hydrates filter controls from shared state when entering and returning to a route", () => {
    sharedFilters.set({
      start: "2025-01-01T00:00:00.000Z",
      end: "2025-01-02T00:00:00.000Z",
      min_mag: 4.5,
      country_id: "ESP",
    });
    fixture.destroy();
    fixture = TestBed.createComponent(EventFiltersComponent);
    fixture.detectChanges();

    expect(fixture.componentInstance.startValue).toBe("2025-01-01T00:00");
    expect(fixture.componentInstance.endValue).toBe("2025-01-02T00:00");
    expect(fixture.componentInstance.minMagnitude).toBe(4.5);
    expect(fixture.componentInstance.countryId).toBe("ESP");
  });
});
