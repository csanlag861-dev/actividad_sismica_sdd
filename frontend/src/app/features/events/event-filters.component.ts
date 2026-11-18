import { Component, OnInit, inject } from "@angular/core";
import { FormsModule } from "@angular/forms";
import { CountryCatalogService } from "./country-catalog.service";
import { QueryStateService } from "../../core/state/query-state.service";
import { EventFilters } from "../../core/models/api.models";

@Component({
  selector: "app-event-filters",
  imports: [FormsModule],
  templateUrl: "./event-filters.component.html",
  styleUrl: "./event-filters.component.css",
})
export class EventFiltersComponent implements OnInit {
  readonly catalog = inject(CountryCatalogService);
  readonly queries = inject(QueryStateService);
  startValue = "";
  endValue = "";
  minMagnitude: number | null = null;
  countryId = "";
  filterError: string | null = null;
  catalogError: string | null = null;

  async ngOnInit(): Promise<void> {
    this.syncFromSharedFilters();
    try {
      await this.catalog.load();
    } catch (error) {
      this.catalogError = error instanceof Error ? error.message : "No se pudo cargar el catálogo de países.";
    }
  }

  apply(): void {
    this.filterError = null;
    try {
      const filters: { start?: string; end?: string; min_mag?: number; country_id?: string } = {};
      if (this.startValue || this.endValue) {
        if (!this.startValue || !this.endValue) {
          throw new TypeError("Selecciona tanto el inicio como el fin del periodo.");
        }
        const start = new Date(`${this.startValue}:00Z`);
        const end = new Date(`${this.endValue}:00Z`);
        if (!Number.isFinite(start.getTime()) || !Number.isFinite(end.getTime()) || start >= end) {
          throw new TypeError("El periodo debe ser válido y el inicio anterior al fin.");
        }
        filters.start = start.toISOString();
        filters.end = end.toISOString();
      }
      if (this.minMagnitude !== null) {
        if (!Number.isFinite(this.minMagnitude)) throw new TypeError("La magnitud mínima debe ser un número finito.");
        filters.min_mag = this.minMagnitude;
      }
      if (this.countryId) filters.country_id = this.countryId;

      this.queries.setFilters(filters);
    } catch (error) {
      this.filterError = error instanceof Error ? error.message : "Los filtros no son válidos.";
    }
  }

  clear(): void {
    this.startValue = "";
    this.endValue = "";
    this.minMagnitude = null;
    this.countryId = "";
    this.filterError = null;
    this.queries.setFilters({});
  }

  private syncFromSharedFilters(): void {
    const filters = this.queries.filters();
    this.startValue = this.toDateTimeLocal(filters.start);
    this.endValue = this.toDateTimeLocal(filters.end);
    this.minMagnitude = filters.min_mag ?? null;
    this.countryId = filters.country_id ?? "";
  }

  private toDateTimeLocal(value: EventFilters["start"]): string {
    if (!value) return "";
    const date = new Date(value);
    if (!Number.isFinite(date.getTime())) return "";
    const pad = (part: number) => String(part).padStart(2, "0");
    return `${date.getUTCFullYear()}-${pad(date.getUTCMonth() + 1)}-${pad(date.getUTCDate())}T${pad(date.getUTCHours())}:${pad(date.getUTCMinutes())}`;
  }
}
