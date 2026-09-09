export interface AppSettings {
  gridResolution: 'FINE' | 'MEDIUM' | 'COARSE';
  highRiskThreshold: number; // e.g. 80
  mediumRiskThreshold: number; // e.g. 50
  predictionHorizon: string; // e.g. '+1H'
  enableHighRiskAlerts: boolean;
  alertThreshold: number; // e.g. 75
  autoRefreshIntervalSec: number; // e.g. 30
  defaultMapLayer: 'ALL' | 'RISK' | 'ROADS' | 'RAINFALL';
  mapGridVisibility: boolean;
  roadLayerVisibility: boolean;
  rainfallOverlayVisibility: boolean;
  drainageOverlayVisibility: boolean;
  soundAlerts: boolean;
}

export const DEFAULT_SETTINGS: AppSettings = {
  gridResolution: 'MEDIUM',
  highRiskThreshold: 80,
  mediumRiskThreshold: 50,
  predictionHorizon: '+1H',
  enableHighRiskAlerts: true,
  alertThreshold: 75,
  autoRefreshIntervalSec: 30,
  defaultMapLayer: 'ALL',
  mapGridVisibility: true,
  roadLayerVisibility: true,
  rainfallOverlayVisibility: true,
  drainageOverlayVisibility: true,
  soundAlerts: false
};
