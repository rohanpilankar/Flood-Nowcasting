"""
Rainfall and Radar API Routes
"""

from fastapi import APIRouter, Query
from typing import Dict, Any
from backend.app.services.rainfall_service import RainfallService

router = APIRouter(prefix="/rainfall", tags=["Rainfall & Radar Telemetry"])


@router.get("/current")
def get_current_rainfall():
    """Returns current city-wide observed precipitation and gauge stations."""
    service = RainfallService.get_instance()
    return service.get_current_rainfall()


@router.get("/radar")
def get_radar_metadata():
    """Returns Doppler Weather Radar overlay metadata and verified Chennai radar cells."""
    service = RainfallService.get_instance()
    return service.get_radar_metadata()


@router.get("/forecast")
def get_rainfall_forecast(horizon: str = Query(default="NOW", description="NOW, +30M, +1H, +2H, +3H")):
    """Returns rainfall forecast for given horizon or explicit unavailable status."""
    service = RainfallService.get_instance()
    return service.get_forecast_for_horizon(horizon=horizon)
