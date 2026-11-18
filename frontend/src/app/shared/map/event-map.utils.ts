import { EventFeature } from "../../core/models/api.models";

const MISSING_DEPTH_COLOR = "#8f7d70";
const NEGATIVE_DEPTH_COLOR = "#71839a";
const SHALLOW_COLOR = [242, 192, 120] as const;
const DEEP_COLOR = [143, 63, 42] as const;

export function eventCoordinates(event: EventFeature): [number, number] {
  const [longitude, latitude] = event.geometry.coordinates;
  return [latitude, longitude];
}

export function hasValidEventCoordinates(event: EventFeature): boolean {
  const [latitude, longitude] = eventCoordinates(event);
  return Number.isFinite(latitude)
    && latitude >= -90
    && latitude <= 90
    && Number.isFinite(longitude)
    && longitude >= -180
    && longitude <= 180;
}

export function markerRadius(magnitude: number | null): number {
  if (magnitude === null || !Number.isFinite(magnitude)) return 5;
  return Math.max(4, Math.min(18, 4 + Math.max(0, magnitude) * 2));
}

export function latestEventIds(events: EventFeature[]): Set<string> {
  const validEvents = events.filter((event) =>
    hasValidEventCoordinates(event)
    && Number.isFinite(event.properties.time));
  if (!validEvents.length) return new Set();
  const latestTime = Math.max(...validEvents.map((event) => event.properties.time));
  return new Set(
    validEvents
      .filter((event) => event.properties.time === latestTime)
      .map((event) => event.id),
  );
}

export function depthBinIndex(depthKm: number): number | null {
  if (!Number.isFinite(depthKm) || depthKm < 0) return null;
  return Math.floor(depthKm / 10);
}

export function depthBinLabel(index: number): string {
  return `[${index * 10}, ${(index + 1) * 10}) km`;
}

export function depthColor(depthKm: number | null): string {
  if (depthKm === null || !Number.isFinite(depthKm)) return MISSING_DEPTH_COLOR;
  if (depthKm < 0) return NEGATIVE_DEPTH_COLOR;

  const bin = depthBinIndex(depthKm) ?? 0;
  const factor = bin / (bin + 4);
  const channels = SHALLOW_COLOR.map((start, index) =>
    Math.round(start + (DEEP_COLOR[index] - start) * factor));
  return `rgb(${channels[0]}, ${channels[1]}, ${channels[2]})`;
}

export function depthLegend(
  maxDepth: number | null,
  hasNegativeDepth = false,
): Array<{ label: string; color: string }> {
  const lastBin = maxDepth === null ? -1 : depthBinIndex(maxDepth) ?? -1;
  const bins = Array.from({ length: lastBin + 1 }, (_, index) => ({
    label: depthBinLabel(index),
    color: depthColor(index * 10),
  }));
  if (hasNegativeDepth) {
    bins.push({ label: "Profundidad negativa (valor recibido)", color: NEGATIVE_DEPTH_COLOR });
  }
  bins.push({ label: "Profundidad desconocida", color: MISSING_DEPTH_COLOR });
  return bins;
}
