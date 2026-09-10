/**
 * FloodWatch AI — EOC Command Center typed data contracts.
 * Chennai (GCC) is the fixed operational geography.
 *
 * These interfaces mirror the intended FastAPI responses so the
 * simulation layer can be swapped for real backends without UI changes.
 */

export type DataMode = 'LIVE' | 'SIMULATION';

export type Severity = 'SAFE' | 'LOW' | 'CAUTION' | 'MEDIUM' | 'HIGH' | 'WARNING' | 'CRITICAL' | 'SEVERE';

export type HorizonKey = 'NOW' | 'T+30' | 'T+60' | 'T+90' | 'T+120';

export interface LatLng {
  lat: number;
  lng: number;
}

/** Per-horizon forecast slice for a zone. */
export interface ZoneHorizonSlice {
  horizon: HorizonKey;
  rainfallMmh: number;
  waterDepthCm: number;
  riskScore: number; // 0-100
  riskLevel: Severity;
  state: 'CURRENT' | 'RISING' | 'PEAK' | 'SEVERE FLOOD' | 'RECEDING';
}

export interface FloodZone extends LatLng {
  id: string;
  zoneName: string;
  ward: string;
  corridor: string;
  optedInCitizens: number;
  notifiedCitizens: number;
  series: ZoneHorizonSlice[];
}

export interface RainfallSample {
  horizon: HorizonKey;
  observedMmh: number | null; // null once we move past observation window
  predictedMmh: number;
}

export interface TelemetrySnapshot {
  radarNowcastMmh: number;
  peakNowcastMmh: number;
  drainageLoadPct: number;
  surchargeNodes: number;
  totalNodes: number;
  floodedRoads: number;
  activeIncidents: number;
  catchmentRiskIndex: number; // 0-100
  catchmentLoadPct: number;
  soilSaturationPct: number;
  predictedPeakAt: string;
  generatedAt: string;
}

export type DrainageNodeType = 'OUTFALL' | 'MANHOLE' | 'PUMP STATION' | 'REGULATOR' | 'BARRAGE' | 'SLUICE';

export type DrainageStatus = 'NOMINAL' | 'WARNING' | 'CRITICAL';

export interface DrainageNode extends LatLng {
  id: string;
  name: string;
  nodeType: DrainageNodeType;
  flowM3s: number;
  hydraulicLoadPct: number;
  waterLevelM: number;
  surchargePct: number;
  status: DrainageStatus;
  /** True when this node is illustrative demo geometry, not confirmed GCC infrastructure. */
  isDemo: boolean;
  series: Array<{ horizon: HorizonKey; surchargePct: number; status: DrainageStatus }>;
}

export interface DrainageLink {
  from: string;
  to: string;
  path: LatLng[];
}

export type IncidentStatus = 'OPEN' | 'MONITORING' | 'RESPONDING' | 'ACKNOWLEDGED' | 'RESOLVED';

export interface EocIncident {
  id: string;
  severity: Severity;
  location: string;
  ward: string;
  description: string;
  waterDepthCm: number;
  expectedAt: HorizonKey;
  issuedAt: string;
  status: IncidentStatus;
  actionLabel: string;
}

export type RoadStatus = 'OPEN' | 'WARNING' | 'RESTRICTED' | 'CLOSED';

export interface RouteAdvisory {
  id: string;
  roadName: string;
  corridor: string;
  floodDepthCm: number;
  status: RoadStatus;
  recommendedAction: string;
  path: LatLng[];
}

export type VehicleKind = 'CAR' | 'SUV' | 'TRUCK' | 'RESCUE';

export interface SafeRoutePlan {
  vehicle: VehicleKind;
  name: string;
  distanceKm: number;
  etaMin: number;
  maxDepthCm: number;
  path: LatLng[];
}

export interface StormArchiveEntry {
  id: string;
  eventName: string;
  eventDate: string;
  peakRainfallMmh: number;
  maxDepthCm: number;
  affectedZones: string[];
  leadTimeMin: number;
  /** Demo values only — never present as validated science. */
  isDemo: boolean;
}

export interface HealthCheck {
  id: string;
  label: string;
  status: 'ONLINE' | 'DEGRADED' | 'OFFLINE';
  detail: string;
}

export interface SystemHealth {
  checks: HealthCheck[];
  lastModelUpdate: string;
  dataLatencySec: number;
  inferenceMs: number;
  apiStatus: string;
}

/** Map layer toggles, grouped per spec section 8. */
export interface MapLayerState {
  base: 'standard' | 'satellite' | 'terrain';
  radar: boolean;
  rainfallIntensity: boolean;
  rainfallAccumulation: boolean;
  aiNowcast: boolean;
  floodDepth: boolean;
  floodRisk: boolean;
  predictedInundation: boolean;
  drainageNetwork: boolean;
  drainageNodes: boolean;
  criticalRoads: boolean;
  incidents: boolean;
  shelters: boolean;
  emergencyRoutes: boolean;
}

export interface Shelter extends LatLng {
  id: string;
  name: string;
  capacity: number;
  occupied: number;
}

/** Observed radar rain cell (IMD/GCC telemetry). */
export interface RadarCell {
  center: [number, number];
  radiusMeters: number;
  intensityMmh: number;
  colorHex: string;
  label: string;
  source: string;
}

/** Drainage corridor geometry (GCC GIS stormwater database). */
export interface Waterway {
  id: string;
  name: string;
  type: string; // SURFACE_RIVER | CANAL | UNDERGROUND_SWD
  coordinates: Array<[number, number]>;
  basin?: string;
  source: string;
}
