from fastapi import APIRouter
from backend.app.schemas.analytics import AnalyticsSummarySchema
from backend.app.services.flood_service import FloodService

router = APIRouter()

@router.get("/analytics/summary", response_model=AnalyticsSummarySchema)
def get_analytics_summary():
    service = FloodService.get_instance()
    return service.get_analytics_summary()
