import {
  depthBinIndex,
  depthBinLabel,
  depthColor,
  depthLegend,
  eventCoordinates,
  hasValidEventCoordinates,
  latestEventIds,
  markerRadius,
} from "./event-map.utils";
import { EventFeature } from "../../core/models/api.models";

describe("event-map utilities", () => {
  it("keeps GeoJSON longitude/latitude coordinates in map order", () => {
    const event: EventFeature = {
      type: "Feature",
      id: "event-1",
      geometry: { type: "Point", coordinates: [-3.7, 40.4, 12] },
      properties: {
        mag: 3.2,
        magType: "ml",
        place: null,
        depth_km: 12,
        time: 1,
        updated: 1,
        country_id: null,
        country_name: null,
      },
    };
    expect(eventCoordinates(event)).toEqual([40.4, -3.7]);
    expect(hasValidEventCoordinates(event)).toBeTrue();
  });

  it("rejects coordinates outside geographic latitude and longitude ranges", () => {
    const event: EventFeature = {
      type: "Feature",
      id: "event-invalid",
      geometry: { type: "Point", coordinates: [181, 40] },
      properties: {
        mag: 1,
        magType: null,
        place: null,
        depth_km: null,
        time: 1,
        updated: 1,
        country_id: null,
        country_name: null,
      },
    };

    expect(hasValidEventCoordinates(event)).toBeFalse();
  });

  it("uses semi-open ten-kilometre depth bins and represents missing values distinctly", () => {
    expect(depthBinIndex(0)).toBe(0);
    expect(depthBinIndex(9.99)).toBe(0);
    expect(depthBinIndex(10)).toBe(1);
    expect(depthBinLabel(1)).toBe("[10, 20) km");
    expect(depthColor(null)).not.toBe(depthColor(0));
    expect(depthBinIndex(-0.1)).toBeNull();
    expect(depthColor(-0.1)).not.toBe(depthColor(0));
    expect(depthColor(-0.1)).not.toBe(depthColor(null));
    expect(depthLegend(-0.1, true).map(({ label }) => label)).toContain(
      "Profundidad negativa (valor recibido)",
    );
  });

  it("scales marker radius by available magnitude and remains bounded", () => {
    expect(markerRadius(null)).toBe(5);
    expect(markerRadius(-1)).toBe(4);
    expect(markerRadius(0)).toBe(4);
    expect(markerRadius(1)).toBeLessThan(markerRadius(5));
    expect(markerRadius(100)).toBe(18);
  });

  it("highlights all valid events tied at the latest occurrence time", () => {
    const event = (id: string, time: number, coordinates: [number, number] = [1, 2]): EventFeature => ({
      type: "Feature",
      id,
      geometry: { type: "Point", coordinates },
      properties: {
        mag: 2,
        magType: null,
        place: null,
        depth_km: null,
        time,
        updated: time + 10_000,
        country_id: null,
        country_name: null,
      },
    });

    expect(latestEventIds([
      event("older", 10),
      event("latest-a", 20),
      event("latest-b", 20),
      event("invalid", 30, [181, 2]),
    ])).toEqual(new Set(["latest-a", "latest-b"]));
    expect(latestEventIds([event("invalid-time", Number.NaN)])).toEqual(new Set());
  });
});
