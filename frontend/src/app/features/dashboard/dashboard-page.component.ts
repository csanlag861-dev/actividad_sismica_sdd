import { Component, inject, signal } from "@angular/core";
import { DatePipe } from "@angular/common";
import { RouterLink } from "@angular/router";
import { EventCollection, EventFeature, EventFilters } from "../../core/models/api.models";
import { QueryStateService } from "../../core/state/query-state.service";
import { EventDetailComponent } from "../events/event-detail.component";
import { EventsTableComponent } from "../events/events-table.component";
import { EventMapComponent } from "../../shared/map/event-map.component";
import { hasValidEventCoordinates } from "../../shared/map/event-map.utils";
import { ResourceStatusComponent } from "../../shared/status/resource-status.component";
import { ActivityTimelineComponent } from "./activity-timeline.component";
import { DistributionSummaryComponent } from "./distribution-summary.component";

@Component({
  selector: "app-dashboard-page",
  imports: [
    ActivityTimelineComponent,
    DatePipe,
    DistributionSummaryComponent,
    EventDetailComponent,
    EventMapComponent,
    EventsTableComponent,
    ResourceStatusComponent,
    RouterLink,
  ],
  templateUrl: "./dashboard-page.component.html",
  styleUrl: "./dashboard-page.component.css",
})
export class DashboardPageComponent {
  readonly queries = inject(QueryStateService);
  private readonly tableSelectedEvent = signal<EventFeature | null>(null);
  selectedId: string | null = null;

  get eventSnapshot() {
    return this.queries.state().events;
  }

  get statisticsSnapshot() {
    return this.queries.state().statistics;
  }

  get displayedEvents(): EventFeature[] {
    const seenIds = new Set<string>();
    return (this.eventSnapshot.data?.features ?? []).filter((event) => {
      if (seenIds.has(event.id)) return false;
      seenIds.add(event.id);
      return true;
    });
  }

  get mapEvents(): EventCollection | null {
    const collection = this.eventSnapshot.data;
    if (!collection) return null;
    return {
      ...collection,
      features: this.displayedEvents.filter(hasValidEventCoordinates),
    };
  }

  get selectedEvent(): EventFeature | null {
    const tableEvent = this.tableSelectedEvent();
    if (tableEvent?.id === this.selectedId) return tableEvent;
    return this.displayedEvents.find((event) => event.id === this.selectedId) ?? null;
  }

  get tableFilters(): EventFilters {
    return this.eventSnapshot.filters ?? this.queries.filters();
  }

  get eventPeriodLabel(): string {
    const period = this.eventSnapshot.period;
    if (!period) {
      return "Últimas 24 horas; periodo predeterminado de la API, sin límites exactos declarados en la respuesta.";
    }
    return `${this.formatUtc(period.start)} – ${this.formatUtc(period.end)} UTC`;
  }

  get eventFiltersLabel(): string {
    const filters = this.eventSnapshot.filters;
    if (!filters) return "Filtros enviados no disponibles para esta lectura.";
    return [
      filters.min_mag === undefined ? "Sin magnitud mínima" : `Magnitud mínima ≥ ${filters.min_mag}`,
      filters.country_id ? `País ${filters.country_id}` : "Todos los países",
    ].join(" · ");
  }

  get statisticsFiltersLabel(): string {
    const filters = this.statisticsSnapshot.data?.filters;
    if (!filters) return "Filtros efectivos no disponibles.";
    return [
      filters.min_mag === null ? "Sin magnitud mínima" : `Magnitud mínima ≥ ${filters.min_mag}`,
      filters.country_id === null ? "Todos los países" : `País ${filters.country_id}`,
    ].join(" · ");
  }

  selectEvent(event: string | EventFeature): void {
    const id = typeof event === "string" ? event : event.id;
    this.selectedId = id;
    this.tableSelectedEvent.set(typeof event === "string" ? null : event);
  }

  private formatUtc(value: string): string {
    return new Date(value).toLocaleString("es-ES", { timeZone: "UTC" });
  }
}
