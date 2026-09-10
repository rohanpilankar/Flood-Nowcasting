"""
Drainage Network and Surcharge API Routes
"""

from fastapi import APIRouter
from typing import Dict, Any, List
from backend.app.schemas.drainage import WaterwaySegmentSchema, DrainageSurchargeResponse
from backend.app.services.drainage_service import DrainageService

router = APIRouter(prefix="/drainage", tags=["Drainage & Surface Water Network"])


@router.get("/surface-waterways", response_model=List[WaterwaySegmentSchema])
def get_surface_waterways():
    """Returns primary surface river channels (Adyar, Cooum, Kosasthalaiyar) and canals."""
    service = DrainageService.get_instance()
    return service.get_surface_waterways()


@router.get("/underground-drains", response_model=List[WaterwaySegmentSchema])
def get_underground_drains():
    """Returns major underground storm water drain trunk corridors."""
    service = DrainageService.get_instance()
    return service.get_underground_drains()


@router.get("/surcharge", response_model=DrainageSurchargeResponse)
def get_drainage_surcharge():
    """
    Returns hydraulic surcharge status.
    In absence of live SCADA telemetry, returns explicit network_data_unavailable status.
    """
    service = DrainageService.get_instance()
    return service.get_surcharge_status()
