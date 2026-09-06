from typing import List, Optional
from pydantic import BaseModel

class RouteRequestSchema(BaseModel):
    source: str
    destination: str
    mode: Optional[str] = "vehicle"

class RouteOptionSchema(BaseModel):
    id: str
    name: str
    type: str # 'RECOMMENDED_SAFE' | 'FASTER_ALTERNATIVE'
    distanceKm: float
    etaMinutes: int
    safetyScore: int
    riskStatus: str # 'SAFE' | 'CAUTION' | 'UNSAFE'
    floodPointsAvoided: int
    hazardExposure: str # 'Low' | 'Medium' | 'High'
    pathCoordinates: List[List[float]]
    notes: str
    isSimulated: bool = False

class RouteHazardSchema(BaseModel):
    id: str
    title: str
    location: str
    coordinates: List[float] # [lat, lon]
    severity: str # 'CAUTION' | 'UNSAFE'
    waterDepthCm: int
    status: str
    isSimulated: bool = False

class RoutePlanResultSchema(BaseModel):
    source: str
    destination: str
    sourceCoords: List[float]
    destCoords: List[float]
    recommendedRoute: RouteOptionSchema
    alternativeRoute: RouteOptionSchema
    hazards: List[RouteHazardSchema]
    isSimulated: bool = False

class PresetRouteSchema(BaseModel):
    id: str
    label: str
    source: str
    destination: str
    description: str
