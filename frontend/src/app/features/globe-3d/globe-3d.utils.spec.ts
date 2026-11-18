import { EventFeature } from "../../core/models/api.models";
import { globeEventMarkers } from "./globe-3d.utils";

describe("globe 3D utilities", () => {
  function event(
    id: string,
    time: number,
    depthKm: number | null,
    coordinates: [number, number] = [10, 20],
  ): EventFeature {
    return {
      type: "Feature",
      id,
      geometry: { type: "Point", coordinates },
      properties: {
        mag: 2,
        magType: null,
        place: id,
        depth_km: depthKm,
        time,
        updated: time + 10_000,
        country_id: null,
        country_name: null,
      },
    };
  }

  it("keeps all globe markers on the surface and represents unknown depth without a value", () => {
    const markers = globeEventMarkers([
      event("unknown", 1, null),
      event("deep-latest", 2, 30),
      event("invalid", 3, 5, [181, 20]),
    ]);

    expect(markers.map((marker) => marker.event.id)).toEqual(["unknown", "deep-latest"]);
    expect(markers[0].coordinates).toEqual([10, 20]);
    expect(markers[0].depthKm).toBeNull();
    expect(markers[0].pixelSize).toBe(8);
    expect(markers[1].coordinates.length).toBe(2);
    expect(markers[1].latest).toBeTrue();
  });

  it("marks every tied latest occurrence instead of using update time", () => {
    const markers = globeEventMarkers([
      event("latest-a", 2, 10),
      event("latest-b", 2, 15),
      event("updated-later", 1, 20),
    ]);

    expect(markers.filter((marker) => marker.latest).map((marker) => marker.event.id))
      .toEqual(["latest-a", "latest-b"]);
  });
});
