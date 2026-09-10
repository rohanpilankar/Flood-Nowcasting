"""
Drainage Network and Surcharge Schemas
"""

from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field
from backend.app.schemas.provenance import ProvenanceStatus


class WaterwaySegmentSchema(BaseModel):
    id: str
    name: str
    type: str = Field(..., description="SURFACE_RIVER, CANAL, or UNDERGROUND_SWD")
    coordinates: List[List[float]] = Field(..., description="Polyline coordinates [[lat, lon], ...]")
    basin: Optional[str] = None
    source: str = "GCC GIS Stormwater Database"
    status: str = "PASSIVE_GRAVITY"


class DrainageSurchargeResponse(BaseModel):
    status: str = Field(default="network_data_unavailable", description="Hydraulic telemetry connection status")
    monitored_nodes_count: int = 0
    surcharge_nodes_count: int = 0
    backflow_nodes_count: int = 0
    utilization_rate: Optional[float] = None
    timestamp: str
    source: str = "SCADA / SWMM Ingestion Interface"
    provenance_status: ProvenanceStatus = ProvenanceStatus.UNAVAILABLE
    message: str = "Continuous in-situ manhole pressure transducer and hydraulic conduit telemetry currently disconnected. Surcharge states cannot be scientifically inferred without sensor telemetry."
