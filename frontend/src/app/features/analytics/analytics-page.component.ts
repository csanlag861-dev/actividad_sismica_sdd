import { DatePipe } from "@angular/common";
import { Component } from "@angular/core";
import { EventFiltersComponent } from "../events/event-filters.component";
import { QueryStateService } from "../../core/state/query-state.service";
import { HistoricalComparisonComponent } from "./historical-comparison.component";
import { StatisticsViewComponent } from "./statistics-view.component";
import { ResourceStatusComponent } from "../../shared/status/resource-status.component";

@Component({
  selector: "app-analytics-page",
  imports: [
    DatePipe,
    EventFiltersComponent,
    HistoricalComparisonComponent,
    StatisticsViewComponent,
    ResourceStatusComponent,
  ],
  templateUrl: "./analytics-page.component.html",
  styleUrl: "./analytics-page.component.css",
})
export class AnalyticsPageComponent {
  constructor(readonly queries: QueryStateService) {}
}
