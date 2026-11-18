import { signal } from "@angular/core";
import { ComponentFixture, TestBed } from "@angular/core/testing";
import { provideRouter } from "@angular/router";
import type { Viewer } from "cesium";
import { EventCollection, EventFeature } from "../../core/models/api.models";
import { ObservatoryApiService } from "../../core/api/observatory-api.service";
import { QueryStateService } from "../../core/state/query-state.service";
import { CountryCatalogService } from "../events/country-catalog.service";
import { Globe3DViewerService } from "./globe-3d-viewer.service";
import { Globe3DPageComponent } from "./globe-3d-page.component";

describe("Globe3DPageComponent", () => {
  let fixture: ComponentFixture<Globe3DPageComponent>;
  let api: jasmine.SpyObj<ObservatoryApiService>;
  let globe: jasmine.SpyObj<Globe3DViewerService>;
  let fromDegrees: jasmine.Spy;
  let viewer: {
    camera: { setView: jasmine.Spy };
    entities: { add: jasmine.Spy; removeAll: jasmine.Spy };
    scene: { renderError: { addEventListener: jasmine.Spy } };
    selectedEntityChanged: { addEventListener: jasmine.Spy };
    selectedEntity: object | null;
    destroy: jasmine.Spy;
    isDestroyed: jasmine.Spy;
  };
  let event: EventFeature;

  function collection(features: EventFeature[]): EventCollection {
    return {
      type: "FeatureCollection",
      metadata: {
        generated: 1,
        last_ingestion: null,
        mode: "live",
        count: features.length,
        total_count: features.length,
        offset: 0,
        limit: 100,
        truncated: false,
      },
      features,
    };
  }

  beforeEach(async () => {
    event = {
      type: "Feature",
      id: "unknown-depth",
      geometry: { type: "Point", coordinates: [10, 20] },
      properties: {
        mag: 2,
        magType: null,
        place: "Unknown depth event",
        depth_km: null,
        time: 1,
        updated: 1,
        country_id: null,
        country_name: null,
      },
    };
    const invalid = {
      ...event,
      id: "invalid-coordinate",
      geometry: { type: "Point" as const, coordinates: [181, 20] as [number, number] },
    };
    api = jasmine.createSpyObj<ObservatoryApiService>(
      "ObservatoryApiService",
      ["fetchEvents", "fetchAllEvents", "getError"],
    );
    api.fetchAllEvents.and.resolveTo(collection([event, invalid]));
    api.getError.and.callFake((error: unknown) => ({
      kind: "http",
      message: error instanceof Error ? error.message : "Error HTTP",
      status: 503,
    }));

    viewer = {
      camera: { setView: jasmine.createSpy("setView") },
      entities: {
        add: jasmine.createSpy("add").and.callFake((options: { id: string }) => ({ id: options.id })),
        removeAll: jasmine.createSpy("removeAll"),
      },
      scene: { renderError: { addEventListener: jasmine.createSpy("renderError") } },
      selectedEntityChanged: { addEventListener: jasmine.createSpy("selectedEntityChanged") },
      selectedEntity: null,
      destroy: jasmine.createSpy("destroy"),
      isDestroyed: jasmine.createSpy("isDestroyed").and.returnValue(false),
    };
    globe = jasmine.createSpyObj<Globe3DViewerService>(
      "Globe3DViewerService",
      ["createViewer", "destroy"],
    );
    globe.createViewer.and.resolveTo(viewer as unknown as Viewer);
    fromDegrees = jasmine.createSpy("fromDegrees").and.returnValue("surface-position");
    const cesium = {
      Cartesian3: { fromDegrees },
      Cartesian2: class { constructor(readonly x: number, readonly y: number) {} },
      Color: {
        fromCssColorString: jasmine.createSpy("fromCssColorString").and.returnValue("color"),
        WHITE: "white",
      },
      HeightReference: { CLAMP_TO_GROUND: "clamp" },
    };
    Object.defineProperty(globe, "library", { value: cesium });

    await TestBed.configureTestingModule({
      imports: [Globe3DPageComponent],
      providers: [
        provideRouter([]),
        { provide: ObservatoryApiService, useValue: api },
        { provide: QueryStateService, useValue: { filters: signal({}), setFilters: jasmine.createSpy() } },
        {
          provide: CountryCatalogService,
          useValue: { countries: signal([]), load: jasmine.createSpy().and.resolveTo() },
        },
        { provide: Globe3DViewerService, useValue: globe },
      ],
    }).compileComponents();
    fixture = TestBed.createComponent(Globe3DPageComponent);
  });

  it("renders valid locations on the surface and keeps unknown depth unset", async () => {
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();

    expect(api.fetchAllEvents).toHaveBeenCalledWith({});
    expect(viewer.entities.add).toHaveBeenCalledOnceWith(jasmine.objectContaining({
      id: "unknown-depth",
      position: "surface-position",
      point: jasmine.objectContaining({ pixelSize: 8 }),
    }));
    expect(fromDegrees).toHaveBeenCalledOnceWith(10, 20);
    expect(fixture.componentInstance.invalidLocationCount).toBe(1);
    expect(fixture.nativeElement.textContent).toContain("1 de 2 eventos consultados se excluyeron");
    fixture.componentInstance.selectEvent("unknown-depth");
    fixture.detectChanges();
    expect(fixture.componentInstance.selectedEvent?.properties.depth_km).toBeNull();
    expect(viewer.selectedEntity).toEqual({ id: "unknown-depth" });
    expect(fixture.nativeElement.textContent).toContain("Desconocida");
  });

  it("shows a fallback after initialization failure, retries, and destroys on teardown", async () => {
    globe.createViewer.and.rejectWith(new Error("WebGL unavailable"));
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain("WebGL unavailable");
    expect(fixture.nativeElement.querySelector('a[href="/eventos"]')).toBeTruthy();

    globe.createViewer.and.resolveTo(viewer as unknown as Viewer);
    await fixture.componentInstance.retry();
    expect(globe.createViewer).toHaveBeenCalledTimes(2);
    fixture.destroy();
    expect(globe.destroy).toHaveBeenCalled();
  });

  it("marks the last successful event response as possibly stale after a refresh fails", async () => {
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();
    api.fetchAllEvents.and.rejectWith(new Error("API unavailable"));

    await fixture.componentInstance.retry();
    fixture.detectChanges();

    expect(fixture.componentInstance.events?.features[0].id).toBe("unknown-depth");
    expect(fixture.nativeElement.textContent).toContain("los eventos mostrados pueden estar desactualizados");
  });
});
