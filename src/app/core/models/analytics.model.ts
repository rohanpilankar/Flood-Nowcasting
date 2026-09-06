export interface RainfallTrendPoint {
  time: string; // e.g. '10:00 AM'
  rainfallMm: number;
  cumulativeMm: number;
  isSimulated: boolean;
}

export interface RiskDistribution {
  noRisk: number;
  low: number;
  medium: number;
  high: number;
  critical: number;
}

export interface AreaRiskRank {
  rank: number;
  area: string;
  riskScore: number;
  trend: 'INCREASING' | 'STABLE' | 'DECREASING';
  rainfall: number;
  elevation: number;
}

export interface InundationHistoryPoint {
  hour: string; // e.g. '-6h', '-4h', '-2h', 'NOW', '+1h', '+2h'
  avgWaterDepthCm: number;
  affectedRoadsCount: number;
}

export interface AnalyticsSummary {
  rainfallTrends: RainfallTrendPoint[];
  riskDistribution: RiskDistribution;
  areaRankings: AreaRiskRank[];
  inundationHistory: InundationHistoryPoint[];
  peakRainfallLocality: string;
  totalVulnerablePopulation: string;
  isSimulated: boolean;
}
