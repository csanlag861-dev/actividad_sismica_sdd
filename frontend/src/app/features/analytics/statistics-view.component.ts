import { AfterViewInit, Component, ElementRef, Input, OnChanges, OnDestroy, QueryList, ViewChildren } from "@angular/core";
import { BarChart } from "echarts/charts";
import { GridComponent, TooltipComponent } from "echarts/components";
import { init, use, ECharts } from "echarts/core";
import type { EChartsOption } from "echarts";
import { CanvasRenderer } from "echarts/renderers";
import { StatisticsResponse } from "../../core/models/api.models";

use([BarChart, GridComponent, TooltipComponent, CanvasRenderer]);

@Component({
  selector: "app-statistics-view",
  templateUrl: "./statistics-view.component.html",
  styleUrl: "./statistics-view.component.css",
})
export class StatisticsViewComponent implements AfterViewInit, OnChanges, OnDestroy {
  @Input({ required: true }) statistics!: StatisticsResponse;
  @ViewChildren("chart") private chartElements!: QueryList<ElementRef<HTMLDivElement>>;
  private charts: ECharts[] = [];
  private resizeObserver: ResizeObserver | null = null;
  private themeObserver: MutationObserver | null = null;
  private viewReady = false;

  get hasUnassignedCountry(): boolean {
    return this.statistics.country_counts.buckets.some((bucket) => bucket.country_id === null);
  }

  get effectiveFiltersLabel(): string {
    const { min_mag: minMagnitude, country_id: countryId } = this.statistics.filters;
    return [
      minMagnitude === null ? "Sin magnitud mínima" : `Magnitud mínima ≥ ${minMagnitude}`,
      countryId === null ? "Todos los países" : `País ${countryId}`,
    ].join(" · ");
  }

  ngAfterViewInit(): void {
    this.viewReady = true;
    this.charts = this.chartElements.map((element) => init(element.nativeElement, undefined, { renderer: "canvas" }));
    this.resizeObserver = new ResizeObserver(() => this.charts.forEach((chart) => chart.resize()));
    this.chartElements.forEach((element) => this.resizeObserver?.observe(element.nativeElement));
    this.themeObserver = new MutationObserver(() => this.renderCharts());
    this.themeObserver.observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
    this.renderCharts();
  }

  ngOnChanges(): void {
    if (this.viewReady) this.renderCharts();
  }

  ngOnDestroy(): void {
    this.resizeObserver?.disconnect();
    this.themeObserver?.disconnect();
    this.charts.forEach((chart) => chart.dispose());
  }

  private renderCharts(): void {
    if (this.charts.length !== 4) return;
    const textColor = getComputedStyle(document.documentElement).getPropertyValue("--color-text-secondary").trim();
    const gridColor = getComputedStyle(document.documentElement).getPropertyValue("--color-border").trim();
    const primaryColor = getComputedStyle(document.documentElement).getPropertyValue("--color-primary").trim();
    const axis = {
      axisLabel: { color: textColor, fontSize: 10 },
      axisLine: { lineStyle: { color: gridColor } },
      splitLine: { lineStyle: { color: gridColor, opacity: 0.55 } },
    };

    this.charts[0].setOption({
      tooltip: { trigger: "axis" },
      grid: { left: 36, right: 12, top: 18, bottom: 52 },
      xAxis: {
        type: "category",
        data: this.statistics.hourly_counts.buckets.map((bucket) => bucket.start),
        axisLabel: { ...axis.axisLabel, rotate: 35, formatter: (value: string) => value.slice(11, 16) },
        axisLine: axis.axisLine,
      },
      yAxis: { type: "value", ...axis },
      series: [{ type: "bar", data: this.statistics.hourly_counts.buckets.map((bucket) => bucket.count), itemStyle: { color: primaryColor } }],
    }, true);

    this.charts[1].setOption({
      tooltip: { trigger: "axis" },
      grid: { left: 100, right: 18, top: 14, bottom: 24 },
      xAxis: { type: "value", ...axis },
      yAxis: {
        type: "category",
        data: this.statistics.country_counts.buckets.map((bucket) => bucket.country_name),
        axisLabel: axis.axisLabel,
        axisLine: axis.axisLine,
      },
      series: [{ type: "bar", data: this.statistics.country_counts.buckets.map((bucket) => bucket.count), itemStyle: { color: primaryColor } }],
    }, true);

    this.charts[2].setOption(this.distributionOption(this.statistics.distributions.magnitude, primaryColor, axis));
    this.charts[3].setOption(this.distributionOption(this.statistics.distributions.depth_km, primaryColor, axis));
  }

  private distributionOption(
    distribution: StatisticsResponse["distributions"]["magnitude"],
    color: string,
    axis: { axisLabel: object; axisLine: object; splitLine: object },
  ): EChartsOption {
    return {
      tooltip: { trigger: "axis" },
      grid: { left: 38, right: 14, top: 18, bottom: 50 },
      xAxis: {
        type: "category",
        data: distribution.buckets.map((bucket) => `[${bucket.min_inclusive}, ${bucket.max_exclusive})`),
        axisLabel: { ...axis.axisLabel, rotate: 30 },
        axisLine: axis.axisLine,
      },
      yAxis: { type: "value", ...axis },
      series: [{ type: "bar", data: distribution.buckets.map((bucket) => bucket.count), itemStyle: { color } }],
    };
  }
}
