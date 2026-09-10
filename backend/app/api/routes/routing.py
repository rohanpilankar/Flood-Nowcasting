from typing import List
from fastapi import APIRouter
from backend.app.schemas.route import RouteRequestSchema, RoutePlanResultSchema, PresetRouteSchema
from backend.app.services.flood_service import FloodService

router = APIRouter()

@router.get("/safe-route/presets", response_model=List[PresetRouteSchema])
def get_preset_routes():
    service = FloodService.get_instance()
    return service.get_preset_routes()

@router.post("/safe-route", response_model=RoutePlanResultSchema)
def calculate_safe_route(payload: RouteRequestSchema):
    service = FloodService.get_instance()
    src = payload.source or payload.origin or "Chennai Central"
    return service.calculate_safe_route(
        source=src,
        destination=payload.destination,
        vehicle_type=payload.vehicle_type or "car"
    )
