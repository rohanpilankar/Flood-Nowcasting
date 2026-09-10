"""
Drainage Service Layer
Separates Surface Water Networks (Adyar, Cooum, Buckingham Canal) from Underground SWD network.
Adheres strictly to zero-fabrication: returns explicit network_data_unavailable for hydraulic surcharges.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from backend.app.schemas.provenance import ProvenanceStatus


class DrainageService:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        # Surface River Corridors & Primary Navigation Canals in Greater Chennai
        self.surface_waterways = [
            {
                "id": "RIV-ADYAR",
                "name": "Adyar River Corridor",
                "type": "SURFACE_RIVER",
                "basin": "Adyar Basin",
                "coordinates": [
                    [12.9850, 80.0500], [12.9980, 80.1200], [13.0080, 80.1800],
                    [13.0110, 80.2200], [13.0125, 80.2500], [13.0090, 80.2780]
                ],
                "source": "GCC Basin Rivers GIS",
                "status": "GRAVITY_OUTFALL"
            },
            {
                "id": "RIV-COOUM",
                "name": "Cooum River Corridor",
                "type": "SURFACE_RIVER",
                "basin": "Cooum Basin",
                "coordinates": [
                    [13.0720, 80.1400], [13.0740, 80.1800], [13.0750, 80.2200],
                    [13.0760, 80.2550], [13.0690, 80.2850]
                ],
                "source": "GCC Basin Rivers GIS",
                "status": "GRAVITY_OUTFALL"
            },
            {
                "id": "CNL-BUCKINGHAM",
                "name": "Buckingham Canal (North-South Tidal Corridor)",
                "type": "CANAL",
                "basin": "Tidal Corridor",
                "coordinates": [
                    [13.1500, 80.2950], [13.1000, 80.2900], [13.0500, 80.2750],
                    [13.0000, 80.2550], [12.9500, 80.2500], [12.8700, 80.2450]
                ],
                "source": "GCC Buckingham Canal GIS",
                "status": "TIDAL_CONFLUENCE"
            },
            {
                "id": "RIV-KOSASTHALAIYAR",
                "name": "Kosasthalaiyar River (North Chennai Catchment)",
                "type": "SURFACE_RIVER",
                "basin": "Kosasthalaiyar Basin",
                "coordinates": [
                    [13.2000, 80.2200], [13.2150, 80.2600], [13.2300, 80.3100], [13.2250, 80.3300]
                ],
                "source": "GCC Basin Rivers GIS",
                "status": "GRAVITY_OUTFALL"
            }
        ]

        # Primary Underground GCC Storm Water Drain (SWD) Arteries
        self.underground_swd_corridors = [
            {
                "id": "SWD-VELACHERY",
                "name": "Velachery Macro Storm Drain Trunk",
                "type": "UNDERGROUND_SWD",
                "basin": "South Chennai SWD",
                "coordinates": [[12.9750, 80.2150], [12.9820, 80.2230], [12.9900, 80.2350]],
                "source": "GCC Storm Water Drains 2023 Vector",
                "status": "PASSIVE_GRAVITY"
            },
            {
                "id": "SWD-TNAGAR",
                "name": "T. Nagar - Mambalam Canal Feeder",
                "type": "UNDERGROUND_SWD",
                "basin": "Central Chennai SWD",
                "coordinates": [[13.0380, 80.2280], [13.0420, 80.2360], [13.0450, 80.2420]],
                "source": "GCC Storm Water Drains 2023 Vector",
                "status": "PASSIVE_GRAVITY"
            },
            {
                "id": "SWD-VYASARPADI",
                "name": "Vyasarpadi - Captain Cotton Canal Link",
                "type": "UNDERGROUND_SWD",
                "basin": "North Chennai SWD",
                "coordinates": [[13.1180, 80.2600], [13.1250, 80.2680], [13.1300, 80.2750]],
                "source": "GCC Storm Water Drains 2023 Vector",
                "status": "PASSIVE_GRAVITY"
            }
        ]

    def get_surface_waterways(self) -> List[Dict[str, Any]]:
        return self.surface_waterways

    def get_underground_drains(self) -> List[Dict[str, Any]]:
        return self.underground_swd_corridors

    def get_surcharge_status(self) -> Dict[str, Any]:
        """
        Returns hydraulic surcharge metrics.
        In the absence of live telemetry, returns explicit network_data_unavailable.
        """
        return {
            "status": "network_data_unavailable",
            "monitored_nodes_count": 0,
            "surcharge_nodes_count": 0,
            "backflow_nodes_count": 0,
            "utilization_rate": None,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": "SCADA / SWMM Ingestion Interface",
            "provenance_status": ProvenanceStatus.UNAVAILABLE.value,
            "message": "Continuous in-situ manhole pressure transducer and hydraulic conduit telemetry currently disconnected. Surcharge states cannot be scientifically inferred without sensor telemetry."
        }
