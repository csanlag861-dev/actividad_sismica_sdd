import { TestBed } from "@angular/core/testing";
import { AppConfigService } from "./app-config.service";
import { ObservatoryApiService } from "./observatory-api.service";
import { EventCollection, EventFeature } from "../models/api.models";

function page(offset: number, features: EventCollection["features"], totalCount: number): EventCollection {
  return {
    type: "FeatureCollection",
    metadata: {
      generated: 1,
      last_ingestion: null,
      mode: "live",
      count: features.length,
      total_count: totalCount,
      offset,
      limit: 100,
      truncated: offset + features.length < totalCount,
    },
    features,
  };
}

function features(start: number, count: number): EventFeature[] {
  return Array.from({ length: count }, (_, index) => ({
    type: "Feature",
    id: `event-${start + index}`,
    geometry: { type: "Point", coordinates: [0, 0] },
    properties: {
      mag: 1,
      magType: null,
      place: null,
      depth_km: null,
      time: start + index,
      updated: start + index,
      country_id: null,
      country_name: null,
    },
  }));
}

describe("ObservatoryApiService", () => {
  let api: ObservatoryApiService;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        ObservatoryApiService,
        { provide: AppConfigService, useValue: { value: { apiBaseUrl: "http://localhost:8000" } } },
      ],
    });
    api = TestBed.inject(ObservatoryApiService);
  });

  it("loads every page and returns complete collection metadata", async () => {
    const firstFeatures = features(0, 100);
    const secondFeatures = features(100, 100);
    const finalFeatures = features(200, 5);
    const fetchEvents = spyOn(api, "fetchEvents").and.returnValues(
      Promise.resolve(page(0, firstFeatures, 205)),
      Promise.resolve(page(100, secondFeatures, 205)),
      Promise.resolve(page(200, finalFeatures, 205)),
    );

    const result = await api.fetchAllEvents({ min_mag: 2 });

    expect(fetchEvents.calls.allArgs()).toEqual([
      [{ min_mag: 2 }, { limit: 100, offset: 0 }],
      [{ min_mag: 2 }, { limit: 100, offset: 100 }],
      [{ min_mag: 2 }, { limit: 100, offset: 200 }],
    ]);
    expect(result.features.length).toBe(205);
    expect(result.metadata.count).toBe(205);
    expect(result.metadata.truncated).toBeFalse();
  });

  it("keeps the collection marked incomplete when a later page is empty", async () => {
    const firstFeatures = features(0, 100);
    spyOn(api, "fetchEvents").and.returnValues(
      Promise.resolve(page(0, firstFeatures, 150)),
      Promise.resolve(page(100, [], 150)),
    );

    const result = await api.fetchAllEvents();

    expect(result.features.length).toBe(100);
    expect(result.metadata.truncated).toBeTrue();
  });
});
