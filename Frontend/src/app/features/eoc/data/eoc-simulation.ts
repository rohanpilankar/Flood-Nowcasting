/**
 * FloodWatch AI — EOC deterministic DEMO/SIMULATION dataset (Chennai, GCC).
 * ==========================================================================
 * ALL values here are illustrative simulation inputs for UI development.
 * They MUST NOT be presented as live measurements. The EOC shell renders a
 * persistent SIMULATION indicator whenever this dataset drives the display.
 * Replace with FastAPI/ML outputs (see eoc-data.service.ts) when available.
 */
import {
  DrainageLink,
  DrainageNode,
  EocIncident,
  FloodZone,
  HealthCheck,
  HorizonKey,
  RainfallSample,
  RouteAdvisory,
  SafeRoutePlan,
  Shelter,
  StormArchiveEntry,
  TelemetrySnapshot,
  VehicleKind,
} from '../models/eoc-models';

export const HORIZONS: HorizonKey[] = ['NOW', 'T+30', 'T+60', 'T+90', 'T+120'];

/** City anchor — Ripon Building, Greater Chennai Corporation. */
export const CHENNAI_CENTER = { lat: 13.0827, lng: 80.2707 };

export const SIM_TELEMETRY: TelemetrySnapshot = {
  radarNowcastMmh: 64.2,
  peakNowcastMmh: 92.5,
  drainageLoadPct: 198,
  surchargeNodes: 21,
  totalNodes: 64,
  floodedRoads: 7,
  activeIncidents: 7,
  catchmentRiskIndex: 94,
  catchmentLoadPct: 198,
  soilSaturationPct: 78,
  predictedPeakAt: 'T+01:30',
  generatedAt: new Date().toISOString(),
};

export const SIM_RAINFALL_SERIES: RainfallSample[] = [
  { horizon: 'NOW', observedMmh: 64.2, predictedMmh: 64.2 },
  { horizon: 'T+30', observedMmh: null, predictedMmh: 78.4 },
  { horizon: 'T+60', observedMmh: null, predictedMmh: 92.5 },
  { horizon: 'T+90', observedMmh: null, predictedMmh: 84.1 },
  { horizon: 'T+120', observedMmh: null, predictedMmh: 61.7 },
];

export const SIM_ZONES: FloodZone[] = [
  {
    id: 'Z-VELACHERY', zoneName: 'Velachery Lowland', ward: 'Zone 13 (Adyar)',
    corridor: 'Velachery Lake Catchment', lat: 12.9816, lng: 80.218,
    optedInCitizens: 125, notifiedCitizens: 112,
    series: [
      { horizon: 'NOW', rainfallMmh: 58, waterDepthCm: 22, riskScore: 82, riskLevel: 'HIGH', state: 'RISING' },
      { horizon: 'T+30', rainfallMmh: 74, waterDepthCm: 38, riskScore: 90, riskLevel: 'CRITICAL', state: 'RISING' },
      { horizon: 'T+60', rainfallMmh: 92, waterDepthCm: 55, riskScore: 96, riskLevel: 'CRITICAL', state: 'PEAK' },
      { horizon: 'T+90', rainfallMmh: 84, waterDepthCm: 61, riskScore: 97, riskLevel: 'CRITICAL', state: 'SEVERE FLOOD' },
      { horizon: 'T+120', rainfallMmh: 60, waterDepthCm: 48, riskScore: 91, riskLevel: 'CRITICAL', state: 'RECEDING' },
    ],
  },
  {
    id: 'Z-MADLEY', zoneName: 'Madley Subway / T. Nagar', ward: 'Zone 10 (Kodambakkam)',
    corridor: 'Madley Underpass Basin', lat: 13.0418, lng: 80.2341,
    optedInCitizens: 94, notifiedCitizens: 89,
    series: [
      { horizon: 'NOW', rainfallMmh: 61, waterDepthCm: 28, riskScore: 86, riskLevel: 'CRITICAL', state: 'RISING' },
      { horizon: 'T+30', rainfallMmh: 79, waterDepthCm: 44, riskScore: 93, riskLevel: 'CRITICAL', state: 'RISING' },
      { horizon: 'T+60', rainfallMmh: 95, waterDepthCm: 63, riskScore: 98, riskLevel: 'CRITICAL', state: 'PEAK' },
      { horizon: 'T+90', rainfallMmh: 86, waterDepthCm: 68, riskScore: 98, riskLevel: 'CRITICAL', state: 'SEVERE FLOOD' },
      { horizon: 'T+120', rainfallMmh: 62, waterDepthCm: 52, riskScore: 92, riskLevel: 'CRITICAL', state: 'RECEDING' },
    ],
  },
  {
    id: 'Z-EGMORE', zoneName: 'Gengu Reddy Subway / Egmore', ward: 'Zone 5 (Royapuram)',
    corridor: 'Cooum Outfall Corridor', lat: 13.0732, lng: 80.2609,
    optedInCitizens: 78, notifiedCitizens: 74,
    series: [
      { horizon: 'NOW', rainfallMmh: 55, waterDepthCm: 24, riskScore: 80, riskLevel: 'HIGH', state: 'RISING' },
      { horizon: 'T+30', rainfallMmh: 71, waterDepthCm: 36, riskScore: 88, riskLevel: 'CRITICAL', state: 'RISING' },
      { horizon: 'T+60', rainfallMmh: 88, waterDepthCm: 51, riskScore: 94, riskLevel: 'CRITICAL', state: 'PEAK' },
      { horizon: 'T+90', rainfallMmh: 80, waterDepthCm: 54, riskScore: 94, riskLevel: 'CRITICAL', state: 'SEVERE FLOOD' },
      { horizon: 'T+120', rainfallMmh: 58, waterDepthCm: 41, riskScore: 87, riskLevel: 'CRITICAL', state: 'RECEDING' },
    ],
  },
  {
    id: 'Z-MUDICHUR', zoneName: 'Mudichur / Adyar Buffer', ward: 'Zone 14 (Perungudi)',
    corridor: 'Adyar River Floodplain', lat: 12.9226, lng: 80.0768,
    optedInCitizens: 62, notifiedCitizens: 58,
    series: [
      { horizon: 'NOW', rainfallMmh: 44, waterDepthCm: 15, riskScore: 58, riskLevel: 'CAUTION', state: 'RISING' },
      { horizon: 'T+30', rainfallMmh: 60, waterDepthCm: 24, riskScore: 71, riskLevel: 'HIGH', state: 'RISING' },
      { horizon: 'T+60', rainfallMmh: 76, waterDepthCm: 35, riskScore: 84, riskLevel: 'HIGH', state: 'PEAK' },
      { horizon: 'T+90', rainfallMmh: 69, waterDepthCm: 38, riskScore: 85, riskLevel: 'CRITICAL', state: 'SEVERE FLOOD' },
      { horizon: 'T+120', rainfallMmh: 50, waterDepthCm: 29, riskScore: 76, riskLevel: 'HIGH', state: 'RECEDING' },
    ],
  },
  {
    id: 'Z-ADYAR', zoneName: 'Adyar River Corridor', ward: 'Zone 13 (Adyar)',
    corridor: 'Adyar Bridge Approach', lat: 13.0105, lng: 80.2647,
    optedInCitizens: 88, notifiedCitizens: 81,
    series: [
      { horizon: 'NOW', rainfallMmh: 52, waterDepthCm: 18, riskScore: 66, riskLevel: 'HIGH', state: 'RISING' },
      { horizon: 'T+30', rainfallMmh: 68, waterDepthCm: 30, riskScore: 79, riskLevel: 'HIGH', state: 'RISING' },
      { horizon: 'T+60', rainfallMmh: 85, waterDepthCm: 44, riskScore: 90, riskLevel: 'CRITICAL', state: 'PEAK' },
      { horizon: 'T+90', rainfallMmh: 78, waterDepthCm: 47, riskScore: 91, riskLevel: 'CRITICAL', state: 'SEVERE FLOOD' },
      { horizon: 'T+120', rainfallMmh: 56, waterDepthCm: 36, riskScore: 83, riskLevel: 'HIGH', state: 'RECEDING' },
    ],
  },
  {
    id: 'Z-AMBATTUR', zoneName: 'Ambattur Industrial Corridor', ward: 'Zone 7 (Ambattur)',
    corridor: 'Surface Runoff Belt', lat: 13.1143, lng: 80.1548,
    optedInCitizens: 54, notifiedCitizens: 47,
    series: [
      { horizon: 'NOW', rainfallMmh: 38, waterDepthCm: 11, riskScore: 47, riskLevel: 'MEDIUM', state: 'RISING' },
      { horizon: 'T+30', rainfallMmh: 52, waterDepthCm: 18, riskScore: 60, riskLevel: 'HIGH', state: 'RISING' },
      { horizon: 'T+60', rainfallMmh: 66, waterDepthCm: 27, riskScore: 74, riskLevel: 'HIGH', state: 'PEAK' },
      { horizon: 'T+90', rainfallMmh: 60, waterDepthCm: 29, riskScore: 75, riskLevel: 'HIGH', state: 'SEVERE FLOOD' },
      { horizon: 'T+120', rainfallMmh: 44, waterDepthCm: 22, riskScore: 64, riskLevel: 'HIGH', state: 'RECEDING' },
    ],
  },
  {
    id: 'Z-GUINDY', zoneName: 'Kathipara / Guindy Elevated', ward: 'Zone 12 (Alandur)',
    corridor: 'Grade Separator Ridge', lat: 13.0067, lng: 80.2206,
    optedInCitizens: 140, notifiedCitizens: 140,
    series: [
      { horizon: 'NOW', rainfallMmh: 30, waterDepthCm: 4, riskScore: 18, riskLevel: 'SAFE', state: 'CURRENT' },
      { horizon: 'T+30', rainfallMmh: 41, waterDepthCm: 6, riskScore: 24, riskLevel: 'LOW', state: 'RISING' },
      { horizon: 'T+60', rainfallMmh: 52, waterDepthCm: 9, riskScore: 33, riskLevel: 'MEDIUM', state: 'PEAK' },
      { horizon: 'T+90', rainfallMmh: 47, waterDepthCm: 9, riskScore: 32, riskLevel: 'MEDIUM', state: 'RECEDING' },
      { horizon: 'T+120', rainfallMmh: 35, waterDepthCm: 6, riskScore: 24, riskLevel: 'LOW', state: 'RECEDING' },
    ],
  },
  {
    id: 'Z-MARINA', zoneName: 'Marina Coastal Lowland', ward: 'Zone 9 (Teynampet)',
    corridor: 'Tidal + Pluvial Interface', lat: 13.05, lng: 80.282,
    optedInCitizens: 71, notifiedCitizens: 63,
    series: [
      { horizon: 'NOW', rainfallMmh: 49, waterDepthCm: 20, riskScore: 70, riskLevel: 'HIGH', state: 'RISING' },
      { horizon: 'T+30', rainfallMmh: 66, waterDepthCm: 34, riskScore: 83, riskLevel: 'HIGH', state: 'RISING' },
      { horizon: 'T+60', rainfallMmh: 82, waterDepthCm: 52, riskScore: 93, riskLevel: 'CRITICAL', state: 'PEAK' },
      { horizon: 'T+90', rainfallMmh: 75, waterDepthCm: 68, riskScore: 95, riskLevel: 'CRITICAL', state: 'SEVERE FLOOD' },
      { horizon: 'T+120', rainfallMmh: 54, waterDepthCm: 55, riskScore: 90, riskLevel: 'CRITICAL', state: 'RECEDING' },
    ],
  },
];

export const SIM_DRAINAGE_NODES: DrainageNode[] = [
  {
    id: 'NODE-20', name: 'South Coastal Sluice — Spillway Gate C', nodeType: 'OUTFALL',
    lat: 12.965, lng: 80.251, flowM3s: 41.2, hydraulicLoadPct: 264, waterLevelM: 4.8,
    surchargePct: 264, status: 'CRITICAL', isDemo: true,
    series: [
      { horizon: 'NOW', surchargePct: 198, status: 'CRITICAL' },
      { horizon: 'T+30', surchargePct: 231, status: 'CRITICAL' },
      { horizon: 'T+60', surchargePct: 264, status: 'CRITICAL' },
      { horizon: 'T+90', surchargePct: 258, status: 'CRITICAL' },
      { horizon: 'T+120', surchargePct: 226, status: 'CRITICAL' },
    ],
  },
  {
    id: 'NODE-10', name: 'Estuary Main Discharge — Outfall B', nodeType: 'OUTFALL',
    lat: 13.012, lng: 80.272, flowM3s: 38.6, hydraulicLoadPct: 263, waterLevelM: 4.5,
    surchargePct: 263, status: 'CRITICAL', isDemo: true,
    series: [
      { horizon: 'NOW', surchargePct: 196, status: 'CRITICAL' },
      { horizon: 'T+30', surchargePct: 229, status: 'CRITICAL' },
      { horizon: 'T+60', surchargePct: 263, status: 'CRITICAL' },
      { horizon: 'T+90', surchargePct: 251, status: 'CRITICAL' },
      { horizon: 'T+120', surchargePct: 218, status: 'CRITICAL' },
    ],
  },
  {
    id: 'NODE-09', name: 'Harbor Tidal Outfall — Gate A', nodeType: 'OUTFALL',
    lat: 13.095, lng: 80.29, flowM3s: 36.1, hydraulicLoadPct: 260, waterLevelM: 4.3,
    surchargePct: 260, status: 'CRITICAL', isDemo: true,
    series: [
      { horizon: 'NOW', surchargePct: 188, status: 'CRITICAL' },
      { horizon: 'T+30', surchargePct: 224, status: 'CRITICAL' },
      { horizon: 'T+60', surchargePct: 260, status: 'CRITICAL' },
      { horizon: 'T+90', surchargePct: 247, status: 'CRITICAL' },
      { horizon: 'T+120', surchargePct: 210, status: 'CRITICAL' },
    ],
  },
  {
    id: 'NODE-24', name: 'Lowland Siphon Terminal Manhole', nodeType: 'MANHOLE',
    lat: 12.985, lng: 80.222, flowM3s: 12.4, hydraulicLoadPct: 250, waterLevelM: 3.9,
    surchargePct: 250, status: 'CRITICAL', isDemo: true,
    series: [
      { horizon: 'NOW', surchargePct: 176, status: 'WARNING' },
      { horizon: 'T+30', surchargePct: 214, status: 'CRITICAL' },
      { horizon: 'T+60', surchargePct: 250, status: 'CRITICAL' },
      { horizon: 'T+90', surchargePct: 238, status: 'CRITICAL' },
      { horizon: 'T+120', surchargePct: 199, status: 'CRITICAL' },
    ],
  },
  {
    id: 'NODE-12', name: 'Adyar Bridge Regulator', nodeType: 'REGULATOR',
    lat: 13.0105, lng: 80.2647, flowM3s: 22.8, hydraulicLoadPct: 168, waterLevelM: 3.1,
    surchargePct: 168, status: 'WARNING', isDemo: true,
    series: [
      { horizon: 'NOW', surchargePct: 121, status: 'WARNING' },
      { horizon: 'T+30', surchargePct: 144, status: 'WARNING' },
      { horizon: 'T+60', surchargePct: 168, status: 'WARNING' },
      { horizon: 'T+90', surchargePct: 161, status: 'WARNING' },
      { horizon: 'T+120', surchargePct: 138, status: 'WARNING' },
    ],
  },
  {
    id: 'NODE-04', name: 'Pallikaranai Pump Station', nodeType: 'PUMP STATION',
    lat: 12.9341, lng: 80.213, flowM3s: 9.6, hydraulicLoadPct: 92, waterLevelM: 1.8,
    surchargePct: 92, status: 'NOMINAL', isDemo: true,
    series: [
      { horizon: 'NOW', surchargePct: 74, status: 'NOMINAL' },
      { horizon: 'T+30', surchargePct: 83, status: 'NOMINAL' },
      { horizon: 'T+60', surchargePct: 92, status: 'NOMINAL' },
      { horizon: 'T+90', surchargePct: 88, status: 'NOMINAL' },
      { horizon: 'T+120', surchargePct: 79, status: 'NOMINAL' },
    ],
  },
  {
    id: 'NODE-17', name: 'Cooum Barrage Shutter 3', nodeType: 'BARRAGE',
    lat: 13.065, lng: 80.265, flowM3s: 15.3, hydraulicLoadPct: 118, waterLevelM: 2.4,
    surchargePct: 118, status: 'WARNING', isDemo: true,
    series: [
      { horizon: 'NOW', surchargePct: 96, status: 'NOMINAL' },
      { horizon: 'T+30', surchargePct: 107, status: 'WARNING' },
      { horizon: 'T+60', surchargePct: 118, status: 'WARNING' },
      { horizon: 'T+90', surchargePct: 114, status: 'WARNING' },
      { horizon: 'T+120', surchargePct: 101, status: 'WARNING' },
    ],
  },
  {
    id: 'NODE-31', name: 'Buckingham Canal Sluice — Perungudi', nodeType: 'SLUICE',
    lat: 12.9698, lng: 80.2505, flowM3s: 7.2, hydraulicLoadPct: 64, waterLevelM: 1.2,
    surchargePct: 64, status: 'NOMINAL', isDemo: true,
    series: [
      { horizon: 'NOW', surchargePct: 52, status: 'NOMINAL' },
      { horizon: 'T+30', surchargePct: 58, status: 'NOMINAL' },
      { horizon: 'T+60', surchargePct: 64, status: 'NOMINAL' },
      { horizon: 'T+90', surchargePct: 61, status: 'NOMINAL' },
      { horizon: 'T+120', surchargePct: 55, status: 'NOMINAL' },
    ],
  },
];

export const SIM_DRAINAGE_LINKS: DrainageLink[] = [
  { from: 'NODE-24', to: 'NODE-12', path: [{ lat: 12.985, lng: 80.222 }, { lat: 12.998, lng: 80.244 }, { lat: 13.0105, lng: 80.2647 }] },
  { from: 'NODE-12', to: 'NODE-10', path: [{ lat: 13.0105, lng: 80.2647 }, { lat: 13.011, lng: 80.269 }] },
  { from: 'NODE-04', to: 'NODE-20', path: [{ lat: 12.9341, lng: 80.213 }, { lat: 12.95, lng: 80.232 }, { lat: 12.965, lng: 80.251 }] },
  { from: 'NODE-17', to: 'NODE-09', path: [{ lat: 13.065, lng: 80.265 }, { lat: 13.08, lng: 80.278 }, { lat: 13.095, lng: 80.29 }] },
];

export const SIM_INCIDENTS: EocIncident[] = [
  {
    id: 'INC-2041', severity: 'CRITICAL', location: 'Adyar River Corridor', ward: 'Zone 13 (Adyar)',
    description: 'Predicted road inundation approaching critical depth on Adyar Bridge approach.',
    waterDepthCm: 44, expectedAt: 'T+60', issuedAt: new Date(Date.now() - 12 * 60000).toISOString(),
    status: 'RESPONDING', actionLabel: 'Dispatch field verification',
  },
  {
    id: 'INC-2040', severity: 'CRITICAL', location: 'Velachery Lowland', ward: 'Zone 13 (Adyar)',
    description: 'Rapid rainfall accumulation and drainage surcharge detected near Velachery lake.',
    waterDepthCm: 55, expectedAt: 'T+60', issuedAt: new Date(Date.now() - 26 * 60000).toISOString(),
    status: 'RESPONDING', actionLabel: 'Activate dewatering pumps',
  },
  {
    id: 'INC-2039', severity: 'CRITICAL', location: 'Marina Coastal Lowland', ward: 'Zone 9 (Teynampet)',
    description: 'Combined tidal + pluvial inundation; 68 cm predicted by T+90.',
    waterDepthCm: 68, expectedAt: 'T+90', issuedAt: new Date(Date.now() - 34 * 60000).toISOString(),
    status: 'MONITORING', actionLabel: 'Restrict coastal access',
  },
  {
    id: 'INC-2038', severity: 'CRITICAL', location: 'Madley Subway / T. Nagar', ward: 'Zone 10 (Kodambakkam)',
    description: 'Underpass depression filling faster than pump discharge capacity.',
    waterDepthCm: 63, expectedAt: 'T+60', issuedAt: new Date(Date.now() - 48 * 60000).toISOString(),
    status: 'RESPONDING', actionLabel: 'Close subway to traffic',
  },
  {
    id: 'INC-2037', severity: 'WARNING', location: 'Perungudi Basin', ward: 'Zone 14 (Perungudi)',
    description: 'Drainage capacity approaching threshold along Buckingham Canal reach.',
    waterDepthCm: 35, expectedAt: 'T+60', issuedAt: new Date(Date.now() - 63 * 60000).toISOString(),
    status: 'MONITORING', actionLabel: 'Monitor continuously',
  },
  {
    id: 'INC-2036', severity: 'WARNING', location: 'Ambattur Industrial Corridor', ward: 'Zone 7 (Ambattur)',
    description: 'Surface runoff increasing across industrial estate low pockets.',
    waterDepthCm: 27, expectedAt: 'T+60', issuedAt: new Date(Date.now() - 81 * 60000).toISOString(),
    status: 'MONITORING', actionLabel: 'Alert estate control room',
  },
  {
    id: 'INC-2035', severity: 'CAUTION', location: 'Saidapet / Taramani Link', ward: 'Zone 12 (Alandur)',
    description: 'Minor waterlogging reported; runoff within drain capacity.',
    waterDepthCm: 9, expectedAt: 'T+60', issuedAt: new Date(Date.now() - 104 * 60000).toISOString(),
    status: 'OPEN', actionLabel: 'Routine patrol',
  },
];

export const SIM_ROUTES: RouteAdvisory[] = [
  {
    id: 'RD-01', roadName: 'Velachery Main Road', corridor: 'Velachery → Guindy',
    floodDepthCm: 68, status: 'CLOSED', recommendedAction: 'Use alternate route via Taramani Link Road',
    path: [{ lat: 12.9816, lng: 80.218 }, { lat: 12.993, lng: 80.2195 }, { lat: 13.0067, lng: 80.2206 }],
  },
  {
    id: 'RD-02', roadName: 'Adyar Bridge Approach', corridor: 'Adyar → Besant Nagar',
    floodDepthCm: 42, status: 'RESTRICTED', recommendedAction: 'Emergency vehicles only',
    path: [{ lat: 13.0105, lng: 80.2647 }, { lat: 13.008, lng: 80.272 }],
  },
  {
    id: 'RD-03', roadName: 'Perungudi Link Road', corridor: 'Perungudi → Sholinganallur',
    floodDepthCm: 31, status: 'WARNING', recommendedAction: 'Monitor continuously; reduce speed',
    path: [{ lat: 12.9698, lng: 80.2435 }, { lat: 12.945, lng: 80.238 }, { lat: 12.923, lng: 80.23 }],
  },
  {
    id: 'RD-04', roadName: 'Madley Subway Underpass', corridor: 'T. Nagar → Saidapet',
    floodDepthCm: 63, status: 'CLOSED', recommendedAction: 'Divert via GN Chetty Rd flyover',
    path: [{ lat: 13.0418, lng: 80.2341 }, { lat: 13.032, lng: 80.2285 }],
  },
  {
    id: 'RD-05', roadName: 'Kathipara Grade Separator', corridor: 'Guindy → Airport',
    floodDepthCm: 4, status: 'OPEN', recommendedAction: 'Preferred emergency corridor',
    path: [{ lat: 13.0067, lng: 80.2206 }, { lat: 12.998, lng: 80.21 }, { lat: 12.99, lng: 80.193 }],
  },
];

const RESCUE_PATH = [
  { lat: 13.0067, lng: 80.2206 }, { lat: 12.998, lng: 80.232 },
  { lat: 12.9867, lng: 80.2433 }, { lat: 12.9816, lng: 80.218 },
];

export function planSafeRoute(vehicle: VehicleKind): SafeRoutePlan {
  const base = {
    CAR: { name: 'Kathipara → Taramani → Velachery relief corridor', distanceKm: 9.4, etaMin: 26, maxDepthCm: 12 },
    SUV: { name: 'Kathipara → Guindy Estate → Velachery lowland edge', distanceKm: 8.1, etaMin: 22, maxDepthCm: 22 },
    TRUCK: { name: 'Airport Rd → Pallavaram → Velachery bypass', distanceKm: 12.6, etaMin: 34, maxDepthCm: 18 },
    RESCUE: { name: 'Rescue priority corridor (open roads, min depth)', distanceKm: 7.3, etaMin: 17, maxDepthCm: 8 },
  }[vehicle];
  return { vehicle, path: RESCUE_PATH, ...base };
}

export const SIM_SHELTERS: Shelter[] = [
  { id: 'SH-01', name: 'Taramani Relief Shelter', lat: 12.9867, lng: 80.2433, capacity: 800, occupied: 312 },
  { id: 'SH-02', name: 'Guindy Community Hall', lat: 13.0025, lng: 80.2125, capacity: 500, occupied: 148 },
  { id: 'SH-03', name: 'Perungudi School Shelter', lat: 12.9698, lng: 80.2485, capacity: 650, occupied: 401 },
];

export const SIM_ARCHIVE: StormArchiveEntry[] = [
  { id: 'ST-06', eventName: 'Northeast Monsoon Burst VI', eventDate: '2025-11-18', peakRainfallMmh: 88.4, maxDepthCm: 61, affectedZones: ['Velachery Lowland', 'Adyar River Corridor'], leadTimeMin: 52, isDemo: true },
  { id: 'ST-05', eventName: 'Northeast Monsoon Burst V', eventDate: '2025-11-02', peakRainfallMmh: 74.1, maxDepthCm: 48, affectedZones: ['Madley Subway / T. Nagar', 'Mudichur / Adyar Buffer'], leadTimeMin: 44, isDemo: true },
  { id: 'ST-04', eventName: 'Cyclonic Inflow Event IV', eventDate: '2025-10-21', peakRainfallMmh: 96.7, maxDepthCm: 68, affectedZones: ['Marina Coastal Lowland', 'Adyar River Corridor'], leadTimeMin: 58, isDemo: true },
  { id: 'ST-03', eventName: 'Convective Storm Cell III', eventDate: '2025-09-30', peakRainfallMmh: 62.3, maxDepthCm: 35, affectedZones: ['Ambattur Industrial Corridor'], leadTimeMin: 31, isDemo: true },
  { id: 'ST-02', eventName: 'Monsoon Trough Event II', eventDate: '2025-09-12', peakRainfallMmh: 55.8, maxDepthCm: 29, affectedZones: ['Perungudi Basin', 'Sholinganallur fringe'], leadTimeMin: 39, isDemo: true },
  { id: 'ST-01', eventName: 'Pre-monsoon Squall I', eventDate: '2025-08-27', peakRainfallMmh: 41.2, maxDepthCm: 16, affectedZones: ['Kathipara / Guindy Elevated'], leadTimeMin: 28, isDemo: true },
];

export const SIM_HEALTH: HealthCheck[] = [
  { id: 'radar', label: 'Doppler Radar', status: 'ONLINE', detail: 'Chennai Port Trust radar · sweep 6 min ago' },
  { id: 'rain', label: 'Rainfall Feed', status: 'ONLINE', detail: 'GCC AWS network · 64 stations reporting' },
  { id: 'floodmodel', label: 'Flood Model', status: 'ONLINE', detail: 'Nowcast surrogate · inference 38 ms' },
  { id: 'drainmodel', label: 'Drainage Model', status: 'DEGRADED', detail: '2 outfall sensors stale > 15 min' },
  { id: 'db', label: 'Database', status: 'ONLINE', detail: 'Primary reachable · replication lag 2 s' },
  { id: 'api', label: 'FastAPI Backend', status: 'OFFLINE', detail: 'EOC feed endpoints unreachable — simulation active' },
];
