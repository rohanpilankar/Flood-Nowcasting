from typing import List, Optional
from pydantic import BaseModel

class FloodAlertSchema(BaseModel):
    id: str # '#ALT-1024'
    title: str
    severity: str # 'HIGH' | 'MEDIUM' | 'LOW'
    location: str
    coordinates: List[float] # [lat, lon]
    description: str
    riskScore: int
    predictionHorizon: str
    generatedTime: str
    timestamp: str
    acknowledged: bool
    aiConfidence: int
    isSimulated: bool = False
    status: str = "ACTIVE" # 'ACTIVE' | 'ACKNOWLEDGED' | 'RESOLVED'
    source: str = "GCC Emergency Operations Center"
    reason: Optional[str] = None
