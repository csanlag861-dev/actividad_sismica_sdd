import { DatePipe } from "@angular/common";
import { Component, Input } from "@angular/core";
import { StatisticsResponse } from "../../core/models/api.models";

@Component({
  selector: "app-activity-timeline",
  imports: [DatePipe],
  templateUrl: "./activity-timeline.component.html",
  styleUrl: "./activity-timeline.component.css",
})
export class ActivityTimelineComponent {
  @Input({ required: true }) statistics!: StatisticsResponse;

  get maxCount(): number {
    return Math.max(0, ...this.statistics.hourly_counts.buckets.map((bucket) => bucket.count));
  }

  barHeight(count: number): number {
    return this.maxCount === 0 ? 0 : (count / this.maxCount) * 100;
  }
}
