from fastapi import APIRouter
from backend.app.schemas.system import AdminSystemOverviewSchema
from backend.app.services.flood_service import FloodService

router = APIRouter()

@router.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "FloodWatch AI API Gateway",
        "study_area": "Greater Mumbai (BMC)",
        "model": "XGBoost-v2.0-Mumbai",
        "timestamp": "now"
    }

@router.get("/health/system-overview", response_model=AdminSystemOverviewSchema)
def get_system_overview():
    service = FloodService.get_instance()
    return service.get_system_overview()
