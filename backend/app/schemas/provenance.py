"""
Data Provenance and Observation Status Schemas
Guarantees scientific integrity and transparent data origin tracking across all feeds.
"""

from enum import Enum
from typing import Optional, Any
from pydantic import BaseModel, Field


class ProvenanceStatus(str, Enum):
    OBSERVED = "OBSERVED"
    FORECAST = "FORECAST"
    MODEL_PREDICTED = "MODEL_PREDICTED"
    DERIVED = "DERIVED"
    SIMULATED = "SIMULATED"
    UNAVAILABLE = "UNAVAILABLE"


class ProvenanceRecord(BaseModel):
    source: str = Field(..., description="Origin data system or sensor network (e.g. IMD Meenambakkam, GCC SWD GIS, XGBoost Baseline)")
    timestamp: str = Field(..., description="ISO-8601 observation or generation timestamp")
    status: ProvenanceStatus = Field(..., description="Physical status of the measurement")
    unit: Optional[str] = Field(None, description="Physical unit of measurement (e.g. mm, mm/h, %, m MSL)")
    confidence: Optional[float] = Field(None, description="Confidence score [0.0, 1.0] if probabilistic")
    notes: Optional[str] = Field(None, description="Contextual qualifications or scientific caveats")
