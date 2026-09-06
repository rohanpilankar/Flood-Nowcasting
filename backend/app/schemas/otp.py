from pydantic import BaseModel, Field

class SendOtpRequest(BaseModel):
    target: str = Field(..., description="Email address or mobile number")
    purpose: str = "REGISTRATION" # REGISTRATION, CONTACT_VERIFICATION, PASSWORD_RESET

class VerifyOtpRequest(BaseModel):
    target: str
    otp_code: str = Field(..., min_length=4, max_length=8)
    purpose: str = "REGISTRATION"

class OtpResponse(BaseModel):
    success: bool
    message: str
    target: str
    is_mock: bool = True
    verified: bool = False
