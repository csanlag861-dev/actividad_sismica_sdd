import { Injectable } from "@angular/core";
import type { Geometry } from "geojson";
import type { Map as MapLibreMap } from "maplibre-gl";

interface CountryProperties {
  ADM0_A3?: string | number;
  NAME_ES?: string;
}

interface CountryCollection {
  type: "FeatureCollection";
  features: Array<{
    type: "Feature";
    properties: CountryProperties;
    geometry: Geometry;
  }>;
}

@Injectable({ providedIn: "root" })
export class MapLayersService {
  async createMap(container: HTMLElement): Promise<MapLibreMap> {
    const maplibregl = await import("maplibre-gl");
    maplibregl.setWorkerUrl("/assets/maplibre/maplibre-gl-worker.mjs");
    const map = new maplibregl.Map({
      container,
      center: [0, 15],
      zoom: 2,
      minZoom: 2,
      style: {
        version: 8,
        sources: {
          openstreetmap: {
            type: "raster",
            tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
            tileSize: 256,
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
          },
        },
        layers: [{ id: "openstreetmap", type: "raster", source: "openstreetmap" }],
      },
    });
    map.addControl(new maplibregl.NavigationControl(), "top-right");
    return map;
  }

  async addCountryBoundaries(map: MapLibreMap, isActive: () => boolean = () => true): Promise<void> {
    const response = await fetch("/datos/paises.geojson", {
      headers: { Accept: "application/geo+json, application/json" },
      credentials: "omit",
    });
    if (!response.ok) {
      throw new Error(`No se pudo cargar el catálogo cartográfico local (HTTP ${response.status}).`);
    }

    const data: unknown = await response.json();
    if (!this.isCountryCollection(data)) {
      throw new TypeError("El catálogo cartográfico local no tiene una estructura GeoJSON válida.");
    }

    if (!isActive()) return;
    if (map.getSource("country-boundaries")) return;
    map.addSource("country-boundaries", {
      type: "geojson",
      data,
    });
    map.addLayer({
      id: "country-boundaries-fill",
      type: "fill",
      source: "country-boundaries",
      paint: {
        "fill-color": "#9b806f",
        "fill-opacity": 0.12,
      },
    });
    map.addLayer({
      id: "country-boundaries-outline",
      type: "line",
      source: "country-boundaries",
      paint: {
        "line-color": "#9b806f",
        "line-width": 0.6,
        "line-opacity": 0.6,
      },
    });
  }

  private isCountryCollection(data: unknown): data is CountryCollection {
    if (typeof data !== "object" || data === null || !("type" in data) || !("features" in data)) {
      return false;
    }
    return data.type === "FeatureCollection"
      && Array.isArray(data.features)
      && data.features.every((feature) =>
        typeof feature === "object"
        && feature !== null
        && feature.type === "Feature"
        && "properties" in feature
        && "geometry" in feature);
  }
}
