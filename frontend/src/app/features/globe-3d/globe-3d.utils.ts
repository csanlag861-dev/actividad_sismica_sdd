import { EventFeature } from "../../core/models/api.models";
import {
  depthColor,
  hasValidEventCoordinates,
  latestEventIds,
} from "../../shared/map/event-map.utils";

export interface GlobeEventMarker {
  event: EventFeature;
  coordinates: [longitude: number, latitude: number];
  depthKm: number | null;
  color: string;
  pixelSize: number;
  latest: boolean;
}

export function globeEventMarkers(events: EventFeature[]): GlobeEventMarker[] {
  const latestIds = latestEventIds(events);
  return events
    .filter(hasValidEventCoordinates)
    .map((event) => {
      const [longitude, latitude] = event.geometry.coordinates;
      const depthKm = event.properties.depth_km;
      const latest = latestIds.has(event.id);
      return {
        event,
        coordinates: [longitude, latitude],
        depthKm,
        color: latest ? "#d83a32" : depthColor(depthKm),
        pixelSize: (depthKm === null ? 8 : 9 + Math.min(depthKm / 30, 12)) + (latest ? 5 : 0),
        latest,
      };
    });
}
