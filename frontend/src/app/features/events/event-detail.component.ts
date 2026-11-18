import { DatePipe } from "@angular/common";
import { Component, Input } from "@angular/core";
import { EventFeature } from "../../core/models/api.models";

@Component({
  selector: "app-event-detail",
  imports: [DatePipe],
  templateUrl: "./event-detail.component.html",
  styleUrl: "./event-detail.component.css",
})
export class EventDetailComponent {
  @Input() event: EventFeature | null = null;

  get coordinateText(): string {
    if (!this.event) return "Desconocidas";
    const [longitude, latitude] = this.event.geometry.coordinates;
    return `${latitude.toFixed(4)}° lat, ${longitude.toFixed(4)}° lon`;
  }

  get modeLabel(): string {
    const mode = this.event?.properties.traceability?.mode;
    if (mode === "live") return "Tiempo real";
    if (mode === "replay") return "Reproducción";
    return "No disponible";
  }
}
