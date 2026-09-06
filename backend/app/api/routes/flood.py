from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from backend.app.schemas.flood import FloodZoneSchema, SystemKPIsSchema, RecentPredictionSchema, RoadSegmentSchema
from backend.app.services.flood_service import FloodService

router = APIRouter()

@router.get("/current-risk/kpis", response_model=SystemKPIsSchema)
def get_current_kpis():
    service = FloodService.get_instance()
    return service.get_kpis()

@router.get("/forecast-risk", response_model=List[FloodZoneSchema])
def get_forecast_risk(horizon: str = Query(default="NOW", description="Prediction horizon (NOW, +30M, +1H, +2H, +3H)")):
    service = FloodService.get_instance()
    return service.get_flood_zones(horizon=horizon)

@router.get("/forecast-risk/recent", response_model=List[RecentPredictionSchema])
def get_recent_predictions():
    service = FloodService.get_instance()
    return service.get_recent_predictions()

@router.get("/map-data/zones/{grid_id}", response_model=FloodZoneSchema)
def get_zone_by_id(grid_id: str):
    service = FloodService.get_instance()
    zone = service.get_zone_by_id(grid_id)
    if not zone:
        raise HTTPException(status_code=404, detail=f"Grid cell {grid_id} not found")
    return zone

@router.get("/map-data/roads", response_model=List[RoadSegmentSchema])
def get_road_segments():
    service = FloodService.get_instance()
    return service.get_road_segments()

@router.get("/location-risk", response_model=FloodZoneSchema)
def get_location_risk(location: str = Query(..., description="Location name or landmark")):
    service = FloodService.get_instance()
    zone = service.get_location_risk(location)
    if not zone:
        raise HTTPException(status_code=404, detail=f"Location {location} not found")
    return zone
