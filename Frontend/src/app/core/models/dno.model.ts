/**
 * FloodWatch AI — Phase 7E: Chennai Hydrodynamic DNO Models
 * TypeScript interfaces matching backend/app/schemas/dno.py Pydantic contract
 */

export interface DNOGridMetadata {
  crs: string;
  domain_name: string;
  width: number;
  height: number;
  cell_size_meters: number;
  cell_area_m2: number;
  bounds_utm44n: number[];
  bounds_wgs84: {
    min_lat: number;
    max_lat: number;
    min_lon: number;
    max_lon: number;
  };
}

export interface DNOModelMetadata {
  model_name: string;
  phase: string;
  alpha: number;
  threshold_m: number;
  loss_type: string;
  training_horizon: string;
  forecast_horizon_minutes: number;
  timestep_minutes: number;
  units: {
    water_depth: string;
    velocity_u: string;
    velocity_v: string;
    velocity_magnitude: string;
  };
}

export interface DepthSeverityBins {
  dry_under_5cm: number;
  low_5_to_10cm: number;
  minor_10_to_20cm: number;
  moderate_20_to_50cm: number;
  severe_50cm_to_1m: number;
  very_severe_1_to_2m: number;
  extreme_over_2m: number;
}

export interface FloodExtentThresholds {
  cells_gt_0_05m: number;
  area_m2_gt_0_05m: number;
  cells_gt_0_10m: number;
  area_m2_gt_0_10m: number;
  cells_gt_0_20m: number;
  area_m2_gt_0_20m: number;
  cells_gt_0_50m: number;
  area_m2_gt_0_50m: number;
  cells_gt_1_00m: number;
  area_m2_gt_1_00m: number;
}

export interface DNOTimestepForecast {
  lead_minutes: number;
  timestep_index: number;
  max_depth_m: number;
  mean_depth_m: number;
  flooded_area_m2: number;
  max_velocity_mps: number;
  mean_velocity_mps: number;
  flood_extent: FloodExtentThresholds;
  depth_severity_cells: DepthSeverityBins;
}

export interface DNOPredictRequest {
  event_id: string;
  include_spatial_grids?: boolean;
  target_lead_minutes_spatial?: number | null;
}

export interface DNOPredictResponse {
  model: string;
  model_version: string;
  input_mode: string;
  event_id: string;
  forecast_horizon_minutes: number;
  timestep_minutes: number;
  num_timesteps: number;
  grid: DNOGridMetadata;
  model_metadata: DNOModelMetadata;
  summary: {
    peak_depth_m: number;
    peak_velocity_mps: number;
    peak_flooded_area_m2: number;
    peak_flooded_area_km2: number;
    total_domain_area_km2: number;
  };
  forecasts: DNOTimestepForecast[];
  spatial_grids?: {
    lead_minutes: number;
    timestep_index: number;
    depth_m: number[][];
    velocity_mps: number[][];
  } | null;
  diagnostics: {
    device: string;
    inference_latency_ms: number;
    postprocessing_latency_ms: number;
    total_latency_ms: number;
    nan_detected: boolean;
    inf_detected: boolean;
    model_load_latency_ms?: number;
  };
  disclaimer: string;
}

export interface DNOHealthResponse {
  status: string;
  model_loaded: boolean;
  model_name: string;
  model_version: string;
  checkpoint_sha256: string;
  checkpoint_size_bytes: number;
  device: string;
  horizon_minutes: number;
  timestep_minutes: number;
  memory_diagnostics: {
    device: string;
    cuda_vram_allocated_mb?: number | null;
    model_load_ms: number;
  };
  production_separation: string;
  disclaimer: string;
}

export interface PreparedStormEvent {
  id: string;
  category: string;
  rainfall_mm: number;
  peak_intensity_mm_h: number;
  profile: string;
  input_tensor_exists: boolean;
  target_tensor_exists: boolean;
}

export interface DNOEventsResponse {
  total_events: number;
  events: PreparedStormEvent[];
  note: string;
}

export interface DNOGeoJsonFeatureProperties {
  grid_row: number;
  grid_col: number;
  depth_m: number;
  velocity_mps: number;
  severity: string;
  lead_minutes: number;
  event_id: string;
}

export interface DNOGeoJsonResponse {
  type: 'FeatureCollection';
  crs?: any;
  properties: {
    event_id: string;
    lead_minutes: number;
    threshold_m: number;
    total_inundated_cells: number;
    crs_source: string;
    disclaimer: string;
  };
  features: Array<{
    type: 'Feature';
    geometry: {
      type: 'Polygon';
      coordinates: number[][][];
    };
    properties: DNOGeoJsonFeatureProperties;
  }>;
}
