import { ComponentFixture, TestBed } from "@angular/core/testing";
import { EventCollection } from "../../core/models/api.models";
import { ObservatoryApiService } from "../../core/api/observatory-api.service";
import { EventsTableComponent } from "./events-table.component";

describe("EventsTableComponent", () => {
  let fixture: ComponentFixture<EventsTableComponent>;
  let api: jasmine.SpyObj<ObservatoryApiService>;
  let collection: EventCollection;

  beforeEach(async () => {
    collection = {
      type: "FeatureCollection",
      metadata: {
        generated: 1,
        last_ingestion: null,
        mode: "live",
        count: 1,
        total_count: 1,
        offset: 0,
        limit: 25,
        truncated: false,
      },
      features: [{
        type: "Feature",
        id: "event-42",
        geometry: { type: "Point", coordinates: [-3.7, 40.4] },
        properties: {
          mag: null,
          magType: null,
          place: null,
          depth_km: null,
          time: Date.UTC(2025, 0, 1),
          updated: Date.UTC(2025, 0, 1),
          country_id: null,
          country_name: null,
        },
      }],
    };
    api = jasmine.createSpyObj<ObservatoryApiService>("ObservatoryApiService", ["fetchEvents", "getError"]);
    api.fetchEvents.and.resolveTo(collection);
    api.getError.and.callFake((error: unknown) => ({
      kind: "http",
      message: error instanceof Error ? error.message : "Error HTTP",
      status: 503,
    }));
    await TestBed.configureTestingModule({
      imports: [EventsTableComponent],
      providers: [{ provide: ObservatoryApiService, useValue: api }],
    }).compileComponents();
    fixture = TestBed.createComponent(EventsTableComponent);
  });

  it("loads the requested page, renders API values, and emits the selected event", async () => {
    fixture.componentRef.setInput("filters", {});
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();
    const selected = jasmine.createSpy("selected");
    fixture.componentInstance.eventSelected.subscribe(selected);
    (fixture.nativeElement.querySelector("tbody button") as HTMLButtonElement).click();

    expect(fixture.nativeElement.textContent).toContain("Desconocido");
    expect(fixture.nativeElement.textContent).toContain("Magnitud");
    expect(api.fetchEvents).toHaveBeenCalledOnceWith({}, { limit: 25, offset: 0 });
    expect(selected).toHaveBeenCalledOnceWith(collection.features[0]);
  });

  it("distinguishes a successful empty collection from missing data", async () => {
    api.fetchEvents.and.resolveTo({
      type: "FeatureCollection",
      metadata: { generated: 1, last_ingestion: null, mode: "live", count: 0, total_count: 0, truncated: false },
      features: [],
    });
    fixture.componentRef.setInput("filters", {});
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain("no devolvió eventos");
  });

  it("requests subsequent pages and changes the page size", async () => {
    fixture.componentRef.setInput("filters", {});
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();
    collection.metadata.total_count = 51;
    api.fetchEvents.and.resolveTo(collection);

    fixture.componentInstance.nextPage();
    await fixture.whenStable();
    expect(api.fetchEvents).toHaveBeenCalledWith({}, { limit: 25, offset: 25 });

    fixture.componentInstance.changePageSize("50");
    await fixture.whenStable();
    expect(api.fetchEvents).toHaveBeenCalledWith({}, { limit: 50, offset: 0 });
  });
});
