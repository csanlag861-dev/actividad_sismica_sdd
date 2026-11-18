import { DatePipe } from "@angular/common";
import {
  Component,
  EventEmitter,
  Input,
  OnChanges,
  Output,
  SimpleChanges,
  inject,
} from "@angular/core";
import { EventCollection, EventFeature, EventFilters, EventMode } from "../../core/models/api.models";
import { ObservatoryApiService } from "../../core/api/observatory-api.service";

@Component({
  selector: "app-events-table",
  imports: [DatePipe],
  templateUrl: "./events-table.component.html",
  styleUrl: "./events-table.component.css",
})
export class EventsTableComponent implements OnChanges {
  private readonly api = inject(ObservatoryApiService);
  private requestId = 0;
  @Input() filters: EventFilters = {};
  @Input() mode: EventMode = "live";
  @Input() queryId = 0;
  @Input() selectedId: string | null = null;
  @Output() eventSelected = new EventEmitter<EventFeature>();

  readonly pageSizes = [25, 50, 100] as const;
  events: EventCollection | null = null;
  errorMessage: string | null = null;
  loading = false;
  pageSize: 25 | 50 | 100 = 25;
  offset = 0;

  get totalCount(): number {
    return this.events?.metadata.total_count ?? this.events?.metadata.count ?? 0;
  }

  get totalPages(): number {
    return Math.ceil(this.totalCount / this.pageSize);
  }

  get currentPage(): number {
    return this.totalCount ? Math.floor(this.offset / this.pageSize) + 1 : 0;
  }

  get firstResult(): number {
    return this.totalCount ? this.offset + 1 : 0;
  }

  get lastResult(): number {
    return Math.min(this.offset + (this.events?.features.length ?? 0), this.totalCount);
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes["filters"] && !changes["filters"].firstChange) {
      this.offset = 0;
      this.events = null;
    }
    if (changes["mode"] && !changes["mode"].firstChange) {
      this.offset = 0;
      this.events = null;
    }
    if (changes["filters"] || changes["mode"] || changes["queryId"]) {
      void this.loadPage();
    }
  }

  async loadPage(): Promise<void> {
    const requestId = ++this.requestId;
    this.loading = true;
    this.errorMessage = null;
    try {
      const response = await this.api.fetchEvents(this.filters, {
        limit: this.pageSize,
        offset: this.offset,
      }, this.mode);
      if (requestId !== this.requestId) return;
      if (
        response.features.length === 0
        && (response.metadata.total_count ?? response.metadata.count) > 0
        && this.offset >= (response.metadata.total_count ?? response.metadata.count)
      ) {
        const total = response.metadata.total_count ?? response.metadata.count;
        this.offset = Math.max(0, Math.floor((total - 1) / this.pageSize) * this.pageSize);
        await this.loadPage();
        return;
      }
      this.events = response;
    } catch (error) {
      if (requestId !== this.requestId) return;
      this.errorMessage = this.api.getError(error).message;
    } finally {
      if (requestId === this.requestId) this.loading = false;
    }
  }

  changePageSize(value: string): void {
    const pageSize = Number(value);
    if (!(this.pageSizes as readonly number[]).includes(pageSize)) {
      throw new TypeError("El tamaño de página debe ser 25, 50 o 100.");
    }
    this.pageSize = pageSize as 25 | 50 | 100;
    this.offset = 0;
    void this.loadPage();
  }

  previousPage(): void {
    if (this.offset === 0 || this.loading) return;
    this.offset = Math.max(0, this.offset - this.pageSize);
    void this.loadPage();
  }

  nextPage(): void {
    if (this.offset + this.pageSize >= this.totalCount || this.loading) return;
    this.offset += this.pageSize;
    void this.loadPage();
  }

  selectEvent(event: EventFeature): void {
    this.eventSelected.emit(event);
  }
}
