import { DatePipe } from "@angular/common";
import { Component, signal } from "@angular/core";
import { EventFeature } from "../../core/models/api.models";
import { QueryStateService } from "../../core/state/query-state.service";
import { EventDetailComponent } from "./event-detail.component";
import { EventFiltersComponent } from "./event-filters.component";
import { EventsTableComponent } from "./events-table.component";
import { EventMapComponent } from "../../shared/map/event-map.component";
import { ResourceStatusComponent } from "../../shared/status/resource-status.component";

@Component({
  selector: "app-events-page",
  imports: [
    EventDetailComponent,
    DatePipe,
    EventFiltersComponent,
    EventsTableComponent,
    EventMapComponent,
    ResourceStatusComponent,
  ],
  templateUrl: "./events-page.component.html",
  styleUrl: "./events-page.component.css",
})
export class EventsPageComponent {
  readonly selectedId = signal<string | null>(null);

  constructor(readonly queries: QueryStateService) {}

  get selectedEvent(): EventFeature | null {
    return this.queries.state().events.data?.features
      .find((event) => event.id === this.selectedId()) ?? null;
  }

  get eventSnapshot() {
    return this.queries.state().events;
  }

  get displayedPeriod(): string {
    const period = this.eventSnapshot.period;
    if (!period) {
      return "Periodo móvil predeterminado de 24 horas; el endpoint de eventos no declara los límites exactos.";
    }
    return `${this.formatUtc(period.start)} – ${this.formatUtc(period.end)} UTC`;
  }

  get displayedFilters(): string {
    const filters = this.eventSnapshot.filters;
    if (!filters) return "Filtros enviados no disponibles para esta lectura.";
    const parts = [
      filters.min_mag === undefined ? "Sin magnitud mínima" : `Magnitud mínima ≥ ${filters.min_mag}`,
      filters.country_id ? `País ${filters.country_id}` : "Todos los países",
    ];
    return parts.join(" · ");
  }

  selectEvent(id: string): void {
    this.selectedId.set(id);
  }

  private formatUtc(value: string): string {
    return new Date(value).toLocaleString("es-ES", { timeZone: "UTC" });
  }
}
