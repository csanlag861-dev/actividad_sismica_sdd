import { Component, Input } from "@angular/core";
import { ResourceSnapshot } from "../../core/models/ui-state.models";

@Component({
  selector: "app-resource-status",
  templateUrl: "./resource-status.component.html",
  styleUrl: "./resource-status.component.css",
})
export class ResourceStatusComponent {
  @Input({ required: true }) snapshot!: ResourceSnapshot<unknown>;
  @Input() label = "recurso";
  @Input() empty = false;
  @Input() truncated = false;
}
