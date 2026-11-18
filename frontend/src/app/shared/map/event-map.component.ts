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
import type { Feature, FeatureCollection, Point } from "geojson";
import type { GeoJSONSource, Map as MapLibreMap } from "maplibre-gl";
import type { MapLibreOverlay } from "@deck.gl/maplibre";
import type { HexagonLayer } from "@deck.gl/aggregation-layers";
import { EventCollection, EventFeature } from "../../core/models/api.models";
import {
  depthColor,
  depthLegend,
  hasValidEventCoordinates,
  latestEventIds,
  markerRadius,
} from "./event-map.utils";
import { MapLayersService } from "./map-layers.service";

interface EventMapProperties {
  eventId: string;
  place: string;
  time: number;
  radius: number;
  depthColor: string;
  latest: boolean;
  selected: boolean;
}

const EVENT_SOURCE = "seismic-events";
const EVENT_LAYER = "seismic-events-points";
const LATEST_LAYER = "seismic-events-latest";

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
  deckError: string | null = null;
  deckLoading = false;
  private map: MapLibreMap | null = null;
  private deckOverlay: MapLibreOverlay | null = null;
  private hexagonLayerFactory: (() => HexagonLayer<EventFeature>) | null = null;
  private deckRequestId = 0;
  private destroyed = false;

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

  get latestCount(): number {
    return latestEventIds(this.events?.features ?? []).size;
  }

  get isTruncated(): boolean {
    const metadata = this.events?.metadata;
    return Boolean(
      metadata?.truncated
      || (metadata?.total_count !== undefined && metadata.total_count > (this.events?.features.length ?? 0)),
    );
  }

  get totalCount(): number {
    return this.events?.metadata.total_count ?? this.events?.metadata.count ?? 0;
  }

  get densityEnabled(): boolean {
    return this.deckOverlay !== null;
  }

  ngAfterViewInit(): void {
    void this.initializeMap();
  }

  private async initializeMap(): Promise<void> {
    try {
      const map = await this.layers.createMap(this.mapContainer.nativeElement);
      if (this.destroyed) {
        map.remove();
        return;
      }
      this.map = map;
      map.on("error", (event) => {
        this.mapError = event.error.message;
      });
      map.on("load", () => this.initializeMapLayers(map));
      setTimeout(() => {
        if (this.map === map) map.resize();
      }, 0);
    } catch (error) {
      this.mapError = error instanceof Error ? error.message : "No se pudo inicializar el mapa.";
    }
  }

  ngOnChanges(_changes: SimpleChanges): void {
    this.updateEventSource();
    if (this.deckOverlay && this.hexagonLayerFactory) {
      this.deckOverlay.setProps({ layers: [this.hexagonLayerFactory()] });
    }
  }

  ngOnDestroy(): void {
    this.destroyed = true;
    this.deckRequestId += 1;
    this.deckOverlay?.finalize();
    this.deckOverlay = null;
    this.hexagonLayerFactory = null;
    this.map?.remove();
    this.map = null;
  }

  async toggleDensity(): Promise<void> {
    if (this.deckOverlay) {
      this.deckOverlay.finalize();
      this.deckOverlay = null;
      this.hexagonLayerFactory = null;
      this.deckError = null;
      return;
    }
    if (!this.map || this.deckLoading) return;

    const requestId = ++this.deckRequestId;
    this.deckLoading = true;
    this.deckError = null;
    try {
      const [{ MapLibreOverlay }, { HexagonLayer }] = await Promise.all([
        import("@deck.gl/maplibre"),
        import("@deck.gl/aggregation-layers"),
      ]);
      if (this.destroyed || requestId !== this.deckRequestId || !this.map) return;
      const createHexagonLayer = () => new HexagonLayer<EventFeature>({
        id: "seismic-event-hexagons",
        data: (this.events?.features ?? []).filter(hasValidEventCoordinates),
        getPosition: (event: EventFeature) => [
          event.geometry.coordinates[0],
          event.geometry.coordinates[1],
        ],
        radius: 50_000,
        extruded: true,
        elevationScale: 4,
        coverage: 0.88,
        pickable: true,
      });
      this.hexagonLayerFactory = createHexagonLayer;
      const overlay = new MapLibreOverlay({
        interleaved: true,
        layers: [createHexagonLayer()],
      });
      this.map.addControl(overlay);
      this.deckOverlay = overlay;
    } catch (error) {
      this.hexagonLayerFactory = null;
      if (requestId === this.deckRequestId) {
        this.deckError = error instanceof Error
          ? error.message
          : "No se pudo cargar la visualización avanzada.";
      }
    } finally {
      if (requestId === this.deckRequestId) this.deckLoading = false;
    }
  }

  private initializeMapLayers(map: MapLibreMap): void {
    if (this.map !== map) return;
    try {
      map.addSource(EVENT_SOURCE, {
        type: "geojson",
        data: this.toMapFeatures(),
      });
      map.addLayer({
        id: LATEST_LAYER,
        type: "circle",
        source: EVENT_SOURCE,
        filter: ["==", ["get", "latest"], true],
        paint: {
          "circle-radius": 15,
          "circle-color": "#dc3b32",
          "circle-opacity": 0.18,
          "circle-stroke-color": "#b42318",
          "circle-stroke-width": 2,
        },
      });
      map.addLayer({
        id: EVENT_LAYER,
        type: "circle",
        source: EVENT_SOURCE,
        paint: {
          "circle-radius": ["get", "radius"],
          "circle-color": ["get", "depthColor"],
          "circle-opacity": 0.86,
          "circle-stroke-color": [
            "case",
            ["get", "selected"],
            "#ffffff",
            ["get", "latest"],
            "#b42318",
            "#49372d",
          ],
          "circle-stroke-width": [
            "case",
            ["get", "selected"],
            3,
            ["get", "latest"],
            2,
            1,
          ],
        },
      });
      map.on("click", EVENT_LAYER, (event) => {
        const eventId = event.features?.[0]?.properties?.["eventId"];
        if (typeof eventId === "string") this.eventSelected.emit(eventId);
      });
      map.on("mouseenter", EVENT_LAYER, () => {
        map.getCanvas().style.cursor = "pointer";
      });
      map.on("mouseleave", EVENT_LAYER, () => {
        map.getCanvas().style.cursor = "";
      });
      void this.layers.addCountryBoundaries(map, () => this.map === map).catch((error: unknown) => {
        if (this.map === map) {
          this.mapError = error instanceof Error ? error.message : "No se pudieron cargar las fronteras.";
        }
      });
      this.updateEventSource();
    } catch (error) {
      this.mapError = error instanceof Error ? error.message : "No se pudo inicializar el mapa.";
    }
  }

  private updateEventSource(): void {
    if (!this.map?.isStyleLoaded()) return;
    const source = this.map.getSource(EVENT_SOURCE) as GeoJSONSource | undefined;
    source?.setData(this.toMapFeatures());
  }

  private toMapFeatures(): FeatureCollection<Point, EventMapProperties> {
    const latestIds = latestEventIds(this.events?.features ?? []);
    const features = (this.events?.features ?? [])
      .filter(hasValidEventCoordinates)
      .map((event: EventFeature): Feature<Point, EventMapProperties> => {
        const [longitude, latitude] = event.geometry.coordinates;
        return {
          type: "Feature",
          id: event.id,
          geometry: { type: "Point", coordinates: [longitude, latitude] },
          properties: {
            eventId: event.id,
            place: event.properties.place ?? "Ubicación desconocida",
            time: event.properties.time,
            radius: markerRadius(event.properties.mag),
            depthColor: depthColor(event.properties.depth_km),
            latest: latestIds.has(event.id),
            selected: event.id === this.selectedId,
          },
        };
      });
    return { type: "FeatureCollection", features };
  }
}
