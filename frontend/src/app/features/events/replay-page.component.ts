import { DatePipe } from "@angular/common";
import { Component, OnInit, signal, inject } from "@angular/core";
import { FormsModule } from "@angular/forms";
import { EventCollection, EventFeature, EventFilters } from "../../core/models/api.models";
import { ObservatoryApiService } from "../../core/api/observatory-api.service";
import { EventDetailComponent } from "./event-detail.component";
import { EventsTableComponent } from "./events-table.component";
import { EventMapComponent } from "../../shared/map/event-map.component";

@Component({
  selector: "app-replay-page",
  imports: [DatePipe, FormsModule, EventDetailComponent, EventsTableComponent, EventMapComponent],
  templateUrl: "./replay-page.component.html",
  styleUrl: "./replay-page.component.css",
})
export class ReplayPageComponent implements OnInit {
  private readonly api = inject(ObservatoryApiService);
  private requestId = 0;
  readonly selectedId = signal<string | null>(null);
  readonly queryId = signal(0);
  startValue = "2025-01-01T00:00";
  endValue = "2025-01-02T00:00";
  minMagnitude: number | null = 4;
  filters: EventFilters = {};
  events: EventCollection | null = null;
  selectedFromTable: EventFeature | null = null;
  loading = false;
  errorMessage: string | null = null;
  filterError: string | null = null;

  get selectedEvent(): EventFeature | null {
    const selectedId = this.selectedId();
    if (this.selectedFromTable?.id === selectedId) return this.selectedFromTable;
    return this.events?.features.find((event) => event.id === selectedId) ?? null;
  }

  ngOnInit(): void {
    this.applyFilters();
  }

  applyFilters(): void {
    this.filterError = null;
    try {
      if (!this.startValue || !this.endValue) {
        throw new TypeError("Selecciona tanto el inicio como el fin del periodo.");
      }
      const start = new Date(`${this.startValue}:00Z`);
      const end = new Date(`${this.endValue}:00Z`);
      if (!Number.isFinite(start.getTime()) || !Number.isFinite(end.getTime()) || start >= end) {
        throw new TypeError("El periodo debe ser válido y el inicio anterior al fin.");
      }
      if (this.minMagnitude !== null && !Number.isFinite(this.minMagnitude)) {
        throw new TypeError("La magnitud mínima debe ser un número finito.");
      }

      this.filters = {
        start: start.toISOString(),
        end: end.toISOString(),
        ...(this.minMagnitude === null ? {} : { min_mag: this.minMagnitude }),
      };
      this.selectedId.set(null);
      this.selectedFromTable = null;
      this.queryId.update((value) => value + 1);
      void this.loadMapEvents();
    } catch (error) {
      this.filterError = error instanceof Error ? error.message : "Los filtros no son válidos.";
    }
  }

  selectEvent(event: string | EventFeature): void {
    this.selectedId.set(typeof event === "string" ? event : event.id);
    this.selectedFromTable = typeof event === "string" ? null : event;
  }

  private async loadMapEvents(): Promise<void> {
    const requestId = ++this.requestId;
    this.loading = true;
    this.errorMessage = null;
    try {
      const response = await this.api.fetchEvents(
        this.filters,
        { limit: 100, offset: 0 },
        "replay",
      );
      if (requestId !== this.requestId) return;
      this.events = response;
    } catch (error) {
      if (requestId !== this.requestId) return;
      this.errorMessage = this.api.getError(error).message;
    } finally {
      if (requestId === this.requestId) this.loading = false;
    }
  }
}
