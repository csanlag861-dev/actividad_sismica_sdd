export interface EventFilters {
  start?: string;
  end?: string;
  min_mag?: number;
  country_id?: string;
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
