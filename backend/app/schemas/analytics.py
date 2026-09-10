from typing import List
from pydantic import BaseModel

class RainfallTrendPointSchema(BaseModel):
    time: str
    rainfallMm: float
    cumulativeMm: float
    isSimulated: bool = False

class RiskDistributionSchema(BaseModel):
    noRisk: int
    low: int
    medium: int
    high: int
    critical: int

class AreaRiskRankSchema(BaseModel):
    rank: int
    area: str
    riskScore: int
    trend: str # 'INCREASING' | 'STABLE' | 'DECREASING'
    rainfall: float
    elevation: float

class InundationHistoryPointSchema(BaseModel):
    hour: str
    avgWaterDepthCm: Optional[float] = None
    affectedRoadsCount: int

class AnalyticsSummarySchema(BaseModel):
    rainfallTrends: List[RainfallTrendPointSchema]
    riskDistribution: RiskDistributionSchema
    areaRankings: List[AreaRiskRankSchema]
    inundationHistory: List[InundationHistoryPointSchema]
    peakRainfallLocality: str
    totalVulnerablePopulation: str
    isSimulated: bool = False
