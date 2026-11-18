import { Injectable, signal } from "@angular/core";

export interface CountryOption {
  id: string;
  name: string;
}

@Injectable({ providedIn: "root" })
export class CountryCatalogService {
  readonly countries = signal<CountryOption[]>([]);

  async load(): Promise<void> {
    const response = await fetch("/datos/paises.geojson", {
      headers: { Accept: "application/geo+json, application/json" },
      credentials: "omit",
    });
    if (!response.ok) {
      throw new Error(`No se pudo cargar el catálogo de países (HTTP ${response.status}).`);
    }

    const data: unknown = await response.json();
    if (typeof data !== "object" || data === null || !("features" in data) || !Array.isArray(data.features)) {
      throw new TypeError("El catálogo local de países no tiene una estructura válida.");
    }

    const countries = data.features.flatMap((feature: unknown) => {
      if (typeof feature !== "object" || feature === null || !("properties" in feature)) return [];
      const properties = feature.properties;
      if (typeof properties !== "object" || properties === null) return [];
      if (!("ADM0_A3" in properties) || !("NAME_ES" in properties)) return [];
      const id = properties.ADM0_A3;
      const name = properties.NAME_ES;
      if (typeof id !== "string" || !/^[A-Z0-9]{3}$/.test(id) || typeof name !== "string" || !name.trim()) {
        return [];
      }
      return [{ id, name }];
    });

    this.countries.set(
      [...new Map(countries.map((country) => [country.id, country])).values()]
        .sort((left, right) => left.name.localeCompare(right.name, "es")),
    );
  }
}
