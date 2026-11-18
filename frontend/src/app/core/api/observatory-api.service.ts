import { DestroyRef, Injectable, inject } from "@angular/core";
import {
  ApiClient,
  ApiHttpError,
  ApiTransportError,
  createApiClient,
} from "../../../api-client.mjs";
import {
  EventCollection,
  EventFilters,
  HealthResponse,
  StatisticsResponse,
} from "../models/api.models";
import { AppConfigService } from "./app-config.service";

@Injectable({ providedIn: "root" })
export class ObservatoryApiService {
  private readonly config = inject(AppConfigService);
  private readonly destroyRef = inject(DestroyRef);
  private readonly client: ApiClient;

  constructor() {
    this.client = createApiClient({ baseUrl: this.config.value.apiBaseUrl });
    this.destroyRef.onDestroy(() => this.client.dispose());
  }

  fetchEvents(filters: EventFilters = {}): Promise<EventCollection> {
    return this.client.fetchEvents(filters);
  }

  fetchStatistics(filters: EventFilters = {}): Promise<StatisticsResponse> {
    return this.client.fetchStatistics(filters);
  }

  fetchHealth(): Promise<HealthResponse> {
    return this.client.fetchHealth();
  }

  getError(error: unknown): { kind: "http" | "transport"; message: string; status?: number } {
    if (error instanceof ApiHttpError) {
      return {
        kind: "http",
        message: `La API respondió con HTTP ${error.status}: ${error.message}`,
        status: error.status,
      };
    }
    if (error instanceof ApiTransportError) {
      const message = error.message === "API request timed out"
        ? "La API no respondió dentro del límite de 15 segundos."
        : error.message.startsWith("API returned an invalid")
          ? "La respuesta de la API no cumple el contrato esperado."
          : "No se pudo establecer comunicación con la API.";
      return { kind: "transport", message };
    }
    throw new TypeError("El error no procede de una respuesta HTTP ni del transporte de la API.", {
      cause: error,
    });
  }
}
