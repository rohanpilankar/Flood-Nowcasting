from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field

class UserLoginRequest(BaseModel):
    login_id: str = Field(..., description="Email or mobile number")
    password: str = Field(..., min_length=6)
    remember_me: bool = False

class EmergencyContactInput(BaseModel):
    full_name: str
    relationship_type: str = "Family"
    mobile: str

class AlertPreferencesInput(BaseModel):
    flood_alerts_enabled: bool = True
    route_warnings_enabled: bool = True
    high_risk_alerts_enabled: bool = True
    push_enabled: bool = True
    email_enabled: bool = False
    sms_enabled: bool = False
    location_alerts_enabled: bool = False
    emergency_contact_notifications_enabled: bool = False

class CitizenRegisterRequest(BaseModel):
    full_name: str = Field(..., min_length=2)
    email: EmailStr
    mobile: str = Field(..., min_length=10)
    password: str = Field(..., min_length=6)
    confirm_password: str
    preferred_language: str = "en"
    alert_preferences: Optional[AlertPreferencesInput] = None
    emergency_contact: Optional[EmergencyContactInput] = None

class UserPublicSchema(BaseModel):
    id: int
    full_name: str
    email: str
    mobile: str
    role: str
    status: str
    email_verified: bool
    mobile_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserPublicSchema

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class SavedLocationSchema(BaseModel):
    id: int
    label: str
    latitude: float
    longitude: float
    alerts_enabled: bool
    created_at: datetime

    class Config:
        from_attributes = True

class GovernmentProfilePublicSchema(BaseModel):
    organization_name: str
    department: str
    designation: str
    official_email: str
    official_phone: str
    jurisdiction: str
    verification_status: str

    class Config:
        from_attributes = True

class UserMeResponse(BaseModel):
    user: UserPublicSchema
    alert_preferences: Optional[AlertPreferencesInput] = None
    government_profile: Optional[GovernmentProfilePublicSchema] = None
    has_active_location: bool = False
    saved_locations: List[SavedLocationSchema] = []
