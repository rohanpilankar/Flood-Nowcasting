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


@router.get("/network-3d")
def get_3d_drainage_network():
    """
    Returns the complete 3D network of Chennai drainage nodes (junctions, outfalls, sumps)
    and pipe conduits with authentic invert and ground elevations for 3D visualization.
    """
    from backend.app.services.drainage_graph_service import DrainageGraphService
    return DrainageGraphService.get_instance().get_3d_network()


@router.get("/hydraulic-inspect")
def inspect_pipe_hydraulics(pipe_id: str = "PIPE-VEL-TRUNK-01", rainfall_mm_h: float = 45.0):
    """
    Performs physical hydraulic evaluation on a selected drainage pipe segment using
    Manning's full conveyance capacity vs. Rational runoff inflow to predict
    underflow vs. surcharge overflow.
    """
    from backend.app.services.drainage_graph_service import DrainageGraphService
    return DrainageGraphService.get_instance().inspect_hydraulic_status(pipe_id, rainfall_mm_h)

