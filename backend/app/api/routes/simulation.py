"""
Simulation API Router
Exposes endpoints for running custom scenario simulations against the XGBoost nowcasting model.
"""

from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from backend.app.services.flood_service import FloodService

router = APIRouter(prefix="/simulation", tags=["Model Simulation Studio"])


class SimulationRequest(BaseModel):
    rainfall_daily_mm: float = Field(85.0, ge=0.0, le=500.0, description="Daily rainfall in mm")
    rainfall_cum_3d_mm: float = Field(140.0, ge=0.0, le=800.0, description="Antecedent 3-day cumulative rainfall in mm")
    rainfall_delta_mm: float = Field(15.0, ge=-100.0, le=200.0, description="Hourly rainfall delta in mm")
    tidal_lock_penalty: float = Field(0.0, ge=0.0, le=1.0, description="Coastal tidal lock restriction penalty factor (0.0 to 1.0)")


@router.post("/run")
def run_simulation(req: SimulationRequest):
    """
    Executes real-time scenario simulation across all 3,963 Chennai sectors
    using the trained XGBoost model.
    """
    service = FloodService.get_instance()
    return service.simulate_scenario(
        rainfall_daily_mm=req.rainfall_daily_mm,
        rainfall_cum_3d_mm=req.rainfall_cum_3d_mm,
        rainfall_delta_mm=req.rainfall_delta_mm,
        tidal_lock_penalty=req.tidal_lock_penalty
    )


@router.get("/presets")
def get_simulation_presets():
    """
    Returns curated historical and synthetic storm scenario presets for Greater Chennai.
    """
    return [
        {
            "id": "preset_normal_monsoon",
            "name": "Typical Monsoon Shower",
            "description": "Standard Northeast Monsoon rain pulse with functioning storm drains.",
            "rainfall_daily_mm": 45.0,
            "rainfall_cum_3d_mm": 60.0,
            "rainfall_delta_mm": 5.0,
            "tidal_lock_penalty": 0.0
        },
        {
            "id": "preset_heavy_surge",
            "name": "Severe Monsoonal Surge",
            "description": "Persistent depression in the Bay of Bengal with continuous rainfall.",
            "rainfall_daily_mm": 135.0,
            "rainfall_cum_3d_mm": 210.0,
            "rainfall_delta_mm": 25.0,
            "tidal_lock_penalty": 0.3
        },
        {
            "id": "preset_2015_deluge",
            "name": "December 2015 Historic Deluge",
            "description": "Record 340+ mm 24h deluge with saturated soil and Adyar river overflowing.",
            "rainfall_daily_mm": 345.0,
            "rainfall_cum_3d_mm": 490.0,
            "rainfall_delta_mm": 65.0,
            "tidal_lock_penalty": 0.8
        },
        {
            "id": "preset_cloudburst",
            "name": "Convective Cloudburst & Tidal Lock",
            "description": "Extreme 100mm convective downburst coinciding with Spring High Tide.",
            "rainfall_daily_mm": 180.0,
            "rainfall_cum_3d_mm": 150.0,
            "rainfall_delta_mm": 80.0,
            "tidal_lock_penalty": 1.0
        }
    ]
