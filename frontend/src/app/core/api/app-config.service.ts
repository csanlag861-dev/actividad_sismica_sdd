import { Injectable } from "@angular/core";

export interface PublicAppConfig {
  apiBaseUrl: string;
}

@Injectable({ providedIn: "root" })
export class AppConfigService {
  private config: PublicAppConfig | null = null;
  private loading: Promise<PublicAppConfig> | null = null;

  load(): Promise<PublicAppConfig> {
    this.loading ??= this.fetchConfig();
    return this.loading;
  }

  get value(): PublicAppConfig {
    if (!this.config) {
      throw new Error("La configuración pública todavía no se ha cargado.");
    }
    return this.config;
  }

  private async fetchConfig(): Promise<PublicAppConfig> {
    let response: Response;
    try {
      response = await fetch("/config.json", {
        method: "GET",
        headers: { Accept: "application/json" },
        credentials: "omit",
      });
    } catch (error) {
      throw new Error("No se pudo cargar la configuración pública de la API.", { cause: error });
    }

    if (!response.ok) {
      throw new Error(`No se pudo cargar la configuración pública (HTTP ${response.status}).`);
    }

    let config: unknown;
    try {
      config = await response.json();
    } catch (error) {
      throw new Error("La configuración pública no contiene JSON válido.", { cause: error });
    }

    if (
      typeof config !== "object"
      || config === null
      || Array.isArray(config)
      || Object.keys(config).length !== 1
      || !("apiBaseUrl" in config)
      || typeof config.apiBaseUrl !== "string"
    ) {
      throw new TypeError("La configuración pública debe contener únicamente apiBaseUrl.");
    }

    const parsedUrl = new URL(config.apiBaseUrl);
    if (
      !["http:", "https:"].includes(parsedUrl.protocol)
      || (parsedUrl.protocol === "http:"
        && !["localhost", "127.0.0.1", "::1"].includes(parsedUrl.hostname))
      || parsedUrl.username
      || parsedUrl.password
      || parsedUrl.search
      || parsedUrl.hash
      || parsedUrl.pathname.replace(/\/+$/, "").endsWith("/api")
    ) {
      throw new TypeError("apiBaseUrl debe ser un origen válido, sin credenciales ni sufijo /api.");
    }

    this.config = { apiBaseUrl: config.apiBaseUrl };
    return this.config;
  }
}
