import { ComponentFixture, TestBed } from "@angular/core/testing";
import { EventFeature } from "../../core/models/api.models";
import { EventDetailComponent } from "./event-detail.component";

describe("EventDetailComponent", () => {
  let fixture: ComponentFixture<EventDetailComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({ imports: [EventDetailComponent] }).compileComponents();
    fixture = TestBed.createComponent(EventDetailComponent);
  });

  it("shows event properties, units, and explicit unknown values", () => {
    const event: EventFeature = {
      type: "Feature",
      id: "event-42",
      geometry: { type: "Point", coordinates: [-3.7, 40.4, 12] },
      properties: {
        mag: 3.2,
        magType: "ml",
        place: null,
        depth_km: null,
        time: Date.UTC(2025, 0, 1),
        updated: Date.UTC(2025, 0, 1),
        country_id: null,
        country_name: null,
        traceability: {
          mode: "live",
          source: "usgs-live",
          ingested_at: Date.UTC(2025, 0, 2),
          ingestion_run_id: "02dfad0c-2c13-431c-95fb-4bdb4d253e23",
        },
      },
    };
    fixture.componentRef.setInput("event", event);
    fixture.detectChanges();

    const text = fixture.nativeElement.textContent as string;
    expect(text).toContain("Ubicación desconocida");
    expect(text).toContain("3.2");
    expect(text).toContain("ml");
    expect(text).toContain("Desconocida");
    expect(text).toContain("40.4000° lat, -3.7000° lon");
    expect(text).toContain("PaísDesconocido");
    expect(text).toContain("event-42");
    expect(text).toContain("Trazabilidad");
    expect(text).toContain("Tiempo real");
    expect(text).toContain("usgs-live");
    expect(text).toContain("02dfad0c-2c13-431c-95fb-4bdb4d253e23");
  });

  it("labels absent traceability as unavailable without inferring values", () => {
    const event: EventFeature = {
      type: "Feature",
      id: "legacy-event",
      geometry: { type: "Point", coordinates: [0, 0] },
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
    };
    fixture.componentRef.setInput("event", event);
    fixture.detectChanges();

    expect(fixture.nativeElement.textContent).toContain("No disponible");
  });
});
