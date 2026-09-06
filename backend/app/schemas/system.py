from typing import List
from pydantic import BaseModel

class DataFeedStatusSchema(BaseModel):
    name: str
    category: str # 'RADAR' | 'IOT' | 'GIS' | 'ROAD_NETWORK' | 'HISTORICAL'
    status: str # 'OPERATIONAL' | 'DEGRADED' | 'MAINTENANCE' | 'PROTOTYPE_SIMULATED'
    lastUpdate: str
    sampleFrequency: str
    sourceType: str
    isSimulated: bool = False

class ModelMetricsSchema(BaseModel):
    name: str
    version: str
    status: str # 'ACTIVE_PROTOTYPE' | 'TRAINING' | 'OFFLINE'
    algorithm: str
    prototypeF1Score: float
    prototypePrecision: float
    prototypeRecall: float
    prototypeAccuracy: float
    simulatedInferenceLatencyMs: float
    featureCount: int
    lastTrained: str
    isSimulated: bool = False

class MicroserviceHealthSchema(BaseModel):
    name: str
    endpoint: str
    status: str
    latencyMs: float
    uptime: str
    version: str
    isMock: bool = False

class SystemLoadSchema(BaseModel):
    cpuPercent: float
    memoryPercent: float
    activeQueriesPerSec: float

class SihDisclaimerSchema(BaseModel):
    projectCode: str
    notice: str
    phase: str

class AdminSystemOverviewSchema(BaseModel):
    dataFeeds: List[DataFeedStatusSchema]
    modelMetrics: ModelMetricsSchema
    microservices: MicroserviceHealthSchema = None
    microservicesList: List[MicroserviceHealthSchema] = []
    microservices: List[MicroserviceHealthSchema]
    systemLoad: SystemLoadSchema
    sihDisclaimer: SihDisclaimerSchema
