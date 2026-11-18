import { ComponentFixture, TestBed } from "@angular/core/testing";
import type { Map as MapLibreMap } from "maplibre-gl";
import { EventCollection, EventFeature } from "../../core/models/api.models";
import { MapLayersService } from "./map-layers.service";
import { EventMapComponent } from "./event-map.component";

describe("EventMapComponent", () => {
  let fixture: ComponentFixture<EventMapComponent>;
  let mapLayers: jasmine.SpyObj<MapLayersService>;

  function makeEvent(id: string, time: number): EventFeature {
    return {
      type: "Feature",
      id,
      geometry: { type: "Point", coordinates: [10, 20, 15] },
      properties: {
        mag: 3,
        magType: "ml",
        place: id,
        depth_km: 15,
        time,
        updated: time + 10_000,
        country_id: null,
        country_name: null,
      },
    };
  }

  function collection(features: EventFeature[]): EventCollection {
    return {
      type: "FeatureCollection",
      metadata: {
        generated: 1,
        last_ingestion: null,
        mode: "live",
        count: features.length,
        total_count: 150,
        limit: 100,
        offset: 0,
        truncated: true,
      },
      features,
    };
  }

  beforeEach(async () => {
    mapLayers = jasmine.createSpyObj<MapLayersService>(
      "MapLayersService",
      ["createMap", "addCountryBoundaries"],
    );
    mapLayers.createMap.and.rejectWith(new Error("worker unavailable"));
    await TestBed.configureTestingModule({
      imports: [EventMapComponent],
      providers: [{ provide: MapLayersService, useValue: mapLayers }],
    }).compileComponents();
    fixture = TestBed.createComponent(EventMapComponent);
  });

  it("counts ties by occurrence time and discloses a partial map page", async () => {
    fixture.componentRef.setInput("events", collection([
      makeEvent("older", 1),
      makeEvent("latest-a", 2),
      makeEvent("latest-b", 2),
    ]));
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();

    expect(fixture.componentInstance.latestCount).toBe(2);
    expect(fixture.componentInstance.isTruncated).toBeTrue();
    expect(fixture.nativeElement.textContent).toContain("Más reciente");
    expect(fixture.nativeElement.textContent).toContain("empatados");
    expect(fixture.nativeElement.textContent).toContain("150");
  });

  it("explains when no displayed event has a valid occurrence time", async () => {
    const invalidTime = makeEvent("invalid-time", Number.NaN);
    fixture.componentRef.setInput("events", collection([invalidTime]));
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();

    expect(fixture.componentInstance.latestCount).toBe(0);
    expect(fixture.nativeElement.textContent).toContain("No se puede identificar el evento más reciente");
    expect(fixture.nativeElement.textContent).toContain("Ningún evento mostrado tiene un tiempo de ocurrencia válido");
  });

  it("surfaces worker initialization failures while keeping the optional overlay disabled", async () => {
    fixture.componentRef.setInput("events", collection([makeEvent("event", 1)]));
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();

    expect(fixture.nativeElement.querySelector('[role="alert"]').textContent).toContain("worker unavailable");
    expect(fixture.componentInstance.densityEnabled).toBeFalse();
    await fixture.componentInstance.toggleDensity();
    expect(fixture.componentInstance.densityEnabled).toBeFalse();
  });

  it("emits the clicked event identity and releases the map on teardown", async () => {
    const source = { setData: jasmine.createSpy("setData") };
    const mapOn = jasmine.createSpy("on");
    const map = {
      on: mapOn,
      isStyleLoaded: jasmine.createSpy("isStyleLoaded").and.returnValue(true),
      getSource: jasmine.createSpy("getSource").and.returnValue(source),
      addSource: jasmine.createSpy("addSource"),
      addLayer: jasmine.createSpy("addLayer"),
      getCanvas: jasmine.createSpy("getCanvas").and.returnValue({ style: { cursor: "" } }),
      remove: jasmine.createSpy("remove"),
    } as unknown as MapLibreMap;
    mapLayers.createMap.and.resolveTo(map);
    mapLayers.addCountryBoundaries.and.resolveTo();
    fixture.componentRef.setInput("events", collection([makeEvent("select-me", 5)]));
    const emit = spyOn(fixture.componentInstance.eventSelected, "emit");

    fixture.detectChanges();
    await fixture.whenStable();
    const loadHandler = mapOn.calls.allArgs().find(([eventName]) => eventName === "load")?.[1] as (() => void) | undefined;
    expect(loadHandler).toBeDefined();
    loadHandler?.();
    await fixture.whenStable();

    const errorHandler = mapOn.calls.allArgs().find(([eventName]) => eventName === "error")?.[1] as
      ((event: { error: Error }) => void) | undefined;
    errorHandler?.({ error: new Error("style failed") });
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('[role="alert"]').textContent).toContain("style failed");

    const clickArgs = mapOn.calls.allArgs()
      .find(([eventName, layer]) => eventName === "click" && layer === "seismic-events-points");
    type MapClickHandler = (event: { features?: Array<{ properties?: { eventId?: string } }> }) => void;
    const clickHandler = clickArgs?.[2] as MapClickHandler | undefined;
    expect(clickHandler).toBeDefined();
    clickHandler?.({ features: [{ properties: { eventId: "select-me" } }] });
    expect(emit).toHaveBeenCalledOnceWith("select-me");

    const finalize = jasmine.createSpy("finalize");
    Object.defineProperty(fixture.componentInstance, "deckOverlay", {
      value: { finalize },
      writable: true,
    });
    fixture.destroy();
    expect(finalize).toHaveBeenCalledOnceWith();
    expect(map.remove).toHaveBeenCalledOnceWith();
  });
});
