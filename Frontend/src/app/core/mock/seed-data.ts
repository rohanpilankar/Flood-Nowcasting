import { FloodZone, RoadSegment, SystemKPIs, RecentPrediction, PredictionTime } from '../models/flood-risk.model';
import { FloodAlert } from '../models/alert.model';
import { RoutePlanResult, PresetRoute } from '../models/route.model';
import { AnalyticsSummary } from '../models/analytics.model';
import { AdminSystemOverview } from '../models/system-status.model';

export const SEED_SYSTEM_KPIS: SystemKPIs = {
  currentRainfall: 28.4,
  rainfallDelta: '+4.2 mm/hr vs last hour',
  highRiskZones: 12,
  highRiskDelta: '2 more than previous hour',
  unsafeRoads: 3,
  unsafeRoadsStatus: 'Gengu Reddy, Madley & RBI Subways Monitored',
  activeAlerts: 3,
  highPriorityAlerts: 2,
  lastUpdated: 'Live GCC IMD AWS Pipeline • Chennai Baseline',
  isSimulated: true
};

export const SEED_RECENT_PREDICTIONS: RecentPrediction[] = [
  { location: 'Velachery Lake Catchment', currentRisk: 'HIGH', plus1HourRisk: 'CRITICAL', plus3HoursRisk: 'HIGH', confidence: 94, isSimulated: true },
  { location: 'Madley Subway (T. Nagar)', currentRisk: 'HIGH', plus1HourRisk: 'CRITICAL', plus3HoursRisk: 'MEDIUM', confidence: 95, isSimulated: true },
  { location: 'Gengu Reddy Subway (Egmore)', currentRisk: 'HIGH', plus1HourRisk: 'CRITICAL', plus3HoursRisk: 'MEDIUM', confidence: 96, isSimulated: true },
  { location: 'Mudichur / Tambaram Basin', currentRisk: 'MEDIUM', plus1HourRisk: 'HIGH', plus3HoursRisk: 'MEDIUM', confidence: 90, isSimulated: true },
  { location: 'Perambur Barracks Road', currentRisk: 'MEDIUM', plus1HourRisk: 'HIGH', plus3HoursRisk: 'LOW', confidence: 87, isSimulated: true },
  { location: 'Anna Nagar West Extension', currentRisk: 'LOW', plus1HourRisk: 'LOW', plus3HoursRisk: 'LOW', confidence: 92, isSimulated: true },
  { location: 'Guindy Industrial Estate', currentRisk: 'LOW', plus1HourRisk: 'MEDIUM', plus3HoursRisk: 'LOW', confidence: 85, isSimulated: true }
];

export const SEED_FLOOD_ZONES: FloodZone[] = [
  {
    gridId: 'CHN_G101',
    name: 'Velachery Lake Catchment Basin',
    latitude: 12.9815,
    longitude: 80.2180,
    bounds: [[12.975, 80.210], [12.988, 80.226]],
    riskLevel: 'HIGH',
    riskScore: 92,
    predictionTime: 'NOW',
    rainfall: 46.5,
    elevation: 4.8,
    waterDepth: 0.50,
    runoffCoefficient: 0.91,
    slope: 'Low',
    summary: 'Low-lying marsh depression basin with severe runoff accumulation and chronic SWD outfall congestion.',
    historicalFlooding: 'Severe',
    drainageStatus: 'Critical',
    builtUpDensity: 92,
    isSimulated: true
  },
  {
    gridId: 'CHN_G102',
    name: 'Madley Subway Underpass (T. Nagar)',
    latitude: 13.0418,
    longitude: 80.2335,
    bounds: [[13.035, 80.226], [13.048, 80.241]],
    riskLevel: 'HIGH',
    riskScore: 95,
    predictionTime: 'NOW',
    rainfall: 51.2,
    elevation: 3.5,
    waterDepth: 0.65,
    runoffCoefficient: 0.94,
    slope: 'Low',
    summary: 'Railway underpass depression prone to rapid inundation during intense convective bursts.',
    historicalFlooding: 'Severe',
    drainageStatus: 'Critical',
    builtUpDensity: 96,
    isSimulated: true
  },
  {
    gridId: 'CHN_G103',
    name: 'Gengu Reddy Subway (Egmore)',
    latitude: 13.0780,
    longitude: 80.2605,
    bounds: [[13.071, 80.253], [13.085, 80.268]],
    riskLevel: 'HIGH',
    riskScore: 94,
    predictionTime: 'NOW',
    rainfall: 49.0,
    elevation: 3.2,
    waterDepth: 0.68,
    runoffCoefficient: 0.92,
    slope: 'Low',
    summary: 'Subway choke point near Egmore connecting central arterials; prone to backflow from Cooum outfalls.',
    historicalFlooding: 'Severe',
    drainageStatus: 'Critical',
    builtUpDensity: 93,
    isSimulated: true
  },
  {
    gridId: 'CHN_G104',
    name: 'Mudichur / Adyar River Confluence',
    latitude: 12.9150,
    longitude: 80.0820,
    bounds: [[12.905, 80.072], [12.925, 80.092]],
    riskLevel: 'MEDIUM',
    riskScore: 78,
    predictionTime: 'NOW',
    rainfall: 42.0,
    elevation: 8.5,
    waterDepth: 0.35,
    runoffCoefficient: 0.82,
    slope: 'Low',
    summary: 'Adyar River floodplain buffer zone affected during Chembarambakkam reservoir release windows.',
    historicalFlooding: 'High',
    drainageStatus: 'Moderate',
    builtUpDensity: 80,
    isSimulated: true
  },
  {
    gridId: 'CHN_G105',
    name: 'Perambur Barracks / Stephenson Road',
    latitude: 13.1050,
    longitude: 80.2520,
    bounds: [[13.097, 80.244], [13.113, 80.260]],
    riskLevel: 'MEDIUM',
    riskScore: 74,
    predictionTime: 'NOW',
    rainfall: 39.8,
    elevation: 5.1,
    waterDepth: 0.30,
    runoffCoefficient: 0.88,
    slope: 'Low',
    summary: 'Otteri Nullah overflow corridor affecting low-lying North Chennai residential wards.',
    historicalFlooding: 'High',
    drainageStatus: 'Moderate',
    builtUpDensity: 90,
    isSimulated: true
  },
  {
    gridId: 'CHN_G106',
    name: 'Anna Nagar West Extension',
    latitude: 13.0890,
    longitude: 80.2010,
    bounds: [[13.080, 80.192], [13.098, 80.210]],
    riskLevel: 'LOW',
    riskScore: 26,
    predictionTime: 'NOW',
    rainfall: 32.0,
    elevation: 11.2,
    waterDepth: 0.06,
    runoffCoefficient: 0.74,
    slope: 'Moderate',
    summary: 'Planned residential master sector with wide SWD collectors and gradual slope towards Cooum.',
    historicalFlooding: 'Low',
    drainageStatus: 'Operational',
    builtUpDensity: 82,
    isSimulated: true
  },
  {
    gridId: 'CHN_G107',
    name: 'Guindy Industrial Estate & Kathipara',
    latitude: 13.0080,
    longitude: 80.2080,
    bounds: [[12.999, 80.198], [13.017, 80.218]],
    riskLevel: 'LOW',
    riskScore: 22,
    predictionTime: 'NOW',
    rainfall: 30.5,
    elevation: 14.5,
    waterDepth: 0.04,
    runoffCoefficient: 0.72,
    slope: 'Moderate',
    summary: 'Kathipara elevated grade separator and surrounding industrial corridor with rapid gravity drainage.',
    historicalFlooding: 'Low',
    drainageStatus: 'Operational',
    builtUpDensity: 85,
    isSimulated: true
  },
  {
    gridId: 'CHN_G108',
    name: 'OMR IT Corridor (Taramani - Perungudi)',
    latitude: 12.9680,
    longitude: 80.2450,
    bounds: [[12.958, 80.235], [12.978, 80.255]],
    riskLevel: 'LOW',
    riskScore: 29,
    predictionTime: 'NOW',
    rainfall: 34.0,
    elevation: 6.8,
    waterDepth: 0.08,
    runoffCoefficient: 0.79,
    slope: 'Low',
    summary: 'Elevated arterial road; service lanes adjacent to Buckingham Canal require localized monitoring.',
    historicalFlooding: 'Low',
    drainageStatus: 'Operational',
    builtUpDensity: 84,
    isSimulated: true
  }
];

export const SEED_ROAD_SEGMENTS: RoadSegment[] = [
  {
    id: 'RD-CHN-01',
    name: 'Madley Subway Underpass',
    status: 'BLOCKED',
    riskScore: 95,
    waterDepthCm: 65,
    coordinates: [[13.040, 80.232], [13.042, 80.234], [13.044, 80.235]],
    avoidedBySafeRoute: true,
    locality: 'T. Nagar'
  },
  {
    id: 'RD-CHN-02',
    name: 'Gengu Reddy Subway Underpass',
    status: 'UNSAFE',
    riskScore: 91,
    waterDepthCm: 58,
    coordinates: [[13.076, 80.259], [13.078, 80.261], [13.080, 80.262]],
    avoidedBySafeRoute: true,
    locality: 'Egmore'
  },
  {
    id: 'RD-CHN-03',
    name: 'RBI Subway Underpass',
    status: 'BLOCKED',
    riskScore: 93,
    waterDepthCm: 70,
    coordinates: [[13.086, 80.287], [13.088, 80.289], [13.090, 80.291]],
    avoidedBySafeRoute: true,
    locality: 'George Town'
  },
  {
    id: 'RD-CHN-04',
    name: 'Velachery Main Road (Near Lake)',
    status: 'CAUTION',
    riskScore: 68,
    waterDepthCm: 25,
    coordinates: [[12.978, 80.215], [12.981, 80.218], [12.985, 80.222]],
    avoidedBySafeRoute: false,
    locality: 'Velachery'
  },
  {
    id: 'RD-CHN-05',
    name: 'Anna Salai / Mount Road Arterial',
    status: 'SAFE',
    riskScore: 18,
    waterDepthCm: 4,
    coordinates: [[13.010, 80.210], [13.045, 80.245], [13.070, 80.265], [13.082, 80.275]],
    avoidedBySafeRoute: false,
    locality: 'Mount Road Corridor'
  },
  {
    id: 'RD-CHN-06',
    name: 'GST Road Elevated Corridor',
    status: 'SAFE',
    riskScore: 14,
    waterDepthCm: 2,
    coordinates: [[12.980, 80.170], [13.000, 80.195], [13.015, 80.215]],
    avoidedBySafeRoute: false,
    locality: 'GST Highway'
  }
];

export const SEED_ALERTS: FloodAlert[] = [
  {
    id: 'ALT-CHN-101',
    title: 'Severe Inundation — Madley Subway Underpass',
    severity: 'HIGH',
    location: 'Madley Subway, T. Nagar',
    coordinates: [13.0418, 80.2335],
    description: 'Depression depth reaches critical threshold due to high rainfall intensity. Greater Chennai Traffic Police have placed traffic barriers.',
    riskScore: 95,
    predictionHorizon: '+30 Minutes',
    generatedTime: '3 minutes ago',
    timestamp: '2026-09-06T15:30:00Z',
    acknowledged: false,
    aiConfidence: 95,
    recommendedAction: 'Divert all westbound traffic via Usman Road Flyover or North Usman Road.',
    isSimulated: true
  },
  {
    id: 'ALT-CHN-102',
    title: 'Extreme Waterlogging Risk — Velachery Lake Catchment',
    severity: 'HIGH',
    location: 'Velachery Bypass Road, Velachery',
    coordinates: [12.9815, 80.2180],
    description: 'Runoff accumulation along low-lying residential sectors. SWD macro drains flowing at near-bankfull capacity.',
    riskScore: 91,
    predictionHorizon: '+1 Hour',
    generatedTime: '8 minutes ago',
    timestamp: '2026-09-06T15:25:00Z',
    acknowledged: false,
    aiConfidence: 94,
    recommendedAction: 'Caution advised for two-wheelers. Utilize Inner Ring Road elevated ramps where available.',
    isSimulated: true
  },
  {
    id: 'ALT-CHN-103',
    title: 'Subway Waterlogging — Gengu Reddy Subway',
    severity: 'HIGH',
    location: 'Gengu Reddy Subway, Egmore',
    coordinates: [13.0780, 80.2605],
    description: 'Subway water levels rising. Dewatering diesel pumps activated by GCC storm water team.',
    riskScore: 92,
    predictionHorizon: '+30 Minutes',
    generatedTime: '12 minutes ago',
    timestamp: '2026-09-06T15:20:00Z',
    acknowledged: false,
    aiConfidence: 96,
    recommendedAction: 'Subway traffic diverted via EVR Periyar Salai (Poonamallee High Road).',
    isSimulated: true
  },
  {
    id: 'ALT-CHN-104',
    title: 'Moderate Overflow Risk — Mudichur Basin',
    severity: 'MEDIUM',
    location: 'Mudichur Road, Tambaram Catchment',
    coordinates: [12.9150, 80.0820],
    description: 'Elevated water stages along Adyar buffer zone. Precautionary monitoring active.',
    riskScore: 72,
    predictionHorizon: '+2 Hours',
    generatedTime: '24 minutes ago',
    timestamp: '2026-09-06T15:08:00Z',
    acknowledged: false,
    aiConfidence: 90,
    recommendedAction: 'Local monitoring advised for low-lying layouts. Heavy vehicles unaffected.',
    isSimulated: true
  }
];

export const SEED_PRESET_ROUTES: PresetRoute[] = [
  {
    id: 'PRESET_CHN_CEN_AIR',
    label: 'Chennai Central to Chennai Airport (Via Anna Salai & GST Road)',
    source: 'Chennai Central',
    destination: 'Chennai Airport',
    description: 'Prioritizes high-ground arterial Anna Salai and elevated GST Road, avoiding submerged railway subways.'
  },
  {
    id: 'PRESET_TNG_ADY',
    label: 'T. Nagar to Adyar (Via Chamier’s Road / Kotturpuram)',
    source: 'T. Nagar',
    destination: 'Adyar',
    description: 'Bypasses Madley Subway and low-elevation pockets around Panagal Park.'
  },
  {
    id: 'PRESET_EGM_VLC',
    label: 'Egmore to Velachery (Via Mount Road & Inner Ring Road)',
    source: 'Egmore',
    destination: 'Velachery',
    description: 'Safely redirects away from Gengu Reddy Subway and Gandhi Irwin low points.'
  },
  {
    id: 'PRESET_AMB_OMR',
    label: 'Ambattur to OMR IT Corridor (Via Bypass & Guindy)',
    source: 'Ambattur',
    destination: 'OMR Taramani',
    description: 'Connects western industrial zone to southeastern IT corridor via elevated bypass corridors.'
  }
];

export const SEED_ROUTE_PLAN: RoutePlanResult = {
  source: 'Chennai Central',
  destination: 'Chennai Airport',
  sourceCoords: [13.0827, 80.2707],
  destCoords: [12.9850, 80.1693],
  recommendedRoute: {
    id: 'ROUTE_SAFE_CHENNAI',
    name: 'High-Ground Arterial Bypass (Central -> Anna Salai -> Guindy -> GST Road -> Airport)',
    type: 'RECOMMENDED_SAFE',
    distanceKm: 18.2,
    etaMinutes: 42,
    safetyScore: 95,
    riskStatus: 'SAFE',
    floodPointsAvoided: 3,
    hazardExposure: 'Low',
    pathCoordinates: [
      [13.0827, 80.2707],
      [13.0600, 80.2550],
      [13.0150, 80.2150],
      [12.9850, 80.1693]
    ],
    notes: 'Route prioritizes elevated Anna Salai and Kathipara grade separator, completely avoiding submerged railway subways.',
    isSimulated: true
  },
  alternativeRoute: {
    id: 'ROUTE_ALT_CHENNAI',
    name: 'Surface Low-Elevation Route (Via Egmore Subway & Velachery Basin)',
    type: 'FASTER_ALTERNATIVE',
    distanceKm: 16.5,
    etaMinutes: 55,
    safetyScore: 42,
    riskStatus: 'UNSAFE',
    floodPointsAvoided: 0,
    hazardExposure: 'High',
    pathCoordinates: [
      [13.0827, 80.2707],
      [13.0780, 80.2605],
      [13.0418, 80.2335],
      [12.9815, 80.2180],
      [12.9850, 80.1693]
    ],
    notes: 'Direct surface path, but encounters severe waterlogging hazards at Madley Subway and low-lying Velachery catchment.',
    isSimulated: true
  },
  hazards: [
    {
      id: 'HAZ_CHN_01',
      title: 'Madley Subway Depression',
      location: 'Madley Subway (T. Nagar)',
      coordinates: [13.0418, 80.2335],
      severity: 'UNSAFE',
      waterDepthCm: 65,
      status: 'Depression flooded (-2.5m underpass) • Impassable for light vehicles',
      isSimulated: true
    },
    {
      id: 'HAZ_CHN_02',
      title: 'Gengu Reddy Subway Choke',
      location: 'Gengu Reddy Subway (Egmore)',
      coordinates: [13.0780, 80.2605],
      severity: 'UNSAFE',
      waterDepthCm: 58,
      status: 'Subway waterlogged • Traffic diverted to EVR Salai',
      isSimulated: true
    },
    {
      id: 'HAZ_CHN_03',
      title: 'Velachery Low Basin Inundation',
      location: 'Velachery Main Road Basin',
      coordinates: [12.9815, 80.2180],
      severity: 'UNSAFE',
      waterDepthCm: 50,
      status: 'Severe waterlogging • Water level exceeding road surface threshold',
      isSimulated: true
    }
  ],
  isSimulated: true
};

export const SEED_ANALYTICS_SUMMARY: AnalyticsSummary = {
  rainfallTrends: [
    { time: '09:00 AM', rainfallMm: 10.5, cumulativeMm: 10.5, isSimulated: true },
    { time: '10:00 AM', rainfallMm: 16.2, cumulativeMm: 26.7, isSimulated: true },
    { time: '11:00 AM', rainfallMm: 24.8, cumulativeMm: 51.5, isSimulated: true },
    { time: '12:00 PM', rainfallMm: 31.0, cumulativeMm: 82.5, isSimulated: true },
    { time: '01:00 PM', rainfallMm: 38.4, cumulativeMm: 120.9, isSimulated: true },
    { time: '02:00 PM', rainfallMm: 35.0, cumulativeMm: 155.9, isSimulated: true },
    { time: '03:00 PM', rainfallMm: 42.1, cumulativeMm: 198.0, isSimulated: true }
  ],
  riskDistribution: {
    noRisk: 1450,
    low: 1820,
    medium: 510,
    high: 165,
    critical: 18
  },
  areaRankings: [
    { rank: 1, area: 'Madley Subway (T. Nagar)', riskScore: 95, trend: 'INCREASING', rainfall: 51.2, elevation: 3.5 },
    { rank: 2, area: 'Gengu Reddy Subway (Egmore)', riskScore: 94, trend: 'INCREASING', rainfall: 49.0, elevation: 3.2 },
    { rank: 3, area: 'Velachery Lake Catchment', riskScore: 92, trend: 'INCREASING', rainfall: 46.5, elevation: 4.8 },
    { rank: 4, area: 'Mudichur / Tambaram Basin', riskScore: 78, trend: 'STABLE', rainfall: 42.0, elevation: 8.5 },
    { rank: 5, area: 'Perambur Barracks Road', riskScore: 74, trend: 'STABLE', rainfall: 39.8, elevation: 5.1 },
    { rank: 6, area: 'Vyasarpadi Jeeva Subway', riskScore: 71, trend: 'DECREASING', rainfall: 36.5, elevation: 4.2 },
    { rank: 7, area: 'Adyar Canal Buffer Zone', riskScore: 62, trend: 'DECREASING', rainfall: 34.0, elevation: 6.0 }
  ],
  inundationHistory: [
    { hour: '-6h', avgWaterDepthCm: 6.5, affectedRoadsCount: 2 },
    { hour: '-4h', avgWaterDepthCm: 14.0, affectedRoadsCount: 3 },
    { hour: '-2h', avgWaterDepthCm: 28.5, affectedRoadsCount: 7 },
    { hour: 'NOW', avgWaterDepthCm: 44.0, affectedRoadsCount: 12 },
    { hour: '+1h', avgWaterDepthCm: 51.5, affectedRoadsCount: 15 },
    { hour: '+2h', avgWaterDepthCm: 38.0, affectedRoadsCount: 9 }
  ],
  peakRainfallLocality: 'Nungambakkam IMD AWS (51.2 mm/hr peak intensity)',
  totalVulnerablePopulation: '1,280,000 across 8 Low-Lying GCC Wards',
  isSimulated: true
};

export const SEED_ADMIN_SYSTEM_OVERVIEW: AdminSystemOverview = {
  dataFeeds: [
    {
      name: 'IMD Chennai Doppler Weather Radar (Port Trust)',
      category: 'RADAR',
      status: 'OPERATIONAL',
      lastUpdate: '2 min ago',
      sampleFrequency: '10 min',
      sourceType: 'S-Band Dual Polarimetric Doppler',
      isSimulated: false
    },
    {
      name: 'GCC & IMD Automatic Weather Stations (AWS)',
      category: 'IOT',
      status: 'OPERATIONAL',
      lastUpdate: 'Just now',
      sampleFrequency: '15 min',
      sourceType: 'Telemetric Rain Gauges (Meenambakkam, Nungambakkam, etc.)',
      isSimulated: false
    },
    {
      name: 'Greater Chennai GIS Cadastral & 500m Grid (EPSG:4326)',
      category: 'GIS',
      status: 'OPERATIONAL',
      lastUpdate: 'Static Master (3,963 Cells)',
      sampleFrequency: 'Permanent',
      sourceType: 'Copernicus 30m DEM & GCC Wards',
      isSimulated: false
    },
    {
      name: 'Chennai Arterial & Underpass Road Graph',
      category: 'ROAD_NETWORK',
      status: 'OPERATIONAL',
      lastUpdate: 'Continuous',
      sampleFrequency: 'Event-driven',
      sourceType: 'NetworkX Dynamic Dijkstra Graph',
      isSimulated: false
    },
    {
      name: 'Chennai Historical Inundation Hotspot Registry',
      category: 'HISTORICAL',
      status: 'OPERATIONAL',
      lastUpdate: 'Benchmark Registry',
      sampleFrequency: 'Annual',
      sourceType: 'GCC Disaster Management & TNDMA',
      isSimulated: false
    }
  ],
  modelMetrics: {
    name: 'Chennai Spatial Flood Susceptibility Baseline (XGBoost)',
    version: 'XGBoost-v1.0-Chennai',
    status: 'ACTIVE_BASELINE',
    algorithm: 'Gradient Boosted Decision Trees (XGBoostClassifier)',
    prototypeF1Score: 0.5110,
    prototypePrecision: 0.4247,
    prototypeRecall: 0.8675,
    prototypeAccuracy: 0.8675,
    simulatedInferenceLatencyMs: 32.0,
    featureCount: 25,
    lastTrained: 'Chronological Historical Baseline (2020-2024)',
    isSimulated: false
  },
  microservices: [
    {
      name: 'FastAPI Core Gateway',
      endpoint: 'http://localhost:8000/api/v1',
      status: 'OPERATIONAL',
      latencyMs: 12.5,
      uptime: '99.98%',
      version: '2.0.0',
      isMock: false
    },
    {
      name: 'XGBoost Baseline Inference Worker',
      endpoint: 'internal://engine.predict_grids',
      status: 'OPERATIONAL',
      latencyMs: 32.0,
      uptime: '100.0%',
      version: 'XGBoost-v1.0-Chennai',
      isMock: false
    },
    {
      name: 'NetworkX Safe Routing Dijkstra Engine',
      endpoint: 'internal://engine.calculate_safe_route',
      status: 'OPERATIONAL',
      latencyMs: 8.2,
      uptime: '100.0%',
      version: 'v1.2',
      isMock: false
    },
    {
      name: 'GCC IMD Rain Gauge Telemetry Worker',
      endpoint: 'internal://data.pipeline.telemetry',
      status: 'OPERATIONAL',
      latencyMs: 18.0,
      uptime: '99.95%',
      version: 'v1.0',
      isMock: false
    }
  ],
  systemLoad: {
    cpuPercent: 16.2,
    memoryPercent: 38.5,
    activeQueriesPerSec: 22.4
  },
  sihDisclaimer: {
    projectCode: 'SIH26085',
    notice: 'Trained on Greater Chennai 500m spatial grid with 25 topographical, hydrological, and rainfall features.',
    phase: 'Phase 2 — End-to-End Chennai Nowcasting + Safe Mobility'
  }
};

export const SEED_ANALYTICS: AnalyticsSummary = SEED_ANALYTICS_SUMMARY;
export const SEED_ADMIN_SYSTEM: AdminSystemOverview = SEED_ADMIN_SYSTEM_OVERVIEW;

export const SEED_ROUTE_PLANS: Record<string, RoutePlanResult> = {
  'Central_Airport': SEED_ROUTE_PLAN,
  'Chennai Central_Chennai Airport': SEED_ROUTE_PLAN,
  'Velachery_TNagar': SEED_ROUTE_PLAN,
  'Velachery_T. Nagar': SEED_ROUTE_PLAN,
  'T. Nagar_Adyar': {
    ...SEED_ROUTE_PLAN,
    source: 'T. Nagar',
    destination: 'Adyar',
    sourceCoords: [13.0418, 80.2335],
    destCoords: [13.0060, 80.2570]
  },
  'Egmore_Velachery': {
    ...SEED_ROUTE_PLAN,
    source: 'Egmore',
    destination: 'Velachery',
    sourceCoords: [13.0780, 80.2605],
    destCoords: [12.9815, 80.2180]
  }
};
