import {
  AfterViewInit,
  Component,
  ElementRef,
  EventEmitter,
  Input,
  OnChanges,
  OnDestroy,
  Output,
  SimpleChanges,
  ViewChild,
} from "@angular/core";
import * as L from "leaflet";
import { EventCollection } from "../../core/models/api.models";
import {
  depthColor,
  depthLegend,
  eventCoordinates,
  hasValidEventCoordinates,
  markerRadius,
} from "./event-map.utils";
import { MapLayersService } from "./map-layers.service";

@Component({
  selector: "app-event-map",
  templateUrl: "./event-map.component.html",
  styleUrl: "./event-map.component.css",
})
export class EventMapComponent implements AfterViewInit, OnChanges, OnDestroy {
  @Input() events: EventCollection | null = null;
  @Input() selectedId: string | null = null;
  @Output() eventSelected = new EventEmitter<string>();
  @ViewChild("mapContainer", { static: true }) private mapContainer!: ElementRef<HTMLElement>;

  readonly depthLegend = depthLegend;
  mapError: string | null = null;
  private map: L.Map | null = null;
  private markers: L.LayerGroup | null = null;

  constructor(private readonly layers: MapLayersService) {}

  get maxDepth(): number | null {
    const depths = (this.events?.features ?? [])
      .map((event) => event.properties.depth_km)
      .filter((depth): depth is number => depth !== null && Number.isFinite(depth));
    return depths.length ? Math.max(...depths) : null;
  }

  get hasNegativeDepth(): boolean {
    return (this.events?.features ?? []).some((event) => {
      const depth = event.properties.depth_km;
      return depth !== null && Number.isFinite(depth) && depth < 0;
    });
  }

  ngAfterViewInit(): void {
    this.map = this.layers.createMap(this.mapContainer.nativeElement);
    this.markers = L.layerGroup().addTo(this.map);
    void this.layers.addCountryBoundaries(this.map).catch((error: unknown) => {
      this.mapError = error instanceof Error ? error.message : "No se pudieron cargar las fronteras.";
    });
    this.updateMarkers();
    setTimeout(() => this.map?.invalidateSize(), 0);
  }

  ngOnChanges(_changes: SimpleChanges): void {
    this.updateMarkers();
  }

  ngOnDestroy(): void {
    this.map?.remove();
    this.map = null;
  }

  private updateMarkers(): void {
    if (!this.map || !this.markers) return;
    this.markers.clearLayers();
    for (const event of this.events?.features ?? []) {
      const [latitude, longitude] = eventCoordinates(event);
      if (!hasValidEventCoordinates(event)) continue;
      const missingMagnitude = event.properties.mag === null;
      const marker = L.circleMarker([latitude, longitude], {
        radius: markerRadius(event.properties.mag) + (event.id === this.selectedId ? 2 : 0),
        color: missingMagnitude ? "var(--color-text-primary)" : depthColor(event.properties.depth_km),
        fillColor: depthColor(event.properties.depth_km),
        fillOpacity: missingMagnitude ? 0.35 : 0.82,
        dashArray: missingMagnitude ? "3 2" : undefined,
        weight: event.id === this.selectedId ? 3 : 1,
      })
        .bindTooltip(event.properties.place ?? "Ubicación desconocida")
        .on("click", () => this.eventSelected.emit(event.id));
      marker.addTo(this.markers);
    }
  }
}
