export type AlertSeverity = 'HIGH' | 'MEDIUM' | 'LOW';

export interface FloodAlert {
  id: string; // e.g. '#ALT-1024'
  title: string;
  severity: AlertSeverity;
  location: string;
  coordinates: [number, number];
  description: string;
  riskScore: number;
  predictionHorizon: string; // e.g. '+30 Minutes'
  generatedTime: string; // e.g. '2 minutes ago'
  timestamp: string;
  acknowledged: boolean;
  aiConfidence: number;
  recommendedAction: string;
  isSimulated: boolean;
}

export interface AlertFilterCriteria {
  severity: 'ALL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'ACKNOWLEDGED';
  searchQuery: string;
}
