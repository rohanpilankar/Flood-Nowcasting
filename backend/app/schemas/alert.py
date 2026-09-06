from typing import List
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
    recommendedAction: str
    isSimulated: bool = False
