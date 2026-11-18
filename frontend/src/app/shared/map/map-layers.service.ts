import { Injectable } from "@angular/core";
import * as L from "leaflet";

interface CountryProperties {
  ADM0_A3?: string | number;
  NAME_ES?: string;
}

interface CountryCollection {
  type: "FeatureCollection";
  features: Array<{
    type: "Feature";
    properties: CountryProperties;
    geometry: GeoJSON.Geometry;
  }>;
}

@Injectable({ providedIn: "root" })
export class MapLayersService {
  createMap(container: HTMLElement): L.Map {
    const map = L.map(container, {
      center: [15, 0],
      zoom: 2,
      minZoom: 2,
      worldCopyJump: true,
    });

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 18,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    }).addTo(map);
    return map;
  }

  async addCountryBoundaries(map: L.Map): Promise<void> {
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

    L.geoJSON(data, {
      style: {
        color: "var(--color-border)",
        weight: 0.6,
        fillColor: "var(--color-surface-elevated)",
        fillOpacity: 0.12,
      },
      interactive: false,
    }).addTo(map);
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
