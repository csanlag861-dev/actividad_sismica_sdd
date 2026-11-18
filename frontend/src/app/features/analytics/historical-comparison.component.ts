import { Component, Input } from "@angular/core";
import { StatisticsResponse } from "../../core/models/api.models";

@Component({
  selector: "app-historical-comparison",
  templateUrl: "./historical-comparison.component.html",
  styleUrl: "./historical-comparison.component.css",
})
export class HistoricalComparisonComponent {
  @Input({ required: true }) statistics!: StatisticsResponse;

  formatNumber(value: number): string {
    return new Intl.NumberFormat("es-ES", { maximumFractionDigits: 2 }).format(value);
  }
}
