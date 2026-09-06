from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

class CitizenAlertItem(BaseModel):
    delivery_id: int
    alert_id: int
    alert_code: str
    title: str
    location_name: str
    severity: str
    risk_score: int
    model_confidence: int
    forecast_horizon: str
    description: str
    recommended_action: str
    status: str
    created_at: datetime
    expires_at: datetime
    read_at: Optional[datetime]
    distance_meters: Optional[float] = None
    is_simulated: bool = False

class SpatialAlertZone(BaseModel):
    alert_id: int
    alert_code: str
    title: str
    severity: str
    risk_score: int
    forecast_horizon: str
    geometry_geojson: str
    status: str
    expires_at: datetime
