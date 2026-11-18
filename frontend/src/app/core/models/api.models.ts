export interface EventFilters {
  start?: string;
  end?: string;
  min_mag?: number;
  country_id?: string;
}

export interface EventPageOptions {
  limit?: 25 | 50 | 100;
  offset?: number;
}

export interface EventFeature {
  type: "Feature";
  id: string;
  geometry: {
    type: "Point";
    coordinates: [longitude: number, latitude: number] | [
      longitude: number,
      latitude: number,
      depthKm: number,
    ];
  };
  properties: {
    mag: number | null;
    magType: string | null;
    place: string | null;
    depth_km: number | null;
    time: number;
    updated: number;
    country_id: string | null;
    country_name: string | null;
    traceability?: EventTraceability;
  };
}

export interface EventTraceability {
  mode: "live" | "replay";
  source: "usgs-live" | "usgs-replay" | null;
  ingested_at: number | null;
  ingestion_run_id: string | null;
}

export interface EventCollection {
  type: "FeatureCollection";
  metadata: {
    generated: number;
    last_ingestion: number | null;
    mode: string;
    count: number;
    truncated: boolean;
    total_count?: number;
    offset?: number;
    limit?: number;
  };
  features: EventFeature[];
}

export interface HealthResponse {
  status: "ok" | "unavailable";
  last_ingestion: number | null;
}

export interface Period {
  start: string;
  end: string;
}

export interface StatisticsResponse {
  period: Period;
  filters: {
    min_mag: number | null;
    country_id: string | null;
  };
  hourly_counts: {
    unit: string;
    missing_count: number;
    buckets: Array<{ start: string; count: number }>;
  };
  country_counts: {
    unit: string;
    missing_count: number;
    buckets: Array<{
      country_id: string | null;
      country_name: string;
      count: number;
    }>;
  };
  distributions: {
    magnitude: Distribution;
    depth_km: Distribution;
  };
  historical_comparison: {
    baseline_period: Period;
    baseline_days: number;
    baseline_available: boolean;
    current_count: number;
    current_period_days: number;
    current_daily_average: number;
    historical_daily_average: number | null;
    daily_rate_difference?: number;
    daily_rate_ratio?: number;
    unit: string;
  };
}

export type ComparisonMode = "live" | "replay";

export type ComparisonPopulation =
  | { type: "all" }
  | { type: "country"; country_id: string }
  | { type: "unassigned" };

export interface ComparisonGroupRequest {
  id: string;
  label: string;
  period: Period;
  population: ComparisonPopulation;
}

export interface TemporalComparisonRequest {
  mode: ComparisonMode;
  filters?: { min_mag?: number | null };
  groups: ComparisonGroupRequest[];
}

export interface ComparisonPopulationResult {
  type: "all" | "country" | "unassigned";
  country_id: string | null;
  country_name: string | null;
}

export interface ComparisonGroupResult {
  id: string;
  label: string;
  period: Period;
  population: ComparisonPopulationResult;
  coverage: {
    status: "complete" | "partial" | "unknown";
    covered_days: number;
    period_days: number;
  };
  observed_count: number;
  unavailable_metrics: Record<string, string>;
  daily_rate: number | null;
  distributions: {
    magnitude: Distribution | null;
    depth_km: Distribution | null;
  };
}

export interface ComparisonPairwiseDifference {
  first_group_id: string;
  second_group_id: string;
  observed_count_difference: number | null;
  daily_rate_difference: number | null;
  unavailable_reasons: Record<string, string>;
  distribution_percentage_point_differences: {
    magnitude: Array<{
      min_inclusive: number;
      max_exclusive: number;
      difference: number;
    }> | null;
    depth_km: Array<{
      min_inclusive: number;
      max_exclusive: number;
      difference: number;
    }> | null;
  };
}

export interface TemporalComparisonResponse {
  mode: ComparisonMode;
  filters: { min_mag: number | null };
  groups: ComparisonGroupResult[];
  pairwise_differences: ComparisonPairwiseDifference[];
}

export interface Distribution {
  unit: string;
  bin_width: number;
  valid_count: number;
  missing_count: number;
  buckets: Array<{
    min_inclusive: number;
    max_exclusive: number;
    count: number;
    percentage: number | null;
  }>;
}
