# FloodWatch AI — API Specification (v2.0.0)

## SIH26085 — AI-Powered Urban Flood Nowcasting and Safe Mobility System

FastAPI Gateway Base URL: `http://localhost:8000/api/v1`  
Interactive Swagger Docs: `http://localhost:8000/docs`  
ReDoc Docs: `http://localhost:8000/redoc`

---

## 1. System Health & Metadata

### `GET /`
Returns top-level project metadata and endpoints.

### `GET /api/v1/health`
Returns gateway and microservice liveness.

**Response**:
```json
{
  "status": "healthy",
  "service": "FloodWatch AI API Gateway",
  "study_area": "Greater Mumbai (BMC)",
  "model": "XGBoost-v2.0-Mumbai",
  "timestamp": "now"
}
```

### `GET /api/v1/health/system-overview`
Returns complete MLOps telemetry, data feeds status, model evaluation card, and hardware loads.

---

## 2. Flood Nowcasting & Geospatial Telemetry

### `GET /api/v1/current-risk/kpis`
Returns live municipal KPIs across Greater Mumbai.

**Response**:
```json
{
  "currentRainfall": 32.2,
  "rainfallDelta": "+6.4 mm/hr vs last hour",
  "highRiskZones": 1584,
  "highRiskDelta": "+3 zones expanding east",
  "unsafeRoads": 3,
  "unsafeRoadsStatus": "Hindmata, Milan & Andheri Subways Blocked",
  "activeAlerts": 4,
  "highPriorityAlerts": 3,
  "lastUpdated": "10:30 UTC • Live BMC AWS Pipeline",
  "isSimulated": false
}
```

### `GET /api/v1/forecast-risk`
Returns high-resolution 500m grid sector predictions for the requested horizon.

**Query Parameters**:
* `horizon` (string, optional, default: `"NOW"`): Temporal nowcasting horizon (`NOW`, `+30M`, `+1H`, `+2H`, `+3H`).

**Response**: `Array<FloodZone>`
```json
[
  {
    "gridId": "MUM_000001",
    "name": "Colaba / Fort",
    "latitude": 18.8977,
    "longitude": 72.7873,
    "bounds": [[18.8955, 72.7851], [18.8999, 72.7895]],
    "riskLevel": "LOW",
    "riskScore": 22,
    "predictionTime": "NOW",
    "rainfall": 30.4,
    "elevation": 14.5,
    "waterDepth": 0.08,
    "runoffCoefficient": 0.72,
    "slope": "Low",
    "summary": "Colaba / Fort sector under LOW flood risk for horizon NOW.",
    "historicalFlooding": "Low",
    "drainageStatus": "Operational",
    "builtUpDensity": 72,
    "isSimulated": false
  }
]
```

### `GET /api/v1/map-data/zones/{grid_id}`
Returns telemetry for a specific 500m sector.

### `GET /api/v1/map-data/roads`
Returns flood status assigned to Mumbai arterial road segments.

---

## 3. Safe Mobility & Graph Dijkstra Routing

### `GET /api/v1/safe-route/presets`
Returns predefined Mumbai commute scenarios (e.g., Dadar to Andheri via WEH vs Milan Subway).

### `POST /api/v1/safe-route`
Calculates dynamic risk-penalized shortest path avoiding submerged roads vs direct surface route.

**Request Body**:
```json
{
  "source": "Dadar",
  "destination": "Andheri",
  "mode": "vehicle"
}
```

**Response**:
```json
{
  "source": "Dadar",
  "destination": "Andheri",
  "sourceCoords": [19.0178, 72.8478],
  "destCoords": [19.1197, 72.8441],
  "recommendedRoute": {
    "id": "ROUTE_SAFE_MUMBAI",
    "name": "Elevated Flyover Bypass (Dadar -> BKC -> Santacruz -> Andheri)",
    "type": "RECOMMENDED_SAFE",
    "distanceKm": 16.5,
    "etaMinutes": 38,
    "safetyScore": 94,
    "riskStatus": "SAFE",
    "floodPointsAvoided": 3,
    "hazardExposure": "Low",
    "pathCoordinates": [[19.0178, 72.8478], [19.0650, 72.8680], [19.0832, 72.8415], [19.1197, 72.8441]],
    "notes": "Route prioritizes elevated Western Express Highway flyovers and ridge arterials, completely avoiding submerged underpasses.",
    "isSimulated": false
  },
  "alternativeRoute": {
    "id": "ROUTE_ALT_MUMBAI",
    "name": "Surface Grade Direct Path (Hindmata & Milan Corridor)",
    "type": "FASTER_ALTERNATIVE",
    "distanceKm": 14.8,
    "etaMinutes": 48,
    "safetyScore": 45,
    "riskStatus": "UNSAFE",
    "floodPointsAvoided": 0,
    "hazardExposure": "High",
    "pathCoordinates": [[19.0178, 72.8478], [19.0125, 72.8428], [19.0350, 72.8600], [19.0832, 72.8415], [19.1197, 72.8441]],
    "notes": "Direct surface route, but encounters severe waterlogging at depressed railway subways and saucer depressions.",
    "isSimulated": false
  },
  "hazards": [
    {
      "id": "HAZ_MUM_01",
      "title": "Milan Subway Inundation",
      "location": "Milan Subway (Santacruz)",
      "coordinates": [19.0832, 72.8415],
      "severity": "UNSAFE",
      "waterDepthCm": 70,
      "status": "Submerged (-3.0m underpass) • Impassable for vehicular transit",
      "isSimulated": false
    }
  ],
  "isSimulated": false
}
```

---

## 4. Disaster Alerts

### `GET /api/v1/alerts`
Returns active emergency warnings and evacuation alerts.

### `PATCH /api/v1/alerts/{alert_id}/acknowledge`
Acknowledges a specific alert by EOC incident commanders.

---

## 5. Flood Analytics

### `GET /api/v1/analytics/summary`
Returns hourly rainfall curves, sector risk distribution, ranked vulnerable areas, and inundation timelines.
