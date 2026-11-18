import { Component, Input } from "@angular/core";
import { Distribution, StatisticsResponse } from "../../core/models/api.models";

@Component({
  selector: "app-distribution-summary",
  templateUrl: "./distribution-summary.component.html",
  styleUrl: "./distribution-summary.component.css",
})
export class DistributionSummaryComponent {
  @Input({ required: true }) statistics!: StatisticsResponse;

  barWidth(distribution: Distribution, count: number): number {
    const maxCount = Math.max(0, ...distribution.buckets.map((bucket) => bucket.count));
    return maxCount === 0 ? 0 : (count / maxCount) * 100;
  }
}
