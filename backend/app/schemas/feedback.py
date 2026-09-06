from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

class CitizenFloodReportCreate(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    location_name: str = "Reported Location"
    observation_status: str = Field(..., description="YES, NO, NOT_SURE")
    water_level: str = Field(default="MEDIUM", description="LOW, MEDIUM, HIGH, NONE")
    description: Optional[str] = None
    photo_reference: Optional[str] = None
    linked_grid_id: Optional[str] = None
    linked_alert_id: Optional[int] = None

class CitizenFloodReportResponse(BaseModel):
    id: int
    user_id: int
    user_name: Optional[str] = None
    latitude: float
    longitude: float
    location_name: str
    observation_status: str
    water_level: str
    description: Optional[str]
    linked_grid_id: Optional[str]
    linked_alert_id: Optional[int]
    validation_status: str # UNVERIFIED, REVIEWED, VALIDATED, REJECTED
    admin_notes: Optional[str]
    reported_at: datetime
    reviewed_at: Optional[datetime]

    class Config:
        from_attributes = True

class ReportReviewRequest(BaseModel):
    validation_status: str = Field(..., description="VALIDATED, REJECTED, REVIEWED")
    admin_notes: Optional[str] = None

class GroundTruthEvaluationSummary(BaseModel):
    total_citizen_reports: int
    unverified_count: int
    validated_count: int
    rejected_count: int
    potential_true_positives: int
    potential_false_positives: int
    potential_false_negatives: int
    accuracy_alignment_pct: float
