import { DatePipe } from "@angular/common";
import { Component, EventEmitter, Input, Output } from "@angular/core";
import { EventCollection } from "../../core/models/api.models";

@Component({
  selector: "app-events-table",
  imports: [DatePipe],
  templateUrl: "./events-table.component.html",
  styleUrl: "./events-table.component.css",
})
export class EventsTableComponent {
  @Input() events: EventCollection | null = null;
  @Input() selectedId: string | null = null;
  @Output() eventSelected = new EventEmitter<string>();
}
