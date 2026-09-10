"""
Rainfall and Radar Telemetry Schemas
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from backend.app.schemas.provenance import ProvenanceStatus


class RainfallReadingSchema(BaseModel):
    station_id: str
    station_name: str
    latitude: float
    longitude: float
    value: float = Field(..., description="Rainfall reading value")
    unit: str = Field(default="mm", description="Precipitation unit")
    accumulation_window: str = Field(default="1h", description="Accumulation period (e.g. 1h, 24h)")
    source: str = Field(default="GCC/IMD Rain Gauge Network")
    timestamp: str
    status: ProvenanceStatus = Field(default=ProvenanceStatus.OBSERVED)


class RadarCellOverlay(BaseModel):
    center: List[float] = Field(..., description="[lat, lon]")
    radius_meters: float
    intensity_mm_per_hr: float
    color_hex: str
    label: str
    source: str
    timestamp: str
    status: ProvenanceStatus


class RadarMetadataSchema(BaseModel):
    station_name: str = Field(default="IMD Chennai S-Band Doppler Radar")
    station_code: str = Field(default="DWR_CHENNAI_PORT")
    latitude: float = 13.0827
    longitude: float = 80.2707
    last_sweep_utc: Optional[str] = None
    status: str = Field(default="operational", description="Radar operational status")
    radar_image_url: Optional[str] = None
    cells: List[RadarCellOverlay] = Field(default_factory=list)
    provenance: dict


class ForecastHorizonStatusSchema(BaseModel):
    horizon: str = Field(..., description="NOW, +30M, +1H, +2H, +3H")
    status: str = Field(..., description="available or forecast_data_unavailable")
    message: str
    source: Optional[str] = None
    timestamp: str
