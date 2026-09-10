"""
Flood Hotspot Schemas
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from backend.app.schemas.provenance import ProvenanceStatus


class FloodHotspotItem(BaseModel):
    grid_id: str
    latitude: float
    longitude: float
    probability: float = Field(..., description="Estimated flood susceptibility probability [0.0, 1.0]")
    risk_level: str = Field(..., description="LOW, MODERATE, HIGH, CRITICAL")
    elevation_m: float
    low_lying_score: float
    dist_to_swd_m: float
    locality: str = Field(..., description="Deterministic nearby landmark or locality name")
    timestamp: str
    source: str = "Chennai XGBoost Baseline Model"
    provenance_status: ProvenanceStatus = ProvenanceStatus.MODEL_PREDICTED


class FloodDepthResponse(BaseModel):
    location: str
    timestamp: str
    depth_cm: Optional[float] = Field(None, description="Depth in centimeters; null when unmeasured")
    confidence: Optional[float] = None
    source: str = "Hydraulic Depth Interface"
    status: str = Field(default="unavailable", description="Physical depth data status")
    message: str = Field(default="No physical hydrodynamic 1D/2D depth sensor is attached. Continuous depth is not fabricated.")
