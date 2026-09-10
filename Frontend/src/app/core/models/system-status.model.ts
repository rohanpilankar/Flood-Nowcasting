export type ServiceState = 'OPERATIONAL' | 'DEGRADED' | 'MAINTENANCE' | 'PROTOTYPE_SIMULATED';

export interface DataFeedStatus {
  name: string;
  category: 'RADAR' | 'IOT' | 'GIS' | 'ROAD_NETWORK' | 'HISTORICAL';
  status: ServiceState;
  lastUpdate: string;
  sampleFrequency: string;
  sourceType: string;
  isSimulated: boolean;
}

export interface ModelMetrics {
  name: string;
  version: string;
  status: 'ACTIVE_PROTOTYPE' | 'ACTIVE_BASELINE' | 'TRAINING' | 'OFFLINE';
  algorithm: string;
  prototypeF1Score: number;
  prototypePrecision: number;
  prototypeRecall: number;
  prototypeAccuracy: number;
  simulatedInferenceLatencyMs: number;
  featureCount: number;
  lastTrained: string;
  isSimulated: boolean;
}

export interface MicroserviceHealth {
  name: string;
  endpoint: string;
  status: ServiceState;
  latencyMs: number;
  uptime: string;
  version: string;
  isMock: boolean;
}

export interface AdminSystemOverview {
  dataFeeds: DataFeedStatus[];
  modelMetrics: ModelMetrics;
  microservices: MicroserviceHealth[];
  systemLoad: {
    cpuPercent: number;
    memoryPercent: number;
    activeQueriesPerSec: number;
  };
  sihDisclaimer: {
    projectCode: string;
    notice: string;
    phase: string;
  };
}
