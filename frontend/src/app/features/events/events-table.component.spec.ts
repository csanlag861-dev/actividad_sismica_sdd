import { ComponentFixture, TestBed } from "@angular/core/testing";
import { EventCollection } from "../../core/models/api.models";
import { EventsTableComponent } from "./events-table.component";

describe("EventsTableComponent", () => {
  let fixture: ComponentFixture<EventsTableComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({ imports: [EventsTableComponent] }).compileComponents();
    fixture = TestBed.createComponent(EventsTableComponent);
  });

  it("renders API values and emits the same event id for selection", () => {
    const collection: EventCollection = {
      type: "FeatureCollection",
      metadata: { generated: 1, last_ingestion: null, mode: "live", count: 1, truncated: false },
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
    fixture.componentRef.setInput("events", collection);
    fixture.detectChanges();
    const selected = jasmine.createSpy("selected");
    fixture.componentInstance.eventSelected.subscribe(selected);
    (fixture.nativeElement.querySelector("tbody button") as HTMLButtonElement).click();

    expect(fixture.nativeElement.textContent).toContain("Desconocido");
    expect(fixture.nativeElement.textContent).toContain("Magnitud");
    expect(selected).toHaveBeenCalledOnceWith("event-42");
  });

  it("distinguishes a successful empty collection from missing data", () => {
    fixture.componentRef.setInput("events", {
      type: "FeatureCollection",
      metadata: { generated: 1, last_ingestion: null, mode: "live", count: 0, truncated: false },
      features: [],
    });
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain("no devolvió eventos");
  });

  it("announces truncated collections as limited samples", () => {
    fixture.componentRef.setInput("events", {
      type: "FeatureCollection",
      metadata: { generated: 1, last_ingestion: null, mode: "live", count: 8, truncated: true },
      features: [],
    });
    fixture.detectChanges();

    expect(fixture.nativeElement.textContent).toContain("no representa un total global");
  });
});
