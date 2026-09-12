from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field

class DNOGridMetadata(BaseModel):
    crs: str = Field(default="EPSG:32644", description="Coordinate Reference System (UTM Zone 44N)")
    domain_name: str = Field(default="Adyar–Velachery Basin (Greater Chennai)", description="Hydrodynamic pilot catchment")
    width: int = Field(default=128, description="Grid width in cells")
    height: int = Field(default=128, description="Grid height in cells")
    cell_size_meters: float = Field(default=78.125, description="Spatial resolution per cell side")
    cell_area_m2: float = Field(default=6103.515625, description="Physical footprint area per cell")
    bounds_utm44n: List[float] = Field(
        default=[410000.0, 1431000.0, 420000.0, 1441000.0],
        description="Bounding box in EPSG:32644 [xmin, ymin, xmax, ymax]"
    )
    bounds_wgs84: Dict[str, float] = Field(
        default={"min_lat": 12.943196, "max_lat": 13.033893, "min_lon": 80.170273, "max_lon": 80.262192},
        description="Bounding box in WGS84 coordinates"
    )

class DNOModelMetadata(BaseModel):
    model_name: str = "Chennai Urban Flood DNO"
    phase: str = "Phase 7C"
    alpha: float = 1.00
    threshold_m: float = 0.15
    loss_type: str = "Thresholded dual-regime depth-weighted loss"
    training_horizon: str = "120 minutes (24 x 5-min intervals)"
    forecast_horizon_minutes: int = 120
    timestep_minutes: int = 5
    units: Dict[str, str] = {
        "water_depth": "meters",
        "velocity_u": "m/s",
        "velocity_v": "m/s",
        "velocity_magnitude": "m/s"
    }

class DepthSeverityBins(BaseModel):
    dry_under_5cm: int = Field(..., description="Cells < 0.05m (effectively dry/thin wetting)")
    low_5_to_10cm: int = Field(..., description="Cells 0.05 - 0.10m")
    minor_10_to_20cm: int = Field(..., description="Cells 0.10 - 0.20m")
    moderate_20_to_50cm: int = Field(..., description="Cells 0.20 - 0.50m")
    severe_50cm_to_1m: int = Field(..., description="Cells 0.50 - 1.00m")
    very_severe_1_to_2m: int = Field(..., description="Cells 1.00 - 2.00m")
    extreme_over_2m: int = Field(..., description="Cells > 2.00m (deep pooling)")

class FloodExtentThresholds(BaseModel):
    cells_gt_0_05m: int
    area_m2_gt_0_05m: float
    cells_gt_0_10m: int
    area_m2_gt_0_10m: float
    cells_gt_0_20m: int
    area_m2_gt_0_20m: float
    cells_gt_0_50m: int
    area_m2_gt_0_50m: float
    cells_gt_1_00m: int
    area_m2_gt_1_00m: float

class DNOTimestepForecast(BaseModel):
    lead_minutes: int = Field(..., description="Forecast lead time in minutes (5, 10, ..., 120)")
    timestep_index: int = Field(..., description="Timestep sequence index (1 to 24)")
    max_depth_m: float = Field(..., description="Domain peak water depth in meters")
    mean_depth_m: float = Field(..., description="Domain mean water depth in meters")
    flooded_area_m2: float = Field(..., description="Total inundated area above 0.05m threshold in m2")
    max_velocity_mps: float = Field(..., description="Peak velocity magnitude in m/s")
    mean_velocity_mps: float = Field(..., description="Mean velocity magnitude in m/s")
    flood_extent: FloodExtentThresholds
    depth_severity_cells: DepthSeverityBins

class DNOPredictRequest(BaseModel):
    event_id: str = Field(default="storm_011", description="Prepared storm event identifier from library (e.g., storm_011, storm_016, storm_007)")
    include_spatial_grids: bool = Field(default=False, description="Optionally include 2D depth/velocity matrices (large payload)")
    target_lead_minutes_spatial: Optional[int] = Field(default=None, description="If include_spatial_grids is True, return spatial grids for this specific lead minute (e.g. 60 or 120)")

class DNOPredictResponse(BaseModel):
    model: str = "chennai_phase7c_dno"
    model_version: str = "phase7c-alpha1.00"
    input_mode: str = "prepared"
    event_id: str
    forecast_horizon_minutes: int = 120
    timestep_minutes: int = 5
    num_timesteps: int = 24
    grid: DNOGridMetadata
    model_metadata: DNOModelMetadata
    summary: Dict[str, Any]
    forecasts: List[DNOTimestepForecast]
    spatial_grids: Optional[Dict[str, Any]] = None
    diagnostics: Dict[str, Any]
    disclaimer: str

class DNOHealthResponse(BaseModel):
    status: str = "ok"
    model_loaded: bool
    model_name: str
    model_version: str
    checkpoint_sha256: str
    checkpoint_size_bytes: int
    device: str
    horizon_minutes: int = 120
    timestep_minutes: int = 5
    memory_diagnostics: Dict[str, Any]
    production_separation: str
    disclaimer: str

class PreparedStormEvent(BaseModel):
    id: str
    category: str
    rainfall_mm: float
    peak_intensity_mm_h: float
    profile: str
    input_tensor_exists: bool
    target_tensor_exists: bool

class DNOEventsResponse(BaseModel):
    total_events: int
    events: List[PreparedStormEvent]
    note: str
