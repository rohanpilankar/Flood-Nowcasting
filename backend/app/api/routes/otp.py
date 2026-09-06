from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.schemas.otp import SendOtpRequest, VerifyOtpRequest, OtpResponse
from backend.app.services.otp_service import OtpService

router = APIRouter(prefix="/auth", tags=["Contact Verification (OTP)"])

@router.post("/send-email-otp", response_model=OtpResponse)
def send_email_otp(payload: SendOtpRequest, db: Session = Depends(get_db)):
    if "@" not in payload.target:
        raise HTTPException(status_code=400, detail="Invalid email address format.")
    res = OtpService.generate_and_send_otp(payload.target.lower().strip(), payload.purpose, db)
    return OtpResponse(
        success=res["success"],
        message=res["message"],
        target=res["target"],
        is_mock=True,
        verified=False
    )

@router.post("/verify-email-otp", response_model=OtpResponse)
def verify_email_otp(payload: VerifyOtpRequest, db: Session = Depends(get_db)):
    is_valid = OtpService.verify_otp(payload.target.lower().strip(), payload.otp_code.strip(), payload.purpose, db)
    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid or expired verification code.")
    return OtpResponse(
        success=True,
        message="Email successfully verified.",
        target=payload.target,
        is_mock=True,
        verified=True
    )

@router.post("/send-mobile-otp", response_model=OtpResponse)
def send_mobile_otp(payload: SendOtpRequest, db: Session = Depends(get_db)):
    if len(payload.target.strip()) < 8:
        raise HTTPException(status_code=400, detail="Invalid mobile number format.")
    res = OtpService.generate_and_send_otp(payload.target.strip(), payload.purpose, db)
    return OtpResponse(
        success=res["success"],
        message=res["message"],
        target=res["target"],
        is_mock=True,
        verified=False
    )

@router.post("/verify-mobile-otp", response_model=OtpResponse)
def verify_mobile_otp(payload: VerifyOtpRequest, db: Session = Depends(get_db)):
    is_valid = OtpService.verify_otp(payload.target.strip(), payload.otp_code.strip(), payload.purpose, db)
    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid or expired verification code.")
    return OtpResponse(
        success=True,
        message="Mobile number successfully verified.",
        target=payload.target,
        is_mock=True,
        verified=True
    )
