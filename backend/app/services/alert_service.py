"""
Alert Service Layer
Manages GCC Emergency Operations Center and Citizen flood alerts.
Adheres strictly to the alert lifecycle: ACTIVE, ACKNOWLEDGED, RESOLVED.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import uuid


class AlertService:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.alerts_db = self._init_chennai_alerts()

    def _init_chennai_alerts(self) -> List[Dict[str, Any]]:
        now_iso = datetime.now(timezone.utc).isoformat()
        return [
            {
                "id": "ALT-CHN-101",
                "title": "Severe Low-Lying Inundation Warning — Velachery Basin",
                "severity": "CRITICAL",
                "status": "ACTIVE",
                "location": "Velachery Lake & Gandhi Salai Corridor",
                "coordinates": [12.9815, 80.2180],
                "description": "Saucer depression index indicates severe water accumulation risk under heavy hydrologic loading. Vulnerable low-lying residential sectors advised to avoid basement parking.",
                "reason": "Topographic depression (low_lying_score > 0.85) and high antecedent rainfall saturation.",
                "riskScore": 92,
                "predictionHorizon": "NOW",
                "generatedTime": "5 minutes ago",
                "timestamp": now_iso,
                "acknowledged": False,
                "aiConfidence": 94,
                "source": "Chennai XGBoost Baseline Susceptibility Model",
                "recommendedAction": "Avoid low-lying internal roads near Velachery Lake; utilize elevated Taramani Link Road corridor.",
                "isSimulated": False
            },
            {
                "id": "ALT-CHN-102",
                "title": "Hydrologic Spillage Advisory — Adyar River Corridor",
                "severity": "WARNING",
                "status": "ACTIVE",
                "location": "Adyar River Basin (Saidapet / Kotturpuram)",
                "coordinates": [13.0180, 80.2220],
                "description": "Upstream reservoir discharge and localized basin rainfall elevate surface stream water levels. Embankment vigilance in effect.",
                "reason": "River proximity corridor (< 250m) during active Northeast Monsoon event.",
                "riskScore": 84,
                "predictionHorizon": "NOW",
                "generatedTime": "12 minutes ago",
                "timestamp": now_iso,
                "acknowledged": False,
                "aiConfidence": 91,
                "source": "GCC Emergency Operations Center",
                "recommendedAction": "Maintain distance from riverbank service roads; follow traffic police diversions across Maraimalai Adigal Bridge.",
                "isSimulated": False
            },
            {
                "id": "ALT-CHN-103",
                "title": "Underpass Transit Advisory — Vyasarpadi Subway",
                "severity": "WARNING",
                "status": "ACTIVE",
                "location": "Vyasarpadi Railway Subway, North Chennai",
                "coordinates": [13.1185, 80.2615],
                "description": "Low-elevation railway underpass subject to surface runoff pooling. Motorists advised to verify passability before proceeding.",
                "reason": "Depressed underpass geometry prone to localized runoff collection.",
                "riskScore": 78,
                "predictionHorizon": "NOW",
                "generatedTime": "20 minutes ago",
                "timestamp": now_iso,
                "acknowledged": False,
                "aiConfidence": 88,
                "source": "GCC Traffic Advisory",
                "recommendedAction": "Risk-based avoidance: prefer elevated Perambur Flyover route.",
                "isSimulated": False
            },
            {
                "id": "ALT-CHN-104",
                "title": "Waterlogging Advisory — Madipakkam Lake Fringe",
                "severity": "WATCH",
                "status": "ACTIVE",
                "location": "Madipakkam Puzhuthivakkam Lowlands",
                "coordinates": [12.9640, 80.1980],
                "description": "High impervious built-up density coupled with low topographic elevation causes surface ponding on secondary link streets.",
                "reason": "High built-up ratio with flat gradient (< 1 degree).",
                "riskScore": 68,
                "predictionHorizon": "NOW",
                "generatedTime": "35 minutes ago",
                "timestamp": now_iso,
                "acknowledged": True,
                "aiConfidence": 86,
                "source": "Chennai XGBoost Baseline Model",
                "recommendedAction": "Slow transit speeds; use primary arterial Medavakkam Main Road.",
                "isSimulated": False
            }
        ]

    def get_alerts(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        if status:
            return [a for a in self.alerts_db if a.get("status", "ACTIVE").upper() == status.upper()]
        return self.alerts_db

    def acknowledge_alert(self, alert_id: str) -> Optional[Dict[str, Any]]:
        for a in self.alerts_db:
            if a["id"] == alert_id:
                a["acknowledged"] = True
                a["status"] = "ACKNOWLEDGED"
                return a
        return None

    def resolve_alert(self, alert_id: str) -> Optional[Dict[str, Any]]:
        for a in self.alerts_db:
            if a["id"] == alert_id:
                a["status"] = "RESOLVED"
                return a
        return None

    def create_alert(self, data: Dict[str, Any]) -> Dict[str, Any]:
        alert = {
            "id": f"ALT-CHN-{uuid.uuid4().hex[:6].upper()}",
            "title": data.get("title", "GCC Disaster Alert"),
            "severity": data.get("severity", "WARNING"),
            "status": "ACTIVE",
            "location": data.get("location", "Greater Chennai"),
            "coordinates": data.get("coordinates", [13.0827, 80.2707]),
            "description": data.get("description", ""),
            "reason": data.get("reason", "Operator Broadcast"),
            "riskScore": data.get("riskScore", 75),
            "predictionHorizon": "NOW",
            "generatedTime": "Just now",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "acknowledged": False,
            "aiConfidence": 90,
            "source": data.get("source", "GCC EOC Operator Dispatch"),
            "recommendedAction": data.get("recommendedAction", "Exercise heightened caution."),
            "isSimulated": False
        }
        self.alerts_db.insert(0, alert)
        return alert
