from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field

class GovernmentInviteRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=2)
    organization_name: str
    department: str
    designation: str
    official_phone: str
    jurisdiction: str = "Greater Mumbai"
    role: str = "GOVERNMENT_OPERATOR" # GOVERNMENT_VIEWER, GOVERNMENT_OPERATOR, GOVERNMENT_SUPERVISOR

class GovernmentVerifyRequest(BaseModel):
    status: str = Field(..., description="VERIFIED, SUSPENDED, PENDING")
    notes: Optional[str] = None

class GovernmentAuthorityItem(BaseModel):
    user_id: int
    full_name: str
    email: str
    role: str
    status: str
    organization_name: str
    department: str
    designation: str
    official_phone: str
    jurisdiction: str
    verification_status: str
    verified_at: Optional[datetime] = None
    created_at: datetime

class GovernmentDashboardMetrics(BaseModel):
    high_risk_zones_count: int
    critical_zones_count: int
    affected_roads_count: int
    active_alerts_count: int
    predicted_1h_risk_trend: str
    predicted_3h_risk_trend: str

    # Privacy-Preserving Aggregate Stats
    eligible_opted_in_citizens: int
    successfully_notified: int
    notifications_pending: int
    notifications_failed: int
