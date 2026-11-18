import { DatePipe, DecimalPipe, KeyValuePipe } from "@angular/common";
import { Component, OnInit, inject } from "@angular/core";
import { FormsModule } from "@angular/forms";
import {
  ComparisonPopulation,
  ComparisonGroupResult,
  TemporalComparisonRequest,
  TemporalComparisonResponse,
} from "../../core/models/api.models";
import { ObservatoryApiService } from "../../core/api/observatory-api.service";
import { CountryCatalogService } from "../events/country-catalog.service";

type PopulationType = ComparisonPopulation["type"];

interface ComparisonFormGroup {
  id: string;
  label: string;
  start: string;
  end: string;
  populationType: PopulationType;
  countryId: string;
}

@Component({
  selector: "app-temporal-comparison",
  imports: [DatePipe, DecimalPipe, FormsModule, KeyValuePipe],
  templateUrl: "./temporal-comparison.component.html",
  styleUrl: "./temporal-comparison.component.css",
})
export class TemporalComparisonComponent implements OnInit {
  readonly catalog = inject(CountryCatalogService);
  readonly metricNames = ["magnitude", "depth_km"] as const;
  mode: "live" | "replay" = "live";
  minimumMagnitude: number | null = null;
  groups: ComparisonFormGroup[] = this.initialGroups();
  result: TemporalComparisonResponse | null = null;
  loading = false;
  errorMessage: string | null = null;
  catalogError: string | null = null;

  private readonly api = inject(ObservatoryApiService);

  async ngOnInit(): Promise<void> {
    try {
      await this.catalog.load();
    } catch (error) {
      this.catalogError = error instanceof Error ? error.message : "No se pudo cargar el catálogo de países.";
    }
  }

  addGroup(): void {
    if (this.groups.length >= 5) return;
    const index = this.groups.length + 1;
    const period = this.defaultPeriod(index - 1);
    this.groups = [
      ...this.groups,
      {
        id: `grupo-${index}`,
        label: `Grupo ${index}`,
        ...period,
        populationType: "all",
        countryId: "",
      },
    ];
  }

  removeGroup(index: number): void {
    if (this.groups.length <= 2) return;
    this.groups = this.groups.filter((_group, groupIndex) => groupIndex !== index);
  }

  async compare(): Promise<void> {
    this.errorMessage = null;
    this.result = null;
    const request = this.buildRequest();
    if (!request) return;

    this.loading = true;
    try {
      this.result = await this.api.fetchComparison(request);
    } catch (error) {
      this.errorMessage = this.api.getError(error).message;
    } finally {
      this.loading = false;
    }
  }

  metricReason(group: ComparisonGroupResult, metric: string): string | null {
    return group.unavailable_metrics[metric] ?? null;
  }

  private buildRequest(): TemporalComparisonRequest | null {
    const ids = new Set<string>();
    const labels = new Set<string>();
    const groups: TemporalComparisonRequest["groups"] = [];
    for (const [index, group] of this.groups.entries()) {
      if (!group.id.trim() || ids.has(group.id)) {
        this.errorMessage = `El identificador del grupo ${index + 1} debe ser único y no estar vacío.`;
        return null;
      }
      if (!group.label.trim() || labels.has(group.label)) {
        this.errorMessage = `La etiqueta del grupo ${index + 1} debe ser única y no estar vacía.`;
        return null;
      }
      ids.add(group.id);
      labels.add(group.label);
      if (!group.start || !group.end) {
        this.errorMessage = `Indica el inicio y el fin del periodo del grupo ${index + 1} en UTC.`;
        return null;
      }
      const start = new Date(`${group.start}:00Z`);
      const end = new Date(`${group.end}:00Z`);
      if (!Number.isFinite(start.getTime()) || !Number.isFinite(end.getTime()) || start >= end) {
        this.errorMessage = `El periodo del grupo ${index + 1} debe ser válido y tener inicio anterior al fin.`;
        return null;
      }

      let population: ComparisonPopulation;
      if (group.populationType === "country") {
        if (!group.countryId) {
          this.errorMessage = `Selecciona un país para el grupo ${index + 1}.`;
          return null;
        }
        population = { type: "country", country_id: group.countryId };
      } else {
        population = { type: group.populationType };
      }
      groups.push({
        id: group.id,
        label: group.label,
        period: { start: start.toISOString(), end: end.toISOString() },
        population,
      });
    }

    if (this.minimumMagnitude !== null && !Number.isFinite(this.minimumMagnitude)) {
      this.errorMessage = "La magnitud mínima debe ser un número finito.";
      return null;
    }
    return {
      mode: this.mode,
      filters: { min_mag: this.minimumMagnitude },
      groups,
    };
  }

  private initialGroups(): ComparisonFormGroup[] {
    return [this.defaultGroup(0), this.defaultGroup(1)];
  }

  private defaultGroup(index: number): ComparisonFormGroup {
    const period = this.defaultPeriod(index);
    return {
      id: `grupo-${index + 1}`,
      label: `Grupo ${index + 1}`,
      ...period,
      populationType: "all",
      countryId: "",
    };
  }

  private defaultPeriod(daysAgo: number): Pick<ComparisonFormGroup, "start" | "end"> {
    const end = new Date();
    end.setUTCMinutes(0, 0, 0);
    end.setUTCHours(0);
    end.setUTCDate(end.getUTCDate() - daysAgo);
    const start = new Date(end);
    start.setUTCDate(start.getUTCDate() - 1);
    const localInputValue = (date: Date) => date.toISOString().slice(0, 16);
    return { start: localInputValue(start), end: localInputValue(end) };
  }
}
