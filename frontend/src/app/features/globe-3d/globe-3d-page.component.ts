import { AfterViewInit, Component, ElementRef, OnDestroy, ViewChild, effect } from "@angular/core";
import { RouterLink } from "@angular/router";
import type { Entity, Viewer } from "cesium";
import { EventCollection, EventFeature } from "../../core/models/api.models";
import { ObservatoryApiService } from "../../core/api/observatory-api.service";
import { QueryStateService } from "../../core/state/query-state.service";
import { EventDetailComponent } from "../events/event-detail.component";
import { EventFiltersComponent } from "../events/event-filters.component";
import { Globe3DViewerService } from "./globe-3d-viewer.service";
import { globeEventMarkers } from "./globe-3d.utils";
import { depthLegend, hasValidEventCoordinates } from "../../shared/map/event-map.utils";

type LoadStatus = "loading" | "success" | "error";

@Component({
  selector: "app-globe-3d-page",
  imports: [EventDetailComponent, EventFiltersComponent, RouterLink],
  templateUrl: "./globe-3d-page.component.html",
  styleUrl: "./globe-3d-page.component.css",
})
export class Globe3DPageComponent implements AfterViewInit, OnDestroy {
  @ViewChild("globeContainer") private globeContainer!: ElementRef<HTMLElement>;
  readonly depthLegend = depthLegend;

  events: EventCollection | null = null;
  selectedEvent: EventFeature | null = null;
  eventStatus: LoadStatus = "loading";
  eventError: string | null = null;
  viewerError: string | null = null;
  private viewer: Viewer | null = null;
  private readonly eventEntities = new Map<string, Entity>();
  private requestId = 0;
  private destroyed = false;

  constructor(
    private readonly api: ObservatoryApiService,
    readonly queries: QueryStateService,
    private readonly globeViewer: Globe3DViewerService,
  ) {
    effect(() => {
      void this.loadEvents(this.queries.filters());
    });
  }

  get totalCount(): number {
    return this.events?.metadata.total_count ?? this.events?.metadata.count ?? 0;
  }

  get isTruncated(): boolean {
    return Boolean(
      this.events?.metadata.truncated
      || (this.events?.metadata.total_count !== undefined
        && this.events.metadata.total_count > (this.events?.features.length ?? 0)),
    );
  }

  get maxDepth(): number | null {
    const depths = (this.events?.features ?? [])
      .map((event) => event.properties.depth_km)
      .filter((depth): depth is number => depth !== null && Number.isFinite(depth));
    return depths.length ? Math.max(...depths) : null;
  }

  get invalidLocationCount(): number {
    return (this.events?.features ?? []).filter((event) => !hasValidEventCoordinates(event)).length;
  }

  ngAfterViewInit(): void {
    void this.initializeViewer();
  }

  async retry(): Promise<void> {
    this.viewerError = null;
    if (!this.viewer) await this.initializeViewer();
    await this.loadEvents(this.queries.filters());
  }

  ngOnDestroy(): void {
    this.destroyed = true;
    this.requestId += 1;
    this.globeViewer.destroy(this.viewer);
    this.viewer = null;
    this.eventEntities.clear();
  }

  selectEvent(eventId: string): void {
    this.selectedEvent = this.events?.features.find((event) => event.id === eventId) ?? null;
    const entity = this.eventEntities.get(eventId);
    if (entity && this.viewer && this.viewer.selectedEntity !== entity) {
      this.viewer.selectedEntity = entity;
    }
  }

  private async loadEvents(filters: ReturnType<QueryStateService["filters"]>): Promise<void> {
    const requestId = ++this.requestId;
    this.eventStatus = "loading";
    this.eventError = null;
    try {
      const events = await this.api.fetchAllEvents(filters);
      if (this.destroyed || requestId !== this.requestId) return;
      this.events = events;
      this.eventStatus = "success";
      this.drawEvents();
    } catch (error) {
      if (this.destroyed || requestId !== this.requestId) return;
      this.eventError = this.api.getError(error).message;
      this.eventStatus = "error";
    }
  }

  private async initializeViewer(): Promise<void> {
    if (this.destroyed || this.viewer) return;
    try {
      this.viewer = await this.globeViewer.createViewer(this.globeContainer.nativeElement);
      if (this.destroyed) {
        this.globeViewer.destroy(this.viewer);
        this.viewer = null;
        return;
      }
      this.viewer.selectedEntityChanged.addEventListener((entity) => {
        const eventId = entity?.id;
        this.selectedEvent = typeof eventId === "string"
          ? this.events?.features.find((event) => event.id === eventId) ?? null
          : null;
      });
      this.viewer.scene.renderError.addEventListener((_scene, error) => this.handleViewerFailure(error));
      this.viewerError = null;
      this.drawEvents();
    } catch (error) {
      this.viewerError = error instanceof Error ? error.message : "No se pudo inicializar el globo 3D.";
      this.globeViewer.destroy(this.viewer);
      this.viewer = null;
    }
  }

  handleViewerFailure(error: unknown): void {
    this.viewerError = error instanceof Error ? error.message : "CesiumJS encontró un error de renderizado.";
    this.globeViewer.destroy(this.viewer);
    this.viewer = null;
    this.eventEntities.clear();
  }

  private drawEvents(): void {
    if (!this.viewer || !this.events) return;
    const Cesium = this.globeViewer.library;
    this.viewer.entities.removeAll();
    this.eventEntities.clear();
    for (const marker of globeEventMarkers(this.events.features)) {
      const { event, coordinates, color, pixelSize, latest } = marker;
      const entity = this.viewer.entities.add({
        id: event.id,
        name: event.properties.place ?? "Ubicación desconocida",
        position: Cesium.Cartesian3.fromDegrees(...coordinates),
        point: {
          pixelSize,
          color: Cesium.Color.fromCssColorString(color),
          outlineColor: Cesium.Color.WHITE,
          outlineWidth: latest ? 3 : 1,
          heightReference: Cesium.HeightReference.CLAMP_TO_GROUND,
        },
        label: latest
          ? {
            text: "Último evento",
            font: "12px sans-serif",
            pixelOffset: new Cesium.Cartesian2(0, -20),
            showBackground: true,
            backgroundColor: Cesium.Color.fromCssColorString("#211a17"),
            fillColor: Cesium.Color.WHITE,
            heightReference: Cesium.HeightReference.CLAMP_TO_GROUND,
            disableDepthTestDistance: 0,
          }
          : undefined,
      });
      this.eventEntities.set(event.id, entity);
    }
  }
}
